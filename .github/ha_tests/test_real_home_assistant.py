"""Config flow, entities and automation actions on a real Home Assistant Core."""

import json
from pathlib import Path

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.rockstar_companion.catalog.gta_vi import (
    GTA6_ACHIEVEMENTS,
    GTA6_CHECKLIST_ITEMS,
    GTA6_STORY_TARGET,
)
from custom_components.rockstar_companion.const import DOMAIN

GAME_SOURCE = "sensor.game_title"


def entity_id(hass, platform, entry, suffix):
    return er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{entry.entry_id}_{suffix}"
    )


async def setup_entry(hass, data=None):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=data or {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    return entry


async def test_user_flow_creates_a_single_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    again = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert again["type"] == "abort" and again["reason"] == "already_configured"


async def test_game_start_and_stale_attributes(hass):
    entry = await setup_entry(hass, {"extra_entities": [GAME_SOURCE]})
    ids = er.async_get(hass)
    assert len(er.async_entries_for_config_entry(ids, entry.entry_id)) == 25
    playing = entity_id(hass, "binary_sensor", entry, "binary_is_playing_gta6")
    lifecycle = entity_id(hass, "event", entry, "event_game_lifecycle")

    hass.states.async_set(GAME_SOURCE, "GTA 6")
    await hass.async_block_till_done()
    assert hass.states.get(playing).state == "on"
    assert hass.states.get(lifecycle).attributes["event_type"] == "game_started"
    assert hass.states.get(lifecycle).attributes["is_gta6"] is True

    hass.states.async_set(GAME_SOURCE, "offline", {"game": "GTA 6"})
    await entry.runtime_data.async_sync_now()
    await hass.async_block_till_done()
    assert hass.states.get(playing).state == "off"
    assert hass.states.get(lifecycle).attributes["event_type"] == "game_stopped"
    assert isinstance(hass.states.get(lifecycle).attributes["duration_seconds"], int)

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_spoilers_catalog_language_actions_and_reload(hass, tmp_path):
    hass.config.config_dir = str(tmp_path)
    entry = await setup_entry(
        hass, {"auto_sync_achievements": True, "gaming_status_player": "Lucia"}
    )
    todo = entity_id(hass, "todo", entry, "todo_gta6_trophy_list")
    language = entity_id(hass, "select", entry, "select_catalog_language")

    async def get_items():
        result = await hass.services.async_call(
            "todo",
            "get_items",
            {"entity_id": todo},
            blocking=True,
            return_response=True,
        )
        return result[todo]["items"]

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": language, "option": "fr"},
        blocking=True,
    )
    item = (await get_items())[1]
    assert item["summary"] == "#02 Trophée caché"
    assert item["uid"] == "trophy-02"

    for game, player in (
        ("Different Game", "Lucia"),
        ("Grand Theft Auto VI", "Jason"),
        ("グランド・セフト・オートVI", "lucia"),
    ):
        hass.bus.async_fire(
            "gaming_status_achievement_unlocked",
            {"game": game, "player": player, "achievement": "Just Like Paradise"},
        )
        await hass.async_block_till_done()
        assert (
            "just_like_paradise" in entry.runtime_data.data.unlocked_achievements
        ) == (player == "lucia")
    item = (await get_items())[1]
    assert item["status"] == "completed"
    assert item["description"] == "Terminez Gone Fishing."

    await hass.services.async_call(
        DOMAIN,
        "set_checklist_progress",
        {"item_id": "stunts", "value": 99},
        blocking=True,
    )
    response = await hass.services.async_call(
        DOMAIN, "export_progress", {}, blocking=True, return_response=True
    )
    backup = json.loads(Path(hass.config.path(response["filename"])).read_text())
    assert backup["progress"]["checklist_progress"]["stunts"] == 99

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.data.unlocked_achievements.keys() == {
        "just_like_paradise"
    }
    assert entry.runtime_data.data.checklist_progress["stunts"] == 99
    assert entry.runtime_data.data.language_mode == "fr"


async def test_catalog_totals_and_native_translations(hass):
    assert len(GTA6_ACHIEVEMENTS) == 55
    assert sum(a.hidden for a in GTA6_ACHIEVEMENTS) == 28
    assert sum(a.gamerscore for a in GTA6_ACHIEVEMENTS) == 1000
    assert len(GTA6_CHECKLIST_ITEMS) == 34

    entry = await setup_entry(hass)
    coordinator = entry.runtime_data
    await coordinator.async_set_story_missions(GTA6_STORY_TARGET)
    assert coordinator.data.completion_percent == 50
    for item in GTA6_CHECKLIST_ITEMS:
        await coordinator.async_set_checklist_progress(item.item_id, item.target)
    assert coordinator.data.completion_percent == 100
    await coordinator.async_set_checklist_progress("marked_bills_fenced", 249999)
    assert coordinator.data.completion_percent < 100
    german = await async_get_translations(hass, "de", "entity", {DOMAIN})
    assert "component.rockstar_companion.entity.sensor.active_platform.name" in german


async def test_linked_platforms_share_session_and_follow_source_registry(hass):
    """Detect renamed presence sensors and ignore stale states."""
    entry = await setup_entry(hass)
    registry = er.async_get(hass)
    xbox = MockConfigEntry(domain="xbox", unique_id="xbox-account")
    xbox.add_to_hass(hass)
    psn = MockConfigEntry(domain="playstation_network", unique_id="psn-account")
    psn.add_to_hass(hass)
    xbox_sensor = registry.async_get_or_create(
        "sensor",
        "xbox",
        "xbox-current-game",
        config_entry=xbox,
        suggested_object_id="jugando",
        translation_key="now_playing",
    )
    playstation = registry.async_get_or_create(
        "media_player",
        "playstation_network",
        "psn-account_ps5",
        config_entry=psn,
        suggested_object_id="salon",
    )
    hass.states.async_set(xbox_sensor.entity_id, "GTA 6")
    hass.states.async_set(
        playstation.entity_id, "playing", {"media_content_id": "PPSA01547_00"}
    )
    await hass.async_block_till_done()
    await entry.runtime_data.async_sync_now()
    assert entry.runtime_data.data.active_platform == "multi"
    assert entry.runtime_data.data.is_playing_gta6

    hass.states.async_set(xbox_sensor.entity_id, "unavailable", {"game": "GTA 6"})
    await entry.runtime_data.async_sync_now()
    assert entry.runtime_data.data.active_platform == "ps5"

    hass.states.async_set(
        playstation.entity_id, "off", {"media_content_id": "PPSA01547_00"}
    )
    await entry.runtime_data.async_sync_now()
    assert entry.runtime_data.data.active_platform == "idle"
