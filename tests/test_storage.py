# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_storage
Description : Tests d'intégration de l'enregistrement et de la relecture
locale d'une route (fichiers réels sur disque, répertoire temporaire),
avec vérification de l'option B (persistance du type IALA d'origine d'un
point).
Classes présentes :
- TestLocalRouteStorage : test_save_and_load_round_trip,
  test_object_code_survives_save_and_load, test_list_routes_after_save.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path

from sara_route_manager.models import SaraRoute, Waypoint
from sara_route_manager.storage import LocalRouteStorage


class TestLocalRouteStorage:
    """Vérifier l'enregistrement et la relecture d'une route locale, fichiers réels."""

    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        """Vérifier qu'une route survit à un enregistrement/relecture sans perte."""
        storage = LocalRouteStorage(tmp_path)
        route = SaraRoute("Route de test", [Waypoint("A", 47.0, -3.0), Waypoint("B", 48.0, -4.0)])
        path = storage.save(route)
        assert path.exists()

        reloaded = storage.load(path.name)
        assert reloaded.name == "Route de test"
        assert len(reloaded.points) == 2
        assert reloaded.points[0].name == "A"

    def test_object_code_survives_save_and_load(self, tmp_path: Path) -> None:
        """Vérifier que le type IALA d'origine d'un point survit à un enregistrement/relecture réel.

        C'est la vérification de bout en bout de l'option B : sans elle,
        une marque SHOM ajoutée à une route redevenait un point générique
        dès que la route était enregistrée puis rouverte.
        """
        storage = LocalRouteStorage(tmp_path)
        point = Waypoint(
            "Balise latérale",
            47.7,
            -3.4,
            object_code="BCNLAT",
            properties={"Category of lateral mark": "port hand"},
        )
        route = SaraRoute("Tour de Groix", [point, Waypoint("Point manuel", 47.8, -3.5)])
        path = storage.save(route)

        reloaded = storage.load(path.name)
        assert reloaded.points[0].object_code == "BCNLAT"
        assert reloaded.points[0].properties == {"Category of lateral mark": "port hand"}
        # Le point de saisie manuelle reste générique, sans que ce soit une erreur.
        assert reloaded.points[1].object_code == ""

    def test_list_routes_after_save(self, tmp_path: Path) -> None:
        """Vérifier que la route enregistrée apparaît dans la liste des routes locales."""
        storage = LocalRouteStorage(tmp_path)
        route = SaraRoute("Route listée", [Waypoint("A", 1, 1), Waypoint("B", 2, 2)])
        storage.save(route)

        routes = storage.list_routes()
        names = [item["name"] for item in routes]
        assert "Route listée" in names
