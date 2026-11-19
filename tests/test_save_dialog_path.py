# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_save_dialog_path
Description : Vérifie la correction du chemin renvoyé par le dialogue natif.
Classes présentes :
- SaveDialogPathTests : test_string_result_is_not_indexed, test_message_area_is_copyable.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import unittest
from pathlib import Path


class SaveDialogPathTests(unittest.TestCase):
    """Contrôler les contrats de régression de l’export natif."""

    def test_string_result_is_not_indexed(self) -> None:
        """Vérifier que le code distingue une chaîne d’une liste de chemins."""
        source = Path("sara_route_manager/__main__.py").read_text(encoding="utf-8")
        self.assertIn("isinstance(result, (str, Path))", source)
        self.assertIn("selected_value = str(result)", source)
        self.assertIn("except PermissionError as exc", source)

    def test_message_area_is_copyable(self) -> None:
        """Vérifier la présence du journal en lecture seule et du bouton Copier."""
        template = Path("sara_route_manager/templates/editor.html").read_text(encoding="utf-8")
        script = Path("sara_route_manager/static/js/unified_editor.js").read_text(encoding="utf-8")
        self.assertIn("<textarea id=\"status-message\"", template)
        self.assertIn("readonly", template)
        self.assertIn("id=\"copy-status-message\"", template)
        self.assertIn("async function copyStatusMessage()", script)


if __name__ == "__main__":
    unittest.main()
