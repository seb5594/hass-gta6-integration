"""Set up Rockstar & Leonida Companion."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .catalog.gta_vi import ACHIEVEMENT_BY_CODE, CHECKLIST_BY_ID
from .const import (
    ATTR_ACHIEVEMENT_ID,
    ATTR_ITEM_ID,
    ATTR_SOURCE,
    ATTR_VALUE,
    DOMAIN,
    SERVICE_EXPORT_PROGRESS,
    SERVICE_SET_CHECKLIST,
    SERVICE_SYNC_NOW,
    SERVICE_UNLOCK_ACHIEVEMENT,
)
from .coordinator import RockstarCoordinator
from .entity_base import build_hub_device

type RockstarConfigEntry = ConfigEntry[RockstarCoordinator]

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.TODO,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.EVENT,
]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register actions before config entries are loaded."""

    def get_coordinator() -> RockstarCoordinator:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="no_entry"
            )
        return entries[0].runtime_data

    async def sync_now(call: ServiceCall) -> None:
        await get_coordinator().async_sync_now()

    async def unlock(call: ServiceCall) -> None:
        code = call.data[ATTR_ACHIEVEMENT_ID].strip()
        if code not in ACHIEVEMENT_BY_CODE:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="unknown_achievement"
            )
        await get_coordinator().async_set_achievement_state(
            code, True, call.data[ATTR_SOURCE]
        )

    async def set_checklist(call: ServiceCall) -> None:
        item_id = call.data[ATTR_ITEM_ID].strip()
        if item_id not in CHECKLIST_BY_ID:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="unknown_checklist_item"
            )
        await get_coordinator().async_set_checklist_progress(
            item_id, call.data[ATTR_VALUE]
        )

    async def export_progress(call: ServiceCall) -> dict[str, str]:
        return {"filename": await get_coordinator().async_export_progress()}

    hass.services.async_register(DOMAIN, SERVICE_SYNC_NOW, sync_now)
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNLOCK_ACHIEVEMENT,
        unlock,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ACHIEVEMENT_ID): cv.string,
                vol.Optional(ATTR_SOURCE, default="service"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CHECKLIST,
        set_checklist,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ITEM_ID): cv.string,
                vol.Required(ATTR_VALUE): vol.All(vol.Coerce(int), vol.Range(min=0)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_PROGRESS,
        export_progress,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: RockstarConfigEntry) -> None:
    """Load the coordinator and entity platforms."""
    coordinator = RockstarCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hub = build_hub_device(entry.entry_id)
    coordinator.hub_device_id = (
        dr.async_get(hass)
        .async_get_or_create(
            config_entry_id=entry.entry_id, identifiers=hub.identifiers, name=hub.name
        )
        .id
    )
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start_listeners()


async def async_unload_entry(hass: HomeAssistant, entry: RockstarConfigEntry) -> None:
    """Unload entity platforms and flush playtime."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="unload_failed"
        )
    await entry.runtime_data.async_save_on_unload()
