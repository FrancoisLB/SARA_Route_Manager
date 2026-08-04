# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_release_completeness
Description : Vérifie la présence des fichiers indispensables à une livraison complète.
Classes présentes :
- ReleaseCompletenessTests : test_required_files, test_required_directories.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "LICENSE.md",
    "CHANGE_LOG.md",
    "docs/SPECIFICATIONS.md",
    "docs/ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "docs/RACCOURCIS_CLAVIER.md",
    "docs/THIRD_PARTY_LICENSES.md",
    "VERSION.txt",
    "requirements.txt",
    "Installer.bat",
    "Lancer_SARA_Route_Manager.bat",
    "Lancer_Mode_Navigateur.bat",
    "setup_environment.bat",
    "docs/USER_GUIDE.md",
    "sara_route_manager/__init__.py",
    "sara_route_manager/__main__.py",
    "sara_route_manager/webapp.py",
    "sara_route_manager/templates/about.html",
    "sara_route_manager/templates/editor.html",
    "sara_route_manager/templates/map.html",
    "sara_route_manager/coastline.py",
    "sara_route_manager/shom_icons.py",
    "sara_route_manager/static/vendor/shom_icons/BCNLAT_B.svg",
    "sara_route_manager/static/vendor/leaflet/leaflet.js",
    "sara_route_manager/static/vendor/leaflet/leaflet.css",
    "sara_route_manager/static/vendor/leaflet/LEAFLET_LICENSE.txt",
    "sara_route_manager/static/js/about.js",
    "sara_route_manager/static/js/file_dialogs.js",
    "sara_route_manager/static/js/keyboard_zones.js",
    "sara_route_manager/static/js/unified_editor.js",
    "sara_route_manager/static/js/map.js",
    "sara_route_manager/static/js/route_math.js",
    "tests/test_keyboard_lists.py",
    "tests/test_details_heading_navigation.py",
    "tests/test_zone_homogeneity.py",
    "tests/test_route_identity_and_credits.py",
    "tests/test_map_window_skeleton.py",
    "tests/test_coastline.py",
    "tests/test_shom_icons.py",
    "tests/test_map_marks_endpoint.py",
    "tests/test_storage.py",
    "tests/test_webapp_static_cache.py",
    "tests/test_list_keyboard_navigation.py",
    "tests/test_configuration_export_import.py",
    "tests/test_license.py",
    "tests/test_shared_venv.py",
    "tests/test_pyinstaller_preparation.py",
    "run_sara_route_manager.py",
    "sara_route_manager.spec",
    "requirements-dev.txt",
    "Construire_Executable.bat",
)

REQUIRED_DIRECTORIES = (
    "docs",
    "examples",
    "sara_route_manager",
    "sara_route_manager/static",
    "sara_route_manager/templates",
    "tests",
)


class ReleaseCompletenessTests(unittest.TestCase):
    """Détecter immédiatement tout fichier ou répertoire oublié dans le ZIP."""

    def test_required_files(self) -> None:
        """Vérifier que tous les fichiers obligatoires sont présents."""
        missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
        self.assertEqual(missing, [], f"Fichiers obligatoires absents : {missing}")

    def test_required_directories(self) -> None:
        """Vérifier que les répertoires structurants sont présents."""
        missing = [name for name in REQUIRED_DIRECTORIES if not (ROOT / name).is_dir()]
        self.assertEqual(missing, [], f"Répertoires obligatoires absents : {missing}")


if __name__ == "__main__":
    unittest.main()
