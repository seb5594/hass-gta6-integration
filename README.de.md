# Rockstar & Leonida Companion

[English](README.md) · **Deutsch**

Die Home-Assistant-Integration erfasst deinen GTA-VI-Fortschritt und meldet, wenn
du spielst. Du kannst die Checklisten auch ohne verknüpfte Konsole verwenden.

## Installation

1. Füge `seb5594/hass-gta6-integration` in HACS als benutzerdefiniertes Repository des
   Typs **Integration** hinzu. Installiere **Rockstar & Leonida Companion**.
2. Starte Home Assistant neu und füge **Rockstar & Leonida Companion** unter
   **Einstellungen → Geräte & Dienste → Integration hinzufügen** hinzu.

Für die manuelle Installation kopierst du den Ordner
`custom_components/rockstar_companion` unter `custom_components/` im
Home-Assistant-Konfigurationsordner. Das Release-ZIP entpackst du direkt nach
`custom_components/rockstar_companion/`. [Repository in HACS hinzufügen](https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&repository=hass-gta6-integration&category=integration)

## Überblick

- **Spielerkennung.** Verknüpfe PlayStation Network, Xbox oder vorhandene
  Spielsensoren und Mediaplayer, zum Beispiel aus Playnite oder MQTT. Die
  automatische Erkennung greift, wenn du in der Integrationsliste nichts
  auswählst und sie aktiviert lässt. Eine PS5-Installationsanzeige setzt eine
  Entität aus der `ps5`-Integration mit einer Liste installierter Titel voraus.
- **Fortschritt.** Markiere 55 Trophäen und 34 gewichtete Nebenaufgaben in zwei
  To-do-Listen. Die Zahlentität erfasst die Hauptmissionen.
  `rockstar_companion.set_checklist_progress` speichert Zwischenstände für einzelne
  Aufgaben. Prozentwerte und Zeitschätzungen basieren auf Community-Leitfäden.
- **Trophäen.** Der Spoiler-Schutz verbirgt gesperrte geheime Trophäen. Wenn du
  den Import aus Gaming Status aktivierst, werden neue Freischaltungen für
  GTA VI übernommen. Mit einem Spielernamen kannst du die Übernahme auf dieses
  Profil begrenzen. Die Standardintegrationen für PlayStation Network und Xbox
  liefern den Spielstatus. Erfolge lassen sich auch manuell abhaken.
- **Sprachen.** Oberfläche, Checklisten und Hinweise gibt es auf Deutsch,
  Englisch, Spanisch, Französisch, Italienisch und brasilianischem Portugiesisch.
  Die Katalogsprache ist separat umschaltbar. **Automatisch** folgt der
  Home-Assistant-Systemsprache und nutzt Englisch als Rückfall. Deutsche
  Trophäentitel sind Community-Übersetzungen. In den übrigen Katalogsprachen
  erscheinen englische Originaltitel.
- **Aktionen.** `rockstar_companion.export_progress` speichert
  `rockstar_companion_progress.json` im Konfigurationsordner. Über den
  Binärsensor **GTA VI aktiv** oder das Ereignis
  `rockstar_companion_game_session` kannst du Licht und andere Geräte steuern.
  Ein Beispiel steht in der englischen README. [Automationsbeispiel](README.md#automation-example)
