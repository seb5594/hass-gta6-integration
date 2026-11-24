"""Switch entities for Rockstar & Leonida Companion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .const import CONF_AUTO_SYNC, CONF_SPOILER_SHIELD
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity


@dataclass(frozen=True, kw_only=True)
class RockstarSwitchDescription(SwitchEntityDescription):
    """Describe a persistent feature toggle."""

    state_key: str


SWITCH_DESCRIPTIONS: tuple[RockstarSwitchDescription, ...] = (
    RockstarSwitchDescription(
        key="spoiler_shield",
        translation_key="spoiler_shield",
        icon="mdi:eye-off-outline",
        state_key=CONF_SPOILER_SHIELD,
    ),
    RockstarSwitchDescription(
        key="auto_sync_achievements",
        translation_key="auto_sync_achievements",
        icon="mdi:sync",
        state_key=CONF_AUTO_SYNC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coord = entry.runtime_data
    async_add_entities(
        RockstarSwitchEntity(coord, desc) for desc in SWITCH_DESCRIPTIONS
    )


class RockstarSwitchEntity(RockstarBaseEntity, SwitchEntity):
    """Persistent boolean control switch."""

    entity_description: RockstarSwitchDescription

    def __init__(
        self,
        coordinator: RockstarCoordinator,
        description: RockstarSwitchDescription,
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator, f"switch_{description.key}", device_scope="gta6")
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return toggle state."""
        return bool(getattr(self.coordinator.data, self.entity_description.state_key))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable feature."""
        await self.coordinator.async_set_flag(self.entity_description.state_key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable feature."""
        await self.coordinator.async_set_flag(self.entity_description.state_key, False)
