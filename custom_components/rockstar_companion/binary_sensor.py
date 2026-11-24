"""Binary sensor entities for Rockstar & Leonida Companion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .catalog.gta_vi import GTA6_ACHIEVEMENTS
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity
from .models import CompanionState


@dataclass(frozen=True, kw_only=True)
class RockstarBinaryDescription(BinarySensorEntityDescription):
    """Describe a Rockstar Companion binary sensor."""

    device_scope: str = "hub"
    value_fn: Callable[[CompanionState], bool | None]


BINARY_DESCRIPTIONS: tuple[RockstarBinaryDescription, ...] = (
    RockstarBinaryDescription(
        key="is_playing_rockstar",
        translation_key="is_playing_rockstar",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.is_playing_rockstar,
    ),
    RockstarBinaryDescription(
        key="is_playing_gta6",
        translation_key="is_playing_gta6",
        icon="mdi:gamepad-variant",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.is_playing_gta6,
    ),
    RockstarBinaryDescription(
        key="is_installed_ps5",
        translation_key="is_installed_ps5",
        icon="mdi:sony-playstation",
        value_fn=lambda d: d.is_installed_ps5,
    ),
    RockstarBinaryDescription(
        key="gta6_platinum_ready",
        translation_key="gta6_platinum_ready",
        device_scope="gta6",
        icon="mdi:trophy-award",
        value_fn=lambda d: all(
            ach.grade == "platinum" or ach.code in d.unlocked_achievements
            for ach in GTA6_ACHIEVEMENTS
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        RockstarBinaryEntity(coordinator, desc) for desc in BINARY_DESCRIPTIONS
    )


class RockstarBinaryEntity(RockstarBaseEntity, BinarySensorEntity):
    """Represent a Rockstar Companion binary sensor."""

    entity_description: RockstarBinaryDescription

    def __init__(
        self,
        coordinator: RockstarCoordinator,
        description: RockstarBinaryDescription,
    ) -> None:
        """Initialize binary sensor."""
        super().__init__(
            coordinator,
            f"binary_{description.key}",
            device_scope=description.device_scope,
        )
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return True if condition holds."""
        return self.entity_description.value_fn(self.coordinator.data)
