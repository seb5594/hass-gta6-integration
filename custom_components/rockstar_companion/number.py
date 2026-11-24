"""Number entities for Rockstar & Leonida Companion."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .catalog.gta_vi import GTA6_STORY_TARGET
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    async_add_entities([StoryMissionsNumberEntity(entry.runtime_data)])


class StoryMissionsNumberEntity(RockstarBaseEntity, NumberEntity):
    """Number input for completed GTA VI main story missions (0..109 = 50% weight)."""

    _attr_translation_key = "story_missions_completed"
    _attr_icon = "mdi:book-open-page-variant"
    _attr_native_min_value = 0
    _attr_native_max_value = GTA6_STORY_TARGET
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: RockstarCoordinator) -> None:
        """Initialize story counter."""
        super().__init__(coordinator, "number_story_missions", device_scope="gta6")

    @property
    def native_value(self) -> float:
        """Return completed story mission count."""
        return float(self.coordinator.data.story_missions_completed)

    async def async_set_native_value(self, value: float) -> None:
        """Update story mission count."""
        await self.coordinator.async_set_story_missions(int(value))
