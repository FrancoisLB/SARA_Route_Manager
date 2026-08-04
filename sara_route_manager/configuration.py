# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.configuration
Description : Lecture, écriture et validation de la configuration utilisateur TOML.
Classes présentes :
- AppConfiguration : load, save, reset, to_dict, update_from_dict, update_settings, ensure_directories.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from dataclasses import dataclass
import os
from pathlib import Path
import re
import tomllib
from typing import Any

# Couleur hexadécimale à 6 chiffres, telle que produite par un champ
# <input type="color"> de formulaire HTML (ex. "#1f6fa3").
_HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(slots=True)
class AppConfiguration:
    """Gérer les paramètres persistants de SARA Route Manager.

    Attributes
    ----------
    config_directory : pathlib.Path
        Dossier contenant ``config.toml``.
    config_file : pathlib.Path
        Chemin complet du fichier de configuration.
    routes_directory : pathlib.Path
        Dossier unique des routes importées, exportées et locales.
    backups_directory : pathlib.Path
        Dossier réservé aux sauvegardes automatiques.
    logs_directory : pathlib.Path
        Dossier contenant ``journal.txt`` et ses rotations.
    """

    config_directory: Path
    config_file: Path
    routes_directory: Path
    backups_directory: Path
    logs_directory: Path
    default_export_format: str = "gpx"
    csv_separator: str = ";"
    confirm_before_overwrite: bool = True
    automatic_connection: bool = True
    remember_email: bool = True
    shom_radius_unit: str = "nm"
    # Pourcentages distincts car le bandeau des tâches Windows, en bas de
    # l'écran, réduit la hauteur utile disponible par rapport à la largeur.
    map_window_width_percent: int = 95
    map_window_height_percent: int = 80
    # Fenêtre principale : mêmes pourcentages que ceux demandés pour la
    # fenêtre principale au démarrage de l'application, distincts de ceux
    # de la fenêtre de visualisation cartographique ci-dessus.
    main_window_width_percent: int = 90
    main_window_height_percent: int = 80
    # Couleurs par défaut de la carte (mer/terre), réglables aussi en
    # direct dans la fenêtre de visualisation elle-même.
    map_sea_color: str = "#1f6fa3"
    map_land_color: str = "#d9c9a3"
    # Jaune vif par défaut : bon contraste sur le bleu de la mer comme sur
    # le beige de la terre, contrairement à l'orange initialement utilisé,
    # signalé insuffisamment contrasté.
    map_route_color: str = "#ffe600"
    map_route_line_width: int = 3
    map_route_line_style: str = "solid"
    map_route_labels_visible: bool = True
    map_route_label_font_size: int = 12
    map_route_label_bordered: bool = True
    # Largeur des icônes IALA du SHOM sur la carte, en pixels (hauteur
    # calculée au double, les fichiers SVG officiels étant au format
    # 200×400, ancrées au centre plutôt qu'en bas comme un marqueur
    # classique en forme de goutte).
    map_marker_size: int = 20

    @classmethod
    def load(cls) -> "AppConfiguration":
        """Charger la configuration ou créer automatiquement les valeurs par défaut.

        Returns
        -------
        AppConfiguration
            Configuration validée et dossiers utilisateur prêts à l'emploi.
        """
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        config_directory = appdata / "SARA Route Manager"
        workspace = Path.home() / "Documents" / "SARA Route Manager"
        instance = cls(
            config_directory=config_directory,
            config_file=config_directory / "config.toml",
            routes_directory=workspace / "routes",
            backups_directory=workspace / "sauvegardes",
            logs_directory=workspace / "journaux",
        )
        if instance.config_file.exists():
            try:
                with instance.config_file.open("rb") as stream:
                    instance.update_from_dict(tomllib.load(stream))
            except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError):
                # Une configuration endommagée ne doit jamais bloquer le démarrage.
                pass
        instance.ensure_directories()
        # Réenregistrer systématiquement, pas seulement si le fichier est
        # absent : un fichier existant mais antérieur à l'ajout de nouveaux
        # réglages (SHOM, fenêtre carte, couleurs, tracé, étiquettes...) ne
        # contenait sinon ces sections qu'après un clic explicite sur
        # « Enregistrer » dans la page Configuration — repéré après
        # signalement, un vieux fichier restait incomplet indéfiniment sans
        # cette action manuelle. `save()` préserve tout ce qui existe déjà
        # et complète seulement les sections manquantes avec leurs valeurs
        # par défaut, sans rien écraser.
        instance.save()
        return instance

    def ensure_directories(self) -> None:
        """Créer tous les dossiers indispensables au premier lancement."""
        for directory in (
            self.config_directory,
            self.routes_directory,
            self.backups_directory,
            self.logs_directory,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Appliquer des valeurs provenant du fichier TOML.

        Parameters
        ----------
        data : dict[str, Any]
            Structure TOML déjà décodée.
        """
        directories = data.get("directories", {})
        files = data.get("files", {})
        account = data.get("account", {})
        for key, attribute in (
            ("routes", "routes_directory"),
            ("backups", "backups_directory"),
            ("logs", "logs_directory"),
        ):
            value = str(directories.get(key, getattr(self, attribute))).strip()
            if value:
                setattr(self, attribute, Path(value).expanduser())
        format_value = str(files.get("default_export_format", self.default_export_format)).lower()
        if format_value in {"gpx", "csv", "json"}:
            self.default_export_format = format_value
        separator = str(files.get("csv_separator", self.csv_separator))
        if separator == "TAB":
            separator = "	"
        if separator in {";", ",", "	"}:
            self.csv_separator = separator
        self.confirm_before_overwrite = bool(files.get("confirm_before_overwrite", True))
        self.automatic_connection = bool(account.get("automatic_connection", True))
        self.remember_email = bool(account.get("remember_email", True))
        shom = data.get("shom", {})
        radius_unit = str(shom.get("radius_unit", self.shom_radius_unit)).lower()
        if radius_unit in {"nm", "km"}:
            self.shom_radius_unit = radius_unit
        map_section = data.get("map", {})
        for key, attribute in (
            ("width_percent", "map_window_width_percent"),
            ("height_percent", "map_window_height_percent"),
        ):
            try:
                value = int(map_section.get(key, getattr(self, attribute)))
            except (TypeError, ValueError):
                continue
            if 50 <= value <= 100:
                setattr(self, attribute, value)
        main_window_section = data.get("main_window", {})
        for key, attribute in (
            ("width_percent", "main_window_width_percent"),
            ("height_percent", "main_window_height_percent"),
        ):
            try:
                value = int(main_window_section.get(key, getattr(self, attribute)))
            except (TypeError, ValueError):
                continue
            if 50 <= value <= 100:
                setattr(self, attribute, value)
        map_colors_section = data.get("map_colors", {})
        for key, attribute in (
            ("sea", "map_sea_color"),
            ("land", "map_land_color"),
            ("route", "map_route_color"),
        ):
            value = str(map_colors_section.get(key, getattr(self, attribute)))
            if _HEX_COLOR_PATTERN.match(value):
                setattr(self, attribute, value)
        route_line_section = data.get("map_route_line", {})
        try:
            width = int(route_line_section.get("width", self.map_route_line_width))
        except (TypeError, ValueError):
            width = self.map_route_line_width
        if 1 <= width <= 10:
            self.map_route_line_width = width
        style = str(route_line_section.get("style", self.map_route_line_style)).lower()
        if style in {"solid", "dashed", "dotted"}:
            self.map_route_line_style = style
        route_labels_section = data.get("map_route_labels", {})
        self.map_route_labels_visible = bool(
            route_labels_section.get("visible", self.map_route_labels_visible)
        )
        self.map_route_label_bordered = bool(
            route_labels_section.get("bordered", self.map_route_label_bordered)
        )
        try:
            font_size = int(route_labels_section.get("font_size", self.map_route_label_font_size))
        except (TypeError, ValueError):
            font_size = self.map_route_label_font_size
        if 8 <= font_size <= 24:
            self.map_route_label_font_size = font_size

        marks_section = data.get("map_marks", {})
        try:
            marker_size = int(marks_section.get("size", self.map_marker_size))
        except (TypeError, ValueError):
            marker_size = self.map_marker_size
        if 10 <= marker_size <= 60:
            self.map_marker_size = marker_size

    def update_settings(self, data: dict[str, Any]) -> None:
        """Mettre à jour les paramètres modifiables depuis l'interface.

        Parameters
        ----------
        data : dict[str, Any]
            Valeurs transmises par la page Configuration.

        Raises
        ------
        ValueError
            Si le dossier ou le format fourni est invalide.
        """
        routes_text = str(data.get("routes_directory", "")).strip()
        if not routes_text:
            raise ValueError("Le répertoire des routes ne peut pas être vide.")
        routes_path = Path(routes_text).expanduser()
        if not routes_path.is_absolute():
            raise ValueError("Le répertoire des routes doit être indiqué avec un chemin complet.")
        export_format = str(data.get("default_export_format", "gpx")).lower()
        if export_format not in {"gpx", "csv", "json"}:
            raise ValueError("Le format d'export sélectionné n'est pas reconnu.")
        separator = str(data.get("csv_separator", ";"))
        if separator == "TAB":
            separator = "	"
        if separator not in {";", ",", "	"}:
            raise ValueError("Le séparateur CSV sélectionné n'est pas reconnu.")
        self.routes_directory = routes_path
        self.default_export_format = export_format
        self.csv_separator = separator
        self.confirm_before_overwrite = bool(data.get("confirm_before_overwrite", True))
        self.automatic_connection = bool(data.get("automatic_connection", True))
        self.remember_email = bool(data.get("remember_email", True))
        radius_unit = str(data.get("shom_radius_unit", self.shom_radius_unit)).lower()
        if radius_unit not in {"nm", "km"}:
            raise ValueError("L’unité de rayon SHOM doit être NM ou km.")
        self.shom_radius_unit = radius_unit
        for key, attribute, label in (
            ("map_window_width_percent", "map_window_width_percent", "largeur (fenêtre carte)"),
            ("map_window_height_percent", "map_window_height_percent", "hauteur (fenêtre carte)"),
            ("main_window_width_percent", "main_window_width_percent", "largeur (fenêtre principale)"),
            ("main_window_height_percent", "main_window_height_percent", "hauteur (fenêtre principale)"),
        ):
            try:
                value = int(data.get(key, getattr(self, attribute)))
            except (TypeError, ValueError):
                raise ValueError(f"Le pourcentage de {label} doit être un nombre entier.")
            if not 50 <= value <= 100:
                raise ValueError(f"Le pourcentage de {label} doit être compris entre 50 et 100.")
            setattr(self, attribute, value)
        for key, attribute, label in (
            ("map_sea_color", "map_sea_color", "mer"),
            ("map_land_color", "map_land_color", "terre"),
            ("map_route_color", "map_route_color", "tracé de route"),
        ):
            value = str(data.get(key, getattr(self, attribute)))
            if not _HEX_COLOR_PATTERN.match(value):
                raise ValueError(f"La couleur de {label} doit être au format hexadécimal (ex. #1f6fa3).")
            setattr(self, attribute, value)

        try:
            line_width = int(data.get("map_route_line_width", self.map_route_line_width))
        except (TypeError, ValueError):
            raise ValueError("L’épaisseur du tracé de route doit être un nombre entier.")
        if not 1 <= line_width <= 10:
            raise ValueError("L’épaisseur du tracé de route doit être comprise entre 1 et 10.")
        self.map_route_line_width = line_width

        line_style = str(data.get("map_route_line_style", self.map_route_line_style)).lower()
        if line_style not in {"solid", "dashed", "dotted"}:
            raise ValueError("Le type de trait de route doit être continu, tireté ou pointillé.")
        self.map_route_line_style = line_style

        self.map_route_labels_visible = bool(data.get("map_route_labels_visible", self.map_route_labels_visible))
        self.map_route_label_bordered = bool(data.get("map_route_label_bordered", self.map_route_label_bordered))

        try:
            label_font_size = int(data.get("map_route_label_font_size", self.map_route_label_font_size))
        except (TypeError, ValueError):
            raise ValueError("La taille du texte des étiquettes de points doit être un nombre entier.")
        if not 8 <= label_font_size <= 24:
            raise ValueError("La taille du texte des étiquettes de points doit être comprise entre 8 et 24.")
        self.map_route_label_font_size = label_font_size

        try:
            marker_size = int(data.get("map_marker_size", self.map_marker_size))
        except (TypeError, ValueError):
            raise ValueError("La taille des icônes des marques SHOM doit être un nombre entier.")
        if not 10 <= marker_size <= 60:
            raise ValueError("La taille des icônes des marques SHOM doit être comprise entre 10 et 60.")
        self.map_marker_size = marker_size

        self.ensure_directories()

    def to_dict(self) -> dict[str, Any]:
        """Retourner les paramètres non secrets destinés à l'interface.

        Returns
        -------
        dict[str, Any]
            Paramètres et chemins utilisateur.
        """
        return {
            "routes_directory": str(self.routes_directory),
            "backups_directory": str(self.backups_directory),
            "logs_directory": str(self.logs_directory),
            "log_file": str(self.logs_directory / "journal.txt"),
            "config_directory": str(self.config_directory),
            "config_file": str(self.config_file),
            "default_export_format": self.default_export_format,
            "csv_separator": "TAB" if self.csv_separator == "	" else self.csv_separator,
            "confirm_before_overwrite": self.confirm_before_overwrite,
            "automatic_connection": self.automatic_connection,
            "remember_email": self.remember_email,
            "shom_radius_unit": self.shom_radius_unit,
            "map_window_width_percent": self.map_window_width_percent,
            "map_window_height_percent": self.map_window_height_percent,
            "main_window_width_percent": self.main_window_width_percent,
            "main_window_height_percent": self.main_window_height_percent,
            "map_sea_color": self.map_sea_color,
            "map_land_color": self.map_land_color,
            "map_route_color": self.map_route_color,
            "map_route_line_width": self.map_route_line_width,
            "map_route_line_style": self.map_route_line_style,
            "map_route_labels_visible": self.map_route_labels_visible,
            "map_route_label_font_size": self.map_route_label_font_size,
            "map_route_label_bordered": self.map_route_label_bordered,
            "map_marker_size": self.map_marker_size,
        }

    def save(self) -> None:
        """Écrire la configuration dans un fichier TOML lisible."""
        self.ensure_directories()

        def clean(path: Path) -> str:
            """Convertir un chemin Windows en valeur TOML lisible."""
            return str(path).replace("\\", "/").replace('"', '\\"')

        separator = "TAB" if self.csv_separator == "\t" else self.csv_separator
        content = (
            "# Configuration de SARA Route Manager\n"
            "# Le mot de passe SARA n'est jamais enregistré dans ce fichier.\n\n"
            "[directories]\n"
            f'routes = "{clean(self.routes_directory)}"\n'
            f'backups = "{clean(self.backups_directory)}"\n'
            f'logs = "{clean(self.logs_directory)}"\n\n'
            "[account]\n"
            f"automatic_connection = {str(self.automatic_connection).lower()}\n"
            f"remember_email = {str(self.remember_email).lower()}\n\n"
            "[shom]\n"
            f'radius_unit = "{self.shom_radius_unit}"\n\n'
            "[map]\n"
            f"width_percent = {self.map_window_width_percent}\n"
            f"height_percent = {self.map_window_height_percent}\n\n"
            "[main_window]\n"
            f"width_percent = {self.main_window_width_percent}\n"
            f"height_percent = {self.main_window_height_percent}\n\n"
            "[map_colors]\n"
            f'sea = "{self.map_sea_color}"\n'
            f'land = "{self.map_land_color}"\n'
            f'route = "{self.map_route_color}"\n\n'
            "[map_route_line]\n"
            f"width = {self.map_route_line_width}\n"
            f'style = "{self.map_route_line_style}"\n\n'
            "[map_route_labels]\n"
            f"visible = {str(self.map_route_labels_visible).lower()}\n"
            f"bordered = {str(self.map_route_label_bordered).lower()}\n"
            f"font_size = {self.map_route_label_font_size}\n\n"
            "[map_marks]\n"
            f"size = {self.map_marker_size}\n\n"
            "[files]\n"
            f'default_export_format = "{self.default_export_format}"\n'
            f'csv_separator = "{separator}"\n'
            f"confirm_before_overwrite = {str(self.confirm_before_overwrite).lower()}\n"
        )
        self.config_file.write_text(content, encoding="utf-8")

    def reset(self) -> None:
        """Rétablir les valeurs par défaut puis les enregistrer."""
        workspace = Path.home() / "Documents" / "SARA Route Manager"
        self.routes_directory = workspace / "routes"
        self.backups_directory = workspace / "sauvegardes"
        self.logs_directory = workspace / "journaux"
        self.default_export_format = "gpx"
        self.csv_separator = ";"
        self.confirm_before_overwrite = True
        self.automatic_connection = True
        self.remember_email = True
        self.shom_radius_unit = "nm"
        self.map_window_width_percent = 95
        self.map_window_height_percent = 80
        self.main_window_width_percent = 90
        self.main_window_height_percent = 80
        self.map_sea_color = "#1f6fa3"
        self.map_land_color = "#d9c9a3"
        self.map_route_color = "#ffe600"
        self.map_route_line_width = 3
        self.map_route_line_style = "solid"
        self.map_route_labels_visible = True
        self.map_route_label_font_size = 12
        self.map_route_label_bordered = True
        self.map_marker_size = 20
        self.save()
