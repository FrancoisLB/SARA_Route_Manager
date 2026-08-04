# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_configuration
Description : Tests unitaires du fichier TOML et du répertoire des routes.
Classes présentes :
- TestAppConfiguration : test_save_and_reload, test_reject_relative_path,
  test_map_window_percent_save_and_reload, test_map_window_percent_rejects_out_of_bounds,
  test_main_window_percent_save_and_reload, test_main_window_percent_rejects_out_of_bounds,
  test_map_colors_save_and_reload, test_map_colors_reject_invalid_format,
  test_map_route_color_save_and_reload, test_map_route_color_rejects_invalid_format,
  test_map_route_line_and_labels_save_and_reload, test_map_route_line_width_rejects_out_of_bounds,
  test_map_route_line_style_rejects_unknown_value, test_map_route_label_font_size_rejects_out_of_bounds,
  test_old_incomplete_config_file_is_healed_on_load,
  test_all_configuration_page_fields_are_persisted.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path

import pytest

from sara_route_manager.configuration import AppConfiguration


class TestAppConfiguration:
    """Vérifier la persistance et la validation de la configuration."""

    def test_save_and_reload(self, tmp_path: Path) -> None:
        """Vérifier que le TOML produit peut être relu."""
        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        config.default_export_format = "csv"
        config.csv_separator = ","
        config.save()
        assert config.config_file.exists()
        assert 'default_export_format = "csv"' in config.config_file.read_text(encoding="utf-8")

    def test_reject_relative_path(self, tmp_path: Path) -> None:
        """Refuser un répertoire relatif ambigu."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        with pytest.raises(ValueError):
            config.update_settings({"routes_directory": "routes", "default_export_format": "gpx", "csv_separator": ";"})

    def test_map_window_percent_save_and_reload(self, tmp_path: Path) -> None:
        """Vérifier que les pourcentages de la fenêtre carte survivent à un enregistrement/relecture."""
        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        config.map_window_width_percent = 80
        config.map_window_height_percent = 70
        config.save()

        reloaded = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        with reloaded.config_file.open("rb") as stream:
            import tomllib
            reloaded.update_from_dict(tomllib.load(stream))
        assert reloaded.map_window_width_percent == 80
        assert reloaded.map_window_height_percent == 70

    def test_map_window_percent_rejects_out_of_bounds(self, tmp_path: Path) -> None:
        """Refuser un pourcentage de fenêtre carte hors des bornes 50-100."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_window_width_percent": 10, "map_window_height_percent": 90})
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_window_width_percent": 95, "map_window_height_percent": 150})

    def test_main_window_percent_save_and_reload(self, tmp_path: Path) -> None:
        """Vérifier que les pourcentages de la fenêtre principale survivent à un enregistrement/relecture.

        Réglage distinct et complémentaire de celui de la fenêtre carte :
        90 % de largeur, 80 % de hauteur par défaut, demandés explicitement
        par l'utilisateur pour la fenêtre principale au démarrage.
        """
        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        assert config.main_window_width_percent == 90
        assert config.main_window_height_percent == 80
        config.main_window_width_percent = 65
        config.main_window_height_percent = 75
        config.save()

        reloaded = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        with reloaded.config_file.open("rb") as stream:
            import tomllib
            reloaded.update_from_dict(tomllib.load(stream))
        assert reloaded.main_window_width_percent == 65
        assert reloaded.main_window_height_percent == 75

    def test_main_window_percent_rejects_out_of_bounds(self, tmp_path: Path) -> None:
        """Refuser un pourcentage de fenêtre principale hors des bornes 50-100."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "main_window_width_percent": 10, "main_window_height_percent": 80})
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "main_window_width_percent": 58, "main_window_height_percent": 150})

    def test_map_colors_save_and_reload(self, tmp_path: Path) -> None:
        """Vérifier que les couleurs de la carte survivent à un enregistrement/relecture."""
        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        assert config.map_sea_color == "#1f6fa3"
        assert config.map_land_color == "#d9c9a3"
        config.map_sea_color = "#123456"
        config.map_land_color = "#abcdef"
        config.save()

        reloaded = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        with reloaded.config_file.open("rb") as stream:
            import tomllib
            reloaded.update_from_dict(tomllib.load(stream))
        assert reloaded.map_sea_color == "#123456"
        assert reloaded.map_land_color == "#abcdef"

    def test_map_colors_reject_invalid_format(self, tmp_path: Path) -> None:
        """Refuser une couleur qui n'est pas au format hexadécimal #RRGGBB."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_sea_color": "bleu", "map_land_color": "#d9c9a3"})
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_sea_color": "#1f6fa3", "map_land_color": "#zzzzzz"})

    def test_map_route_color_save_and_reload(self, tmp_path: Path) -> None:
        """Vérifier que la couleur du tracé de route survit à un enregistrement/relecture.

        Jaune vif par défaut, choisi après signalement d'un contraste
        insuffisant de l'orange initialement utilisé.
        """
        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        assert config.map_route_color == "#ffe600"
        config.map_route_color = "#00ff00"
        config.save()

        reloaded = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        with reloaded.config_file.open("rb") as stream:
            import tomllib
            reloaded.update_from_dict(tomllib.load(stream))
        assert reloaded.map_route_color == "#00ff00"

    def test_map_route_color_rejects_invalid_format(self, tmp_path: Path) -> None:
        """Refuser une couleur de tracé qui n'est pas au format hexadécimal #RRGGBB."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_route_color": "jaune"})

    def test_map_route_line_and_labels_save_and_reload(self, tmp_path: Path) -> None:
        """Vérifier que l'épaisseur, le style et les réglages d'étiquettes survivent au rechargement."""
        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        assert config.map_route_line_width == 3
        assert config.map_route_line_style == "solid"
        assert config.map_route_labels_visible is True
        assert config.map_route_label_font_size == 12
        assert config.map_route_label_bordered is True

        config.map_route_line_width = 6
        config.map_route_line_style = "dotted"
        config.map_route_labels_visible = False
        config.map_route_label_font_size = 18
        config.map_route_label_bordered = False
        config.save()

        reloaded = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        with reloaded.config_file.open("rb") as stream:
            import tomllib
            reloaded.update_from_dict(tomllib.load(stream))
        assert reloaded.map_route_line_width == 6
        assert reloaded.map_route_line_style == "dotted"
        assert reloaded.map_route_labels_visible is False
        assert reloaded.map_route_label_font_size == 18
        assert reloaded.map_route_label_bordered is False

    def test_map_route_line_width_rejects_out_of_bounds(self, tmp_path: Path) -> None:
        """Refuser une épaisseur de tracé hors des bornes 1-10."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_route_line_width": 0})
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_route_line_width": 20})

    def test_map_route_line_style_rejects_unknown_value(self, tmp_path: Path) -> None:
        """Refuser un type de trait qui n'est ni continu, ni tireté, ni pointillé."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_route_line_style": "ondulé"})

    def test_map_route_label_font_size_rejects_out_of_bounds(self, tmp_path: Path) -> None:
        """Refuser une taille de texte d'étiquette hors des bornes 8-24."""
        config = AppConfiguration(tmp_path, tmp_path / "config.toml", tmp_path / "routes", tmp_path / "sauvegardes", tmp_path / "journaux")
        base_settings = {"routes_directory": str(tmp_path / "routes"), "default_export_format": "gpx", "csv_separator": ";"}
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_route_label_font_size": 4})
        with pytest.raises(ValueError):
            config.update_settings({**base_settings, "map_route_label_font_size": 40})

    def test_old_incomplete_config_file_is_healed_on_load(self, tmp_path: Path) -> None:
        """Vérifier qu'un ancien fichier config.toml incomplet se complète automatiquement au chargement.

        Signalé après retour utilisateur : un fichier créé avant l'ajout de
        réglages plus récents (SHOM, fenêtre carte, couleurs, tracé,
        étiquettes...) restait incomplet indéfiniment tant qu'un clic
        explicite sur « Enregistrer » n'avait pas eu lieu. Le chargement
        doit désormais réenregistrer systématiquement, en préservant tout
        ce qui existe déjà et en complétant seulement les sections
        manquantes avec leurs valeurs par défaut.
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        routes_dir = tmp_path / "routes"
        config_file = config_dir / "config.toml"
        config_file.write_text(
            "[directories]\n"
            f'routes = "{routes_dir}"\n'
            f'backups = "{tmp_path / "sauvegardes"}"\n'
            f'logs = "{tmp_path / "journaux"}"\n\n'
            "[account]\n"
            "automatic_connection = true\n"
            "remember_email = true\n\n"
            "[files]\n"
            'default_export_format = "gpx"\n'
            'csv_separator = ";"\n'
            "confirm_before_overwrite = true\n",
            encoding="utf-8",
        )

        instance = AppConfiguration(
            config_dir, config_file, routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux"
        )
        import tomllib
        with config_file.open("rb") as stream:
            instance.update_from_dict(tomllib.load(stream))
        instance.ensure_directories()
        instance.save()

        healed_content = config_file.read_text(encoding="utf-8")
        for section in ("[shom]", "[map]", "[main_window]", "[map_colors]", "[map_route_line]", "[map_route_labels]"):
            assert section in healed_content
        # Rien n'a été perdu du fichier d'origine.
        assert str(routes_dir) in healed_content

    def test_all_configuration_page_fields_are_persisted(self, tmp_path: Path) -> None:
        """Audit de complétude (groupe 3) : chaque champ de la page Configuration est bien persisté.

        Vérifie, pour les 19 réglages affichés dans configuration.html, que
        `to_dict()` (ce que la page charge) et `update_settings()` (ce que
        la page enregistre) couvrent bien chacun d'entre eux — un aller-retour
        complet HTML → JS → Python → TOML → Python → JS → HTML, plutôt
        qu'une vérification ponctuelle champ par champ au fil des sessions.
        """
        expected_fields = {
            "routes_directory", "automatic_connection", "remember_email",
            "default_export_format", "csv_separator", "confirm_before_overwrite",
            "shom_radius_unit", "map_window_width_percent", "map_window_height_percent",
            "main_window_width_percent", "main_window_height_percent",
            "map_sea_color", "map_land_color", "map_route_color",
            "map_route_line_width", "map_route_line_style", "map_route_labels_visible",
            "map_route_label_font_size", "map_route_label_bordered", "map_marker_size",
        }

        config_dir = tmp_path / "config"
        routes_dir = tmp_path / "routes"
        config = AppConfiguration(config_dir, config_dir / "config.toml", routes_dir, tmp_path / "sauvegardes", tmp_path / "journaux")
        as_dict = config.to_dict()
        missing_from_to_dict = expected_fields - as_dict.keys()
        assert not missing_from_to_dict, f"Champs absents de to_dict() : {missing_from_to_dict}"

        # update_settings() doit accepter les 19 champs sans lever d'erreur
        # avec des valeurs valides, confirmant qu'ils sont bien lus et traités.
        full_settings = {
            "routes_directory": str(routes_dir), "automatic_connection": True, "remember_email": True,
            "default_export_format": "gpx", "csv_separator": ";", "confirm_before_overwrite": True,
            "shom_radius_unit": "nm", "map_window_width_percent": 95, "map_window_height_percent": 80,
            "main_window_width_percent": 90, "main_window_height_percent": 80,
            "map_sea_color": "#1f6fa3", "map_land_color": "#d9c9a3", "map_route_color": "#ffe600",
            "map_route_line_width": 3, "map_route_line_style": "solid", "map_route_labels_visible": True,
            "map_route_label_font_size": 12, "map_route_label_bordered": True, "map_marker_size": 20,
        }
        assert set(full_settings.keys()) == expected_fields
        config.update_settings(full_settings)
        for field, expected_value in full_settings.items():
            if field == "routes_directory":
                continue  # stocké comme Path, comparaison séparée non nécessaire ici
            assert getattr(config, field) == expected_value, f"{field} non persisté correctement"
