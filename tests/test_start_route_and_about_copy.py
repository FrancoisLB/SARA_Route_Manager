# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_start_route_and_about_copy
Description : Vérifie trois corrections signalées après test manuel sous
NVDA : le libellé du bouton de création, le masquage effectif de la zone de
démarrage une fois la route active, et la possibilité de copier la liste
Informations générales de la page À propos.
Classes présentes :
- StartRouteAndAboutCopyTests : test_button_label, test_hidden_actions_css_rule,
  test_general_information_copy_button, test_general_information_copy_handler.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StartRouteAndAboutCopyTests(unittest.TestCase):
    """Contrôler les trois corrections apportées après le retour de test."""

    def test_button_label(self) -> None:
        """Vérifier que le bouton de création porte le libellé « Créer cette route »."""
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="start-route" type="button">Créer cette route</button>', editor)
        self.assertNotIn("Commencer cette route", editor)

    def test_hidden_actions_css_rule(self) -> None:
        """Vérifier que .actions[hidden] restaure bien display:none.

        Sans cette règle, `.actions{display:flex}` (règle d'auteur) l'emporte
        sur le style par défaut du navigateur pour l'attribut `hidden`
        (règle de l'agent utilisateur), et l'élément resterait visible et
        cliquable malgré `element.hidden = true` en JavaScript.
        """
        css = (ROOT / "sara_route_manager/static/css/main.css").read_text(
            encoding="utf-8"
        )
        self.assertIn(".actions[hidden]", css)
        self.assertIn("display:none", css)

    def test_general_information_copy_button(self) -> None:
        """Vérifier la présence du bouton de copie de la liste Informations générales."""
        about = (ROOT / "sara_route_manager/templates/about.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="about-general-list"', about)
        self.assertIn('id="copy-general-information"', about)

    def test_general_information_copy_handler(self) -> None:
        """Vérifier que le gestionnaire copie le texte réellement affiché."""
        script = (ROOT / "sara_route_manager/static/js/about.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function formatGeneralInformation", script)
        self.assertIn('getElementById("about-general-list")', script)
        self.assertIn("navigator.clipboard.writeText(formatGeneralInformation())", script)


if __name__ == "__main__":
    unittest.main()
