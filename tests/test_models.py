# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_models
Description : Tests unitaires des modèles et du décodage SARA.
Classes présentes :
- ModelTests : tests des charges JSON et validations, et de l'option B
  (persistance locale du type IALA d'origine d'un point).
"""

__version__ = "0.2.0"
__date__ = "2026-08-04"

import unittest

from sara_route_manager.models import SaraRoute, ValidationError, Waypoint


class ModelTests(unittest.TestCase):
    """Vérifier les structures JSON, UUID et limites géographiques."""

    def test_sara_payload(self) -> None:
        """Vérifier les propriétés exigées par CruiseCourse.decode."""
        route = SaraRoute("Test", [Waypoint("A", 47.0, -3.0), Waypoint("B", 48.0, -4.0)])
        payload = route.to_sara_dict("uid-test")
        self.assertEqual(payload["status"], 2)
        self.assertEqual(payload["owner"], "uid-test")
        self.assertEqual(payload["points"][0]["distanceThreshold"], 100.0)
        self.assertFalse(payload["reversed"])

    def test_decode_remote_route(self) -> None:
        """Vérifier qu’une route Firebase conserve ses identifiants."""
        data = {
            "id": "ROUTE-ID",
            "name": "Route distante",
            "owner": "OWNER-ID",
            "lastUpdateTime": "2026-07-26_20:00:00",
            "reversed": False,
            "points": [
                {"id": "P1", "name": "A", "distanceThreshold": 100.0, "gpsPosition": {"id": "G1", "latitude": 47.0, "longitude": -3.0}},
                {"id": "P2", "name": "B", "distanceThreshold": 150.0, "gpsPosition": {"id": "G2", "latitude": 48.0, "longitude": -4.0}},
            ],
        }
        route = SaraRoute.from_sara_dict(data, remote_key="Route distante")
        self.assertEqual(route.id, "ROUTE-ID")
        self.assertEqual(route.owner, "OWNER-ID")
        self.assertEqual(route.points[1].gps_id, "G2")

    def test_invalid_latitude(self) -> None:
        """Refuser une latitude impossible."""
        with self.assertRaises(ValidationError):
            Waypoint.from_form({"name": "A", "latitude": 91, "longitude": 0, "distance_threshold": 100})

    def test_forbidden_route_name(self) -> None:
        """Refuser les caractères interdits dans une clé Firebase."""
        route = SaraRoute("A/B", [Waypoint("A", 1, 1), Waypoint("B", 2, 2)])
        with self.assertRaises(ValidationError):
            route.validate()

    def test_sara_dict_never_leaks_object_code(self) -> None:
        """Vérifier que object_code et properties ne fuient jamais vers le format SARA.

        Le format échangé avec SARA Navigation ne doit avoir aucune trace
        du type d'origine d'un point (option B) : ce n'est pas un oubli de
        leur part, un point de route n'a plus besoin de connaître son type
        une fois devenu un simple point de passage GPS.
        """
        point = Waypoint("Balise", 47.0, -3.0, object_code="BCNLAT", properties={"Object name": "Balise"})
        payload = point.to_sara_dict()
        self.assertNotIn("objectCode", payload)
        self.assertNotIn("properties", payload)
        self.assertEqual(set(payload.keys()), {"id", "name", "distanceThreshold", "gpsPosition"})

    def test_local_dict_round_trip_preserves_object_code(self) -> None:
        """Vérifier que object_code et properties survivent à un enregistrement/relecture local.

        C'est la correction directe du manque identifié après analyse du
        code source iOS : sans cette option B, le type IALA d'un point
        disparaissait dès qu'une route était enregistrée puis rouverte.
        """
        point = Waypoint(
            "Balise",
            47.0,
            -3.0,
            object_code="BCNLAT",
            properties={"Category of lateral mark": "port hand"},
        )
        route = SaraRoute("Route de test", [point, Waypoint("B", 48.0, -4.0)])
        local_dict = route.to_local_dict()
        self.assertEqual(local_dict["points"][0]["objectCode"], "BCNLAT")
        self.assertEqual(local_dict["points"][0]["properties"], {"Category of lateral mark": "port hand"})

        reloaded = SaraRoute.from_local_dict(local_dict, remote_key="Route de test")
        self.assertEqual(reloaded.points[0].object_code, "BCNLAT")
        self.assertEqual(reloaded.points[0].properties, {"Category of lateral mark": "port hand"})
        # Un point sans type d'origine (saisie manuelle) reste un simple
        # point générique, sans que ce soit une erreur.
        self.assertEqual(reloaded.points[1].object_code, "")

    def test_route_received_from_sara_has_no_object_code(self) -> None:
        """Vérifier qu'une route reçue de SARA Navigation redevient générique, sans erreur.

        `from_local_dict` doit accepter aussi bien un fichier local complet
        (avec `objectCode`) qu'une route strictement au format SARA (sans
        ce champ) : dans ce second cas, les points restent génériques,
        sans icône IALA associée — c'est le comportement attendu, pas un
        défaut de chargement.
        """
        sara_style_data = {
            "id": "ROUTE-ID",
            "name": "Route reçue de SARA",
            "points": [
                {"id": "P1", "name": "A", "distanceThreshold": 100.0, "gpsPosition": {"id": "G1", "latitude": 47.0, "longitude": -3.0}},
                {"id": "P2", "name": "B", "distanceThreshold": 100.0, "gpsPosition": {"id": "G2", "latitude": 48.0, "longitude": -4.0}},
            ],
        }
        route = SaraRoute.from_local_dict(sara_style_data, remote_key="Route reçue de SARA")
        self.assertEqual(route.points[0].object_code, "")
        self.assertEqual(route.points[0].properties, {})


if __name__ == "__main__":
    unittest.main()
