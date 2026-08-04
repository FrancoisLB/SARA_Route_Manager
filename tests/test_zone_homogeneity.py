# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_zone_homogeneity
Description : Vérifie que le pattern « zone F6 » est appliqué de façon
identique sur toutes les pages de l'application (0.6.13), avec la même
exception volontaire pour la zone Messages, et que la navigation F6 est
mutualisée dans un unique script chargé globalement.
Classes présentes :
- ZoneHomogeneityTests : test_every_page_has_f6_zones, test_messages_zone_excluded,
  test_h1_is_focusable, test_keyboard_zones_loaded_globally,
  test_page_scripts_do_not_duplicate_f6_handler.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

# Chaque page listée doit avoir au moins une zone F6, à l'exception de la
# zone Messages qui reste volontairement hors de ce pattern sur toutes les
# pages (c'est un journal passif, pas une zone de travail à atteindre par F6).
PAGE_TEMPLATES = (
    "home.html",
    "routes.html",
    "editor.html",
    "configuration.html",
    "about.html",
)


class ZoneHomogeneityTests(unittest.TestCase):
    """Contrôler l'homogénéité du pattern d'accessibilité entre les pages."""

    def test_every_page_has_f6_zones(self) -> None:
        """Vérifier qu'aucune page ne reste sans zone F6."""
        for name in PAGE_TEMPLATES:
            template = (ROOT / "sara_route_manager/templates" / name).read_text(
                encoding="utf-8"
            )
            self.assertGreater(
                template.count('class="f6-zone"') + template.count('f6-zone" data-zone-name'),
                0,
                f"{name} ne définit aucune zone F6.",
            )

    def test_messages_zone_excluded(self) -> None:
        """Vérifier que la zone Messages n'est jamais une zone F6, partout pareil."""
        for name in PAGE_TEMPLATES:
            template = (ROOT / "sara_route_manager/templates" / name).read_text(
                encoding="utf-8"
            )
            match = re.search(
                r'<section[^>]*aria-labelledby="messages-heading"[^>]*>', template
            )
            if match is None:
                continue
            self.assertNotIn("f6-zone", match.group(0), f"{name} : la zone Messages ne doit pas être une zone F6.")

    def test_h1_is_focusable(self) -> None:
        """Vérifier que chaque H1 de page porte tabindex="-1", comme les zones."""
        for name in PAGE_TEMPLATES:
            template = (ROOT / "sara_route_manager/templates" / name).read_text(
                encoding="utf-8"
            )
            match = re.search(r"<h1[^>]*>", template)
            self.assertIsNotNone(match, f"{name} ne contient aucun H1.")
            self.assertIn('tabindex="-1"', match.group(0), f"{name} : le H1 n'est pas focusable.")

    def test_keyboard_zones_loaded_globally(self) -> None:
        """Vérifier que keyboard_zones.js est chargé depuis base.html, pour toutes les pages."""
        base = (ROOT / "sara_route_manager/templates/base.html").read_text(encoding="utf-8")
        self.assertIn("js/keyboard_zones.js", base)

    def test_page_scripts_do_not_duplicate_f6_handler(self) -> None:
        """Vérifier que la logique F6 n'est plus dupliquée dans les scripts de page."""
        for name in ("routes.js", "unified_editor.js", "about.js", "account.js", "configuration.js"):
            script = (ROOT / "sara_route_manager/static/js" / name).read_text(encoding="utf-8")
            self.assertNotIn(
                'document.querySelectorAll(".f6-zone")',
                script,
                f"{name} ne doit plus implémenter sa propre navigation F6.",
            )


if __name__ == "__main__":
    unittest.main()
