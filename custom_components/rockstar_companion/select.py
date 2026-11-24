"""Select entity for switching catalog language on the fly."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .const import CONF_LANGUAGE_MODE, LANGUAGE_OPTIONS
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    async_add_entities([CatalogLanguageSelectEntity(entry.runtime_data)])


class CatalogLanguageSelectEntity(RockstarBaseEntity, SelectEntity):
    """Runtime selector for catalog language."""

    _attr_translation_key = "catalog_language"
    _attr_icon = "mdi:translate"
    _attr_options = LANGUAGE_OPTIONS

    def __init__(self, coordinator: RockstarCoordinator) -> None:
        """Initialize language selector."""
        super().__init__(coordinator, "select_catalog_language", device_scope="hub")

    @property
    def current_option(self) -> str:
        """Return currently configured catalog language mode."""
        return self.coordinator.data.language_mode

    async def async_select_option(self, option: str) -> None:
        """Update catalog language immediately."""
        if option in LANGUAGE_OPTIONS:
            await self.coordinator.async_set_flag(CONF_LANGUAGE_MODE, option)
