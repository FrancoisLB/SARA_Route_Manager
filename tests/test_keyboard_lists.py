# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_keyboard_lists
Description : Vérifie les contrats clavier et menus contextuels de la version 0.6.12.
Classes présentes :
- KeyboardListTests : test_library_keyboard_contract, test_editor_keyboard_contract, test_context_menu_markup.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KeyboardListTests(unittest.TestCase):
    """Contrôler statiquement les commandes clavier essentielles."""

    def test_library_keyboard_contract(self) -> None:
        """Vérifier Entrée, F2, Suppr, Menu et Maj+F10 dans la bibliothèque."""
        source = (ROOT / "sara_route_manager/static/js/routes.js").read_text(encoding="utf-8")
        for token in ('event.key === "Enter"', 'event.key === "F2"', 'event.key === "Delete"',
                      'event.key === "ContextMenu"', 'event.shiftKey && event.key === "F10"'):
            self.assertIn(token, source)

    def test_editor_keyboard_contract(self) -> None:
        """Vérifier le menu contextuel et Suppr dans les listes de points."""
        source = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(encoding="utf-8")
        self.assertIn('openPointContextMenu', source)
        self.assertIn('event.key === "Delete"', source)
        self.assertIn('event.key === "ContextMenu"', source)

    def test_context_menu_markup(self) -> None:
        """Vérifier la présence des deux menus avec le rôle ARIA menu."""
        routes = (ROOT / "sara_route_manager/templates/routes.html").read_text(encoding="utf-8")
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(encoding="utf-8")
        self.assertIn('id="route-context-menu"', routes)
        self.assertIn('id="point-context-menu"', editor)
        self.assertIn('role="menu"', routes)
        self.assertIn('role="menu"', editor)


if __name__ == "__main__":
    unittest.main()
