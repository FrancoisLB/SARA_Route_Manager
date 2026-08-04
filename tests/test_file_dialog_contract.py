# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_file_dialog_contract
Description : Vérifie le mécanisme commun d’enregistrement de la version 0.6.12.
Classes présentes :
- FileDialogContractTests : test_desktop_api_contract, test_shared_javascript_contract.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FileDialogContractTests(unittest.TestCase):
    """Contrôler statiquement l’homogénéité des exports de fichiers."""

    def test_desktop_api_contract(self) -> None:
        """Vérifier la présence du dialogue natif et du chemin retourné."""
        source = (ROOT / "sara_route_manager/__main__.py").read_text(encoding="utf-8")
        self.assertIn("def save_file(", source)
        self.assertIn("save_filename=safe_name", source)
        self.assertIn("directory=initial_directory", source)
        self.assertIn("configuration.confirm_before_overwrite", source)
        self.assertIn('"path": str(selected_path.resolve())', source)
        self.assertIn('"cancelled": True', source)

    def test_shared_javascript_contract(self) -> None:
        """Vérifier que les exports utilisent le même service JavaScript."""
        helper = (ROOT / "sara_route_manager/static/js/file_dialogs.js").read_text(
            encoding="utf-8"
        )
        editor = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        routes = (ROOT / "sara_route_manager/static/js/routes.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("async function saveBlobWithDialog", helper)
        self.assertGreaterEqual(editor.count("saveBlobWithDialog("), 2)
        self.assertIn("saveBlobWithDialog(blob, filename", routes)
        self.assertIn("Fichier : ${result.path}", editor)
        self.assertIn("Fichier : ${result.path}", routes)
        self.assertIn("loadExportConfiguration", editor)
        self.assertIn("configuration.csv_separator", editor)


if __name__ == "__main__":
    unittest.main()
