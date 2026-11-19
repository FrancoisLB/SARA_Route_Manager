# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.webapp
Description : Application Flask multipage et API de synchronisation accessible.
Classes présentes :
- ApplicationState
Fonctions principales :
- build_route_from_json
- route_to_api_dict
- create_app
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from dataclasses import dataclass, field
from pathlib import Path
import io
import platform
import secrets
import sys
import time
import tomllib
from threading import Lock
from typing import Any
from uuid import uuid4

from flask import Flask, jsonify, make_response, render_template, request, send_file
import keyring.errors

from .app_logging import configure_logging, get_logger
from .coastline import CoastlineError, fetch_coastline
from .configuration import AppConfiguration
from . import __version__ as PACKAGE_VERSION
from .credentials import CredentialStore
from .firebase_client import (
    FirebaseSession,
    SaraConnectionError,
    SaraRouteExistsError,
    SaraRouteOwnedByOtherError,
)
from .models import SaraRoute, ValidationError, Waypoint
from .storage import LocalRouteStorage
from .route_formats import RouteFormatError, export_route, import_route
from .shom import ShomImportError, download_shom_marks, haversine_distance_km
from .shom_icons import icon_filename_for_mark


@dataclass(slots=True)
class ApplicationState:
    """Regrouper l’état temporaire de l’application locale."""

    firebase: FirebaseSession = field(default_factory=FirebaseSession)
    lock: Lock = field(default_factory=Lock)
    automatic_login_message: str | None = None
    # Jetons de transmission de route vers la fenêtre de visualisation
    # cartographique : {jeton: {"data": ..., "created_at": ...}}. Un jeton
    # évite de dépendre de sessionStorage, qui ne se partage pas forcément
    # entre deux fenêtres pywebview créées séparément côté Python.
    map_tokens: dict[str, dict[str, Any]] = field(default_factory=dict)


# Durée de vie d'un jeton de visualisation cartographique, en secondes. Assez
# long pour couvrir une session de consultation normale, assez court pour ne
# pas accumuler indéfiniment des routes en mémoire.
MAP_TOKEN_TTL_SECONDS = 600


def _prune_map_tokens(state: ApplicationState) -> None:
    """Retirer les jetons de visualisation expirés de l’état applicatif.

    Parameters
    ----------
    state : ApplicationState
        État applicatif contenant les jetons à nettoyer.
    """

    now = time.time()
    expired = [
        token
        for token, entry in state.map_tokens.items()
        if now - entry["created_at"] > MAP_TOKEN_TTL_SECONDS
    ]
    for token in expired:
        del state.map_tokens[token]


def build_route_from_json(data: dict[str, Any]) -> SaraRoute:
    """Construire une route validée depuis la charge JSON du navigateur."""
    raw_points = data.get("points")
    if not isinstance(raw_points, list):
        raise ValidationError("La liste des points est absente.")
    points = [Waypoint.from_form(point) for point in raw_points]
    route = SaraRoute(
        name=str(data.get("name", "")),
        points=points,
        reversed=bool(data.get("reversed", False)),
        id=str(data.get("id") or uuid4()).upper(),
        owner=str(data.get("owner")) if data.get("owner") else None,
        last_update_time=str(data.get("last_update_time")) if data.get("last_update_time") else None,
        remote_key=str(data.get("remote_key")) if data.get("remote_key") else None,
    )
    route.validate()
    return route


def route_to_api_dict(route: SaraRoute, own: bool = False) -> dict[str, Any]:
    """Créer une représentation sans secret destinée au navigateur."""
    return {
        "id": route.id,
        "name": route.name,
        "reversed": route.reversed,
        "owner": route.owner,
        "own": own,
        "last_update_time": route.last_update_time,
        "remote_key": route.remote_key or route.name,
        "points_count": len(route.points),
        "points": [
            {
                "id": point.id,
                "gps_id": point.gps_id,
                "name": point.name,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "distance_threshold": point.distance_threshold,
                "source": point.source,
                "properties": point.properties,
            }
            for point in route.points
        ],
    }


