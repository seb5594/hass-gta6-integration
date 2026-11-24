"""Repository and locale checks without a Home Assistant installation."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "custom_components" / "rockstar_companion"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def leaves(values, prefix=()):
    for key, value in values.items():
        path = (*prefix, key)
        if isinstance(value, dict):
            yield from leaves(value, path)
        else:
            yield path


class IntegrationLayout(unittest.TestCase):
    def test_hacs_matches_manifest_and_constants(self):
        manifest = read_json(COMPONENT / "manifest.json")
        hacs = read_json(ROOT / "hacs.json")
        self.assertEqual(manifest["domain"], COMPONENT.name)
        self.assertEqual(hacs["name"], manifest["name"])
        self.assertEqual(hacs["filename"], f"{COMPONENT.name}.zip")
        self.assertIn(
            f'DOMAIN = "{COMPONENT.name}"', (COMPONENT / "const.py").read_text()
        )

    def test_locales_have_every_interface_string(self):
        translations = COMPONENT / "translations"
        english = read_json(translations / "en.json")
        expected = set(leaves(english))
        for language in ("de", "es", "fr", "it", "pt-BR"):
            with self.subTest(language=language):
                self.assertEqual(
                    set(leaves(read_json(translations / f"{language}.json"))), expected
                )
