# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.route_formats
Description : Importer et exporter des routes SARA en CSV, GPX et JSON.
Classes présentes :
- RouteFormatError
  Méthodes : héritées de ValueError.
Fonctions principales :
- import_route
- export_route
- import_csv
- export_csv
- import_gpx
- export_gpx
- import_json
- export_json
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

import csv
import io
import json
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree as ET

from .models import SaraRoute, ValidationError, Waypoint


class RouteFormatError(ValueError):
    """Signaler un fichier de route absent, invalide ou non pris en charge."""


def _new_waypoint(name: str, latitude: Any, longitude: Any, threshold: Any = 100.0) -> Waypoint:
    """Créer et valider un waypoint à partir de valeurs importées.

    Parameters
    ----------
    name : str
        Nom affiché du point.
    latitude : Any
        Latitude décimale comprise entre -90 et 90.
    longitude : Any
        Longitude décimale comprise entre -180 et 180.
    threshold : Any, default=100.0
        Distance de validation du point, en mètres.

    Returns
    -------
    Waypoint
        Point SARA validé.

    Raises
    ------
    RouteFormatError
        Si les valeurs ne permettent pas de créer un point valide.
    """
    try:
        return Waypoint.from_form(
            {
                "name": str(name).strip() or "Point sans nom",
                "latitude": latitude,
                "longitude": longitude,
                "distance_threshold": threshold,
            }
        )
    except (TypeError, ValueError, ValidationError) as exc:
        raise RouteFormatError(f"Point invalide : {exc}") from exc


