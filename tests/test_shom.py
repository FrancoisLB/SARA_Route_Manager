# -*- coding: utf-8 -*-
from __future__ import annotations

"""Tests du module web de marques SHOM."""

import json
from unittest.mock import patch

from sara_route_manager.shom import SARA_FEATURE_TYPES, download_shom_marks


class _Response:
    """Simuler une réponse HTTP du serveur WFS."""
    def __init__(self, payload: dict) -> None:
        self._data = json.dumps(payload).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def read(self) -> bytes:
        return self._data


def test_download_shom_marks_from_sara_wfs() -> None:
    payload = {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"foid": "123", "Object name": "Bouée test", "featureType": "lateral", "Category of lateral mark": "port-hand"},
        "geometry": {"type": "Point", "coordinates": [-3.0, 47.0]},
    }]}
    with patch("sara_route_manager.shom.urlopen", return_value=_Response(payload)) as mocked:
        marks = download_shom_marks(47.0, -3.0, 1.0, "nm", {"Latérale"})
    assert len(marks) == len([x for x in SARA_FEATURE_TYPES if x in {"BCNLAT", "BOYLAT"}])
    assert marks[0]["name"] == "Bouée test"
    assert mocked.call_count == len(SARA_FEATURE_TYPES)


def test_kilometres_are_converted_before_request() -> None:
    payload = {"type": "FeatureCollection", "features": []}
    with patch("sara_route_manager.shom.urlopen", return_value=_Response(payload)) as mocked:
        download_shom_marks(47.0, -3.0, 1.852, "km", set())
    requested_url = mocked.call_args_list[0].args[0].full_url
    assert "LENGTH=1.0" in requested_url


def test_shom_mark_preserves_web_properties():
    """Vérifier que les propriétés WFS restent disponibles pour les détails."""
    from sara_route_manager.shom import _mark_from_sara_feature

    feature = {
        "geometry": {"coordinates": [-3.1, 47.7]},
        "properties": {
            "Object name": "Balise test",
            "foid": "ABC123",
            "Colour": ["red", "green"],
            "Light character": "Fl(2) 6s",
        },
    }
    mark = _mark_from_sara_feature(feature, "BOYLAT")
    assert mark is not None
    data = mark.to_dict(1.852)
    assert data["properties"]["Light character"] == "Fl(2) 6s"
    assert data["properties"]["Colour"] == "red, green"
