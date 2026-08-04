# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.firebase_client
Description : Authentification et synchronisation des routes SARA via Firebase.
Classes présentes :
- SaraConnectionError : exception réseau ou serveur.
- FirebaseSession : sign_in, list_routes, upload_route, delete_route, route_exists, close.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests

from .models import SaraRoute, ValidationError

FIREBASE_API_KEY = "AIzaSyCpXCdtgBkLAnmox24wovZBUE5_IcxzleQ"
DATABASE_URL = "https://sara-nav-release-default-rtdb.europe-west1.firebasedatabase.app"
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


class SaraConnectionError(RuntimeError):
    """Signaler une erreur compréhensible de connexion au service SARA."""


@dataclass(slots=True)
class FirebaseSession:
    """Conserver une session Firebase authentifiée.

    Attributes
    ----------
    id_token : str | None
        Jeton temporaire utilisé pour les requêtes à la base.
    local_id : str | None
        UID Firebase du compte SARA.
    email : str | None
        Adresse du compte connecté.
    """

    id_token: str | None = None
    local_id: str | None = None
    email: str | None = None

    def sign_in(self, email: str, password: str) -> str:
        """Authentifier un compte SARA par e-mail et mot de passe."""
        if not email.strip() or not password:
            raise SaraConnectionError("L’adresse électronique et le mot de passe sont obligatoires.")
        payload = {"email": email.strip(), "password": password, "returnSecureToken": True}
        try:
            response = requests.post(AUTH_URL, params={"key": FIREBASE_API_KEY}, json=payload, timeout=20)
        except requests.RequestException as exc:
            raise SaraConnectionError("Impossible de contacter le service d’authentification SARA.") from exc
        if not response.ok:
            try:
                code = response.json().get("error", {}).get("message", "AUTHENTICATION_FAILED")
            except ValueError:
                code = "AUTHENTICATION_FAILED"
            messages = {
                "INVALID_LOGIN_CREDENTIALS": "Adresse électronique ou mot de passe incorrect.",
                "EMAIL_NOT_FOUND": "Compte SARA introuvable.",
                "INVALID_PASSWORD": "Mot de passe incorrect.",
                "USER_DISABLED": "Ce compte SARA est désactivé.",
                "TOO_MANY_ATTEMPTS_TRY_LATER": "Trop de tentatives. Réessayez plus tard.",
            }
            raise SaraConnectionError(messages.get(code, f"Authentification refusée : {code}."))
        result = response.json()
        self.id_token = result["idToken"]
        self.local_id = result["localId"]
        self.email = result.get("email", email.strip())
        return self.local_id

    def list_routes(self) -> tuple[list[SaraRoute], list[SaraRoute], list[str]]:
        """Télécharger et classer les routes SARA Navigation.

        Returns
        -------
        tuple[list[SaraRoute], list[SaraRoute], list[str]]
            Mes routes, routes communautaires, puis avertissements de décodage.
        """
        self._require_session()
        try:
            response = requests.get(
                f"{DATABASE_URL}/courses.json",
                params={"auth": self.id_token},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise SaraConnectionError("Impossible de télécharger les routes SARA.") from exc
        if not response.ok:
            raise SaraConnectionError(f"Lecture des routes refusée par Firebase ({response.status_code}).")
        raw = response.json() or {}
        if not isinstance(raw, dict):
            raise SaraConnectionError("La liste des routes reçue de SARA est invalide.")

        mine: list[SaraRoute] = []
        community: list[SaraRoute] = []
        warnings: list[str] = []
        for remote_key, route_data in raw.items():
            # La présence de « reversed » distingue SARA Navigation de SARA Régate.
            if not isinstance(route_data, dict) or "reversed" not in route_data:
                continue
            try:
                route = SaraRoute.from_sara_dict(route_data, remote_key=str(remote_key))
            except ValidationError as exc:
                warnings.append(f"Route « {remote_key} » ignorée : {exc}")
                continue
            if route.owner == self.local_id:
                mine.append(route)
            else:
                community.append(route)

        sort_key = lambda route: route.name.casefold()
        mine.sort(key=sort_key)
        community.sort(key=sort_key)
        return mine, community, warnings

    def route_exists(self, route_name: str) -> bool:
        """Vérifier si un nom de route existe déjà dans Firebase."""
        self._require_session()
        url = f"{DATABASE_URL}/courses/{quote(route_name, safe='')}.json"
        try:
            response = requests.get(url, params={"auth": self.id_token}, timeout=20)
        except requests.RequestException as exc:
            raise SaraConnectionError("Impossible de vérifier le nom de la route.") from exc
        if not response.ok:
            raise SaraConnectionError(f"Vérification refusée par Firebase ({response.status_code}).")
        return response.json() is not None

    def upload_route(self, route: SaraRoute, overwrite: bool = False) -> None:
        """Envoyer une route dans ``/courses/<nom>`` comme l’application iOS."""
        self._require_session()
        if not overwrite and self.route_exists(route.name):
            raise SaraConnectionError("Une route portant ce nom existe déjà sur SARA.")
        url = f"{DATABASE_URL}/courses/{quote(route.name, safe='')}.json"
        payload = route.to_sara_dict(self.local_id or "")
        try:
            response = requests.put(url, params={"auth": self.id_token}, json=payload, timeout=25)
        except requests.RequestException as exc:
            raise SaraConnectionError("Impossible d’envoyer la route vers SARA.") from exc
        if not response.ok:
            raise SaraConnectionError(
                f"Firebase a refusé l’envoi ({response.status_code}). Détail : {response.text[:300]}"
            )

    def delete_route(self, remote_key: str) -> None:
        """Supprimer une route distante uniquement lorsqu’elle appartient au compte.

        Parameters
        ----------
        remote_key : str
            Clé exacte de la route sous ``/courses``.

        Raises
        ------
        SaraConnectionError
            Si la route est absente, appartient à autrui ou si Firebase refuse.
        """
        self._require_session()
        url = f"{DATABASE_URL}/courses/{quote(remote_key, safe='')}.json"
        try:
            current = requests.get(url, params={"auth": self.id_token}, timeout=20)
        except requests.RequestException as exc:
            raise SaraConnectionError("Impossible de vérifier la route à supprimer.") from exc
        if not current.ok:
            raise SaraConnectionError(f"Lecture de la route refusée ({current.status_code}).")
        data = current.json()
        if not isinstance(data, dict):
            raise SaraConnectionError("La route distante n’existe plus.")
        if data.get("owner") != self.local_id:
            raise SaraConnectionError("Vous ne pouvez pas supprimer la route d’un autre membre.")
        try:
            deleted = requests.delete(url, params={"auth": self.id_token}, timeout=20)
        except requests.RequestException as exc:
            raise SaraConnectionError("Impossible de supprimer la route distante.") from exc
        if not deleted.ok:
            raise SaraConnectionError(f"Suppression refusée par Firebase ({deleted.status_code}).")

    def close(self) -> None:
        """Effacer les informations temporaires de session en mémoire."""
        self.id_token = None
        self.local_id = None
        self.email = None

    def _require_session(self) -> None:
        """Vérifier qu’une authentification a été réalisée."""
        if not self.id_token or not self.local_id:
            raise SaraConnectionError("Vous devez d’abord vous connecter au compte SARA.")
