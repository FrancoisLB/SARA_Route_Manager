# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.coastline
Description : Récupération du trait de côte (limite terre/mer) auprès du
service WFS officiel du SHOM, pour affichage sur la fenêtre de
visualisation cartographique.

Interroge d'abord la couche « Limite terre-mer » (recommandée, couvre la
France métropolitaine). Si elle ne renvoie aucune entité pour l'emprise
demandée, se rabat automatiquement sur « Trait de Côte HISTOLITT® »
(nécessaire pour l'outre-mer, où « Limite terre-mer » n'existe pas encore) —
sans qu'aucune carte de référence des frontières ne soit maintenue par
l'application elle-même.

AVERTISSEMENT : le nom exact de la couche « Limite terre-mer » a été vérifié
via la fiche de métadonnées officielle du SHOM. Celui d'HISTOLITT n'a pas pu
être confirmé de la même façon (accès réseau limité pendant le
développement) : il s'agit d'une meilleure estimation, à vérifier sur un
poste ayant un accès réel au service, par exemple via une requête
``GetCapabilities`` sur ``SHOM_WFS_URL``.

Classes présentes :
- CoastlineError
Fonctions présentes :
- fetch_coastline
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SHOM_WFS_URL = "https://services.data.shom.fr/INSPIRE/wfs"

# Vérifié via la fiche de métadonnées officielle du SHOM (couche polygones,
# la plus adaptée pour distinguer visuellement terre et mer).
LIMITE_TERRE_MER_TYPENAME = "LIMTM_2154_WFS:limite_terre_mer_france_metropolitaine_polygones"

# NON CONFIRMÉ — meilleure estimation en l'absence d'accès réseau pour la
# vérifier directement. À corriger après une requête GetCapabilities réelle
# si le repli outre-mer ne fonctionne pas.
HISTOLITT_TYPENAME = "TCH_FRA:trait_de_cote_histolitt"

# Citations exactes exigées par les fiches de métadonnées officielles.
ATTRIBUTION_LIMITE_TERRE_MER = "Shom-IGN, 2021. https://dx.doi.org/10.17183/LIMTM"
ATTRIBUTION_HISTOLITT = "© IGN-Shom 2009"


class CoastlineError(Exception):
    """Erreur lors de la récupération du trait de côte."""


def _fetch_typename(
    typename: str,
    bbox: tuple[float, float, float, float],
    timeout: float,
) -> dict[str, Any]:
    """Interroger une couche WFS et renvoyer sa réponse GeoJSON décodée.

    Parameters
    ----------
    typename : str
        Nom complet (espace de noms inclus) de la couche WFS interrogée.
    bbox : tuple of float
        Emprise ``(min_longitude, min_latitude, max_longitude, max_latitude)``
        en degrés décimaux WGS84.
    timeout : float
        Délai maximal de la requête HTTP, en secondes.

    Returns
    -------
    dict[str, Any]
        Réponse GeoJSON décodée (``FeatureCollection``).

    Raises
    ------
    CoastlineError
        Si la requête échoue ou si la réponse n'est pas un JSON exploitable.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    parameters = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": typename,
        # Demander explicitement une reprojection en WGS84 au serveur :
        # la couche "Limite terre-mer" est nativement en Lambert 93
        # (EPSG:2154, visible dans son propre nom de couche), et éviter une
        # dépendance à pyproj/GDAL pour reprojeter nous-mêmes est un des
        # principes déjà posés pour ce chantier.
        "SRSNAME": "EPSG:4326",
        "BBOX": f"{min_lon},{min_lat},{max_lon},{max_lat},EPSG:4326",
        "OUTPUTFORMAT": "application/json",
        "COUNT": "500",
    }
    request_url = f"{SHOM_WFS_URL}?{urlencode(parameters)}"
    request = Request(
        request_url,
        headers={
            "User-Agent": "SARA-Route-Manager/0.7.0",
            "Accept": "application/json",
            "Connection": "close",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw_payload = response.read()
            status = getattr(response, "status", 200)
            if status != 200:
                raise CoastlineError(f"réponse HTTP {status} pour la couche {typename}.")
            return json.loads(raw_payload.decode("utf-8-sig"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoastlineError(f"Impossible d’interroger la couche {typename} : {exc}") from exc


def fetch_coastline(
    min_latitude: float,
    max_latitude: float,
    min_longitude: float,
    max_longitude: float,
    *,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Récupérer le trait de côte pour une emprise géographique donnée.

    Parameters
    ----------
    min_latitude, max_latitude, min_longitude, max_longitude : float
        Emprise géographique en degrés décimaux WGS84.
    timeout : float, optional
        Délai maximal d'une requête HTTP, en secondes.

    Returns
    -------
    dict[str, Any]
        ``{"geojson": ..., "layer": "limite_terre_mer" | "histolitt", "attribution": str}``.

    Raises
    ------
    CoastlineError
        Si ni « Limite terre-mer » ni « Trait de Côte HISTOLITT® » n'ont pu
        être interrogées avec succès pour cette emprise.
    """
    bbox = (min_longitude, min_latitude, max_longitude, max_latitude)

    try:
        payload = _fetch_typename(LIMITE_TERRE_MER_TYPENAME, bbox, timeout)
        if payload.get("features"):
            return {
                "geojson": payload,
                "layer": "limite_terre_mer",
                "attribution": ATTRIBUTION_LIMITE_TERRE_MER,
            }
    except CoastlineError:
        pass  # Repli sur Histolitt avant d'abandonner.

    payload = _fetch_typename(HISTOLITT_TYPENAME, bbox, timeout)
    return {
        "geojson": payload,
        "layer": "histolitt",
        "attribution": ATTRIBUTION_HISTOLITT,
    }
