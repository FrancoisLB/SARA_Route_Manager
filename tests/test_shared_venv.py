# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_shared_venv
Description : Vérifie que l'environnement virtuel Python est créé et
réutilisé à un emplacement partagé et stable (`%LOCALAPPDATA%\\SARA Route
Manager\\venv`), en dehors des dossiers versionnés — corrige la friction de
distribution où l'utilisateur recopiait manuellement le `.venv` de la
version précédente à chaque nouvelle livraison (groupe 5, phase E).
Classes présentes :
- TestSharedVenv : test_installer_uses_shared_venv_location,
  test_installer_no_longer_creates_local_venv,
  test_installer_exports_venv_python_path_to_caller,
  test_launchers_use_exported_venv_python_path,
  test_gitignore_comment_reflects_shared_location.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestSharedVenv:
    """Vérifier le passage à un environnement virtuel Python partagé et stable."""

    def test_installer_uses_shared_venv_location(self) -> None:
        """Vérifier qu'Installer.bat cible %LOCALAPPDATA%\\SARA Route Manager\\venv."""
        content = (ROOT / "Installer.bat").read_text(encoding="utf-8")
        assert 'set "VENV_DIR=%LOCALAPPDATA%\\SARA Route Manager\\venv"' in content

    def test_installer_no_longer_creates_local_venv(self) -> None:
        """Vérifier qu'aucune création ou vérification ne cible plus le dossier local `.venv`."""
        content = (ROOT / "Installer.bat").read_text(encoding="utf-8")
        assert '.venv\\Scripts\\python.exe' not in content
        assert "-m venv .venv" not in content
        assert "%VENV_DIR%\\Scripts\\python.exe" in content

    def test_installer_exports_venv_python_path_to_caller(self) -> None:
        """Vérifier qu'Installer.bat rend le chemin du Python partagé disponible au script appelant.

        Technique `endlocal & set` : nécessaire pour qu'un script appelant
        (`Lancer_*.bat`) reçoive la variable au-delà de la portée locale
        d'Installer.bat.
        """
        content = (ROOT / "Installer.bat").read_text(encoding="utf-8")
        assert (
            'endlocal & set "SARA_VENV_PYTHON=%LOCALAPPDATA%\\SARA Route Manager\\venv\\Scripts\\python.exe"'
            in content
        )

    def test_launchers_use_exported_venv_python_path(self) -> None:
        """Vérifier que les deux scripts de lancement utilisent la variable partagée, pas un chemin local."""
        for filename in ("Lancer_SARA_Route_Manager.bat", "Lancer_Mode_Navigateur.bat"):
            content = (ROOT / filename).read_text(encoding="utf-8")
            assert '"%SARA_VENV_PYTHON%"' in content
            assert '.venv\\Scripts\\python.exe' not in content
            assert "call Installer.bat" in content

    def test_gitignore_comment_reflects_shared_location(self) -> None:
        """Vérifier que le commentaire du .gitignore reflète le nouvel emplacement, pas l'ancien."""
        content = (ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "%LOCALAPPDATA%\\SARA Route" in content
        assert ".venv/" in content  # conservé par précaution, voir commentaire
