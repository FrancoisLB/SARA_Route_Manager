# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_pyinstaller_preparation
Description : Vérifie la préparation de la construction de l'exécutable
Windows autonome avec PyInstaller (groupe 5, phase E, étape 3). La
construction et le test de l'exécutable lui-même nécessitent un poste
Windows, hors de portée de cet environnement de préparation Linux — ces
tests ne vérifient donc que le contenu des fichiers préparés, pas le
résultat d'une construction réelle.
Classes présentes :
- TestPyinstallerPreparation : test_entry_point_script_exists_and_uses_absolute_import,
  test_spec_file_exists_and_targets_entry_point,
  test_spec_file_includes_templates_and_static_data,
  test_spec_file_is_onefile_windowed,
  test_spec_file_declares_hidden_imports,
  test_gitignore_has_explicit_exception_for_spec_file,
  test_dev_requirements_pin_pyinstaller_separately_from_main_requirements,
  test_build_script_uses_shared_venv_and_dev_requirements.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestPyinstallerPreparation:
    """Vérifier les fichiers préparés pour la construction PyInstaller."""

    def test_entry_point_script_exists_and_uses_absolute_import(self) -> None:
        """Vérifier le script d'entrée dédié, avec import absolu plutôt que relatif.

        `sara_route_manager/__main__.py` utilise des imports relatifs, qui
        échoueraient si le fichier était pointé directement comme script
        autonome par PyInstaller — d'où ce petit script d'entrée séparé.
        """
        content = (ROOT / "run_sara_route_manager.py").read_text(encoding="utf-8")
        assert "from sara_route_manager.__main__ import main" in content
        assert "if __name__ == \"__main__\":" in content
        assert "main()" in content

    def test_spec_file_exists_and_targets_entry_point(self) -> None:
        """Vérifier que le fichier .spec cible bien le script d'entrée dédié."""
        content = (ROOT / "sara_route_manager.spec").read_text(encoding="utf-8")
        assert '["run_sara_route_manager.py"]' in content

    def test_spec_file_includes_templates_and_static_data(self) -> None:
        """Vérifier que les templates et fichiers statiques sont bien inclus.

        PyInstaller n'inclut pas automatiquement les fichiers non-Python :
        sans cette déclaration explicite, l'exécutable démarrerait mais
        échouerait à servir les pages (gabarits Jinja et fichiers
        statiques absents du paquet construit).
        """
        content = (ROOT / "sara_route_manager.spec").read_text(encoding="utf-8")
        assert '("sara_route_manager/templates", "sara_route_manager/templates")' in content
        assert '("sara_route_manager/static", "sara_route_manager/static")' in content

    def test_spec_file_is_onefile_windowed(self) -> None:
        """Vérifier la construction en un seul fichier, sans console (application graphique).

        Demandé explicitement (`pyinstaller --onefile ...`) — en
        configuration .spec, un seul EXE() sans COLLECT() équivaut à
        --onefile.
        """
        content = (ROOT / "sara_route_manager.spec").read_text(encoding="utf-8")
        assert "console=False" in content
        assert "COLLECT(" not in content

    def test_spec_file_declares_hidden_imports(self) -> None:
        """Vérifier les imports cachés (backends pywebview et keyring), confirmés en conditions réelles.

        Construction et test réels sur Windows le 4 août 2026 : connexion
        au compte SARA, recherche/ajout de marques SHOM et fenêtre de
        visualisation cartographique tous vérifiés fonctionnels dans
        l'exécutable construit — l'estimation initiale s'est avérée juste.
        """
        content = (ROOT / "sara_route_manager.spec").read_text(encoding="utf-8")
        assert "webview.platforms.edgechromium" in content
        assert "webview.platforms.winforms" in content
        assert "keyring.backends.Windows" in content
        assert "confirmes en conditions reelles" in content

    def test_gitignore_has_explicit_exception_for_spec_file(self) -> None:
        """Vérifier que .gitignore exclut les .spec en général, sauf celui-ci explicitement."""
        content = (ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "*.spec" in content
        assert "!sara_route_manager.spec" in content

    def test_dev_requirements_pin_pyinstaller_separately_from_main_requirements(self) -> None:
        """Vérifier que PyInstaller est une dépendance de construction séparée, pas imposée à l'utilisateur final."""
        dev_requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        assert "pyinstaller" in dev_requirements.lower()
        assert "-r requirements.txt" in dev_requirements
        main_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        assert "pyinstaller" not in main_requirements.lower()

    def test_build_script_uses_shared_venv_and_dev_requirements(self) -> None:
        """Vérifier que le script de construction réutilise le venv partagé et requirements-dev.txt."""
        content = (ROOT / "Construire_Executable.bat").read_text(encoding="utf-8")
        assert "call Installer.bat" in content
        assert '"%SARA_VENV_PYTHON%"' in content
        assert "requirements-dev.txt" in content
        assert "sara_route_manager.spec" in content

    def test_documentation_explains_executable_distribution(self) -> None:
        """Vérifier que la documentation explique le devenir de l'exécutable construit.

        Signalé après question de l'utilisateur : la documentation
        expliquait comment construire l'exécutable, mais pas ce qu'il en
        advient (exclu du dépôt Git, distribution via une Release GitHub).
        """
        specifications = (ROOT / "docs/SPECIFICATIONS.md").read_text(encoding="utf-8")
        assert "Distribution de l'exécutable construit" in specifications
        assert "Release" in specifications
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "Releases" in readme or "*Releases*" in readme
