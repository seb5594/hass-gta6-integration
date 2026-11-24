"""Constants for the Rockstar & Leonida Companion integration."""

from __future__ import annotations

import re

DOMAIN = "rockstar_companion"
STORAGE_VERSION = 1

DEFAULT_SCAN_INTERVAL = 30
DEFAULT_NEWSWIRE_INTERVAL = 7200
PLATFORM_STATES = ["idle", "ps5", "ps4", "psn", "xbox", "pc", "custom", "multi"]

CONF_AUTO_DISCOVER = "auto_discover"
CONF_LINKED_ENTRIES = "linked_entries"
CONF_EXTRA_ENTITIES = "extra_entities"
CONF_LANGUAGE_MODE = "language_mode"
CONF_SPOILER_SHIELD = "spoiler_shield"
CONF_AUTO_SYNC = "auto_sync_achievements"
CONF_GAMING_STATUS_PLAYER = "gaming_status_player"
CONF_NEWSWIRE_URL = "newswire_url"
CONF_SCAN_INTERVAL = "scan_interval"

LANG_AUTO = "auto"
LANG_DE = "de"
LANG_EN = "en"
CATALOG_LANGUAGES = (LANG_EN, LANG_DE, "es", "fr", "it", "pt-BR")
LANGUAGE_OPTIONS = [LANG_AUTO, *CATALOG_LANGUAGES]

KNOWN_INTEGRATION_DOMAINS: tuple[str, ...] = (
    "playstation_network",
    "ps4",
    "ps5",
    "xbox",
    "steam_online",
    "system_bridge",
    "playnite_connect",
    "playnite_web_mqtt",
    "gaming_status",
)

PLATFORM_MAP: dict[str, str] = {
    "playstation_network": "psn",
    "ps4": "ps4",
    "ps5": "ps5",
    "xbox": "xbox",
    "steam_online": "pc",
    "system_bridge": "pc",
    "playnite_connect": "pc",
    "playnite_web_mqtt": "pc",
    "gaming_status": "custom",
}

GTA6_PS5_TITLE_IDS: frozenset[str] = frozenset(
    {"PPSA01547_00", "PPSA29660_00", "PPSA01547", "PPSA29660"}
)
GTA6_XBOX_PRODUCT_IDS: frozenset[str] = frozenset({"9NL3WWNZLZZN"})
GTA6_XBOX_TITLE_IDS: frozenset[str] = frozenset({"2035456122", "7952987A"})
GTA6_XBOX_PACKAGES: frozenset[str] = frozenset(
    {"RockstarGamesInc.28872443D20A7_k2ss7vbb13xte"}
)

GTA6_TITLE_REGEX = re.compile(
    r"(?:grand\s+theft\s+auto|gta)\s*[:–-]?\s*(?:vi|6)(?:\s*[™®])?(?:\s*[-–:]?\s*(?:standard|special|ultimate)\s+edition)?",
    re.IGNORECASE,
)
OTHER_ROCKSTAR_TITLE_REGEX = re.compile(
    r"\b(grand\s+theft\s+auto\s*(v|5|online)|gta\s*(v|5|online)|red\s+dead\s+redemption\s*2)\b",
    re.IGNORECASE,
)
EVENT_ACHIEVEMENT_UNLOCKED = f"{DOMAIN}_achievement_unlocked"
EVENT_GAME_SESSION = f"{DOMAIN}_game_session"

SERVICE_SYNC_NOW = "sync_now"
SERVICE_UNLOCK_ACHIEVEMENT = "unlock_achievement"
SERVICE_SET_CHECKLIST = "set_checklist_progress"
SERVICE_EXPORT_PROGRESS = "export_progress"

ATTR_ACHIEVEMENT_ID = "achievement_id"
ATTR_ITEM_ID = "item_id"
ATTR_VALUE = "value"
ATTR_SOURCE = "source"

GTA6_100_BENCHMARK_HOURS = 110.0
GTA6_PLATINUM_BENCHMARK_HOURS = 200.0
