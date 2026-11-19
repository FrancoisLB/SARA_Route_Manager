"use strict";

/**
 * Module : route_math.js
 * Description : Fonctions de géométrie de route partagées entre l'éditeur
 * et la fenêtre de visualisation cartographique (distance orthodromique,
 * cap initial, construction des segments, protection de cellules CSV).
 * Chargé globalement depuis base.html et map.html, au même titre que
 * file_dialogs.js — ses fonctions doivent donc rester de vraies fonctions
 * globales, appelables depuis unified_editor.js et map.js.
 *
 * Les constantes de version portent un nom spécifique au fichier
 * (ROUTE_MATH_VERSION/ROUTE_MATH_DATE) plutôt que __version__/__date__ :
 * comme ce script n'est pas isolé dans une IIFE (ses fonctions doivent
 * rester globales), un simple `const __version__` entrerait en collision
 * avec celui de file_dialogs.js, chargé sur les mêmes pages.
 *
 * Fonctions présentes : segmentDistanceNm, segmentInitialBearing,
 * buildRouteSegments, csvCell, buildSegmentsCsvRows.
 */

const ROUTE_MATH_VERSION = "0.9.4";
const ROUTE_MATH_DATE = "2026-11-19";

/**
 * Calculer la distance orthodromique entre deux points en milles nautiques.
 *
 * Parameters
 * ----------
 * startPoint : object
 *     Point de départ, avec `latitude` et `longitude`.
 * endPoint : object
 *     Point d'arrivée, avec `latitude` et `longitude`.
 *
 * Returns
 * -------
 * number
 *     Distance du segment en milles nautiques.
 */
function segmentDistanceNm(startPoint, endPoint) {
  const toRadians = degrees => degrees * Math.PI / 180;
  const earthRadiusNm = 3440.065;
  const startLatitude = toRadians(Number(startPoint.latitude));
  const endLatitude = toRadians(Number(endPoint.latitude));
  const latitudeDifference = endLatitude - startLatitude;
  const longitudeDifference = toRadians(Number(endPoint.longitude) - Number(startPoint.longitude));

  const haversine = Math.sin(latitudeDifference / 2) ** 2
    + Math.cos(startLatitude) * Math.cos(endLatitude)
    * Math.sin(longitudeDifference / 2) ** 2;
  const centralAngle = 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));
  return earthRadiusNm * centralAngle;
}

/**
 * Calculer le cap vrai initial d'un segment.
 *
 * Parameters
 * ----------
 * startPoint : object
 *     Point de départ, avec `latitude` et `longitude`.
 * endPoint : object
 *     Point d'arrivée, avec `latitude` et `longitude`.
 *
 * Returns
 * -------
 * number
 *     Cap vrai initial, compris entre 0 et 360 degrés.
 */
function segmentInitialBearing(startPoint, endPoint) {
  const toRadians = degrees => degrees * Math.PI / 180;
  const toDegrees = radians => radians * 180 / Math.PI;
  const startLatitude = toRadians(Number(startPoint.latitude));
  const endLatitude = toRadians(Number(endPoint.latitude));
  const longitudeDifference = toRadians(Number(endPoint.longitude) - Number(startPoint.longitude));
  const y = Math.sin(longitudeDifference) * Math.cos(endLatitude);
  const x = Math.cos(startLatitude) * Math.sin(endLatitude)
    - Math.sin(startLatitude) * Math.cos(endLatitude) * Math.cos(longitudeDifference);
  return (toDegrees(Math.atan2(y, x)) + 360) % 360;
}

/**
 * Construire la liste ordonnée des segments d'une liste de points.
 *
 * Parameters
 * ----------
 * points : Array<object>
 *     Points de la route, dans l'ordre, chacun avec `latitude`/`longitude`.
 *
 * Returns
 * -------
 * Array<object>
 *     Segments avec numéro, extrémités, longueur et cap.
 */
function buildRouteSegments(points) {
  const segments = [];
  for (let index = 0; index < points.length - 1; index += 1) {
    const startPoint = points[index];
    const endPoint = points[index + 1];
    segments.push({
      number: index + 1,
      startPoint,
      endPoint,
      distanceNm: segmentDistanceNm(startPoint, endPoint),
      bearingDegrees: segmentInitialBearing(startPoint, endPoint)
    });
  }
  return segments;
}

/**
 * Protéger une valeur destinée à un fichier CSV configurable.
 *
 * Parameters
 * ----------
 * value : *
 *     Valeur à protéger.
 * separator : str
 *     Séparateur de colonnes utilisé (`;`, `,` ou `\t`).
 *
 * Returns
 * -------
 * str
 *     Valeur textuelle, entourée de guillemets si nécessaire.
 */
function csvCell(value, separator) {
  const textValue = String(value ?? "");
  const escapedSeparator = separator === "\t" ? "\t" : separator.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const protectedCharacters = new RegExp(`[${escapedSeparator}"\r\n]`);
  return protectedCharacters.test(textValue)
    ? `"${textValue.replaceAll('"', '""')}"`
    : textValue;
}

/**
 * Construire les lignes texte (en-tête incluse) du relevé CSV des segments.
 *
 * Parameters
 * ----------
 * segments : Array<object>
 *     Segments construits par `buildRouteSegments`.
 * separator : str
 *     Séparateur de colonnes utilisé (`;`, `,` ou `\t`).
 *
 * Returns
 * -------
 * Array<str>
 *     Lignes prêtes à être jointes par un saut de ligne.
 */
function buildSegmentsCsvRows(segments, separator) {
  const rows = [[
    "Numero_segment",
    "Marque_debut",
    "Marque_fin",
    "Longueur_NM",
    "Cap_degres"
  ].join(separator)];
  segments.forEach(segment => {
    rows.push([
      segment.number,
      csvCell(segment.startPoint.name, separator),
      csvCell(segment.endPoint.name, separator),
      segment.distanceNm.toFixed(2).replace(".", ","),
      Math.round(segment.bearingDegrees)
    ].join(separator));
  });
  return rows;
}
