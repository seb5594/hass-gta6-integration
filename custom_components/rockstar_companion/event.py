"""Native EventEntities for game lifecycle and achievement automations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity


@dataclass(frozen=True, kw_only=True)
class RockstarEventDescription(EventEntityDescription):
    """Describe an EventEntity channel."""

    channel: str
    device_scope: str


EVENT_DESCRIPTIONS: tuple[RockstarEventDescription, ...] = (
    RockstarEventDescription(
        key="game_lifecycle",
        translation_key="game_lifecycle",
        channel="game_lifecycle",
        device_scope="hub",
        event_types=["game_started", "game_stopped", "platform_switched"],
    ),
    RockstarEventDescription(
        key="achievement_events",
        translation_key="achievement_events",
        channel="achievement_events",
        device_scope="gta6",
        event_types=["achievement_unlocked", "milestone_reached"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EventEntities."""
    coord = entry.runtime_data
    async_add_entities(RockstarEventEntity(coord, desc) for desc in EVENT_DESCRIPTIONS)


class RockstarEventEntity(RockstarBaseEntity, EventEntity):
    """Emit structured events to Home Assistant UI triggers."""

    entity_description: RockstarEventDescription

    def __init__(
        self,
        coordinator: RockstarCoordinator,
        description: RockstarEventDescription,
    ) -> None:
        """Initialize event entity."""
        super().__init__(
            coordinator,
            f"event_{description.key}",
            device_scope=description.device_scope,
        )
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        """Register coordinator event callback."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.register_event_listener(self._on_coordinator_event)
        )

    @callback
    def _on_coordinator_event(
        self, channel: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Trigger HA EventEntity when channel matches."""
        if channel == self.entity_description.channel:
            self._trigger_event(event_type, payload)
            self.async_write_ha_state()
