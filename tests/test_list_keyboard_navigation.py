# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_list_keyboard_navigation
Description : Vérifie la correction de la navigation clavier dans les
listes (sélection par défaut au premier focus, pour donner aux flèches
haut/bas une position de départ) et l'ouverture d'une route par
double-clic, dans l'éditeur et l'onglet Bibliothèque.
Classes présentes :
- TestListKeyboardNavigation : test_editor_lists_default_selection_on_focus,
  test_library_lists_default_selection_on_focus,
  test_library_lists_open_on_double_click,
  test_library_lists_open_on_enter_still_present.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestListKeyboardNavigation:
    """Vérifier que les flèches haut/bas ont une position de départ dès le premier focus clavier.

    Signalé après retour utilisateur : le focus (F6/Tab) atteignait bien la
    liste, mais les flèches n'y naviguaient qu'après un clic souris
    préalable. Cause identifiée : `selectedIndex` restait à -1 (aucune
    option choisie) tant qu'aucune interaction n'avait eu lieu, privant les
    flèches de tout point de départ.
    """

    def test_editor_lists_default_selection_on_focus(self) -> None:
        """Vérifier la correction dans les listes de points de l'éditeur."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        assert 'list.addEventListener("focus", () => {' in script
        assert "if (list.selectedIndex === -1 && list.options.length > 0) {" in script
        assert "list.selectedIndex = 0;" in script

    def test_library_lists_default_selection_on_focus(self) -> None:
        """Vérifier la correction dans les listes de routes de la Bibliothèque."""
        script = (ROOT / "sara_route_manager/static/js/routes.js").read_text(encoding="utf-8")
        assert 'list.addEventListener("focus", () => {' in script
        assert "if (list.selectedIndex === -1 && list.options.length > 0) {" in script
        assert "list.selectedIndex = 0;" in script

    def test_library_lists_open_on_double_click(self) -> None:
        """Vérifier que le double-clic ouvre directement la route sélectionnée.

        Demandé en plus du raccourci clavier Entrée, déjà en place.
        """
        script = (ROOT / "sara_route_manager/static/js/routes.js").read_text(encoding="utf-8")
        # 0.8.0 : liste unique, le double-clic appelle directement openSelected.
        assert 'list.addEventListener("dblclick", openSelected);' in script
        assert "async function openSelected()" in script

    def test_library_lists_open_on_enter_still_present(self) -> None:
        """Vérifier que le raccourci Entrée pour ouvrir une route existait déjà et reste actif.

        Il n'a pas fallu l'ajouter : seul le double-clic manquait.
        """
        script = (ROOT / "sara_route_manager/static/js/routes.js").read_text(encoding="utf-8")
        assert 'if (event.key === "Enter") {' in script
