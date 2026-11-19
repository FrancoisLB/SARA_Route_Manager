# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_configuration_export_import
Description : Vérifie les endpoints d'export et d'import du fichier de
configuration (groupe 3), ainsi que le dossier initial proposé
(« sauvegardes », réservé jusqu'ici) et la structure de titres hiérarchiques
de la page Configuration.
Classes présentes :
- TestConfigurationExportImport : test_export_returns_toml_attachment,
  test_export_without_saved_file_returns_404, test_import_replaces_settings,
  test_import_rejects_invalid_toml, test_import_rejects_missing_file,
  test_export_import_round_trip_preserves_values.
- TestConfigurationHeadingStructure : test_map_window_zone_has_four_subheadings.
- TestSaveFileDirectoryKind : test_save_file_uses_backups_directory_for_config.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import io
from pathlib import Path

from sara_route_manager.webapp import create_app


class TestConfigurationExportImport:
    """Vérifier le cycle export/import du fichier de configuration."""

    def _client_with_saved_config(self):
        client = create_app().test_client()
        client.post(
            "/api/configuration",
            json={
                "routes_directory": str(Path.home() / "Documents" / "SARA Route Manager" / "routes"),
                "automatic_connection": True,
                "remember_email": True,
                "default_export_format": "gpx",
                "csv_separator": ";",
                "confirm_before_overwrite": True,
                "shom_radius_unit": "nm",
                "map_window_width_percent": 95,
                "map_window_height_percent": 80,
                "main_window_width_percent": 90,
                "main_window_height_percent": 80,
                "map_sea_color": "#1f6fa3",
                "map_land_color": "#d9c9a3",
                "map_route_color": "#ffe600",
                "map_route_line_width": 7,
                "map_route_line_style": "dotted",
                "map_route_labels_visible": False,
                "map_route_label_font_size": 16,
                "map_route_label_bordered": False,
            },
        )
        return client

    def test_export_returns_toml_attachment(self) -> None:
        """Vérifier les en-têtes et le contenu de l'export."""
        client = self._client_with_saved_config()
        response = client.get("/api/configuration/export")
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("application/toml")
        assert response.headers["Content-Disposition"] == 'attachment; filename="config.toml"'
        content = response.get_data(as_text=True)
        assert "width = 7" in content
        assert 'style = "dotted"' in content

    def test_export_without_saved_file_returns_404(self) -> None:
        """Vérifier que le garde-fou « aucun fichier » existe dans le code.

        Scénario en pratique inatteignable via `create_app()` :
        `AppConfiguration.load()` garantit toujours qu'un fichier de
        configuration existe (le crée avec les valeurs par défaut s'il est
        absent) — ce garde-fou protège seulement un cas limite (le fichier
        supprimé manuellement entre le démarrage et l'export), pas testable
        de bout en bout ici, donc vérifié directement dans le code source.
        """
        script = (
            Path(__file__).resolve().parents[1] / "sara_route_manager" / "webapp.py"
        ).read_text(encoding="utf-8")
        export_section = script.split("def export_configuration():")[1][:600]
        assert "if not configuration.config_file.exists():" in export_section
        assert "404" in export_section

    def test_import_replaces_settings(self) -> None:
        """Vérifier qu'importer un fichier remplace bien les réglages actuels."""
        exporter = self._client_with_saved_config()
        exported_content = exporter.get("/api/configuration/export").get_data(as_text=True)

        importer = create_app().test_client()
        response = importer.post(
            "/api/configuration/import",
            data={"file": (io.BytesIO(exported_content.encode("utf-8")), "config.toml")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["configuration"]["map_route_line_width"] == 7
        assert data["configuration"]["map_route_line_style"] == "dotted"
        assert data["configuration"]["map_route_labels_visible"] is False

    def test_import_rejects_invalid_toml(self) -> None:
        """Vérifier qu'un fichier qui n'est pas du TOML valide est refusé proprement."""
        client = create_app().test_client()
        response = client.post(
            "/api/configuration/import",
            data={"file": (io.BytesIO(b"ceci n'est pas du TOML valide {{{"), "config.toml")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert response.get_json()["ok"] is False

    def test_import_rejects_missing_file(self) -> None:
        """Vérifier qu'une requête sans fichier est refusée proprement."""
        client = create_app().test_client()
        response = client.post("/api/configuration/import", data={}, content_type="multipart/form-data")
        assert response.status_code == 400
        assert response.get_json()["ok"] is False

    def test_export_import_round_trip_preserves_values(self) -> None:
        """Vérifier qu'un cycle complet export puis import redonne exactement les mêmes valeurs."""
        client = self._client_with_saved_config()
        before = client.get("/api/configuration").get_json()["configuration"]
        exported_content = client.get("/api/configuration/export").get_data(as_text=True)

        client.post(
            "/api/configuration/import",
            data={"file": (io.BytesIO(exported_content.encode("utf-8")), "config.toml")},
            content_type="multipart/form-data",
        )
        after = client.get("/api/configuration").get_json()["configuration"]
        assert before == after


class TestConfigurationHeadingStructure:
    """Vérifier la structure de titres hiérarchiques de la page Configuration (groupe 3)."""

    def test_map_window_zone_has_four_subheadings(self) -> None:
        """Vérifier les 4 sous-titres h3 de la zone fenêtre carte.

        La zone regroupait 9 champs sous un seul h2, sans sous-titres pour
        naviguer rapidement au clavier entre ces groupes (repéré lors du
        rebalayage du 4 août 2026).
        """
        client = create_app().test_client()
        page = client.get("/configuration").get_data(as_text=True)
        for subheading in ("Taille de la fenêtre", "Couleurs", "Tracé de route", "Étiquettes des points de route"):
            assert f"<h3>{subheading}</h3>" in page


class TestSaveFileDirectoryKind:
    """Vérifier que save_file() propose le bon dossier initial selon le type d'export."""

    def test_save_file_uses_backups_directory_for_config(self) -> None:
        """Vérifier que le paramètre directory_kind='backups' est bien pris en charge.

        Le dossier « sauvegardes » (`backups_directory`) était configuré
        depuis le début du projet mais jamais utilisé jusqu'ici — un
        export de configuration est sémantiquement une sauvegarde des
        réglages, à sa place dans ce dossier plutôt que dans « routes »
        (utilisé par tous les autres exports).
        """
        script = (
            Path(__file__).resolve().parents[1] / "sara_route_manager" / "__main__.py"
        ).read_text(encoding="utf-8")
        assert 'directory_kind: str = "routes"' in script
        assert "configuration.backups_directory if directory_kind ==" in script
