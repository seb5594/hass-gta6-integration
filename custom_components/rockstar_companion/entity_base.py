"""Shared base entity and DeviceInfo helpers."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RockstarCoordinator


def build_hub_device(entry_id: str) -> DeviceInfo:
    """Create DeviceInfo for the central Rockstar & Leonida Hub."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_hub")},
        name="Rockstar & Leonida Hub",
    )


def build_gta6_device(entry_id: str, hub_device_id: str) -> DeviceInfo:
    """Create DeviceInfo for the GTA VI companion device."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_gta6")},
        via_device_id=hub_device_id,
        name="Grand Theft Auto VI — Leonida Tracker",
        configuration_url="https://www.rockstargames.com/VI",
    )


class RockstarBaseEntity(CoordinatorEntity[RockstarCoordinator]):
    """Common base class for all Rockstar & Leonida entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RockstarCoordinator,
        unique_suffix: str,
        *,
        device_scope: str = "hub",
    ) -> None:
        """Bind entity to coordinator and target DeviceInfo."""
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{unique_suffix}"
        self._attr_device_info = (
            build_gta6_device(entry_id, coordinator.hub_device_id)
            if device_scope == "gta6"
            else build_hub_device(entry_id)
        )
