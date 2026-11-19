# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.models
Description : Modèles, décodage et validation des routes SARA Navigation.
Classes présentes :
- ValidationError : exception de validation.
- to_float32 : arrondir un nombre à la précision « Float » de SARA Navigation.
- Waypoint : to_sara_dict, to_local_dict, from_form, from_sara_dict, from_local_dict.
- SaraRoute : validate, to_sara_dict, to_local_dict, from_sara_dict, from_local_dict.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import struct
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


class ValidationError(ValueError):
    """Signaler une donnée de route invalide."""


def to_float32(value: float) -> float:
    """Arrondir un nombre à la précision d'un ``Float`` Swift (32 bits).

    SARA Navigation décode les latitudes, longitudes et distances de
    validation avec ``as? Float`` (voir ``GPSPosition.decode`` et
    ``CoursePoint.decodePoint`` dans le code source de l'application). Or une
    valeur JSON à 64 bits qui n'est pas *exactement* représentable en 32 bits
    (par exemple 47.6821118) est refusée par ce transtypage : le point perd
    alors sa position GPS, et la visualisation de la route fait planter
    l'application. L'application iOS écrit elle-même des valeurs déjà
    arrondies à 32 bits ; il faut donc faire de même.

    Parameters
    ----------
    value : float
        Nombre à arrondir.

    Returns
    -------
    float
        Le nombre 32 bits le plus proche, exprimé en 64 bits (donc
        exactement représentable en ``Float``). L'écart est inférieur à
        0,5 m pour une latitude ou une longitude de nos régions.
    """
    return struct.unpack("f", struct.pack("f", float(value)))[0]


