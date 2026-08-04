# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_coastline
Description : Tests unitaires du module de récupération du trait de côte,
avec le réseau entièrement simulé (aucun appel WFS réel pendant les tests).
Classes présentes :
- TestFetchCoastline : test_limite_terre_mer_used_when_features_present,
  test_falls_back_to_histolitt_when_empty,
  test_falls_back_to_histolitt_on_error, test_raises_when_both_fail,
  test_srsname_requests_wgs84.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

import json
from unittest.mock import patch, MagicMock

import pytest

from sara_route_manager.coastline import (
    CoastlineError,
    LIMITE_TERRE_MER_TYPENAME,
    HISTOLITT_TYPENAME,
    fetch_coastline,
)


def _fake_response(payload: dict) -> MagicMock:
    """Construire un faux objet de réponse HTTP pour simuler urlopen()."""
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.status = 200
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)
    return response


class TestFetchCoastline:
    """Vérifier la logique de repli Limite terre-mer → HISTOLITT."""

    def test_limite_terre_mer_used_when_features_present(self) -> None:
        """Utiliser Limite terre-mer directement si elle renvoie des entités."""
        payload = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
        with patch("sara_route_manager.coastline.urlopen", return_value=_fake_response(payload)) as mocked:
            result = fetch_coastline(47.5, 47.9, -3.5, -3.2)
        assert result["layer"] == "limite_terre_mer"
        assert result["geojson"] == payload
        assert mocked.call_count == 1

    def test_falls_back_to_histolitt_when_empty(self) -> None:
        """Basculer sur HISTOLITT si Limite terre-mer ne renvoie aucune entité."""
        empty_payload = {"type": "FeatureCollection", "features": []}
        histolitt_payload = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
        responses = [_fake_response(empty_payload), _fake_response(histolitt_payload)]
        with patch("sara_route_manager.coastline.urlopen", side_effect=responses) as mocked:
            result = fetch_coastline(-21.2, -20.9, 55.2, 55.5)  # ex. La Réunion
        assert result["layer"] == "histolitt"
        assert mocked.call_count == 2

    def test_falls_back_to_histolitt_on_error(self) -> None:
        """Basculer sur HISTOLITT si la requête Limite terre-mer échoue franchement."""
        histolitt_payload = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
        with patch(
            "sara_route_manager.coastline.urlopen",
            side_effect=[TimeoutError("délai dépassé"), _fake_response(histolitt_payload)],
        ):
            result = fetch_coastline(-21.2, -20.9, 55.2, 55.5)
        assert result["layer"] == "histolitt"

    def test_raises_when_both_fail(self) -> None:
        """Lever CoastlineError si les deux couches échouent."""
        with patch(
            "sara_route_manager.coastline.urlopen",
            side_effect=[TimeoutError("délai dépassé"), TimeoutError("délai dépassé")],
        ):
            with pytest.raises(CoastlineError):
                fetch_coastline(47.5, 47.9, -3.5, -3.2)

    def test_srsname_requests_wgs84(self) -> None:
        """Vérifier que la requête demande une reprojection en WGS84.

        La couche Limite terre-mer est nativement en Lambert 93
        (EPSG:2154, visible dans son propre nom de couche) : demander
        SRSNAME=EPSG:4326 au serveur évite une dépendance à pyproj/GDAL
        pour reprojeter nous-mêmes.
        """
        payload = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
        with patch("sara_route_manager.coastline.urlopen", return_value=_fake_response(payload)) as mocked:
            fetch_coastline(47.5, 47.9, -3.5, -3.2)
        request = mocked.call_args[0][0]
        assert "SRSNAME=EPSG%3A4326" in request.full_url
        assert LIMITE_TERRE_MER_TYPENAME.replace(":", "%3A") in request.full_url or LIMITE_TERRE_MER_TYPENAME in request.full_url
