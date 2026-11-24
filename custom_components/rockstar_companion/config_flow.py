"""Configure sources, catalog preferences and the optional Newswire feed."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .adapters import discover_gaming_config_entries
from .const import (
    CONF_AUTO_DISCOVER,
    CONF_AUTO_SYNC,
    CONF_EXTRA_ENTITIES,
    CONF_GAMING_STATUS_PLAYER,
    CONF_LANGUAGE_MODE,
    CONF_LINKED_ENTRIES,
    CONF_NEWSWIRE_URL,
    CONF_SCAN_INTERVAL,
    CONF_SPOILER_SHIELD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LANG_AUTO,
    LANGUAGE_OPTIONS,
)
from .newswire import is_feed_url

TITLE = "Rockstar & Leonida Companion"
ADVANCED = "advanced_options"


def _schema(hass: HomeAssistant, values: dict[str, Any]) -> vol.Schema:
    fields = {}
    discovered = discover_gaming_config_entries(hass)
    if discovered:
        entry_ids = {item["entry_id"] for item in discovered}
        fields[
            vol.Optional(
                CONF_LINKED_ENTRIES,
                default=[
                    entry_id
                    for entry_id in values.get(CONF_LINKED_ENTRIES, [])
                    if entry_id in entry_ids
                ],
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {
                        "value": item["entry_id"],
                        "label": f"{item['title']} ({item['domain']})",
                    }
                    for item in discovered
                ],
                multiple=True,
            )
        )

    fields.update(
        {
            vol.Optional(
                CONF_AUTO_DISCOVER, default=values.get(CONF_AUTO_DISCOVER, True)
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_EXTRA_ENTITIES, default=values.get(CONF_EXTRA_ENTITIES, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["media_player", "sensor"],
                    multiple=True,
                    exclude_entities=[
                        entity.entity_id
                        for entity in er.async_get(hass).entities.values()
                        if entity.platform == DOMAIN
                    ],
                )
            ),
            vol.Optional(
                CONF_LANGUAGE_MODE, default=values.get(CONF_LANGUAGE_MODE, LANG_AUTO)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=LANGUAGE_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="language_mode",
                )
            ),
            vol.Optional(ADVANCED): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_SPOILER_SHIELD,
                            default=values.get(CONF_SPOILER_SHIELD, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_AUTO_SYNC, default=values.get(CONF_AUTO_SYNC, False)
                        ): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_GAMING_STATUS_PLAYER,
                            default=values.get(CONF_GAMING_STATUS_PLAYER, ""),
                        ): selector.TextSelector(),
                        vol.Optional(
                            CONF_SCAN_INTERVAL,
                            default=values.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=10,
                                max=600,
                                step=1,
                                unit_of_measurement="s",
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            CONF_NEWSWIRE_URL, default=values.get(CONF_NEWSWIRE_URL, "")
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.URL
                            )
                        ),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )
    return vol.Schema(fields)


def _parse(values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    settings = dict(values)
    settings.update(settings.pop(ADVANCED, {}))
    url = settings.get(CONF_NEWSWIRE_URL, "").strip()
    if url and not is_feed_url(url):
        return settings, {"base": "invalid_feed_url"}
    if CONF_NEWSWIRE_URL in settings:
        settings[CONF_NEWSWIRE_URL] = url
    return settings, {}


class RockstarCompanionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure the single companion entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set up the companion from the UI."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        settings, errors = _parse(user_input or {})
        if user_input is not None and not errors:
            return self.async_create_entry(title=TITLE, data=settings)
        return self.async_show_form(
            step_id="user", data_schema=_schema(self.hass, settings), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Replace settings while keeping the same entry and entities."""
        entry = self._get_reconfigure_entry()
        previous = {**entry.data, **entry.options}
        settings, errors = _parse(user_input or {})
        merged = {**previous, **settings}
        if user_input is not None and not errors:
            return self.async_update_reload_and_abort(entry, data=merged, options={})
        return self.async_show_form(
            step_id="reconfigure", data_schema=_schema(self.hass, merged), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Create a flow for updating settings."""
        return RockstarCompanionOptionsFlow()


class RockstarCompanionOptionsFlow(OptionsFlowWithReload):
    """Update companion settings."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and save options."""
        entry = self.config_entry
        settings, errors = _parse(user_input or {})
        if user_input is not None and not errors:
            return self.async_create_entry(data={**entry.options, **settings})
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.hass, {**entry.data, **entry.options, **settings}),
            errors=errors,
        )
