# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_map_marks_endpoint
Description : Vérifie l'endpoint de récupération des marques SHOM pour la
fenêtre de visualisation cartographique, réseau entièrement simulé.
Classes présentes :
- TestMapMarksEndpoint : test_marks_endpoint_contract,
  test_marks_endpoint_unknown_token, test_marks_endpoint_shom_error,
  test_marks_endpoint_radius_covers_route.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from unittest.mock import patch

from sara_route_manager.shom import ShomImportError
from sara_route_manager.webapp import create_app


def _create_token(client, points):
    payload = {"name": "Route de test", "points": points}
    response = client.post("/api/map/token", json=payload)
    return response.get_json()["token"]


class TestMapMarksEndpoint:
    """Vérifier le contrat de l'endpoint /api/map/marks/<jeton>."""

    def test_marks_endpoint_contract(self) -> None:
        """Vérifier qu'une marque reçoit bien son icône, et qu'une autre sans info reçoit None."""
        client = create_app().test_client()
        token = _create_token(
            client,
            [
                {"name": "Départ", "latitude": 47.7, "longitude": -3.4},
                {"name": "Arrivée", "latitude": 47.75, "longitude": -3.35},
            ],
        )
        fake_marks = [
            {
                "name": "Balise test",
                "latitude": 47.72,
                "longitude": -3.38,
                "object_code": "BCNLAT",
                "category": "Latérale",
                "description": "",
                "source_id": "",
                "properties": {"Category of lateral mark": "port hand"},
            },
            {
                "name": "Bouée sans info",
                "latitude": 47.73,
                "longitude": -3.37,
                "object_code": "BOYCAR",
                "category": "Cardinale",
                "description": "",
                "source_id": "",
                "properties": {},
            },
        ]
        with patch("sara_route_manager.webapp.download_shom_marks", return_value=fake_marks):
            response = client.get(f"/api/map/marks/{token}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["marks"][0]["icon_filename"] == "BCNLAT_B.svg"
        assert data["marks"][1]["icon_filename"] is None

    def test_marks_endpoint_unknown_token(self) -> None:
        """Vérifier qu'un jeton inconnu renvoie 404."""
        client = create_app().test_client()
        response = client.get("/api/map/marks/jeton-inconnu")
        assert response.status_code == 404

    def test_marks_endpoint_shom_error(self) -> None:
        """Vérifier qu'un échec du WFS reste une erreur 502 gracieuse."""
        client = create_app().test_client()
        token = _create_token(
            client,
            [{"latitude": 1, "longitude": 1}, {"latitude": 2, "longitude": 2}],
        )
        with patch(
            "sara_route_manager.webapp.download_shom_marks",
            side_effect=ShomImportError("réseau indisponible"),
        ):
            response = client.get(f"/api/map/marks/{token}")
        assert response.status_code == 502
        assert response.get_json()["ok"] is False

    def test_marks_endpoint_radius_covers_route(self) -> None:
        """Vérifier que le rayon transmis couvre bien toute l'étendue de la route.

        Le rayon doit être au moins égal à la distance du centre au point
        le plus éloigné de la route, avec une marge de contexte.
        """
        client = create_app().test_client()
        token = _create_token(
            client,
            [
                {"latitude": 47.6, "longitude": -3.5},
                {"latitude": 47.9, "longitude": -3.1},
            ],
        )
        with patch("sara_route_manager.webapp.download_shom_marks", return_value=[]) as mocked:
            client.get(f"/api/map/marks/{token}")
        center_lat, center_lon, radius_nm, unit = mocked.call_args[0]
        assert unit == "nm"
        assert 47.6 <= center_lat <= 47.9
        assert -3.5 <= center_lon <= -3.1
        assert radius_nm >= 1.0
