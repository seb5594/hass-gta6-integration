"""Catalog language resolution and display strings."""

from ..const import CATALOG_LANGUAGES

_CATALOG_LANGUAGE_CODES = {
    language.casefold(): language for language in CATALOG_LANGUAGES
}
_CATALOG_LANGUAGE_CODES["pt"] = "pt-BR"
_LABELS = {
    "en": (
        "Hidden trophy",
        "Reveal by completing the trophy or disabling spoiler protection.",
        "Platinum",
        "Gold",
        "Silver",
        "Bronze",
        "Tasks",
        "Exploration and activities",
        "Discovery",
    ),
    "de": (
        "Versteckte Trophäe",
        "Wird beim Freischalten oder Deaktivieren des Spoiler-Schutzes sichtbar.",
        "Platin",
        "Gold",
        "Silber",
        "Bronze",
        "Aufgaben",
        "Erkundung und Aktivitäten",
        "Entdeckungen",
    ),
    "es": (
        "Trofeo oculto",
        "Se revela al desbloquearlo o desactivar la protección contra spoilers.",
        "Platino",
        "Oro",
        "Plata",
        "Bronce",
        "Tareas",
        "Exploración y actividades",
        "Descubrimientos",
    ),
    "fr": (
        "Trophée caché",
        "Se révèle en le débloquant ou en désactivant la protection contre les spoilers.",
        "Platine",
        "Or",
        "Argent",
        "Bronze",
        "Tâches",
        "Exploration et activités",
        "Découvertes",
    ),
    "it": (
        "Trofeo nascosto",
        "Si rivela sbloccandolo o disattivando la protezione spoiler.",
        "Platino",
        "Oro",
        "Argento",
        "Bronzo",
        "Incarichi",
        "Esplorazione e attività",
        "Scoperte",
    ),
    "pt-BR": (
        "Troféu oculto",
        "Revele o troféu ao desbloqueá-lo ou desativar a proteção contra spoilers.",
        "Platina",
        "Ouro",
        "Prata",
        "Bronze",
        "Tarefas",
        "Exploração e atividades",
        "Descobertas",
    ),
}
_KEYS = (
    "hidden",
    "hidden_help",
    "platinum",
    "gold",
    "silver",
    "bronze",
    "tasks",
    "exploration",
    "discovery",
)


def catalog_language(language: str | None) -> str:
    """Map a full or regional language tag onto a supported locale."""
    tag = (language or "en").casefold().replace("_", "-")
    return _CATALOG_LANGUAGE_CODES.get(
        tag, _CATALOG_LANGUAGE_CODES.get(tag.split("-")[0], "en")
    )


def catalog_label(language: str, key: str) -> str:
    """Return a localized catalog interface label."""
    return _LABELS[language][_KEYS.index(key)]
