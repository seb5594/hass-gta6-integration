"""Sensor entities for Rockstar & Leonida Companion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .catalog.gta_vi import ACHIEVEMENT_BY_CODE, GTA6_ACHIEVEMENTS
from .const import PLATFORM_STATES
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity
from .models import CompanionState


@dataclass(frozen=True, kw_only=True)
class RockstarSensorDescription(SensorEntityDescription):
    """Describe a Rockstar Companion sensor."""

    device_scope: str = "hub"
    value_fn: Callable[[RockstarCoordinator, CompanionState], Any]
    attrs_fn: Callable[[RockstarCoordinator, CompanionState], dict[str, Any]] | None = (
        None
    )


def _latest_achievement_value(
    _coord: RockstarCoordinator, data: CompanionState
) -> str | None:
    if not data.latest_achievement_id:
        return None
    ach = ACHIEVEMENT_BY_CODE.get(data.latest_achievement_id)
    if ach is None:
        return None
    return ach.localized_name(data.resolved_language)


def _trophy_attrs(coord: RockstarCoordinator, data: CompanionState) -> dict[str, Any]:
    counts = {"platinum": 0, "gold": 0, "silver": 0, "bronze": 0}
    for code in data.unlocked_achievements:
        ach = ACHIEVEMENT_BY_CODE.get(code)
        if ach and ach.grade in counts:
            counts[ach.grade] += 1
    hidden_locked = sum(
        1
        for ach in GTA6_ACHIEVEMENTS
        if ach.hidden and ach.code not in data.unlocked_achievements
    )
    return {
        "total": len(GTA6_ACHIEVEMENTS),
        "unlocked_by_grade": counts,
        "hidden_locked_count": hidden_locked,
        "eta_platinum_hours": coord.estimate_remaining_hours(platinum=True),
    }


SENSOR_DESCRIPTIONS: tuple[RockstarSensorDescription, ...] = (
    RockstarSensorDescription(
        key="active_platform",
        translation_key="active_platform",
        icon="mdi:controller",
        device_class=SensorDeviceClass.ENUM,
        options=PLATFORM_STATES,
        value_fn=lambda _c, d: d.active_platform,
        attrs_fn=lambda _c, d: {
            "source_entity": d.source_entity,
            "matched_id": d.matched_id,
            "discovered_sources": d.discovered_sources,
        },
    ),
    RockstarSensorDescription(
        key="now_playing",
        translation_key="now_playing",
        icon="mdi:gamepad-variant",
        value_fn=lambda _c, d: d.now_playing,
        attrs_fn=lambda _c, d: {
            "artwork_url": d.artwork_url,
            "is_gta6": d.is_playing_gta6,
            "is_rockstar": d.is_playing_rockstar,
            "source_entity": d.source_entity,
        },
    ),
    RockstarSensorDescription(
        key="active_sources_count",
        translation_key="active_sources_count",
        icon="mdi:hubspot",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _c, d: len(d.discovered_sources),
        attrs_fn=lambda _c, d: {"domains": d.discovered_sources},
    ),
    RockstarSensorDescription(
        key="total_playtime_hours",
        translation_key="total_playtime_hours",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda _c, d: round(d.total_playtime_seconds / 3600, 2),
    ),
    RockstarSensorDescription(
        key="current_session_minutes",
        translation_key="current_session_minutes",
        icon="mdi:play-speed",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _c, d: round(d.current_session_seconds / 60, 1),
    ),
    RockstarSensorDescription(
        key="latest_newswire",
        translation_key="latest_newswire",
        icon="mdi:newspaper-variant-outline",
        value_fn=lambda _c, d: d.newswire.title if d.newswire else None,
        attrs_fn=lambda _c, d: (
            {"link": d.newswire.link, "published": d.newswire.published}
            if d.newswire
            else {}
        ),
    ),
    RockstarSensorDescription(
        key="gta6_completion_percent",
        translation_key="gta6_completion_percent",
        device_scope="gta6",
        icon="mdi:progress-check",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _c, d: d.completion_percent,
        attrs_fn=lambda _c, d: {
            "weights_breakdown": d.section_breakdown,
            "story_missions": d.story_missions_completed,
        },
    ),
    RockstarSensorDescription(
        key="gta6_trophies_unlocked",
        translation_key="gta6_trophies_unlocked",
        device_scope="gta6",
        icon="mdi:trophy",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _c, d: len(d.unlocked_achievements),
        attrs_fn=_trophy_attrs,
    ),
    RockstarSensorDescription(
        key="gta6_gamerscore_earned",
        translation_key="gta6_gamerscore_earned",
        device_scope="gta6",
        icon="mdi:microsoft-xbox",
        native_unit_of_measurement="G",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda _c, d: d.gamerscore_earned,
        attrs_fn=lambda _c, _d: {"xbox_max": 1000},
    ),
    RockstarSensorDescription(
        key="gta6_latest_achievement",
        translation_key="gta6_latest_achievement",
        device_scope="gta6",
        icon="mdi:medal",
        value_fn=_latest_achievement_value,
    ),
    RockstarSensorDescription(
        key="gta6_eta_100_hours",
        translation_key="gta6_eta_100_hours",
        device_scope="gta6",
        icon="mdi:clock-fast",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda c, _d: c.estimate_remaining_hours(platinum=False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rockstar Companion sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        RockstarSensorEntity(coordinator, desc) for desc in SENSOR_DESCRIPTIONS
    )


class RockstarSensorEntity(RockstarBaseEntity, SensorEntity):
    """Represent a Rockstar & Leonida sensor."""

    entity_description: RockstarSensorDescription

    def __init__(
        self,
        coordinator: RockstarCoordinator,
        description: RockstarSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            f"sensor_{description.key}",
            device_scope=description.device_scope,
        )
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return sensor value."""
        return self.entity_description.value_fn(self.coordinator, self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return optional extra state attributes."""
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator, self.coordinator.data)
