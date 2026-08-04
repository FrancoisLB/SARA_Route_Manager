# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.shom
Description : Import, normalisation et filtrage géographique de marques nautiques SHOM.
Classes présentes :
- ShomImportError : aucune méthode.
- ShomMark : to_dict.
Fonctions présentes :
- import_shom_marks
- filter_marks
- haversine_distance_km
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from dataclasses import dataclass, field
import csv
import io
import json
import logging
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)


class ShomImportError(ValueError):
    """Signaler un fichier de marques SHOM illisible ou incompatible."""


@dataclass(slots=True, frozen=True)
class ShomMark:
    """Représenter une marque nautique utilisable comme point de route.

    Parameters
    ----------
    name : str
        Nom lisible de la marque.
    latitude : float
        Latitude décimale WGS84.
    longitude : float
        Longitude décimale WGS84.
    object_code : str
        Code d'objet nautique, par exemple ``BOYLAT`` ou ``BCNCAR``.
    category : str
        Catégorie simplifiée affichée dans l'interface.
    description : str, default=""
        Informations complémentaires issues du fichier source.
    source_id : str, default=""
        Identifiant fourni par la source, lorsqu'il existe.
    """

    name: str
    latitude: float
    longitude: float
    object_code: str
    category: str
    description: str = ""
    source_id: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, distance_km: float | None = None) -> dict[str, Any]:
        """Convertir la marque en dictionnaire sérialisable.

        Parameters
        ----------
        distance_km : float | None, optional
            Distance au centre de recherche, en kilomètres.

        Returns
        -------
        dict[str, Any]
            Données destinées à l'interface web locale.
        """
        result: dict[str, Any] = {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "object_code": self.object_code,
            "category": self.category,
            "description": self.description,
            "source_id": self.source_id,
            "properties": self.properties,
        }
        if distance_km is not None:
            result["distance_km"] = round(distance_km, 3)
            result["distance_nm"] = round(distance_km / 1.852, 3)
        return result


_CATEGORY_BY_CODE = {
    "BCNLAT": "Latérale", "BOYLAT": "Latérale",
    "BCNCAR": "Cardinale", "BOYCAR": "Cardinale",
    "BCNISD": "Danger isolé", "BOYISD": "Danger isolé",
    "BCNSAW": "Eaux saines", "BOYSAW": "Eaux saines",
    "BCNSPP": "Marque spéciale", "BOYSPP": "Marque spéciale",
    "LNDMRK": "Amer", "LIGHTS": "Feu",
}


def _first(properties: dict[str, Any], *names: str, default: Any = "") -> Any:
    """Retourner la première propriété présente, sans distinction de casse."""
    lowered = {str(key).lower(): value for key, value in properties.items()}
    for name in names:
        if name.lower() in lowered and lowered[name.lower()] not in (None, ""):
            return lowered[name.lower()]
    return default


def _category(code: str) -> str:
    """Déduire une catégorie simplifiée depuis un code d'objet nautique."""
    normalized = code.strip().upper()
    if normalized in _CATEGORY_BY_CODE:
        return _CATEGORY_BY_CODE[normalized]
    for candidate, category in _CATEGORY_BY_CODE.items():
        if candidate in normalized:
            return category
    return "Autre"


