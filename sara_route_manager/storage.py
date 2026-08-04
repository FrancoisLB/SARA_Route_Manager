# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.storage
Description : Sauvegarde, lecture et index local des routes SARA.
Classes présentes :
- LocalRouteStorage : set_directory, save, list_routes, load.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

import json
import re
from pathlib import Path
from typing import Any

from .models import SaraRoute, ValidationError


class LocalRouteStorage:
    """Gérer les routes dans le répertoire défini par la configuration."""

    def __init__(self, directory: Path) -> None:
        """Initialiser le stockage local.

        Parameters
        ----------
        directory : pathlib.Path
            Dossier autorisé pour les routes locales.
        """
        self.set_directory(directory)

    def set_directory(self, directory: Path) -> None:
        """Changer le dossier de stockage et le créer si nécessaire.

        Parameters
        ----------
        directory : pathlib.Path
            Nouveau dossier des routes.
        """
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, route: SaraRoute) -> Path:
        """Sauvegarder une route au format JSON UTF-8."""
        safe_name = re.sub(r"[^A-Za-z0-9 _-]", "_", route.name).strip() or "route"
        path = self.directory / f"{safe_name}.json"
        path.write_text(json.dumps(route.to_local_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def list_routes(self) -> list[dict[str, Any]]:
        """Lister les fichiers locaux valides avec leurs informations principales."""
        result: list[dict[str, Any]] = []
        for path in sorted(self.directory.glob("*.json"), key=lambda item: item.name.casefold()):
            try:
                route = self.load(path.name)
            except (OSError, ValueError, ValidationError):
                continue
            result.append({"file": path.name, "name": route.name, "points_count": len(route.points), "last_update_time": route.last_update_time, "remote_key": route.remote_key})
        return result

    def load(self, filename: str) -> SaraRoute:
        """Lire une route locale en bloquant toute sortie du dossier autorisé."""
        path = self.directory / Path(filename).name
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValidationError("Le fichier local ne contient pas une route valide.")
        return SaraRoute.from_local_dict(data, remote_key=data.get("remoteKey"))