@dataclass(slots=True)
class Waypoint:
    """Représenter un point de passage compatible avec SARA Navigation.

    Parameters
    ----------
    name : str
        Nom annoncé pour le point.
    latitude : float
        Latitude décimale comprise entre -90 et 90.
    longitude : float
        Longitude décimale comprise entre -180 et 180.
    distance_threshold : float, default=100.0
        Rayon de validation du point, en mètres.
    id : str
        Identifiant UUID du point.
    gps_id : str
        Identifiant UUID de la position GPS.
    """

    name: str
    latitude: float
    longitude: float
    distance_threshold: float = 100.0
    id: str = field(default_factory=lambda: str(uuid4()).upper())
    gps_id: str = field(default_factory=lambda: str(uuid4()).upper())
    source: str = "manual"
    properties: dict[str, Any] = field(default_factory=dict)
    # Code d'objet S-57 d'origine (ex. "BCNLAT"), utilisé pour retrouver
    # l'icône IALA correcte à l'affichage. Uniquement conservé dans la
    # sauvegarde locale (`to_local_dict`) : le format échangé avec SARA
    # Navigation (`to_sara_dict`) n'a pas ce champ, et ne doit pas l'avoir —
    # ce n'est pas un oubli de leur part, un point de route n'a plus besoin
    # de connaître son type d'origine une fois devenu un simple point de
    # passage GPS (voir docs/SPECIFICATIONS.md, option B).
    object_code: str = ""

    def to_sara_dict(self, float32: bool = False) -> dict[str, Any]:
        """Convertir le point vers le dictionnaire attendu par SARA.

        Parameters
        ----------
        float32 : bool, default=False
            Si vrai, arrondit latitude, longitude et distance de validation
            à la précision 32 bits de SARA Navigation (voir `to_float32`).
            À utiliser pour tout envoi vers Firebase ; la sauvegarde locale
            garde les valeurs d'origine.

        Returns
        -------
        dict[str, Any]
            Structure directement sérialisable en JSON Firebase.
        """
        convert = to_float32 if float32 else float
        return {
            "id": self.id,
            "name": self.name.strip(),
            "distanceThreshold": convert(self.distance_threshold),
            "gpsPosition": {
                "id": self.gps_id,
                "latitude": convert(self.latitude),
                "longitude": convert(self.longitude),
            },
        }

    @classmethod
    def from_form(cls, data: dict[str, Any]) -> "Waypoint":
        """Créer et valider un point depuis un formulaire ou un JSON local.

        Parameters
        ----------
        data : dict[str, Any]
            Données contenant le nom, les coordonnées et la distance.

        Returns
        -------
        Waypoint
            Point validé, avec conservation éventuelle de ses UUID.

        Raises
        ------
        ValidationError
            Si une valeur est absente ou hors limites.
        """
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValidationError("Le nom du point est obligatoire.")
        try:
            latitude = float(str(data.get("latitude", "")).replace(",", "."))
            longitude = float(str(data.get("longitude", "")).replace(",", "."))
            threshold = float(str(data.get("distance_threshold", 100)).replace(",", "."))
        except (TypeError, ValueError) as exc:
            raise ValidationError("Les coordonnées et la distance doivent être numériques.") from exc
        if not -90 <= latitude <= 90:
            raise ValidationError("La latitude doit être comprise entre -90 et 90.")
        if not -180 <= longitude <= 180:
            raise ValidationError("La longitude doit être comprise entre -180 et 180.")
        if threshold < 0:
            raise ValidationError("La distance de validation ne peut pas être négative.")
        return cls(
            name=name,
            latitude=latitude,
            longitude=longitude,
            distance_threshold=threshold,
            id=str(data.get("id") or uuid4()).upper(),
            gps_id=str(data.get("gps_id") or uuid4()).upper(),
            source=str(data.get("source") or "manual"),
            properties=dict(data.get("properties") or {}),
            object_code=str(data.get("object_code") or "").strip().upper(),
        )

    @classmethod
    def from_sara_dict(cls, data: dict[str, Any]) -> "Waypoint":
        """Décoder un point reçu de Firebase.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionnaire SARA contenant ``gpsPosition``.

        Returns
        -------
        Waypoint
            Point de passage décodé.
        """
        gps = data.get("gpsPosition")
        if not isinstance(gps, dict):
            raise ValidationError("Un point distant ne contient pas de position GPS valide.")
        return cls.from_form(
            {
                "id": data.get("id"),
                "gps_id": gps.get("id"),
                "name": data.get("name"),
                "latitude": gps.get("latitude"),
                "longitude": gps.get("longitude"),
                "distance_threshold": data.get("distanceThreshold", 100),
            }
        )

    def to_local_dict(self) -> dict[str, Any]:
        """Convertir le point vers la sauvegarde locale, avec son type d'origine.

        À la différence de `to_sara_dict`, conserve `objectCode` et
        `properties` : cette information sert uniquement à retrouver
        l'icône IALA correcte à l'affichage sur la carte, elle n'est jamais
        envoyée à SARA Navigation (voir docs/SPECIFICATIONS.md, option B).

        Returns
        -------
        dict[str, Any]
            Structure sérialisable en JSON, réutilisable uniquement par
            SARA Route Manager lui-même.
        """
        result = self.to_sara_dict()
        result["objectCode"] = self.object_code
        result["properties"] = self.properties
        return result

    @classmethod
    def from_local_dict(cls, data: dict[str, Any]) -> "Waypoint":
        """Décoder un point depuis une sauvegarde locale de SARA Route Manager.

        Accepte aussi un point au format SARA strict (sans `objectCode` ni
        `properties`) : une route reçue de SARA Navigation, sans ces
        champs, redevient simplement un point générique, sans icône IALA
        associée — ce n'est pas une erreur de chargement.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionnaire local contenant ``gpsPosition``.

        Returns
        -------
        Waypoint
            Point de passage décodé.
        """
        gps = data.get("gpsPosition")
        if not isinstance(gps, dict):
            raise ValidationError("Un point local ne contient pas de position GPS valide.")
        return cls.from_form(
            {
                "id": data.get("id"),
                "gps_id": gps.get("id"),
                "name": data.get("name"),
                "latitude": gps.get("latitude"),
                "longitude": gps.get("longitude"),
                "distance_threshold": data.get("distanceThreshold", 100),
                "object_code": data.get("objectCode", ""),
                "properties": data.get("properties") or {},
            }
        )


