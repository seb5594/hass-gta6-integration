"""Read game presence from existing Home Assistant entities."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterator

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    GTA6_PS5_TITLE_IDS,
    GTA6_TITLE_REGEX,
    GTA6_XBOX_PACKAGES,
    GTA6_XBOX_PRODUCT_IDS,
    GTA6_XBOX_TITLE_IDS,
    KNOWN_INTEGRATION_DOMAINS,
    OTHER_ROCKSTAR_TITLE_REGEX,
    PLATFORM_MAP,
)
from .models import PlatformSnapshot

GTA6_TITLE = "Grand Theft Auto VI"
_GTA6_IDS = {
    identifier.casefold()
    for identifier in (
        GTA6_PS5_TITLE_IDS
        | GTA6_XBOX_PACKAGES
        | GTA6_XBOX_PRODUCT_IDS
        | GTA6_XBOX_TITLE_IDS
    )
}
_INACTIVE = {
    "",
    "unknown",
    "unavailable",
    "off",
    "offline",
    "standby",
    "idle",
    "none",
    "not_playing",
    "home",
    "away",
    "false",
    "stopped",
    "not_running",
}


def match_gta6(*candidates: object) -> str | None:
    """Return a matched GTA VI identifier or a canonical title match."""
    for raw in candidates:
        if not isinstance(raw, (str, int)):
            continue
        text = unicodedata.normalize("NFKC", str(raw)).strip()
        if text.casefold() in _GTA6_IDS:
            return text.upper()
        if re.fullmatch(
            r"[A-Z]{2}\d{4}-(PPSA01547|PPSA29660)_00-[A-Z0-9]{16}", text.upper()
        ):
            return text.upper().split("-")[1]
        # Allow a Windows process path as well as a title from a presence sensor.
        name = re.split(r"[/\\]", text.casefold())[-1].removesuffix(".exe")
        if GTA6_TITLE_REGEX.fullmatch(name) or name.strip("『』") in {
            "gta6",
            "gtavi",
            "grandtheftautovi",
            "playgta6",
            "グランド・セフト・オートvi",
        }:
            return "TITLE_MATCH_GTA6"
    return None


def discover_gaming_config_entries(hass: HomeAssistant) -> list[dict[str, str]]:
    """Return the configured gaming integrations available for selection."""
    return [
        {"entry_id": entry.entry_id, "domain": domain, "title": entry.title or domain}
        for domain in KNOWN_INTEGRATION_DOMAINS
        for entry in hass.config_entries.async_entries(domain)
        if not entry.disabled_by
    ]


def iter_linked_entities(
    hass: HomeAssistant, linked_entry_ids: list[str] | None, extra_entities: list[str]
) -> Iterator[tuple[str, str | None, str, str | None]]:
    """Yield account-level entities and any explicitly selected entities."""
    entries = {
        item["entry_id"]: item["domain"]
        for item in discover_gaming_config_entries(hass)
        if linked_entry_ids is None or item["entry_id"] in linked_entry_ids
    }
    registry = er.async_get(hass)
    extra = set(extra_entities)
    for entity_id in extra_entities:
        reg_item = registry.async_get(entity_id)
        if reg_item and reg_item.platform == DOMAIN:
            continue
        domain = reg_item.platform if reg_item else "custom_entities"
        yield (
            entity_id,
            reg_item.config_entry_id if reg_item else None,
            domain,
            (reg_item.translation_key if reg_item else None),
        )

    for reg_item in registry.entities.values():
        if (
            reg_item.entity_id not in extra
            and reg_item.config_entry_id in entries
            and reg_item.config_subentry_id is None
            and reg_item.disabled_by is None
            and reg_item.domain in {"media_player", "sensor"}
        ):
            yield (
                reg_item.entity_id,
                reg_item.config_entry_id,
                entries[reg_item.config_entry_id],
                reg_item.translation_key,
            )


def _platform(domain: str, state: State, matched: str | None) -> str:
    if domain == "playstation_network":
        if matched in GTA6_PS5_TITLE_IDS or state.entity_id.endswith("_ps5"):
            return "ps5"
        if state.entity_id.endswith("_ps4"):
            return "ps4"
    if domain == "gaming_status":
        platform = state.attributes.get("active_platform_key")
        if platform in {"ps4", "ps5", "xbox", "pc"}:
            return platform
        if platform in {"psn", "playstation"}:
            return "ps5" if matched in GTA6_PS5_TITLE_IDS else "psn"
        if platform in {"steam", "playnite", "gsa", "epic", "rockstar"}:
            return "pc"
    if domain == "xbox" and str(state.attributes.get("platform")).casefold() == "pc":
        return "pc"
    return PLATFORM_MAP.get(domain, "custom")


def collect_platform_snapshots(
    hass: HomeAssistant, linked_entry_ids: list[str] | None, extra_entities: list[str]
) -> list[PlatformSnapshot]:
    """Read each source independently so title, IDs and activity stay together."""
    snapshots = []
    extra = set(extra_entities)
    for entity_id, entry_id, domain, translation_key in iter_linked_entities(
        hass, linked_entry_ids, extra_entities
    ):
        state = hass.states.get(entity_id)
        if (
            state is None
            or state.state.strip().casefold().replace(" ", "_") in _INACTIVE
        ):
            continue
        attrs = state.attributes
        snap = PlatformSnapshot(
            domain=domain,
            platform_family=_platform(domain, state, None),
            entry_id=entry_id,
            source_entity=entity_id,
        )
        titles = attrs.get("titles")
        if domain == "ps5" and isinstance(titles, list):
            snap.installed_gta6 = any(
                isinstance(item, dict)
                and match_gta6(item.get("title_id"), item.get("name"))
                for item in titles
            )
            snapshots.append(snap)
            continue

        if state.domain == "media_player":
            if state.state not in {"playing", "on", "paused"}:
                continue
            title = attrs.get("media_title") or attrs.get("app_name")
        elif (
            entity_id in extra
            or translation_key == "now_playing"
            or (
                translation_key == "account"
                and domain == "steam_online"
                and attrs.get("game")
            )
            or (
                domain in {"gaming_status", "playnite_connect", "playnite_web_mqtt"}
                and (attrs.get("current_game") or attrs.get("game"))
            )
        ):
            title = (
                attrs.get("current_game")
                or attrs.get("game")
                or attrs.get("media_title")
                or attrs.get("process_name")
                or state.state
            )
        else:
            continue

        matched = match_gta6(
            title,
            attrs.get("media_content_id"),
            attrs.get("title_id"),
            attrs.get("product_id"),
            attrs.get("package_name"),
        )
        if not matched and not (
            isinstance(title, str) and OTHER_ROCKSTAR_TITLE_REGEX.fullmatch(title)
        ):
            continue
        snap.active = True
        snap.title = GTA6_TITLE if matched else title
        snap.matched_id = matched
        snap.is_gta6 = bool(matched)
        snap.is_rockstar = True
        snap.platform_family = _platform(domain, state, matched)
        snap.artwork_url = attrs.get("entity_picture") or attrs.get("game_cover_art")
        snapshots.append(snap)
    return snapshots
