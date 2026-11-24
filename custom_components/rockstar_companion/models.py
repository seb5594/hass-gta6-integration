"""Data models for Rockstar & Leonida Companion."""

from __future__ import annotations

from dataclasses import dataclass, field

from .catalog.translations import ACHIEVEMENT_DESCRIPTIONS, CHECKLIST_NAMES


@dataclass(frozen=True, slots=True)
class AchievementDef:
    """Immutable definition of an achievement or PlayStation trophy."""

    idx: int
    code: str
    name_en: str
    name_de: str
    desc_en: str
    desc_de: str
    grade: str
    gamerscore: int
    hidden: bool
    category: str

    def localized_name(self, lang: str) -> str:
        """Return localized achievement title."""
        return self.name_de if lang == "de" else self.name_en

    def localized_desc(self, lang: str) -> str:
        """Return localized achievement description."""
        if lang == "de":
            return self.desc_de
        return ACHIEVEMENT_DESCRIPTIONS.get(lang, {}).get(self.code, self.desc_en)


@dataclass(frozen=True, slots=True)
class ChecklistDef:
    """Immutable weighted requirement for 100% completion."""

    item_id: str
    section: str
    name_en: str
    name_de: str
    weight_pct: float
    target: int
    unit: str = "count"

    def localized_name(self, lang: str) -> str:
        """Return localized checklist item label."""
        if lang == "de":
            return self.name_de
        return CHECKLIST_NAMES.get(lang, {}).get(self.item_id, self.name_en)


@dataclass(slots=True)
class PlatformSnapshot:
    """Normalized state across one detected gaming integration."""

    domain: str
    platform_family: str
    entry_id: str | None
    title: str | None = None
    active: bool = False
    is_gta6: bool = False
    is_rockstar: bool = False
    installed_gta6: bool | None = None
    artwork_url: str | None = None
    matched_id: str | None = None
    source_entity: str | None = None


@dataclass(slots=True)
class NewswireItem:
    """Normalized Rockstar Newswire post."""

    title: str
    link: str = ""
    published: str = ""


@dataclass(slots=True)
class CompanionState:
    """Aggregated coordinator output consumed by all entities."""

    active_platform: str = "idle"
    now_playing: str | None = None
    is_playing_rockstar: bool = False
    is_playing_gta6: bool = False
    is_installed_ps5: bool | None = None
    artwork_url: str | None = None
    matched_id: str | None = None
    source_entity: str | None = None
    discovered_sources: list[str] = field(default_factory=list)
    snapshots: list[PlatformSnapshot] = field(default_factory=list)
    total_playtime_seconds: int = 0
    current_session_seconds: int = 0
    unlocked_achievements: dict[str, str] = field(default_factory=dict)
    checklist_progress: dict[str, int] = field(default_factory=dict)
    story_missions_completed: int = 0
    completion_percent: float = 0.0
    section_breakdown: dict[str, float] = field(default_factory=dict)
    gamerscore_earned: int = 0
    latest_achievement_id: str | None = None
    spoiler_shield: bool = True
    auto_sync_achievements: bool = True
    language_mode: str = "auto"
    resolved_language: str = "en"
    newswire: NewswireItem | None = None
