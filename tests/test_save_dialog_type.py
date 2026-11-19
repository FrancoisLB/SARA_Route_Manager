# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_save_dialog_type
Description : Vérifie que l'export ouvre un vrai dialogue « Enregistrer sous ».
Classes présentes :
- SaveDialogTypeTests : test_save_dialog_uses_pywebview_save_constant,
  test_numeric_folder_dialog_value_is_not_used_for_save.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import unittest
from pathlib import Path


class SaveDialogTypeTests(unittest.TestCase):
    """Prévenir la régression vers un simple sélecteur de dossier."""

    def test_save_dialog_uses_pywebview_save_constant(self) -> None:
        """Vérifier l'utilisation de FileDialog.SAVE ou SAVE_DIALOG."""
        source = Path("sara_route_manager/__main__.py").read_text(encoding="utf-8")
        self.assertIn('hasattr(file_dialog_enum, "SAVE")', source)
        self.assertIn("save_dialog_type = file_dialog_enum.SAVE", source)
        self.assertIn("save_dialog_type = webview.SAVE_DIALOG", source)
        self.assertIn("save_filename=safe_name", source)

    def test_numeric_folder_dialog_value_is_not_used_for_save(self) -> None:
        """Vérifier que la valeur 20 n'est plus utilisée comme type d'export."""
        source = Path("sara_route_manager/__main__.py").read_text(encoding="utf-8")
        save_method = source.split("def save_file(", 1)[1].split("def choose_routes_directory", 1)[0]
        self.assertNotIn("create_file_dialog(\n                20,", save_method)
        self.assertIn("create_file_dialog(\n                save_dialog_type,", save_method)


if __name__ == "__main__":
    unittest.main()
