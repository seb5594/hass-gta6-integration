<!-- header:begin (generated from project metadata) -->
<h1 align="center">Rockstar &amp; Leonida Companion</h1>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&amp;repository=hass-gta6-integration&amp;category=integration"><img src="https://img.shields.io/static/v1?label=HACS%20%C2%B7%20Marketplace&amp;message=Add%20integration&amp;color=41BDF5&amp;logo=homeassistantcommunitystore&amp;logoColor=white&amp;style=for-the-badge" alt="HACS · Marketplace" height="28"></a>
  <a href="https://github.com/seb5594/hass-gta6-integration/actions/workflows/compat.yml"><img src="https://img.shields.io/static/v1?label=home%20assistant&amp;message=%E2%89%A5%202026.11.0&amp;color=1877A5&amp;style=for-the-badge" alt="home assistant" height="28"></a><br>
  <a href="https://github.com/seb5594/hass-gta6-integration/releases"><img src="https://img.shields.io/static/v1?label=integration%20version&amp;message=0.1.0&amp;color=1877A5&amp;style=for-the-badge" alt="integration version" height="28"></a>
  <a href="https://github.com/seb5594/hass-gta6-integration/releases"><img src="https://img.shields.io/github/downloads/seb5594/hass-gta6-integration/latest/total?label=downloads&amp;color=1877A5&amp;style=for-the-badge" alt="downloads" height="28"></a><br>
  <a href="https://github.com/seb5594/hass-gta6-integration/stargazers"><img src="https://img.shields.io/github/stars/seb5594/hass-gta6-integration?label=stars&amp;style=flat" alt="stars" height="20"></a>
  <a href="https://github.com/seb5594/hass-gta6-integration/forks"><img src="https://img.shields.io/github/forks/seb5594/hass-gta6-integration?label=forks&amp;style=flat" alt="forks" height="20"></a>
  <a href="https://github.com/seb5594/hass-gta6-integration/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/seb5594/hass-gta6-integration/ci.yml?branch=main&amp;label=checks&amp;style=flat" alt="checks" height="20"></a>
  <a href="https://github.com/seb5594/hass-gta6-integration/issues"><img src="https://img.shields.io/github/issues/seb5594/hass-gta6-integration?label=issues&amp;style=flat" alt="issues" height="20"></a><br>
  <a href="https://paypal.me/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=PayPal&amp;color=0070BA&amp;logo=paypal&amp;logoColor=white&amp;style=for-the-badge" alt="PayPal" height="24"></a>
  <a href="https://buymeacoffee.com/seb5594"><img src="https://raw.githubusercontent.com/seb5594/Home-Assistant-Apps/473dc258f963096745aac327df54950eb9b59066/.github/assets/support-beer.svg" alt="Buy me a beer" height="24"></a><br>
  <a href="https://github.com/seb5594/hass-gta6-integration#license"><img src="https://img.shields.io/github/license/seb5594/hass-gta6-integration?label=license&amp;style=flat" alt="license" height="20"></a>
</p>
<!-- header:end -->

**English** · [Deutsch](README.de.md)

Track your GTA VI progress and turn game activity into Home Assistant automations.
Rockstar & Leonida Companion is a community integration that can run with just the
local tracker. Existing gaming entities add play detection and session tracking.

## Installation

- **HACS** — Add `seb5594/hass-gta6-integration` as a custom repository of type
  **Integration**, then install **Rockstar & Leonida Companion**.
- **Manual** — Copy `custom_components/rockstar_companion` into your Home Assistant
  configuration folder under `custom_components/`. If you use the release ZIP,
  extract it directly into `custom_components/rockstar_companion/`.

Restart Home Assistant and add **Rockstar & Leonida Companion** under
**Settings → Devices & services → Add integration**. [Add this repository to HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&repository=hass-gta6-integration&category=integration)

## Game detection and progress

- Link the PlayStation Network or Xbox integration for game presence, or select a
  game-title sensor or media player from another source, such as Playnite or MQTT.
  Keep automatic discovery enabled and leave the selection empty to discover
  supported gaming integrations as they appear. Choose individual entities to
  include friends or other profiles explicitly.
- The hub exposes the active platform, playtime, the current session and a
  dedicated **GTA VI active** binary sensor. PS5 installation status needs an
  entity from the `ps5` integration that exposes an installed titles list.
- Track 55 trophies and 34 weighted checklist items. Set completed story missions
  with the number entity. Check off whole items in To-do lists and use
  `rockstar_companion.set_checklist_progress` to enter partial counts.
  Completion percentages and time estimates use community guide data.
- Unrevealed secret trophies are masked by default. To import individual GTA VI
  unlocks, enable the Gaming Status option. This uses new, game-specific unlock
  events from the connected instance. Configure a player name to import unlocks
  from just that player. Each console's built-in integration provides
  presence data, while your progress and trophies can also be tracked manually.
- The Home Assistant UI, checklist labels and trophy hints are available in
  English, German, Spanish, French, Italian and Brazilian Portuguese. The catalog
  selector follows the Home Assistant system language in **Automatic** mode and
  falls back to English. German trophy titles are community translations. Other
  catalog languages use the English title to help match it in guides.
- You can configure a Newswire feed in RSS, Atom or JSON Feed format. The sensor
  displays the feed's headline in its original language.
- `rockstar_companion.export_progress` writes `rockstar_companion_progress.json`
  in the Home Assistant configuration folder and can return its filename to an
  automation. Home Assistant also stores the live tracker state in its own backups.

## Automation example

Replace `light.living_room` with the light you want to control. Use the
`game_stopped` event and its `duration_seconds` field for end-of-session automations.
The separate `rockstar_companion_achievement_unlocked` event carries
`achievement_unlocked` and `milestone_reached` as `event_type`.

```yaml
alias: GTA VI ambient lighting
triggers:
  - trigger: event
    event_type: rockstar_companion_game_session
    event_data:
      event_type: game_started
      is_gta6: true
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room
    data:
      rgb_color: [255, 42, 164]
      brightness_pct: 55
```

## Development

CI, compatibility testing and ZIP packaging use the shared
[`hass-workflows` engine](https://github.com/seb5594/hass-workflows).
The current minimum supported Home Assistant release is in [hacs.json](hacs.json).
Run the repository checks with `python -m unittest discover -s .github/tests -v`.
The Compatibility workflow runs `.github/ha_tests/` against Home Assistant Core.

The adapter design and initial tracker catalog came from the
[shared Gemini draft](https://gemini.google.com/share/174df5371d21).
Platform availability and catalog figures were checked against the
[Rockstar launch announcement](https://www.rockstargames.com/VI/out-now),
[PlayStation Store](https://store.playstation.com/en-us/product/EP1004-PPSA01547_00-GTAVISTANDARD001/),
[Xbox Store](https://www.xbox.com/en-gb/games/store/grand-theft-auto-vi/9nl3wwnzlzzn),
[TrueAchievements](https://www.trueachievements.com/news/grand-theft-auto-6-xbox-achievements)
and [GTA Base](https://www.gtabase.com/gta-6/achievements).

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://paypal.me/seb5594) [![Buy me a beer](https://raw.githubusercontent.com/seb5594/Home-Assistant-Apps/473dc258f963096745aac327df54950eb9b59066/.github/assets/support-beer.svg)](https://buymeacoffee.com/seb5594)
<!-- support:end -->

<!-- license:begin (generated from the license file) -->
## License

[![license](https://img.shields.io/static/v1?label=license&message=Apache-2.0&color=5B6770&style=flat)](LICENSE)

Published under the [Apache License 2.0](LICENSE).
<!-- license:end -->
