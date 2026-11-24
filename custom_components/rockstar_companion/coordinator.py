"""Coordinate game presence, persistent progress and Newswire updates."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from time import monotonic
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.file import write_utf8_file_atomic

from .adapters import (
    collect_platform_snapshots,
    discover_gaming_config_entries,
    iter_linked_entities,
    match_gta6,
)
from .catalog.gta_vi import (
    ACHIEVEMENT_BY_CODE,
    CHECKLIST_BY_ID,
    GTA6_ACHIEVEMENTS,
    GTA6_CHECKLIST_ITEMS,
    GTA6_STORY_TARGET,
    GTA6_STORY_WEIGHT,
)
from .catalog.locale import catalog_language
from .const import (
    CONF_AUTO_DISCOVER,
    CONF_AUTO_SYNC,
    CONF_EXTRA_ENTITIES,
    CONF_GAMING_STATUS_PLAYER,
    CONF_LANGUAGE_MODE,
    CONF_LINKED_ENTRIES,
    CONF_NEWSWIRE_URL,
    CONF_SCAN_INTERVAL,
    CONF_SPOILER_SHIELD,
    DEFAULT_NEWSWIRE_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_ACHIEVEMENT_UNLOCKED,
    EVENT_GAME_SESSION,
    GTA6_100_BENCHMARK_HOURS,
    GTA6_PLATINUM_BENCHMARK_HOURS,
    LANG_AUTO,
    STORAGE_VERSION,
)
from .models import CompanionState, NewswireItem
from .newswire import async_fetch_newswire

_LOGGER = logging.getLogger(__name__)
_PLAYTIME_SAVE_INTERVAL = 60
_PREFERENCES = {
    CONF_SPOILER_SHIELD: True,
    CONF_AUTO_SYNC: False,
    CONF_LANGUAGE_MODE: LANG_AUTO,
}


class RockstarCoordinator(DataUpdateCoordinator[CompanionState]):
    """Track existing game entities and local GTA VI progress."""

    hub_device_id: str

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.settings = {**entry.data, **entry.options}
        self._linked_entries = self.settings.get(CONF_LINKED_ENTRIES) or (
            None if self.settings.get(CONF_AUTO_DISCOVER, True) else []
        )
        self._refresh_lock = asyncio.Lock()
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=int(
                    self.settings.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                )
            ),
        )
        self.config_entry = entry
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}", atomic_writes=True
        )
        self._persisted: dict[str, Any] = {}
        self._save_lock = asyncio.Lock()
        self._last_save = monotonic()
        self._state_unsub: Callable[[], None] | None = None
        self._watched: set[str] = set()
        self._event_callbacks: list[Callable[[str, str, dict[str, Any]], None]] = []
        self._session_started_at: float | None = None
        self._last_tick: float | None = None
        self._total_playtime = 0.0
        self._next_feed_fetch = 0.0
        self._newswire: NewswireItem | None = None

    async def _async_setup(self) -> None:
        """Load progress and apply explicitly changed configuration preferences."""
        loaded = await self._store.async_load()
        self._persisted = loaded if isinstance(loaded, dict) else {}
        self._persisted.setdefault("unlocked_achievements", {})
        self._persisted.setdefault("checklist_progress", {})
        self._persisted.setdefault("story_missions_completed", 0)
        self._persisted.setdefault("total_playtime_seconds", 0)
        self._persisted.pop("last_xbox_gamerscore", None)
        self._total_playtime = float(self._persisted["total_playtime_seconds"])

        previous = self._persisted.get("_last_options", {})
        for key, default in _PREFERENCES.items():
            if key not in self._persisted or (
                key in self.settings and self.settings[key] != previous.get(key)
            ):
                self._persisted[key] = self.settings.get(key, default)
        self._persisted["_last_options"] = {
            key: self.settings[key] for key in _PREFERENCES if key in self.settings
        }
        await self._async_save()

    @callback
    def async_start_listeners(self) -> None:
        """Listen for presence changes, late sources and explicit achievement events."""
        self._sync_state_listener()
        self.config_entry.async_on_unload(self._remove_state_listener)
        for event_type in (er.EVENT_ENTITY_REGISTRY_UPDATED, EVENT_CORE_CONFIG_UPDATE):
            self.config_entry.async_on_unload(
                self.hass.bus.async_listen(
                    event_type, self._handle_registry_or_language
                )
            )
        self.config_entry.async_on_unload(
            self.hass.bus.async_listen(
                "gaming_status_achievement_unlocked", self._handle_external_achievement
            )
        )

    @callback
    def _sync_state_listener(self) -> None:
        watched = {
            entity_id
            for entity_id, *_ in iter_linked_entities(
                self.hass,
                self._linked_entries,
                self.settings.get(CONF_EXTRA_ENTITIES, []),
            )
        }
        if watched == self._watched:
            return
        self._remove_state_listener()
        self._watched = watched
        if watched:
            self._state_unsub = async_track_state_change_event(
                self.hass, watched, self._handle_presence_change
            )

    @callback
    def _remove_state_listener(self) -> None:
        if self._state_unsub is not None:
            self._state_unsub()
            self._state_unsub = None
        self._watched.clear()

    @callback
    def _handle_presence_change(self, _event: Event) -> None:
        self.config_entry.async_create_task(
            self.hass, self.async_request_refresh(), "rockstar presence refresh"
        )

    @callback
    def _handle_registry_or_language(self, event: Event) -> None:
        previous = self._watched.copy()
        self._sync_state_listener()
        if previous != self._watched or event.event_type == EVENT_CORE_CONFIG_UPDATE:
            self._handle_presence_change(event)

    async def _handle_external_achievement(self, event: Event) -> None:
        """Import achievement events carrying an explicit GTA VI game and name."""
        if not self._persisted[CONF_AUTO_SYNC]:
            return
        payload = event.data
        player = self.settings.get(CONF_GAMING_STATUS_PLAYER, "").strip().casefold()
        if player and str(payload.get("player", "")).strip().casefold() != player:
            return
        if not match_gta6(
            payload.get("game"),
            payload.get("game_name"),
            payload.get("game_title"),
            payload.get("game_id"),
            payload.get("title_id"),
            payload.get("product_id"),
        ):
            return
        label = (
            payload.get("achievement_name")
            or payload.get("achievement")
            or payload.get("title")
        )
        if not isinstance(label, str):
            return
        needle = label.strip().casefold()
        for achievement in GTA6_ACHIEVEMENTS:
            if needle in (
                achievement.code,
                achievement.name_en.casefold(),
                achievement.name_de.casefold(),
            ):
                await self.async_set_achievement_state(
                    achievement.code, True, event.event_type
                )
                break

    @callback
    def register_event_listener(
        self, cb: Callable[[str, str, dict[str, Any]], None]
    ) -> Callable[[], None]:
        """Subscribe an event entity."""
        self._event_callbacks.append(cb)

        @callback
        def remove() -> None:
            self._event_callbacks.remove(cb)

        return remove

    @callback
    def _emit_event(
        self, channel: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        for cb in tuple(self._event_callbacks):
            cb(channel, event_type, payload)
        bus_name = (
            EVENT_ACHIEVEMENT_UNLOCKED
            if channel == "achievement_events"
            else EVENT_GAME_SESSION
        )
        self.hass.bus.async_fire(bus_name, {"event_type": event_type, **payload})

    def resolve_language(self) -> str:
        """Resolve the catalog language from the manual choice or HA settings."""
        mode = self._persisted[CONF_LANGUAGE_MODE]
        return catalog_language(
            self.hass.config.language if mode == LANG_AUTO else mode
        )

    async def _async_update_data(self) -> CompanionState:
        """Refresh linked game states and calculate progress."""
        async with self._refresh_lock:
            return await self._async_collect_data()

    async def _async_collect_data(self) -> CompanionState:
        feed = self.settings.get(CONF_NEWSWIRE_URL)
        if feed and monotonic() >= self._next_feed_fetch:
            self._next_feed_fetch = monotonic() + DEFAULT_NEWSWIRE_INTERVAL
            self._newswire = (
                await async_fetch_newswire(self.hass, feed) or self._newswire
            )

        linked = self._linked_entries
        snapshots = collect_platform_snapshots(
            self.hass, linked, self.settings.get(CONF_EXTRA_ENTITIES, [])
        )
        active = [snapshot for snapshot in snapshots if snapshot.active]
        primary = next((snapshot for snapshot in active if snapshot.is_gta6), None)
        primary = primary or (active[0] if active else None)
        platforms = {snapshot.platform_family for snapshot in active}
        if platforms & {"ps4", "ps5"}:
            platforms.discard("psn")
        platform = "multi" if len(platforms) > 1 else next(iter(platforms), "idle")
        now = monotonic()
        ended_at = self._session_started_at if not active else None
        self._tick(now, bool(active))
        if (
            now - self._last_save >= _PLAYTIME_SAVE_INTERVAL
            and int(self._total_playtime) != self._persisted["total_playtime_seconds"]
        ):
            await self._async_save()

        title = primary.title if primary else None
        self._schedule_lifecycle(
            platform,
            title,
            bool(primary and primary.is_gta6),
            int(now - ended_at) if ended_at is not None else None,
        )
        completion, sections = self._calculate_completion()
        unlocked = {
            code: stamp
            for code, stamp in self._persisted["unlocked_achievements"].items()
            if code in ACHIEVEMENT_BY_CODE
        }
        domains = {
            item["domain"]
            for item in discover_gaming_config_entries(self.hass)
            if linked is None or item["entry_id"] in linked
        }
        if self.settings.get(CONF_EXTRA_ENTITIES):
            domains.add("custom_entities")

        return CompanionState(
            active_platform=platform,
            now_playing=title,
            is_playing_rockstar=bool(active),
            is_playing_gta6=bool(primary and primary.is_gta6),
            is_installed_ps5=max(
                (s.installed_gta6 for s in snapshots if s.installed_gta6 is not None),
                default=None,
            ),
            artwork_url=primary.artwork_url if primary else None,
            matched_id=primary.matched_id if primary else None,
            source_entity=primary.source_entity if primary else None,
            discovered_sources=sorted(domains),
            snapshots=snapshots,
            total_playtime_seconds=int(self._total_playtime),
            current_session_seconds=int(now - self._session_started_at)
            if self._session_started_at is not None
            else 0,
            unlocked_achievements=unlocked,
            checklist_progress=dict(self._persisted["checklist_progress"]),
            story_missions_completed=self._persisted["story_missions_completed"],
            completion_percent=completion,
            section_breakdown=sections,
            gamerscore_earned=sum(
                ACHIEVEMENT_BY_CODE[code].gamerscore for code in unlocked
            ),
            latest_achievement_id=max(unlocked, key=unlocked.__getitem__, default=None),
            spoiler_shield=self._persisted[CONF_SPOILER_SHIELD],
            auto_sync_achievements=self._persisted[CONF_AUTO_SYNC],
            language_mode=self._persisted[CONF_LANGUAGE_MODE],
            resolved_language=self.resolve_language(),
            newswire=self._newswire,
        )

    def _tick(self, now: float, active: bool) -> None:
        if self._last_tick is not None:
            # Do not count long gaps where HA was suspended or updates failed.
            elapsed = now - self._last_tick
            if elapsed <= 2 * self.update_interval.total_seconds() + 10:
                self._total_playtime += elapsed
        if active and self._session_started_at is None:
            self._session_started_at = now
        if not active:
            self._session_started_at = None
        self._last_tick = now if active else None

    def _schedule_lifecycle(
        self,
        platform: str,
        title: str | None,
        is_gta6: bool,
        duration_seconds: int | None,
    ) -> None:
        old = self.data
        if old is None:
            return
        if title and (not old.now_playing or title != old.now_playing):
            event_type = "game_started"
        elif not title and old.now_playing:
            event_type = "game_stopped"
        elif platform != old.active_platform:
            event_type = "platform_switched"
        else:
            return
        payload = {
            "platform": platform,
            "title": title or old.now_playing,
            "is_gta6": is_gta6 if title else old.is_playing_gta6,
            "previous_platform": old.active_platform,
            "previous_title": old.now_playing,
        }
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds
        self.hass.loop.call_soon(
            self._emit_event, "game_lifecycle", event_type, payload
        )

    def _calculate_completion(self) -> tuple[float, dict[str, float]]:
        story_done = max(
            0, min(self._persisted["story_missions_completed"], GTA6_STORY_TARGET)
        )
        sections = {
            "story": story_done / GTA6_STORY_TARGET * GTA6_STORY_WEIGHT,
            "tasks": 0.0,
            "exploration": 0.0,
            "discovery": 0.0,
        }
        progress = self._persisted["checklist_progress"]
        for item in GTA6_CHECKLIST_ITEMS:
            done = min(max(progress.get(item.item_id, 0), 0), item.target)
            sections[item.section] += done / item.target * item.weight_pct

        full = story_done == GTA6_STORY_TARGET and all(
            progress.get(item.item_id, 0) >= item.target
            for item in GTA6_CHECKLIST_ITEMS
        )
        total = 100.0 if full else min(99.99, round(sum(sections.values()), 2))
        return total, {section: round(value, 2) for section, value in sections.items()}

    async def _async_save(self) -> None:
        async with self._save_lock:
            self._persisted["total_playtime_seconds"] = int(self._total_playtime)
            await self._store.async_save(deepcopy(self._persisted))
            self._last_save = monotonic()

    async def async_save_on_unload(self) -> None:
        """Persist the final tracked playtime on unload."""
        self._tick(monotonic(), False)
        await self._async_save()

    async def async_set_achievement_state(
        self, code: str, unlocked: bool, source: str = "manual"
    ) -> None:
        """Persist and publish a changed achievement."""
        achievement = ACHIEVEMENT_BY_CODE.get(code)
        if achievement is None:
            return
        progress = self._persisted["unlocked_achievements"]
        if unlocked == (code in progress):
            return
        if unlocked:
            progress[code] = datetime.now(UTC).isoformat()
        else:
            progress.pop(code)
        await self._async_save()
        await self.async_refresh()
        if unlocked:
            self._emit_event(
                "achievement_events",
                "achievement_unlocked",
                {
                    "code": code,
                    "name": achievement.localized_name(self.resolve_language()),
                    "grade": achievement.grade,
                    "gamerscore": achievement.gamerscore,
                    "hidden": achievement.hidden,
                    "source": source,
                },
            )

    async def async_set_story_missions(self, count: int) -> None:
        """Set the number of completed main story missions."""
        self._persisted["story_missions_completed"] = max(
            0, min(int(count), GTA6_STORY_TARGET)
        )
        await self._async_save()
        await self.async_refresh()

    async def async_set_checklist_progress(self, item_id: str, value: int) -> None:
        """Persist checklist progress and announce newly completed items."""
        item = CHECKLIST_BY_ID[item_id]
        clamped = max(0, min(int(value), item.target))
        progress = self._persisted["checklist_progress"]
        if clamped == progress.get(item_id, 0):
            return
        progress[item_id] = clamped
        await self._async_save()
        await self.async_refresh()
        if clamped == item.target:
            self._emit_event(
                "achievement_events",
                "milestone_reached",
                {
                    "item_id": item_id,
                    "name": item.localized_name(self.resolve_language()),
                },
            )

    async def async_set_flag(self, key: str, value: Any) -> None:
        """Save a runtime preference and refresh its entities."""
        self._persisted[key] = value
        await self._async_save()
        await self.async_refresh()

    async def async_reset_session_timer(self) -> None:
        """Reset the active timer while keeping total playtime."""
        now = monotonic()
        self._tick(now, self.data.is_playing_rockstar)
        if self.data.is_playing_rockstar:
            self._session_started_at = now
        await self.async_refresh()

    async def async_sync_now(self) -> None:
        """Refresh game presence and the optional feed immediately."""
        self._next_feed_fetch = 0
        await self.async_refresh()

    async def async_export_progress(self) -> str:
        """Write a progress backup in the HA configuration folder."""
        filename = f"{DOMAIN}_progress.json"
        async with self._save_lock:
            snapshot = deepcopy(self._persisted)
            snapshot.pop("_last_options", None)
            snapshot["total_playtime_seconds"] = int(self._total_playtime)
            await self.hass.async_add_executor_job(
                write_utf8_file_atomic,
                self.hass.config.path(filename),
                json.dumps(
                    {
                        "exported_at": datetime.now(UTC).isoformat(),
                        "progress": snapshot,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                True,
            )
        return filename

    def estimate_remaining_hours(self, *, platinum: bool = False) -> float:
        """Estimate remaining time from community guide benchmarks."""
        if platinum:
            ratio = len(self.data.unlocked_achievements) / len(GTA6_ACHIEVEMENTS)
            return round(GTA6_PLATINUM_BENCHMARK_HOURS * (1 - ratio), 1)
        return round(
            GTA6_100_BENCHMARK_HOURS * (1 - self.data.completion_percent / 100), 1
        )
