# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_details_heading_navigation
Description : Vérifie le titre hiérarchique et l’accès F6 de la zone de détails.
Classes présentes :
- DetailsHeadingNavigationTests : test_heading_markup, test_f6_contract, test_enter_moves_to_heading.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DetailsHeadingNavigationTests(unittest.TestCase):
    """Contrôler l’accès rapide aux informations du point dans la page Routes."""

    def test_heading_markup(self) -> None:
        """Vérifier que la zone possède un vrai titre H2 correctement associé."""
        template = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '<section class="f6-zone" data-zone-name="Informations sur le point" '
            'aria-labelledby="details-heading">',
            template,
        )
        self.assertIn(
            '<h2 id="details-heading" tabindex="-1">Informations sur le point</h2>',
            template,
        )

    def test_f6_contract(self) -> None:
        """Vérifier que F6 parcourt toutes les sections portant la classe f6-zone.

        Cette logique est mutualisée dans keyboard_zones.js depuis la 0.6.13
        et s'applique identiquement à toutes les pages de l'application.
        """
        script = (ROOT / "sara_route_manager/static/js/keyboard_zones.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('event.key !== "F6"', script)
        self.assertIn('document.querySelectorAll(".f6-zone")', script)
        self.assertIn('querySelector("h2,h3,input,select,button,a")', script)

    def test_enter_moves_to_heading(self) -> None:
        """Vérifier que Entrée depuis une liste place le focus sur le titre des détails."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('$("details-heading").focus();', script)


if __name__ == "__main__":
    unittest.main()
