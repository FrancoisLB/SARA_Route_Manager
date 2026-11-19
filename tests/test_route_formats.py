# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_route_formats
Description : Tester les imports et exports CSV, GPX et JSON SARA.
Classes présentes : aucune.
Fonctions principales :
- test_csv_round_trip
- test_gpx_round_trip
- test_json_round_trip
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from sara_route_manager.models import SaraRoute, Waypoint
from sara_route_manager.route_formats import export_route, import_route


def sample_route() -> SaraRoute:
    """Créer une route minimale utilisée par les tests."""
    return SaraRoute(
        name="Route test",
        points=[
            Waypoint(name="Départ", latitude=47.7, longitude=-3.3, distance_threshold=100),
            Waypoint(name="Arrivée", latitude=47.8, longitude=-3.4, distance_threshold=120),
        ],
    )


def check_round_trip(format_name: str) -> None:
    """Vérifier qu’un export puis import conserve les deux points."""
    content, _mime, extension = export_route(sample_route(), format_name)
    imported = import_route(content, f"route.{extension}")
    assert len(imported.points) == 2
    assert imported.points[0].name == "Départ"


def test_csv_round_trip() -> None:
    check_round_trip("csv")


def test_gpx_round_trip() -> None:
    check_round_trip("gpx")


def test_json_round_trip() -> None:
    check_round_trip("json")


def test_import_wpt_textuel():
    """Vérifier l'import d'un fichier WPT simple."""
    from sara_route_manager.route_formats import import_route
    route = import_route(b"Nom;Latitude;Longitude\nA;47.1;-3.1\nB;47.2;-3.2\n", "test.wpt")
    assert route.name == "test"
    assert len(route.points) == 2
    assert route.points[0].source == "wpt"


def test_csv_export_uses_configured_separator() -> None:
    """Vérifier que l'export CSV accepte la virgule et la tabulation."""
    comma_content, _mime, _extension = export_route(
        sample_route(), "csv", csv_delimiter=","
    )
    tab_content, _mime, _extension = export_route(
        sample_route(), "csv", csv_delimiter="\t"
    )

    assert "ordre,nom,latitude" in comma_content.decode("utf-8-sig")
    assert "ordre\tnom\tlatitude" in tab_content.decode("utf-8-sig")


def test_configured_csv_exports_can_be_reimported() -> None:
    """Vérifier la réimportation des CSV à virgule et à tabulation."""
    for delimiter in (",", "\t"):
        content, _mime, extension = export_route(
            sample_route(), "csv", csv_delimiter=delimiter
        )
        imported = import_route(content, f"route.{extension}")
        assert len(imported.points) == 2
        assert imported.points[1].name == "Arrivée"