def import_csv(content: bytes, filename: str) -> SaraRoute:
    """Importer une route depuis un fichier CSV à séparateur reconnu.

    Le séparateur est détecté parmi le point-virgule, la virgule et la
    tabulation afin qu'un fichier exporté selon la configuration puisse être
    réimporté sans conversion manuelle.
    """
    text = content.decode("utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise RouteFormatError("Le fichier CSV ne contient pas d’en-tête.")
    normalized = {field.strip().lower(): field for field in reader.fieldnames}
    required = {"nom", "latitude", "longitude"}
    if not required.issubset(normalized):
        raise RouteFormatError("Le CSV doit contenir les colonnes nom, latitude et longitude.")
    points: list[Waypoint] = []
    for index, row in enumerate(reader, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        try:
            points.append(
                _new_waypoint(
                    row.get(normalized["nom"], ""),
                    row.get(normalized["latitude"], ""),
                    row.get(normalized["longitude"], ""),
                    row.get(normalized.get("distance_validation", ""), 100.0) or 100.0,
                )
            )
        except RouteFormatError as exc:
            raise RouteFormatError(f"Ligne {index} : {exc}") from exc
    route = SaraRoute(name=Path(filename).stem, points=points)
    route.validate()
    return route


def export_csv(route: SaraRoute, delimiter: str = ";") -> bytes:
    """Exporter une route vers un CSV UTF-8 avec le séparateur demandé.

    Parameters
    ----------
    route : SaraRoute
        Route à sérialiser.
    delimiter : str, optional
        Séparateur CSV, limité au point-virgule, à la virgule ou à la
        tabulation. La valeur par défaut est le point-virgule.

    Returns
    -------
    bytes
        Fichier CSV encodé en UTF-8 avec marqueur BOM.

    Raises
    ------
    RouteFormatError
        Si le séparateur n’est pas pris en charge.
    """
    if delimiter not in {";", ",", "\t"}:
        raise RouteFormatError("Séparateur CSV non pris en charge.")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter)
    writer.writerow(["ordre", "nom", "latitude", "longitude", "distance_validation"])
    for index, point in enumerate(route.points, start=1):
        writer.writerow([index, point.name, f"{point.latitude:.8f}", f"{point.longitude:.8f}", point.distance_threshold])
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def import_json(content: bytes, filename: str) -> SaraRoute:
    """Importer une route depuis un JSON SARA ou un JSON exporté par l’application."""
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteFormatError(f"JSON invalide : {exc}") from exc
    if not isinstance(data, dict):
        raise RouteFormatError("La racine du fichier JSON doit être un objet.")
    raw_points = data.get("points", [])
    points: list[Waypoint] = []
    for item in raw_points:
        gps = item.get("gpsPosition", {}) if isinstance(item, dict) else {}
        points.append(
            _new_waypoint(
                item.get("name", "Point sans nom"),
                item.get("latitude", gps.get("latitude")),
                item.get("longitude", gps.get("longitude")),
                item.get("distance_threshold", item.get("distanceThreshold", 100.0)),
            )
        )
    route = SaraRoute(
        name=str(data.get("name") or Path(filename).stem),
        points=points,
        reversed=bool(data.get("reversed", False)),
        id=str(data.get("id") or uuid4()).upper(),
    )
    route.validate()
    return route


def export_json(route: SaraRoute) -> bytes:
    """Exporter une route dans un JSON SARA lisible et sans identifiant propriétaire."""
    payload = {
        "id": route.id,
        "name": route.name,
        "status": 2,
        "reversed": route.reversed,
        "points": [
            {
                "id": point.id,
                "name": point.name,
                "distanceThreshold": point.distance_threshold,
                "gpsPosition": {
                    "id": point.gps_id,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                },
            }
            for point in route.points
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def import_gpx(content: bytes, filename: str) -> SaraRoute:
    """Importer la première route GPX, ou à défaut la première trace ou les waypoints."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise RouteFormatError(f"GPX invalide : {exc}") from exc
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}", 1)[0] + "}"

    def name_of(element: ET.Element, fallback: str) -> str:
        child = element.find(f"{namespace}name")
        return child.text.strip() if child is not None and child.text else fallback

    points: list[Waypoint] = []
    route_element = root.find(f"{namespace}rte")
    route_name = Path(filename).stem
    if route_element is not None:
        route_name = name_of(route_element, route_name)
        candidates = route_element.findall(f"{namespace}rtept")
    else:
        track = root.find(f"{namespace}trk")
        if track is not None:
            route_name = name_of(track, route_name)
            candidates = track.findall(f".//{namespace}trkpt")
        else:
            candidates = root.findall(f"{namespace}wpt")
    for index, element in enumerate(candidates, start=1):
        points.append(_new_waypoint(name_of(element, f"Point {index}"), element.get("lat"), element.get("lon"), 100.0))
    route = SaraRoute(name=route_name, points=points)
    route.validate()
    return route


def export_gpx(route: SaraRoute) -> bytes:
    """Exporter une route SARA en GPX 1.1 avec éléments rte et rtept."""
    gpx = ET.Element("gpx", attrib={"version": "1.1", "creator": "SARA Route Manager", "xmlns": "http://www.topografix.com/GPX/1/1"})
    rte = ET.SubElement(gpx, "rte")
    ET.SubElement(rte, "name").text = route.name
    for point in route.points:
        rtept = ET.SubElement(rte, "rtept", attrib={"lat": f"{point.latitude:.8f}", "lon": f"{point.longitude:.8f}"})
        ET.SubElement(rtept, "name").text = point.name
        extensions = ET.SubElement(rtept, "extensions")
        ET.SubElement(extensions, "distanceThreshold").text = str(point.distance_threshold)
    return ET.tostring(gpx, encoding="utf-8", xml_declaration=True)



def import_wpt(content: bytes, filename: str) -> SaraRoute:
    """Importer un fichier WPT textuel simple.

    Parameters
    ----------
    content : bytes
        Contenu du fichier encodé en UTF-8 ou Windows-1252.
    filename : str
        Nom utilisé pour proposer le nom de route.

    Returns
    -------
    SaraRoute
        Route contenant les waypoints importés.

    Notes
    -----
    Les lignes acceptées utilisent un séparateur point-virgule, virgule ou
    tabulation, dans l'ordre nom, latitude, longitude. Une ligne d'en-tête est
    tolérée.
    """
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
    points: list[Waypoint] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        delimiter = "\t" if "\t" in line else ";" if ";" in line else ","
        parts = [part.strip() for part in line.split(delimiter)]
        if len(parts) < 3:
            raise RouteFormatError(f"Ligne {line_number} : trois champs sont attendus : nom, latitude, longitude.")
        if line_number == 1 and parts[1].lower().startswith("lat"):
            continue
        try:
            point = _new_waypoint(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else 100.0)
            point.source = "wpt"
            points.append(point)
        except RouteFormatError as exc:
            raise RouteFormatError(f"Ligne {line_number} : {exc}") from exc
    route = SaraRoute(name=Path(filename).stem, points=points)
    route.validate()
    return route

def import_route(content: bytes, filename: str) -> SaraRoute:
    """Importer une route selon l’extension du fichier fourni."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return import_csv(content, filename)
    if suffix == ".gpx":
        return import_gpx(content, filename)
    if suffix == ".json":
        return import_json(content, filename)
    if suffix == ".wpt":
        return import_wpt(content, filename)
    raise RouteFormatError("Format non pris en charge. Utilisez CSV, GPX, WPT ou JSON.")


def export_route(
    route: SaraRoute,
    format_name: str,
    csv_delimiter: str = ";",
) -> tuple[bytes, str, str]:
    """Exporter une route et renvoyer contenu, type MIME et extension.

    Parameters
    ----------
    route : SaraRoute
        Route à exporter.
    format_name : str
        Format cible : CSV, GPX ou JSON.
    csv_delimiter : str, optional
        Séparateur utilisé uniquement pour le format CSV.
    """
    normalized = format_name.strip().lower()
    if normalized == "csv":
        return export_csv(route, csv_delimiter), "text/csv; charset=utf-8", "csv"
    if normalized == "gpx":
        return export_gpx(route), "application/gpx+xml", "gpx"
    if normalized == "json":
        return export_json(route), "application/json; charset=utf-8", "json"
    raise RouteFormatError("Format d’export inconnu.")