def _validate_coordinates(latitude: Any, longitude: Any) -> tuple[float, float]:
    """Convertir et valider une paire de coordonnées WGS84."""
    try:
        lat = float(str(latitude).replace(",", "."))
        lon = float(str(longitude).replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise ShomImportError("Une marque contient des coordonnées non numériques.") from exc
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ShomImportError("Une marque contient des coordonnées hors limites.")
    return lat, lon


def _mark_from_properties(properties: dict[str, Any], latitude: Any, longitude: Any) -> ShomMark:
    """Construire une marque depuis des propriétés GeoJSON ou CSV."""
    lat, lon = _validate_coordinates(latitude, longitude)
    code = str(_first(properties, "object_code", "code", "objnam", "layer", "type", "classe", default="AUTRE")).upper()
    name = str(_first(properties, "name", "nom", "objnam", "libelle", "label", default=code)).strip() or code
    description = str(_first(properties, "description", "desc", "inform", "remarque", default="")).strip()
    source_id = str(_first(properties, "id", "fid", "identifiant", "lnam", default="")).strip()
    clean_properties = {str(key): value for key, value in properties.items() if value not in (None, "", [])}
    return ShomMark(name, lat, lon, code, _category(code), description, source_id, clean_properties)


def _import_geojson(content: bytes) -> list[ShomMark]:
    """Lire un document GeoJSON FeatureCollection ou Feature."""
    try:
        document = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ShomImportError("Le fichier GeoJSON n'est pas un JSON UTF-8 valide.") from exc
    features = document.get("features", []) if document.get("type") == "FeatureCollection" else [document]
    marks: list[ShomMark] = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            continue
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            continue
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        marks.append(_mark_from_properties(properties, coordinates[1], coordinates[0]))
    if not marks:
        raise ShomImportError("Aucune géométrie ponctuelle exploitable n'a été trouvée dans le GeoJSON.")
    return marks


def _import_csv(content: bytes) -> list[ShomMark]:
    """Lire un CSV SHOM utilisant le point-virgule, la virgule ou la tabulation."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise ShomImportError("Le fichier CSV doit être encodé en UTF-8 ou Windows-1252.") from exc
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise ShomImportError("Le fichier CSV ne contient pas de ligne d'en-tête.")
    marks: list[ShomMark] = []
    for row in reader:
        latitude = _first(row, "latitude", "lat", "y")
        longitude = _first(row, "longitude", "lon", "lng", "x")
        if latitude in (None, "") or longitude in (None, ""):
            continue
        marks.append(_mark_from_properties(row, latitude, longitude))
    if not marks:
        raise ShomImportError("Aucune marque avec colonnes latitude et longitude n'a été trouvée dans le CSV.")
    return marks


def import_shom_marks(content: bytes, filename: str) -> list[ShomMark]:
    """Importer des marques depuis un fichier GeoJSON ou CSV.

    Parameters
    ----------
    content : bytes
        Contenu brut du fichier choisi.
    filename : str
        Nom du fichier, utilisé pour déterminer le format.

    Returns
    -------
    list[ShomMark]
        Marques normalisées.

    Raises
    ------
    ShomImportError
        Si le format ou le contenu n'est pas exploitable.
    """
    suffix = Path(filename).suffix.lower()
    if suffix in {".geojson", ".json"}:
        return _import_geojson(content)
    if suffix in {".csv", ".txt"}:
        return _import_csv(content)
    raise ShomImportError("Format SHOM non pris en charge. Utilisez GeoJSON ou CSV.")



SARA_WFS_URL = "http://sara.orion-brest.com/wfs"
SARA_FEATURE_TYPES = (
    "BCNLAT", "BOYLAT", "BCNCAR", "BOYCAR", "BCNSPP", "BOYSPP",
    "BCNSAW", "BOYSAW", "BCNISD", "BOYISD", "LNDMRK",
)




def _json_safe_value(value: Any) -> Any:
    """Convertir récursivement une valeur WFS en donnée JSON sûre.

    Parameters
    ----------
    value : Any
        Valeur provenant des propriétés GeoJSON du serveur WFS.

    Returns
    -------
    Any
        Valeur composée uniquement de types sérialisables en JSON.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    return str(value)

def _mark_from_sara_feature(feature: dict[str, Any], feature_type: str) -> ShomMark | None:
    """Convertir une entité GeoJSON renvoyée par le serveur WFS de SARA.

    Parameters
    ----------
    feature : dict[str, Any]
        Entité GeoJSON reçue depuis le serveur Orion.
    feature_type : str
        Type WFS demandé, par exemple ``BOYLAT``.

    Returns
    -------
    ShomMark | None
        Marque normalisée, ou ``None`` si l'entité est incomplète.
    """
    geometry = feature.get("geometry") if isinstance(feature, dict) else None
    properties = feature.get("properties") if isinstance(feature, dict) else None
    if not isinstance(geometry, dict) or not isinstance(properties, dict):
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    name = properties.get("Object name")
    if not isinstance(name, str) or not name.strip():
        return None
    try:
        latitude, longitude = _validate_coordinates(coordinates[1], coordinates[0])
    except ShomImportError:
        return None
    source_id = str(properties.get("foid", "")).strip()
    description_parts = []
    clean_properties: dict[str, Any] = {}
    for key, raw_value in properties.items():
        if raw_value in (None, "", []):
            continue
        value = ", ".join(str(item) for item in raw_value) if isinstance(raw_value, list) else raw_value
        clean_properties[str(key)] = _json_safe_value(value)
        if key in ("featureType", "Category of lateral mark", "Category of cardinal mark", "Function"):
            description_parts.append(f"{key} : {value}")
    return ShomMark(
        name=name.strip(),
        latitude=latitude,
        longitude=longitude,
        object_code=feature_type,
        category=_category(feature_type),
        description=" ; ".join(description_parts),
        source_id=source_id,
        properties=clean_properties,
    )


def download_shom_marks(
    center_latitude: float,
    center_longitude: float,
    radius: float,
    unit: str,
    categories: set[str] | None = None,
    *,
    server_url: str = SARA_WFS_URL,
    timeout: float = 10.0,
) -> list[dict[str, Any]]:
    """Télécharger les marques depuis le serveur WFS utilisé par SARA Navigation.

    Parameters
    ----------
    center_latitude, center_longitude : float
        Centre de recherche en degrés décimaux WGS84.
    radius : float
        Rayon positif exprimé dans ``unit``.
    unit : str
        ``nm`` pour milles nautiques ou ``km`` pour kilomètres.
    categories : set[str] | None, optional
        Catégories à conserver.
    server_url : str, optional
        Adresse du service WFS Orion.
    timeout : float, optional
        Délai maximal d'une requête HTTP, en secondes.

    Returns
    -------
    list[dict[str, Any]]
        Marques triées par distance au centre.

    Raises
    ------
    ShomImportError
        Si les paramètres sont invalides ou si le serveur ne répond pas.
    """
    _validate_coordinates(center_latitude, center_longitude)
    if unit not in {"nm", "km"}:
        raise ShomImportError("L’unité du rayon doit être NM ou km.")
    if radius <= 0:
        raise ShomImportError("Le rayon doit être strictement positif.")

    # Le code original de SARA transmet LENGTH en milles nautiques.
    radius_nm = radius if unit == "nm" else radius / 1.852
    marks: list[ShomMark] = []
    errors: list[str] = []

    for feature_type in SARA_FEATURE_TYPES:
        parameters = {
            "INFO_FORMAT": "application/json",
            "BBOX": "0,0,0,0",
            "SRS": "EPSG:4326",
            "FeatureType": feature_type,
            "LAT": f"{center_latitude}",
            "LONG": f"{center_longitude}",
            "LENGTH": f"{radius_nm}",
            "SERVICE": "WFS",
            "REQUEST": "GetFeature",
        }
        request_url = f"{server_url}?{urlencode(parameters)}"
        request = Request(
            request_url,
            headers={
                "User-Agent": "SARA-Route-Manager/0.6.12",
                "Accept": "application/json",
                "Connection": "close",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw_payload = response.read()
                status = getattr(response, "status", 200)
                if status != 200:
                    raise ShomImportError(f"réponse HTTP {status}")
                payload = json.loads(raw_payload.decode("utf-8-sig"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, ShomImportError) as exc:
            message = f"{feature_type}: {exc}"
            LOGGER.warning("Échec de la requête SHOM %s : %s", feature_type, exc)
            errors.append(message)
            continue
        features = payload.get("features", []) if isinstance(payload, dict) else []
        LOGGER.info("Requête SHOM %s réussie : %d entité(s)", feature_type, len(features))
        for feature in features:
            mark = _mark_from_sara_feature(feature, feature_type)
            if mark is not None:
                marks.append(mark)

    if errors and not marks:
        raise ShomImportError(
            "Impossible de récupérer les marques depuis le serveur SARA/Orion. "
            + " ; ".join(errors[:3])
        )

    # Le serveur applique déjà le rayon, mais ce filtrage local sécurise le résultat
    # et fournit les distances dans les deux unités.
    return filter_marks(marks, center_latitude, center_longitude, radius, unit, categories)


def haversine_distance_km(latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float) -> float:
    """Calculer la distance orthodromique entre deux positions.

    Parameters
    ----------
    latitude_1, longitude_1, latitude_2, longitude_2 : float
        Coordonnées décimales WGS84.

    Returns
    -------
    float
        Distance en kilomètres.
    """
    earth_radius_km = 6371.0088
    lat1, lon1, lat2, lon2 = map(radians, (latitude_1, longitude_1, latitude_2, longitude_2))
    delta_latitude = lat2 - lat1
    delta_longitude = lon2 - lon1
    value = sin(delta_latitude / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_longitude / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(value))


def filter_marks(
    marks: list[ShomMark],
    center_latitude: float,
    center_longitude: float,
    radius: float,
    unit: str,
    categories: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Filtrer et trier des marques autour d'un centre.

    Parameters
    ----------
    marks : list[ShomMark]
        Marques importées.
    center_latitude, center_longitude : float
        Centre de la recherche en degrés décimaux.
    radius : float
        Rayon positif exprimé dans ``unit``.
    unit : str
        ``nm`` pour mille nautique ou ``km`` pour kilomètre.
    categories : set[str] | None, optional
        Catégories françaises à conserver. Une valeur vide conserve tout.

    Returns
    -------
    list[dict[str, Any]]
        Marques retenues, triées de la plus proche à la plus éloignée.
    """
    if unit not in {"nm", "km"}:
        raise ShomImportError("L'unité du rayon doit être NM ou km.")
    if radius <= 0:
        raise ShomImportError("Le rayon doit être strictement positif.")
    _validate_coordinates(center_latitude, center_longitude)
    radius_km = radius * 1.852 if unit == "nm" else radius
    selected: list[tuple[float, ShomMark]] = []
    for mark in marks:
        if categories and mark.category not in categories:
            continue
        distance = haversine_distance_km(center_latitude, center_longitude, mark.latitude, mark.longitude)
        if distance <= radius_km:
            selected.append((distance, mark))
    selected.sort(key=lambda item: (item[0], item[1].name.casefold()))
    return [mark.to_dict(distance) for distance, mark in selected]
