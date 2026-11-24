"""Diagnostics support with sensitive field redaction."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import RockstarConfigEntry
from .const import CONF_NEWSWIRE_URL

TO_REDACT = {CONF_NEWSWIRE_URL, "artwork_url", "entry_id", "source_entity"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: RockstarConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics payload for debugging dynamic platform adapters."""
    data = entry.runtime_data.data
    return {
        "entry": async_redact_data(
            {"data": dict(entry.data), "options": dict(entry.options)}, TO_REDACT
        ),
        "state": {
            "active_platform": data.active_platform,
            "now_playing": data.now_playing,
            "discovered_sources": data.discovered_sources,
            "completion_percent": data.completion_percent,
            "unlocked_count": len(data.unlocked_achievements),
            "snapshots": [
                async_redact_data(asdict(s), TO_REDACT) for s in data.snapshots
            ],
        },
    }
