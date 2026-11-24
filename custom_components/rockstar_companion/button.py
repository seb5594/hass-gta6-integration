"""Button entities for Rockstar & Leonida Companion."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity


@dataclass(frozen=True, kw_only=True)
class RockstarButtonDescription(ButtonEntityDescription):
    """Describe an action button."""

    press_fn: Callable[[RockstarCoordinator], Awaitable[None]]


BUTTON_DESCRIPTIONS: tuple[RockstarButtonDescription, ...] = (
    RockstarButtonDescription(
        key="sync_integrations",
        translation_key="sync_integrations",
        icon="mdi:refresh",
        press_fn=lambda c: c.async_sync_now(),
    ),
    RockstarButtonDescription(
        key="reset_session_timer",
        translation_key="reset_session_timer",
        icon="mdi:timer-refresh-outline",
        press_fn=lambda c: c.async_reset_session_timer(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coord = entry.runtime_data
    async_add_entities(
        RockstarButtonEntity(coord, desc) for desc in BUTTON_DESCRIPTIONS
    )


class RockstarButtonEntity(RockstarBaseEntity, ButtonEntity):
    """Action trigger button."""

    entity_description: RockstarButtonDescription

    def __init__(
        self,
        coordinator: RockstarCoordinator,
        description: RockstarButtonDescription,
    ) -> None:
        """Initialize button."""
        super().__init__(coordinator, f"button_{description.key}", device_scope="hub")
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle button press."""
        await self.entity_description.press_fn(self.coordinator)
