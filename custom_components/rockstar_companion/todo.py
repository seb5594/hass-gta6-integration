"""Interactive To-Do lists for GTA VI 100% completion and trophy tracking."""

from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RockstarConfigEntry
from .catalog.gta_vi import (
    CHECKLIST_BY_ID,
    GTA6_ACHIEVEMENTS,
    GTA6_CHECKLIST_ITEMS,
)
from .catalog.locale import catalog_label
from .coordinator import RockstarCoordinator
from .entity_base import RockstarBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up interactive To-Do entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            Gta6ChecklistTodoEntity(coordinator),
            Gta6TrophyTodoEntity(coordinator),
        ]
    )


class Gta6ChecklistTodoEntity(RockstarBaseEntity, TodoListEntity):
    """Interactive 100% completion checklist."""

    _attr_translation_key = "gta6_100_checklist"
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(self, coordinator: RockstarCoordinator) -> None:
        """Initialize checklist entity."""
        super().__init__(coordinator, "todo_gta6_100_checklist", device_scope="gta6")

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return localized 100% checklist items."""
        data = self.coordinator.data
        lang = data.resolved_language
        progress = data.checklist_progress
        items: list[TodoItem] = []

        for entry in GTA6_CHECKLIST_ITEMS:
            cur = min(int(progress.get(entry.item_id, 0)), entry.target)
            done = cur >= entry.target
            items.append(
                TodoItem(
                    uid=entry.item_id,
                    summary=f"{entry.localized_name(lang)} [{cur}/{entry.target} — {entry.weight_pct:.0f}%]",
                    status=(
                        TodoItemStatus.COMPLETED
                        if done
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                    description=catalog_label(lang, entry.section),
                )
            )
        return items

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Toggle checklist item between 0 and its full target value."""
        if not item.uid or item.uid not in CHECKLIST_BY_ID:
            return
        target = CHECKLIST_BY_ID[item.uid].target
        if item.status == TodoItemStatus.COMPLETED:
            await self.coordinator.async_set_checklist_progress(item.uid, target)
        elif self.coordinator.data.checklist_progress.get(item.uid) == target:
            await self.coordinator.async_set_checklist_progress(item.uid, 0)


class Gta6TrophyTodoEntity(RockstarBaseEntity, TodoListEntity):
    """Interactive 55-trophy list with Spoiler Shield masking."""

    _attr_translation_key = "gta6_trophy_list"
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(self, coordinator: RockstarCoordinator) -> None:
        """Initialize trophy To-Do entity."""
        super().__init__(coordinator, "todo_gta6_trophy_list", device_scope="gta6")

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return localized trophies respecting spoiler_shield."""
        data = self.coordinator.data
        lang = data.resolved_language
        unlocked_map = data.unlocked_achievements
        items: list[TodoItem] = []

        for ach in GTA6_ACHIEVEMENTS:
            unlocked = ach.code in unlocked_map
            if ach.hidden and data.spoiler_shield and not unlocked:
                summary = f"#{ach.idx:02d} {catalog_label(lang, 'hidden')}"
                desc = catalog_label(lang, "hidden_help")
            else:
                summary = f"#{ach.idx:02d} {ach.localized_name(lang)} [{catalog_label(lang, ach.grade)} / {ach.gamerscore} G]"
                desc = ach.localized_desc(lang)

            items.append(
                TodoItem(
                    uid=f"trophy-{ach.idx:02d}",
                    summary=summary,
                    status=(
                        TodoItemStatus.COMPLETED
                        if unlocked
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                    description=desc,
                )
            )
        return items

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Toggle achievement completion directly from To-Do UI."""
        achievement = next(
            (ach for ach in GTA6_ACHIEVEMENTS if item.uid == f"trophy-{ach.idx:02d}"),
            None,
        )
        if achievement is not None:
            await self.coordinator.async_set_achievement_state(
                achievement.code,
                unlocked=item.status == TodoItemStatus.COMPLETED,
                source="todo_ui",
            )