def create_app() -> Flask:
    """Créer l’application Flask locale avec ses pages et routes JSON."""
    app = Flask(__name__)
    app.config.update(JSON_AS_ASCII=False, MAX_CONTENT_LENGTH=2 * 1024 * 1024)
    # WebView2 conserve un cache disque persistant qui survit à la fermeture
    # complète de l'application (contrairement à un onglet de navigateur
    # classique) : sans cette ligne, un script/style modifié pourrait
    # continuer à être servi depuis le cache indéfiniment tant que son URL
    # ne change pas, même après plusieurs relances de l'application.
    # `SEND_FILE_MAX_AGE_DEFAULT = 0` force une revalidation systématique,
    # en complément (pas en remplacement) du paramètre `v=` de
    # cache-busting déjà présent sur chaque script, qu'il faut continuer à
    # incrémenter à chaque modification.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    state = ApplicationState()
    configuration = AppConfiguration.load()
    configure_logging(configuration.logs_directory)
    logger = get_logger()
    logger.info("Initialisation de l’application Flask %s", PACKAGE_VERSION)
    storage = LocalRouteStorage(configuration.routes_directory)
    credentials = CredentialStore()

    # Une reconnexion automatique rend l’état du compte explicite dès l’ouverture.
    saved_email = credentials.load_email()
    saved_password = credentials.load_password(saved_email)
    if configuration.automatic_connection and saved_email and saved_password:
        try:
            state.firebase.sign_in(saved_email, saved_password)
            state.automatic_login_message = f"Connexion automatique réussie pour {saved_email}."
        except SaraConnectionError as exc:
            state.automatic_login_message = f"Connexion automatique impossible : {exc}"

    @app.get("/")
    def home():
        return render_template("home.html", version=PACKAGE_VERSION)

    @app.get("/routes")
    def routes_page():
        return render_template("routes.html", version=PACKAGE_VERSION)

    @app.get("/editor")
    def editor_page():
        return render_template("editor.html", version=PACKAGE_VERSION, default_unit=configuration.shom_radius_unit)

    @app.get("/configuration")
    def configuration_page():
        return render_template("configuration.html", version=PACKAGE_VERSION)

    @app.get("/about")
    def about_page():
        return render_template("about.html", version=PACKAGE_VERSION, configuration=configuration.to_dict())

    @app.get("/map")
    def map_page():
        return render_template("map.html", version=PACKAGE_VERSION)

    @app.post("/api/map/token")
    def create_map_token():
        """Enregistrer temporairement une route et renvoyer un jeton de consultation.

        Ce jeton permet à la fenêtre de visualisation cartographique de
        récupérer la route sans dépendre de ``sessionStorage``, qui ne se
        partage pas forcément entre deux fenêtres pywebview créées
        séparément côté Python (contrairement à deux onglets de navigateur
        ouverts via ``window.open``).
        """
        data = request.get_json(silent=True) or {}
        raw_points = data.get("points")
        if not isinstance(raw_points, list) or len(raw_points) < 2:
            return jsonify({"ok": False, "message": "La route doit contenir au moins deux points."}), 400
        with state.lock:
            _prune_map_tokens(state)
            token = secrets.token_urlsafe(16)
            state.map_tokens[token] = {
                "data": {"name": str(data.get("name", "")), "points": raw_points},
                "created_at": time.time(),
            }
        return jsonify({"ok": True, "token": token})

    @app.get("/api/map/data/<token>")
    def get_map_data(token: str):
        """Récupérer la route associée à un jeton de visualisation.

        Chaque point reçoit en plus le nom du fichier d'icône SHOM
        correspondant, lorsque son `object_code` d'origine a survécu
        jusqu'ici (composition en cours de session, ou route rouverte
        depuis une sauvegarde locale — voir docs/SPECIFICATIONS.md,
        option B). Une route reçue de SARA Navigation n'a pas cette
        information : ses points restent des marqueurs génériques, ce qui
        est le comportement attendu, pas une erreur.
        """
        with state.lock:
            _prune_map_tokens(state)
            entry = state.map_tokens.get(token)
        if entry is None:
            return jsonify({"ok": False, "message": "Jeton inconnu ou expiré. Relancez la visualisation depuis l’éditeur."}), 404

        route_data = dict(entry["data"])
        enriched_points = []
        for point in route_data.get("points", []):
            enriched_point = dict(point)
            object_code = str(point.get("object_code", "")).strip()
            try:
                latitude = float(point.get("latitude"))
                longitude = float(point.get("longitude"))
            except (TypeError, ValueError):
                latitude = longitude = None
            if object_code and latitude is not None and longitude is not None:
                enriched_point["icon_filename"] = icon_filename_for_mark(
                    object_code, point.get("properties", {}), latitude, longitude
                )
            else:
                enriched_point["icon_filename"] = None
            enriched_points.append(enriched_point)
        route_data["points"] = enriched_points

        return jsonify({"ok": True, "route": route_data})

    @app.get("/api/map/coastline/<token>")
    def get_map_coastline(token: str):
        """Récupérer le trait de côte autour de la route associée à un jeton.

        Interroge le WFS du SHOM sur l'emprise géographique de la route (avec
        une marge de contexte), avec repli automatique sur HISTOLITT si
        « Limite terre-mer » ne couvre pas la zone (outre-mer). Un échec de
        cette requête ne doit jamais empêcher l'affichage des points de la
        route eux-mêmes : cette fonctionnalité reste un complément visuel,
        pas un prérequis.
        """
        with state.lock:
            _prune_map_tokens(state)
            entry = state.map_tokens.get(token)
        if entry is None:
            return jsonify({"ok": False, "message": "Jeton inconnu ou expiré."}), 404

        points = entry["data"].get("points", [])
        try:
            latitudes = [float(point["latitude"]) for point in points]
            longitudes = [float(point["longitude"]) for point in points]
        except (KeyError, TypeError, ValueError):
            return jsonify({"ok": False, "message": "Coordonnées de route invalides."}), 400
        if not latitudes or not longitudes:
            return jsonify({"ok": False, "message": "Aucun point à cadrer."}), 400

        min_lat, max_lat = min(latitudes), max(latitudes)
        min_lon, max_lon = min(longitudes), max(longitudes)
        # Marge de contexte autour du tracé : 20 % de son étendue, avec un
        # minimum en degrés pour une route très courte ou très resserrée.
        lat_margin = max((max_lat - min_lat) * 0.2, 0.05)
        lon_margin = max((max_lon - min_lon) * 0.2, 0.05)

        try:
            result = fetch_coastline(
                min_lat - lat_margin,
                max_lat + lat_margin,
                min_lon - lon_margin,
                max_lon + lon_margin,
            )
            return jsonify({"ok": True, **result})
        except CoastlineError as exc:
            return jsonify({"ok": False, "message": f"Trait de côte indisponible : {exc}"}), 502

    @app.get("/api/map/marks/<token>")
    def get_map_marks(token: str):
        """Récupérer les marques SHOM autour de la route associée à un jeton.

        Interroge le WFS Orion sur l'emprise géographique de la route (avec
        une marge de contexte), indépendamment de ce qui a pu être recherché
        pendant la composition de la route dans l'éditeur — même principe
        que le trait de côte : une lecture fraîche et contextuelle, pas une
        synchronisation d'état entre les deux fenêtres. Chaque marque reçoit
        en plus le nom du fichier d'icône SHOM correspondant, lorsqu'il en
        existe un (voir `shom_icons.py`).
        """
        with state.lock:
            _prune_map_tokens(state)
            entry = state.map_tokens.get(token)
        if entry is None:
            return jsonify({"ok": False, "message": "Jeton inconnu ou expiré."}), 404

        points = entry["data"].get("points", [])
        try:
            latitudes = [float(point["latitude"]) for point in points]
            longitudes = [float(point["longitude"]) for point in points]
        except (KeyError, TypeError, ValueError):
            return jsonify({"ok": False, "message": "Coordonnées de route invalides."}), 400
        if not latitudes or not longitudes:
            return jsonify({"ok": False, "message": "Aucun point à cadrer."}), 400

        min_lat, max_lat = min(latitudes), max(latitudes)
        min_lon, max_lon = min(longitudes), max(longitudes)
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        # Rayon de recherche : distance du centre au point le plus éloigné
        # de la route, avec une marge de contexte de 20 % (minimum 1 NM
        # pour une route très courte ou très resserrée).
        corner_distance_km = max(
            haversine_distance_km(center_lat, center_lon, lat, lon)
            for lat, lon in zip(latitudes, longitudes)
        )
        radius_nm = max((corner_distance_km / 1.852) * 1.2, 1.0)

        try:
            marks = download_shom_marks(center_lat, center_lon, radius_nm, "nm")
        except ShomImportError as exc:
            return jsonify({"ok": False, "message": f"Marques SHOM indisponibles : {exc}"}), 502

        marks_payload = []
        for mark in marks:
            icon_filename = icon_filename_for_mark(
                mark["object_code"], mark.get("properties", {}), mark["latitude"], mark["longitude"]
            )
            marks_payload.append({**mark, "icon_filename": icon_filename})

        return jsonify({"ok": True, "marks": marks_payload})


    @app.get("/api/configuration")
    def get_configuration():
        return jsonify({"ok": True, "configuration": configuration.to_dict()})

    @app.post("/api/configuration")
    def save_configuration():
        data = request.get_json(silent=True) or {}
        try:
            configuration.update_settings(data)
            configuration.save()
            logger.info("Configuration utilisateur enregistrée")
            storage.set_directory(configuration.routes_directory)
            return jsonify({"ok": True, "message": "Configuration enregistrée.", "configuration": configuration.to_dict()})
        except (OSError, ValueError) as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/configuration/reset")
    def reset_configuration():
        try:
            configuration.reset()
            storage.set_directory(configuration.routes_directory)
            return jsonify({"ok": True, "message": "Configuration par défaut rétablie.", "configuration": configuration.to_dict()})
        except OSError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.get("/api/configuration/export")
    def export_configuration():
        """Exporter le fichier de configuration actuel, pour sauvegarde ou transfert.

        Exporte l'état réellement enregistré sur disque, pas d'éventuelles
        modifications en cours dans le formulaire non encore enregistrées —
        cohérent avec le bouton « Enregistrer » qui doit être utilisé
        d'abord pour que ces modifications soient prises en compte.
        """
        if not configuration.config_file.exists():
            return jsonify({"ok": False, "message": "Aucun fichier de configuration à exporter pour le moment."}), 404
        content = configuration.config_file.read_text(encoding="utf-8")
        response = make_response(content)
        response.headers["Content-Type"] = "application/toml; charset=utf-8"
        response.headers["Content-Disposition"] = 'attachment; filename="config.toml"'
        return response

    @app.post("/api/configuration/import")
    def import_configuration():
        """Importer un fichier de configuration TOML, en remplaçant les réglages actuels."""
        uploaded = request.files.get("file")
        if uploaded is None or not uploaded.filename:
            return jsonify({"ok": False, "message": "Aucun fichier n’a été sélectionné."}), 400
        try:
            parsed = tomllib.loads(uploaded.read().decode("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            return jsonify({"ok": False, "message": f"Fichier de configuration invalide : {exc}"}), 400
        try:
            configuration.update_from_dict(parsed)
            configuration.save()
            storage.set_directory(configuration.routes_directory)
            logger.info("Configuration importée depuis %s", uploaded.filename)
            return jsonify({"ok": True, "message": "Configuration importée.", "configuration": configuration.to_dict()})
        except (OSError, ValueError) as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/open-path")
    def open_path():
        data = request.get_json(silent=True) or {}
        target_name = str(data.get("target", ""))
        project_root = Path(__file__).resolve().parent.parent
        targets: dict[str, Path | str] = {
            "routes": configuration.routes_directory,
            "config_directory": configuration.config_directory,
            "config_file": configuration.config_file,
            "logs": configuration.logs_directory,
            "log_file": configuration.logs_directory / "journal.txt",
            "user_guide": project_root / "docs" / "USER_GUIDE.md",
            "keyboard_shortcuts": project_root / "docs" / "RACCOURCIS_CLAVIER.md",
            "change_log": project_root / "CHANGE_LOG.md",
            # Cible web : ouverte dans le navigateur par défaut, jamais dans la
            # fenêtre pywebview elle-même (qui n'a ni onglet ni bouton retour).
            "orion_brest_website": "https://orion-brest.com/SARA.html",
            "gpl_license_url": "https://www.gnu.org/licenses/gpl-3.0.fr.html",
            "cc_by_sa_license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.fr",
        }
        target = targets.get(target_name)
        if target is None:
            return jsonify({"ok": False, "message": "Emplacement inconnu."}), 400
        try:
            import os
            if isinstance(target, str):
                os.startfile(target)  # type: ignore[attr-defined]
                return jsonify({"ok": True, "message": f"Ouverture de {target}."})
            if not target.exists():
                if target.suffix:
                    configuration.save()
                else:
                    target.mkdir(parents=True, exist_ok=True)
            os.startfile(str(target))  # type: ignore[attr-defined]
            return jsonify({"ok": True, "message": f"Ouverture de {target}."})
        except (OSError, AttributeError) as exc:
            return jsonify({"ok": False, "message": f"Impossible d’ouvrir cet emplacement : {exc}"}), 400

    @app.get("/api/technical-information")
    def technical_information():
        """Retourner les informations utiles au support, sans secret."""
        try:
            import flask
            import webview
            flask_version = getattr(flask, "__version__", "inconnue")
            webview_version = getattr(webview, "__version__", "inconnue")
        except ImportError:
            flask_version = "inconnue"
            webview_version = "inconnue"
        information = {
            "application": "SARA Route Manager",
            "version": PACKAGE_VERSION,
            "python": platform.python_version(),
            "operating_system": platform.platform(),
            "routes_directory": str(configuration.routes_directory),
            "configuration_directory": str(configuration.config_directory),
            "configuration_file": str(configuration.config_file),
            "logs_directory": str(configuration.logs_directory),
            "log_file": str(configuration.logs_directory / "journal.txt"),
            "flask": flask_version,
            "pywebview": webview_version,
            "webview_engine": "Microsoft Edge WebView2 (mode pywebview)",
        }
        return jsonify({"ok": True, "information": information})

    @app.get("/api/status")
    def status():
        remembered_email = credentials.load_email()
        return jsonify(
            {
                "ok": True,
                "connected": bool(state.firebase.id_token),
                "email": state.firebase.email,
                "remembered_email": remembered_email,
                "credentials_saved": bool(credentials.load_password(remembered_email)),
                "automatic_login_message": state.automatic_login_message,
            }
        )

    @app.post("/api/login")
    def login():
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip()
        password = str(data.get("password", ""))
        remember = bool(data.get("remember", True))
        try:
            with state.lock:
                state.firebase.sign_in(email, password)
            logger.info("Connexion SARA réussie pour %s", email)
            if remember:
                credentials.save(email, password)
            return jsonify(
                {
                    "ok": True,
                    "message": f"Connexion au compte SARA réussie pour {state.firebase.email}.",
                    "email": state.firebase.email,
                    "credentials_saved": remember,
                }
            )
        except (SaraConnectionError, keyring.errors.KeyringError) as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/logout")
    def logout():
        data = request.get_json(silent=True) or {}
        with state.lock:
            state.firebase.close()
        if bool(data.get("forget", False)):
            credentials.clear()
        return jsonify({"ok": True, "message": "Déconnexion effectuée."})

    @app.get("/api/routes/remote")
    def remote_routes():
        try:
            with state.lock:
                mine, community, warnings = state.firebase.list_routes()
            logger.info("Synchronisation reçue : %d route(s) personnelle(s), %d communautaire(s)", len(mine), len(community))
            return jsonify(
                {
                    "ok": True,
                    "mine": [route_to_api_dict(route, own=True) for route in mine],
                    "community": [route_to_api_dict(route, own=False) for route in community],
                    "warnings": warnings,
                    "message": f"{len(mine)} route(s) personnelle(s) et {len(community)} route(s) communautaire(s) récupérée(s).",
                }
            )
        except SaraConnectionError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.get("/api/routes/local")
    def local_routes():
        return jsonify({"ok": True, "routes": storage.list_routes()})

    @app.get("/api/routes/local/<path:filename>")
    def load_local_route(filename: str):
        try:
            route = storage.load(filename)
            return jsonify({"ok": True, "route": route_to_api_dict(route), "message": "Route locale chargée."})
        except (OSError, ValueError, ValidationError) as exc:
            return jsonify({"ok": False, "message": f"Impossible de lire la route locale : {exc}"}), 400



    @app.post("/api/routes/local/exists")
    def local_route_exists():
        """Indiquer si l'enregistrement d'une route écraserait un fichier local."""
        data = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "exists": storage.exists(str(data.get("name", "")))})

    @app.post("/api/routes/local/delete")
    def delete_local_route():
        """Supprimer une route enregistrée sur ce PC."""
        data = request.get_json(silent=True) or {}
        filename = str(data.get("file", "")).strip()
        if not filename:
            return jsonify({"ok": False, "message": "La route locale à supprimer n’est pas indiquée."}), 400
        try:
            storage.delete(filename)
            return jsonify({"ok": True, "message": "La route a été supprimée avec succès."})
        except OSError as exc:
            return jsonify({"ok": False, "message": f"Suppression impossible : {exc}"}), 400

    @app.post("/api/shom/search")
    def search_shom_web():
        """Récupérer les marques depuis le serveur WFS utilisé par SARA Navigation."""
        data = request.get_json(silent=True) or {}
        try:
            center_latitude = float(str(data.get("center_latitude", "")).replace(",", "."))
            center_longitude = float(str(data.get("center_longitude", "")).replace(",", "."))
            radius = float(str(data.get("radius", "")).replace(",", "."))
            unit = str(data.get("unit", configuration.shom_radius_unit)).lower()
            categories = {str(value) for value in data.get("categories", []) if value}
            selected = download_shom_marks(center_latitude, center_longitude, radius, unit, categories)
            logger.info("Recherche SHOM web : %d marque(s) retenue(s)", len(selected))
            return jsonify({
                "ok": True,
                "marks": selected,
                "message": f"{len(selected)} marque(s) récupérée(s) depuis le serveur SARA/Orion.",
            })
        except (ValueError, ShomImportError) as exc:
            logger.warning("Recherche SHOM impossible : %s", exc)
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:  # pragma: no cover - filet de sécurité applicatif
            logger.exception("Erreur inattendue pendant la recherche SHOM")
            return jsonify({
                "ok": False,
                "message": f"Erreur inattendue pendant la recherche SHOM : {exc}",
            }), 500

    @app.post("/api/routes/import")
    def import_route_file():
        """Importer un fichier CSV, GPX ou JSON et renvoyer la route à l’éditeur."""
        uploaded = request.files.get("file")
        if uploaded is None or not uploaded.filename:
            return jsonify({"ok": False, "message": "Aucun fichier n’a été sélectionné."}), 400
        try:
            route = import_route(uploaded.read(), uploaded.filename)
            return jsonify({"ok": True, "route": route_to_api_dict(route), "message": f"Route « {route.name} » importée avec {len(route.points)} point(s)."})
        except (RouteFormatError, ValidationError) as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/routes/export/<format_name>")
    def export_route_file(format_name: str):
        """Exporter la route courante dans le format demandé."""
        try:
            route = build_route_from_json(request.get_json(silent=True) or {})
            content, mimetype, extension = export_route(
                route, format_name, csv_delimiter=configuration.csv_separator
            )
            safe_name = "".join(char if char.isalnum() or char in "-_ " else "_" for char in route.name).strip() or "route"
            return send_file(
                io.BytesIO(content),
                mimetype=mimetype,
                as_attachment=True,
                download_name=f"{safe_name}.{extension}",
            )
        except (ValidationError, RouteFormatError) as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/routes/save")
    def save_route():
        try:
            route = build_route_from_json(request.get_json(silent=True) or {})
            path = storage.save(route)
            return jsonify({"ok": True, "message": f"Route enregistrée dans {path}.", "file": path.name})
        except ValidationError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/routes/upload")
    def upload_route():
        data = request.get_json(silent=True) or {}
        try:
            route = build_route_from_json(data)
            with state.lock:
                state.firebase.upload_route(route, overwrite=bool(data.get("overwrite", False)))
            logger.info("Route mise en ligne : %s", route.name)
            # Même formulation que SARA Navigation (« Déposer en ligne »).
            return jsonify({"ok": True, "message": "La route a été mise en ligne avec succès !"})
        except SaraRouteExistsError as exc:
            # 409 + `exists` : l'interface propose alors d'écraser sa propre route.
            return jsonify({"ok": False, "exists": True, "message": str(exc)}), 409
        except SaraRouteOwnedByOtherError as exc:
            # 409 sans `exists` : aucune proposition d'écrasement, simple message d'erreur.
            return jsonify({"ok": False, "exists": False, "owned_by_other": True, "message": str(exc)}), 409
        except (ValidationError, SaraConnectionError) as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.post("/api/routes/delete")
    def delete_remote_route():
        data = request.get_json(silent=True) or {}
        remote_key = str(data.get("remote_key", "")).strip()
        if not remote_key:
            return jsonify({"ok": False, "message": "La route à supprimer n’est pas indiquée."}), 400
        try:
            with state.lock:
                state.firebase.delete_route(remote_key)
            return jsonify({"ok": True, "message": "La route a été supprimée avec succès."})
        except SaraConnectionError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    return app

