# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.shom_icons
Description : Sélection du fichier SVG officiel du SHOM correspondant aux
attributs S-57 d'une marque nautique (bouée, balise), pour l'affichage sur
la fenêtre de visualisation cartographique.

La convention de nommage a été établie en inspectant directement les 53
fichiers du paquet officiel « Balisage maritime » du SHOM (Licence Ouverte
2.0) : ``{CODE_S57}_{catégorie}_{T si voyant}_{IALAB si région B}.svg``.

Toutes les combinaisons ne sont pas forcément couvertes par le jeu officiel
(par exemple, une marque latérale sans voyant n'a pas de variante IALA B) :
``select_icon_filename`` renvoie ``None`` dès qu'aucune correspondance
fiable n'existe, laissant l'appelant se replier sur un marqueur générique.

Classes présentes :
- Aucune.
Fonctions présentes :
- is_iala_region_b
- select_icon_filename
- icon_filename_for_mark
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"


# CATLAM (catégorie de marque latérale) : 1 = bâbord (port), 2 = tribord
# (starboard), d'après la table de correspondance officielle (lut.json).
_LATERAL_SIDE_BY_CATLAM = {1: "B", 2: "T"}

# CATCAM (catégorie de marque cardinale) : 1 = nord, 2 = est, 3 = sud,
# 4 = ouest, d'après la même table.
_CARDINAL_DIRECTION_BY_CATCAM = {1: "N", 2: "E", 3: "S", 4: "W"}

# Classes d'objets disposant d'une simple variante avec/sans voyant, sans
# sous-catégorie supplémentaire (danger isolé, eaux saines, spéciale).
_PLAIN_TOPMARK_CODES = {"BCNISD", "BOYISD", "BCNSAW", "BOYSAW", "BCNSPP", "BOYSPP"}

# Classes d'objets à icône unique, sans variante, confirmées dans le jeu de
# 53 fichiers officiels du SHOM.
_SINGLE_ICON_CODES = {"DAYMAR", "NEWOBJ", "OFSPLF", "PILPNT", "SILTNK", "VEGATN", "FORSTC"}

# Emprises approximatives des territoires français en région IALA B
# (Antilles, Guyane, Saint-Pierre-et-Miquelon) : (lat_min, lat_max, lon_min,
# lon_max). Utilisées seulement en repli si l'information n'est pas
# directement disponible dans les propriétés de la marque elle-même.
_IALA_REGION_B_BOUNDING_BOXES = (
    (14.0, 18.5, -63.5, -60.5),  # Guadeloupe, Martinique
    (2.0, 6.0, -54.6, -51.6),  # Guyane française
    (46.5, 47.5, -56.5, -55.8),  # Saint-Pierre-et-Miquelon
)


def is_iala_region_b(latitude: float, longitude: float) -> bool:
    """Déterminer si une position se situe dans un territoire français en région IALA B.

    Sert de repli approximatif lorsque la région IALA n'est pas directement
    fournie par la source de données. La très large majorité des positions
    (métropole, Réunion, Mayotte, Polynésie, Nouvelle-Calédonie) reste en
    région IALA A.

    Parameters
    ----------
    latitude : float
        Latitude décimale WGS84.
    longitude : float
        Longitude décimale WGS84.

    Returns
    -------
    bool
        ``True`` si la position est en région IALA B.
    """
    for min_lat, max_lat, min_lon, max_lon in _IALA_REGION_B_BOUNDING_BOXES:
        if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
            return True
    return False


def _parse_lateral_side(properties: dict[str, object]) -> int | None:
    """Déduire le côté d'une marque latérale (CATLAM) depuis les propriétés brutes.

    AVERTISSEMENT : le texte exact renvoyé par le WFS Orion pour l'attribut
    ``Category of lateral mark`` n'a pas pu être vérifié en direct (accès
    réseau limité pendant le développement) — cette fonction reconnaît les
    mots anglais habituels de la norme S-57 (« port », « starboard »), sur
    le modèle du décodeur observé dans le code source de SARA Navigation.
    À confirmer sur une vraie réponse WFS.
    """
    text = str(properties.get("Category of lateral mark", "")).lower()
    if "port" in text:
        return 1
    if "starboard" in text:
        return 2
    return None


def _parse_cardinal_direction(properties: dict[str, object]) -> int | None:
    """Déduire la direction d'une marque cardinale (CATCAM) depuis les propriétés brutes.

    Même avertissement que `_parse_lateral_side` : à confirmer sur une
    vraie réponse WFS.
    """
    text = str(properties.get("Category of cardinal mark", "")).lower()
    if "north" in text:
        return 1
    if "east" in text:
        return 2
    if "south" in text:
        return 3
    if "west" in text:
        return 4
    return None


def _has_topmark(properties: dict[str, object]) -> bool:
    """Déduire la présence d'un voyant depuis les propriétés brutes.

    AVERTISSEMENT : le WFS Orion (utilisé par l'éditeur pour la recherche
    de marques) est un service simplifié pour la navigation, distinct du
    Shapefile officiel du SHOM inspecté par ailleurs — rien ne garantit
    qu'il expose un attribut de liaison ``topmar`` équivalent. Cette
    fonction cherche une clé contenant « topmar » avec une valeur non
    vide ; à défaut, elle considère qu'il n'y a pas de voyant (plutôt que
    de risquer d'en supposer un à tort). À confirmer sur une vraie réponse
    WFS.
    """
    for key, value in properties.items():
        if "topmar" in str(key).lower() and value not in (None, "", []):
            return True
    return False


def icon_filename_for_mark(
    object_code: str,
    properties: dict[str, object],
    latitude: float,
    longitude: float,
) -> str | None:
    """Sélectionner l'icône SHOM d'une marque à partir de ses propriétés WFS brutes.

    Combine `select_icon_filename` avec l'extraction des attributs
    nécessaires (catégorie latérale/cardinale, présence d'un voyant, région
    IALA) depuis les propriétés brutes renvoyées par le WFS Orion.

    Parameters
    ----------
    object_code : str
        Code d'objet S-57 de la marque, par exemple ``BCNLAT``.
    properties : dict[str, object]
        Propriétés brutes de la marque, telles que renvoyées par le WFS.
    latitude, longitude : float
        Position de la marque en degrés décimaux WGS84.

    Returns
    -------
    str or None
        Nom du fichier SVG, ou ``None`` si aucune correspondance fiable.
    """
    return select_icon_filename(
        object_code,
        catlam=_parse_lateral_side(properties),
        catcam=_parse_cardinal_direction(properties),
        has_topmark=_has_topmark(properties),
        iala_region_b=is_iala_region_b(latitude, longitude),
    )


def select_icon_filename(
    object_code: str,
    *,
    catlam: int | None = None,
    catcam: int | None = None,
    has_topmark: bool = False,
    iala_region_b: bool = False,
) -> str | None:
    """Sélectionner le nom du fichier SVG officiel du SHOM pour une marque.

    Parameters
    ----------
    object_code : str
        Code d'objet S-57, par exemple ``BCNLAT`` ou ``BOYCAR``.
    catlam : int or None, optional
        Catégorie de marque latérale (1 = bâbord, 2 = tribord), lorsqu'elle
        s'applique.
    catcam : int or None, optional
        Catégorie de marque cardinale (1 = nord, 2 = est, 3 = sud,
        4 = ouest), lorsqu'elle s'applique.
    has_topmark : bool, default=False
        ``True`` si un voyant est associé à ce support (présence d'un
        identifiant dans l'attribut de liaison ``topmar``).
    iala_region_b : bool, default=False
        ``True`` si la marque se situe en région IALA B (Antilles, Guyane,
        Saint-Pierre-et-Miquelon).

    Returns
    -------
    str or None
        Nom du fichier SVG (par exemple ``"BCNLAT_B_T.svg"``), ou ``None``
        si aucune correspondance fiable n'existe dans le jeu officiel — dans
        ce cas, l'appelant doit se replier sur un marqueur générique plutôt
        que d'inventer un nom de fichier.
    """
    code = object_code.strip().upper()
    topmark_suffix = "_T" if has_topmark else ""

    if code in ("BCNCAR", "BOYCAR"):
        direction = _CARDINAL_DIRECTION_BY_CATCAM.get(catcam)
        if direction is None:
            return None
        return f"{code}_{direction}{topmark_suffix}.svg"

    if code in ("BCNLAT", "BOYLAT"):
        side = _LATERAL_SIDE_BY_CATLAM.get(catlam)
        if side is None:
            return None
        region_suffix = "_IALAB" if iala_region_b else ""
        # Le jeu officiel ne comporte pas de variante IALA B pour BCNLAT
        # sans voyant (seulement BOYLAT en propose une) : dans ce cas précis,
        # revenir à la variante région A plutôt que d'inventer un nom de
        # fichier inexistant.
        if code == "BCNLAT" and region_suffix and not topmark_suffix:
            region_suffix = ""
        return f"{code}_{side}{topmark_suffix}{region_suffix}.svg"

    if code in _PLAIN_TOPMARK_CODES:
        return f"{code}{topmark_suffix}.svg"

    if code in _SINGLE_ICON_CODES:
        return f"{code}.svg"

    if code == "LNDMRK":
        return "LNDMRK_default.svg"

    return None