@dataclass(slots=True)
class SaraRoute:
    """Représenter une route de croisière SARA Navigation.

    Parameters
    ----------
    name : str
        Nom unique utilisé également comme clé Firebase.
    points : list[Waypoint]
        Points ordonnés de la route.
    reversed : bool, default=False
        Indique si la route est présentée en sens inverse.
    id : str
        Identifiant UUID interne.
    owner : str | None
        UID Firebase du propriétaire distant.
    last_update_time : str | None
        Horodatage fourni par SARA.
    remote_key : str | None
        Clé exacte utilisée sous ``/courses``.
    """

    name: str
    points: list[Waypoint]
    reversed: bool = False
    id: str = field(default_factory=lambda: str(uuid4()).upper())
    owner: str | None = None
    last_update_time: str | None = None
    remote_key: str | None = None

    def validate(self) -> None:
        """Valider le nom et le nombre de points.

        Raises
        ------
        ValidationError
            Si le nom est invalide ou si la route contient moins de deux points.
        """
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("Le nom de la route est obligatoire.")
        forbidden = set(".#$/[]")
        if any(character in forbidden for character in self.name):
            raise ValidationError("Le nom contient un caractère interdit : . # $ / [ ou ].")
        if len(self.points) < 2:
            raise ValidationError("La route doit contenir au moins deux points.")

    def to_sara_dict(self, owner_uid: str) -> dict[str, Any]:
        """Créer la charge JSON complète attendue par Firebase.

        Parameters
        ----------
        owner_uid : str
            Identifiant Firebase du compte connecté.

        Returns
        -------
        dict[str, Any]
            Route compatible avec ``CruiseCourse.decode``.
        """
        self.validate()
        return {
            "id": self.id,
            "name": self.name,
            "status": 2,
            # Valeurs 32 bits : SARA Navigation refuse les nombres 64 bits inexacts.
            "points": [point.to_sara_dict(float32=True) for point in self.points],
            "reversed": bool(self.reversed),
            "owner": owner_uid,
            "lastUpdateTime": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
        }

    def to_local_dict(self) -> dict[str, Any]:
        """Créer une sauvegarde locale avec les métadonnées de provenance.

        Returns
        -------
        dict[str, Any]
            Données réutilisables sans secret d’authentification.
        """
        self.validate()
        return {
            "id": self.id,
            "name": self.name,
            "reversed": self.reversed,
            "owner": self.owner,
            "lastUpdateTime": self.last_update_time,
            "remoteKey": self.remote_key,
            "points": [point.to_local_dict() for point in self.points],
        }

    @classmethod
    def from_local_dict(cls, data: dict[str, Any], remote_key: str | None = None) -> "SaraRoute":
        """Décoder une route depuis une sauvegarde locale de SARA Route Manager.

        À la différence de `from_sara_dict` (format d'échange avec SARA
        Navigation, sans type d'origine par point), restaure aussi
        `objectCode`/`properties` de chaque point lorsqu'ils sont présents
        — voir docs/SPECIFICATIONS.md, option B.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionnaire local complet.
        remote_key : str | None
            Clé Firebase parente, généralement identique au nom.

        Returns
        -------
        SaraRoute
            Route décodée et validée.
        """
        raw_points = data.get("points")
        if not isinstance(raw_points, list):
            raise ValidationError("La route locale ne contient pas de liste de points.")
        route = cls(
            name=str(data.get("name") or remote_key or "").strip(),
            points=[Waypoint.from_local_dict(point) for point in raw_points if isinstance(point, dict)],
            reversed=bool(data.get("reversed", False)),
            id=str(data.get("id") or uuid4()).upper(),
            owner=str(data.get("owner")) if data.get("owner") else None,
            last_update_time=str(data.get("lastUpdateTime")) if data.get("lastUpdateTime") else None,
            remote_key=remote_key,
        )
        route.validate()
        return route

    @classmethod
    def from_sara_dict(cls, data: dict[str, Any], remote_key: str | None = None) -> "SaraRoute":
        """Décoder une route de navigation reçue de Firebase.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionnaire distant complet.
        remote_key : str | None
            Clé Firebase parente, généralement identique au nom.

        Returns
        -------
        SaraRoute
            Route décodée et validée.
        """
        raw_points = data.get("points")
        if not isinstance(raw_points, list):
            raise ValidationError("La route distante ne contient pas de liste de points.")
        route = cls(
            name=str(data.get("name") or remote_key or "").strip(),
            points=[Waypoint.from_sara_dict(point) for point in raw_points if isinstance(point, dict)],
            reversed=bool(data.get("reversed", False)),
            id=str(data.get("id") or uuid4()).upper(),
            owner=str(data.get("owner")) if data.get("owner") else None,
            last_update_time=str(data.get("lastUpdateTime")) if data.get("lastUpdateTime") else None,
            remote_key=remote_key,
        )
        route.validate()
        return route
