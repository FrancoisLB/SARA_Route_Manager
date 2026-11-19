"use strict";

/**
 * Module : map.js
 * Description : Fenêtre de visualisation cartographique de la route active
 * (création ou modification). Récupère la route via le jeton temporaire
 * transmis dans l'URL, affiche les points reliés par un trait sur une
 * carte Leaflet (zoom à la molette et déplacement au clic-glisser natifs),
 * superpose le trait de côte du SHOM, puis propose l'export du relevé de
 * segments (CSV) et de la carte (SVG). Contenu de la carte strictement
 * illustratif : `role="img"` sur le conteneur, jamais un canal
 * d'information exclusif — mais les deux exports restent des données
 * réelles, au même titre que dans l'éditeur.
 * Fonctions présentes : announce, fetchRoute, fetchCoastline, fetchMarks,
 * renderRoute, renderCoastline, renderMarks, updateRouteSummary,
 * loadDisplayColors, niceGridStep, buildGrid, toggleGrid,
 * computeNiceNauticalStep, addNauticalScaleControl, metersToLongitudeDelta,
 * metersToLatitudeDelta, addNauticalTickMarks, setMeasureModeActive,
 * openMeasureDialog, closeMeasureDialog, setupMeasureTool,
 * openMarkerInfoDialog, closeMarkerInfoDialog,
 * exportSegmentsCsvFromMap, projectPoint, geoJsonRingsToSvgPath,
 * buildMapSvgString, exportMapSvg, closeMapWindow, initialize.
 */

// L'ensemble du fichier est isolé dans une fonction immédiatement invoquée
// (IIFE) : les scripts classiques chargés côté page partagent le même
// environnement global, et cette isolation évite toute collision de nom
// (par exemple __version__/__date__) avec file_dialogs.js et route_math.js,
// chargés globalement sur cette même page.
(function () {
  const __version__ = "0.9.4";
  const __date__ = "2026-11-19";

  const statusElement = document.getElementById("map-status");
  const routeNameElement = document.getElementById("map-route-name");
  const routeSummaryElement = document.getElementById("map-route-summary");
  const coastlineCreditElement = document.getElementById("coastline-credit");

  // Route et trait de côte actuellement affichés, conservés pour être
  // réutilisés par les deux boutons d'export sans refaire de requête.
  let currentRoute = null;
  let currentCoastline = null;
  let currentMap = null;

  // Couleurs actuelles (mer/terre/tracé), valeurs de repli avant que la
  // configuration ne soit chargée — réglables uniquement en page
  // Configuration depuis l'option A (préférences durables, pas
  // d'ajustement en direct dans cette fenêtre).
  let currentSeaColor = "#1f6fa3";
  let currentLandColor = "#d9c9a3";
  let currentRouteColor = "#ffe600";
  let currentRouteLineWidth = 3;
  let currentRouteLineStyle = "solid";
  // Ceux-ci restent, en plus de leur défaut en Configuration, ajustables
  // en direct dans cette fenêtre (case à cocher), car c'est le rendu par
  // défaut (texte trop grand, encadrés qui masquent des éléments de la
  // carte) qui a motivé la demande d'un accès rapide, sans repasser par
  // la Configuration à chaque fois.
  let currentRouteLabelsVisible = true;
  let currentRouteLabelFontSize = 12;
  let currentRouteLabelBordered = true;
  let currentMarkerSize = 20;
  // Calque de la grille latitude/longitude, créé/retiré par la case à
  // cocher correspondante.
  let currentGridLayer = null;

  // Un groupe de calques Leaflet par catégorie de marque SHOM (Latérale,
  // Cardinale...), pour afficher/masquer chaque catégorie via les cases à
  // cocher sans avoir à reconstruire les marqueurs.
  const markCategoryGroups = {};

  /**
   * Annoncer un message dans la zone de statut (masquée visuellement).
   *
   * Parameters
   * ----------
   * message : str
   *     Texte à annoncer.
   */
  function announce(message) {
    statusElement.textContent = "";
    window.setTimeout(() => { statusElement.textContent = message; }, 20);
  }

  /** Lire le jeton de route transmis dans l'URL de cette fenêtre. */
  function readToken() {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      throw new Error("Aucun jeton de route dans l’adresse de cette fenêtre.");
    }
    return token;
  }

  /**
   * Récupérer la route associée à un jeton.
   *
   * Parameters
   * ----------
   * token : str
   *     Jeton de route transmis dans l'URL.
   *
   * @returns {Promise<{name: string, points: Array<object>}>}
   */
  async function fetchRoute(token) {
    const response = await fetch(`/api/map/data/${encodeURIComponent(token)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Route introuvable ou jeton expiré.");
    }
    return data.route;
  }

  /**
   * Récupérer le trait de côte autour de la route associée à un jeton.
   *
   * Parameters
   * ----------
   * token : str
   *     Jeton de route transmis dans l'URL.
   *
   * @returns {Promise<{geojson: object, layer: string, attribution: string}>}
   */
  async function fetchCoastline(token) {
    const response = await fetch(`/api/map/coastline/${encodeURIComponent(token)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Trait de côte indisponible.");
    }
    return data;
  }

  /**
   * Mettre à jour le titre et le résumé (nombre de points, distance totale).
   *
   * L'unité est écrite en toutes lettres (« milles nautiques »), jamais
   * abrégée en « NM » : NVDA lit cette abréviation comme « nanomètre ».
   *
   * Parameters
   * ----------
   * route : {name: string, points: Array<object>}
   *     Route actuellement affichée.
   */
  function updateRouteSummary(route) {
    routeNameElement.textContent = route.name ? `Route : ${route.name}` : "Route sans nom";
    const segments = buildRouteSegments(route.points || []);
    const totalDistance = segments.reduce((total, segment) => total + segment.distanceNm, 0);
    const pointCount = route.points.length;
    routeSummaryElement.textContent =
      `${pointCount} point${pointCount > 1 ? "s" : ""} — `
      + `${totalDistance.toFixed(2).replace(".", ",")} milles nautiques`;
  }

  /**
   * Construire la carte Leaflet et y placer la route.
   *
   * Parameters
   * ----------
   * points : Array<object>
   *     Points de la route, avec `latitude`, `longitude` et `name`.
   *
   * Returns
   * -------
   * L.Map
   *     Carte construite, réutilisée ensuite pour y superposer le trait de côte.
   */
  function renderRoute(points) {
    const map = L.map("map-container", {
      attributionControl: false,
      zoomSnap: 0.25
    });

    // Fixé après l'initialisation : Leaflet applique son propre style au
    // conteneur au démarrage, ce qui écraserait un simple `style=""` posé
    // sur le `<div>` avant que la carte n'existe.
    map.getContainer().style.background = currentSeaColor;
    map.getContainer().classList.toggle("hide-route-labels", !currentRouteLabelsVisible);
    map.getContainer().classList.toggle("route-label-no-frame", !currentRouteLabelBordered);

    const latLngs = points.map(point => [point.latitude, point.longitude]);

    L.polyline(latLngs, {
      color: currentRouteColor,
      weight: currentRouteLineWidth,
      dashArray: routeDashArrayForStyle(currentRouteLineStyle)
    }).addTo(map);

    points.forEach((point, index) => {
      const label = point.name || `Point ${index + 1}`;
      let marker;
      if (point.icon_filename) {
        // Icône IALA retrouvée grâce au type d'origine du point (survit à
        // un enregistrement/réouverture local, option B — voir
        // docs/SPECIFICATIONS.md). Ancrée au centre (200×400 px), comme
        // pour les marques SHOM environnantes.
        const icon = L.icon({
          iconUrl: `/static/vendor/shom_icons/${point.icon_filename}`,
          iconSize: [currentMarkerSize, currentMarkerSize * 2],
          iconAnchor: [currentMarkerSize / 2, currentMarkerSize]
        });
        marker = L.marker([point.latitude, point.longitude], {icon});
      } else {
        marker = L.circleMarker([point.latitude, point.longitude], {
          radius: 7,
          color: "#000",
          weight: 1,
          fillColor: "#d40000",
          fillOpacity: 1
        });
      }
      marker.addTo(map).bindTooltip(label, {
        permanent: true, direction: "right", offset: [8, 0], className: "route-point-tooltip"
      });
      // Annonce vocale au survol à la souris : ne dépend pas d'un réglage
      // NVDA à activer soi-même (contrairement à sa fonction native
      // « Annoncer l'objet sous la souris »), puisque le nom est déjà
      // visible dans l'étiquette permanente — sert surtout aux marques
      // SHOM environnantes ci-dessous, sans étiquette permanente par
      // défaut, mais ajoutée ici aussi pour un comportement cohérent.
      marker.on("mouseover", () => {
        const preciseType = describeMarkType(point.type || point.source || "Inconnu", point.icon_filename);
        announce(`${label} — ${preciseType}`);
      });
      // Boîte de dialogue d'informations au double-clic, demandée
      // explicitement : source (route ou SHOM) et type de balise.
      marker.on("dblclick", () => {
        const preciseType = describeMarkType(point.type || point.source || "Inconnu", point.icon_filename);
        openMarkerInfoDialog(label, "Point de la route", preciseType);
      });
      // La taille de texte est une valeur numérique réglable (page
      // Configuration) : plus simple à appliquer en style en ligne, qui
      // l'emporte naturellement sur la règle CSS de base, qu'à multiplier
      // les variantes de classes CSS.
      const tooltipElement = marker.getTooltip()?.getElement();
      if (tooltipElement) tooltipElement.style.fontSize = `${currentRouteLabelFontSize}px`;
    });

    // Cadrage automatique sur l'ensemble du tracé. La marge de droite est
    // plus large que les autres car les étiquettes de nom sont affichées à
    // droite de chaque point : sans cette marge asymétrique, le nom du
    // point le plus à droite peut sortir du cadre visible.
    map.fitBounds(L.latLngBounds(latLngs), {
      paddingTopLeft: [40, 40],
      paddingBottomRight: [160, 40]
    });

    // La hauteur de la carte dépend désormais de la mise en page flexible
    // de la page (boutons en colonne à gauche), pas d'une valeur fixe :
    // recalculer sa taille au redimensionnement évite un rendu tronqué ou
    // mal centré si la fenêtre change de dimensions après coup.
    window.addEventListener("resize", () => map.invalidateSize());

    return map;
  }

  /**
   * Superposer le trait de côte sur la carte et afficher sa citation.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte déjà construite par `renderRoute`.
   * coastline : {geojson: object, layer: string, attribution: string}
   *     Résultat renvoyé par `/api/map/coastline/<jeton>`.
   */
  function renderCoastline(map, coastline) {
    // Les terres émergées sont dessinées par-dessus le fond bleu déjà en
    // place, sous le tracé et les points (ajoutés après par renderRoute,
    // donc déjà au-dessus dans l'ordre des calques Leaflet).
    L.geoJSON(coastline.geojson, {
      style: {color: "#7a6a4f", weight: 1, fillColor: currentLandColor, fillOpacity: 1}
    }).addTo(map);

    // La licence d'HISTOLITT exige, en plus de la citation textuelle, les
    // logos IGN et SHOM avec liens dès lors que la donnée est représentée
    // sur une interface — contrainte propre à cette couche, absente pour
    // Limite terre-mer (simple citation textuelle suffisante).
    if (coastline.layer === "histolitt") {
      coastlineCreditElement.innerHTML =
        `Trait de côte : ${coastline.attribution} — ` +
        '<a href="https://www.ign.fr" target="_blank" rel="noopener">IGN</a> / ' +
        '<a href="https://www.shom.fr" target="_blank" rel="noopener">SHOM</a>';
    } else {
      coastlineCreditElement.textContent = `Trait de côte : ${coastline.attribution}`;
    }
  }

  /** Charger les préférences utiles à l’export sans bloquer la fenêtre. */
  async function loadExportConfiguration() {
    try {
      const response = await fetch("/api/configuration");
      const data = await response.json();
      return data.configuration;
    } catch (_error) {
      return {csv_separator: ";"};
    }
  }

  /**
   * Construire un nom de fichier sûr à partir du nom de la route.
   *
   * Parameters
   * ----------
   * suffix : str
   *     Ajouté après le nom nettoyé (ex. `"_segments.csv"`, `".svg"`).
   *
   * Returns
   * -------
   * str
   *     Nom de fichier sans accent ni caractère interdit sous Windows.
   */
  function safeFilename(suffix) {
    const routeName = (currentRoute?.name?.trim() || "route")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[<>:"/\\|?*]+/g, "_")
      .replace(/\s+/g, "_");
    return `${routeName}${suffix}`;
  }

  /** Produire puis enregistrer le relevé détaillé des segments au format CSV UTF-8. */
  async function exportSegmentsCsvFromMap() {
    if (!currentRoute) return;
    const segments = buildRouteSegments(currentRoute.points || []);
    if (segments.length === 0) {
      announce("Impossible d’exporter : la route ne contient aucun segment.");
      return;
    }

    const configuration = await loadExportConfiguration();
    const separator = configuration.csv_separator === "TAB" ? "\t" : configuration.csv_separator;
    const rows = buildSegmentsCsvRows(segments, separator);
    const blob = new Blob(["\uFEFF", rows.join("\r\n"), "\r\n"], {type: "text/csv;charset=utf-8"});

    try {
      const result = await saveBlobWithDialog(blob, safeFilename("_segments.csv"), exportFileTypes("csv"));
      if (result.cancelled) {
        announce("Export annulé.");
        return;
      }
      if (!result.saved) throw new Error(result.message || "Le fichier n’a pas pu être enregistré.");
      announce(`Export terminé. Fichier : ${result.path}`);
    } catch (error) {
      announce(`Export impossible : ${error.message}`);
    }
  }

  /**
   * Projeter un point géographique dans un repère SVG local.
   *
   * Projection équirectangulaire simple avec correction grossière de
   * l'aplatissement des longitudes à la latitude moyenne de l'emprise —
   * suffisant pour un export schématique, sans prétention cartographique
   * précise (même principe que le rendu SVG fait main de l'étape 1).
   *
   * Parameters
   * ----------
   * lon, lat : float
   *     Coordonnées WGS84 du point à projeter.
   * frame : object
   *     Cadre de projection construit par `buildMapSvgString`.
   *
   * Returns
   * -------
   * [number, number]
   *     Coordonnées `[x, y]` dans le repère SVG.
   */
  function projectPoint(lon, lat, frame) {
    const x = (lon - frame.west) * frame.lonScale * frame.scale + frame.marginLeft;
    const y = frame.height - frame.marginBottom - (lat - frame.south) * frame.scale;
    return [x, y];
  }

  /**
   * Convertir un anneau de coordonnées GeoJSON en portion de tracé SVG (`M...Z`).
   *
   * Parameters
   * ----------
   * ring : Array<[number, number]>
   *     Anneau `[longitude, latitude]` (extérieur ou trou) d'un polygone GeoJSON.
   * frame : object
   *     Cadre de projection construit par `buildMapSvgString`.
   *
   * Returns
   * -------
   * str
   *     Portion de tracé SVG pour cet anneau.
   */
  function ringToSvgPath(ring, frame) {
    return ring
      .map(([lon, lat], index) => {
        const [x, y] = projectPoint(lon, lat, frame);
        return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ") + " Z";
  }

  /**
   * Convertir une géométrie GeoJSON (Polygon ou MultiPolygon) en tracé SVG complet.
   *
   * Parameters
   * ----------
   * geometry : object
   *     Géométrie GeoJSON du trait de côte.
   * frame : object
   *     Cadre de projection construit par `buildMapSvgString`.
   *
   * Returns
   * -------
   * str
   *     Attribut `d` combinant tous les anneaux, à dessiner avec
   *     `fill-rule="evenodd"` pour que les trous (îles intérieures, lacs)
   *     restent creusés.
   */
  function geometryToSvgPath(geometry, frame) {
    if (!geometry) return "";
    const polygons = geometry.type === "MultiPolygon" ? geometry.coordinates : [geometry.coordinates];
    return polygons
      .flatMap(rings => rings.map(ring => ringToSvgPath(ring, frame)))
      .join(" ");
  }

  /**
   * Construire un document SVG autonome représentant la vue actuelle de la carte.
   *
   * Recalcule sa propre projection à partir des données déjà en mémoire
   * (points de la route, trait de côte) plutôt que d'extraire le rendu
   * interne de Leaflet (positionné via des transformations CSS relatives
   * au défilement en cours, peu adapté à un export autonome) : le résultat
   * est ainsi toujours correct, indépendamment de l'état de défilement.
   *
   * Returns
   * -------
   * str
   *     Contenu SVG complet, prêt à être enregistré dans un fichier.
   */
  function buildMapSvgString() {
    const width = 1200;
    const height = 900;
    const marginLeft = 40;
    const marginRight = 200;
    const marginTop = 40;
    const marginBottom = 40;

    const points = currentRoute.points;
    const latitudes = points.map(point => point.latitude);
    const longitudes = points.map(point => point.longitude);
    const south = Math.min(...latitudes);
    const north = Math.max(...latitudes);
    const west = Math.min(...longitudes);
    const east = Math.max(...longitudes);

    const midLatitudeRad = ((south + north) / 2) * (Math.PI / 180);
    const lonScale = Math.max(Math.cos(midLatitudeRad), 0.1);
    const lonSpan = Math.max((east - west) * lonScale, 0.0001);
    const latSpan = Math.max(north - south, 0.0001);
    const scale = Math.min(
      (width - marginLeft - marginRight) / lonSpan,
      (height - marginTop - marginBottom) / latSpan
    );

    const frame = {west, south, lonScale, scale, height, marginLeft, marginBottom};

    const coastlinePath = currentCoastline
      ? (currentCoastline.geojson.features || [])
          .map(feature => geometryToSvgPath(feature.geometry, frame))
          .join(" ")
      : "";

    const latLngPoints = points.map(point => projectPoint(point.longitude, point.latitude, frame));
    const polylinePoints = latLngPoints.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

    const circlesAndLabels = points.map((point, index) => {
      const [x, y] = latLngPoints[index];
      const label = (point.name || `Point ${index + 1}`).replace(/[<>&]/g, "");
      const labelMarkup = currentRouteLabelsVisible
        ? `<text x="${(x + 9).toFixed(1)}" y="${(y + 4).toFixed(1)}" font-size="${currentRouteLabelFontSize}" fill="#111" font-family="sans-serif">${label}</text>`
        : "";
      return (
        `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="6" fill="#d40000" stroke="#000" stroke-width="1"></circle>` +
        labelMarkup
      );
    }).join("");

    const creditText = currentCoastline
      ? `Trait de côte : ${currentCoastline.attribution}`.replace(/[<>&]/g, "")
      : "";

    return (
      `<svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">` +
      `<rect x="0" y="0" width="${width}" height="${height}" fill="#1f6fa3"></rect>` +
      (coastlinePath ? `<path d="${coastlinePath}" fill="#d9c9a3" stroke="#7a6a4f" stroke-width="1" fill-rule="evenodd"></path>` : "") +
      `<polyline points="${polylinePoints}" fill="none" stroke="${currentRouteColor}" stroke-width="${currentRouteLineWidth}"${svgDashArrayAttribute(currentRouteLineStyle)}></polyline>` +
      circlesAndLabels +
      (creditText ? `<text x="10" y="${height - 10}" font-size="11" fill="#333" font-family="sans-serif">${creditText}</text>` : "") +
      `</svg>`
    );
  }

  /** Produire puis enregistrer la carte au format SVG. */
  async function exportMapSvg() {
    if (!currentRoute) return;
    try {
      const svgContent = buildMapSvgString();
      const blob = new Blob([svgContent], {type: "image/svg+xml;charset=utf-8"});
      const result = await saveBlobWithDialog(blob, safeFilename(".svg"), exportFileTypes("svg"));
      if (result.cancelled) {
        announce("Export annulé.");
        return;
      }
      if (!result.saved) throw new Error(result.message || "Le fichier n’a pas pu être enregistré.");
      announce(`Carte exportée. Fichier : ${result.path}`);
    } catch (error) {
      announce(`Export impossible : ${error.message}`);
    }
  }

  /**
   * Récupérer les marques SHOM autour de la route associée à un jeton.
   *
   * Parameters
   * ----------
   * token : str
   *     Jeton de route transmis dans l'URL.
   *
   * @returns {Promise<Array<object>>}
   */
  async function fetchMarks(token) {
    const response = await fetch(`/api/map/marks/${encodeURIComponent(token)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "Marques SHOM indisponibles.");
    }
    return data.marks;
  }

  /**
   * Superposer les marques SHOM sur la carte, groupées par catégorie.
   *
   * Chaque catégorie devient un calque Leaflet indépendant, affiché ou
   * masqué par la case à cocher correspondante — sans reconstruire les
   * marqueurs à chaque changement.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte déjà construite par `renderRoute`.
   * marks : Array<object>
   *     Marques renvoyées par `/api/map/marks/<jeton>`, chacune avec son
   *     `icon_filename` éventuel (voir `shom_icons.py`).
   */
  function renderMarks(map, marks) {
    marks.forEach(mark => {
      const category = mark.category || "Autre";
      if (!markCategoryGroups[category]) {
        markCategoryGroups[category] = L.layerGroup().addTo(map);
      }

      let marker;
      if (mark.icon_filename) {
        // Icônes officielles du SHOM : 200×400 px, centrées sur le milieu
        // de l'image (pas ancrées en bas comme un marqueur classique en
        // forme de goutte) — voir docs/SPECIFICATIONS.md.
        const icon = L.icon({
          iconUrl: `/static/vendor/shom_icons/${mark.icon_filename}`,
          iconSize: [currentMarkerSize, currentMarkerSize * 2],
          iconAnchor: [currentMarkerSize / 2, currentMarkerSize]
        });
        marker = L.marker([mark.latitude, mark.longitude], {icon});
      } else {
        // Repli générique lorsqu'aucune icône fiable n'a pu être
        // déterminée (voir `select_icon_filename` dans shom_icons.py).
        marker = L.circleMarker([mark.latitude, mark.longitude], {
          radius: 5,
          color: "#000",
          weight: 1,
          fillColor: "#888888",
          fillOpacity: 1
        });
      }
      marker.bindTooltip(mark.name || category, {permanent: true, direction: "top", offset: [0, -10], className: "mark-tooltip"});
      marker.on("mouseover", () => {
        announce(`${mark.name || category} — ${describeMarkType(category, mark.icon_filename)}`);
      });
      marker.on("dblclick", () => {
        openMarkerInfoDialog(mark.name || category, "Marque SHOM environnante", describeMarkType(category, mark.icon_filename));
      });
      markCategoryGroups[category].addLayer(marker);
    });

    document.querySelectorAll('#marks-filter .marks-category-checkbox').forEach(checkbox => {
      checkbox.addEventListener("change", () => {
        const group = markCategoryGroups[checkbox.value];
        if (!group) return;
        if (checkbox.checked) {
          map.addLayer(group);
        } else {
          map.removeLayer(group);
        }
      });
    });
  }

  /**
   * Charger les couleurs par défaut de la page Configuration.
   *
   * Option A retenue après discussion : les couleurs (mer, terre, tracé de
   * route) sont des préférences durables, réglables uniquement en page
   * Configuration — pas d'ajustement en direct dans cette fenêtre, pour ne
   * pas la surcharger. Un échec (réseau, configuration indisponible)
   * n'empêche jamais l'affichage : les couleurs de repli déjà définies
   * restent utilisées.
   */
  async function loadDisplayColors() {
    try {
      const response = await fetch("/api/configuration");
      const data = await response.json();
      if (data.configuration) {
        currentSeaColor = data.configuration.map_sea_color || currentSeaColor;
        currentLandColor = data.configuration.map_land_color || currentLandColor;
        currentRouteColor = data.configuration.map_route_color || currentRouteColor;
        currentRouteLineWidth = data.configuration.map_route_line_width || currentRouteLineWidth;
        currentRouteLineStyle = data.configuration.map_route_line_style || currentRouteLineStyle;
        currentRouteLabelsVisible = data.configuration.map_route_labels_visible ?? currentRouteLabelsVisible;
        currentRouteLabelFontSize = data.configuration.map_route_label_font_size || currentRouteLabelFontSize;
        currentRouteLabelBordered = data.configuration.map_route_label_bordered ?? currentRouteLabelBordered;
        currentMarkerSize = data.configuration.map_marker_size || currentMarkerSize;
      }
    } catch (_error) {
      // Valeurs de repli déjà définies, rien de plus à faire.
    }
    document.getElementById("toggle-route-labels").checked = currentRouteLabelsVisible;
  }

  /**
   * Convertir un style de trait configuré en motif de tirets Leaflet.
   *
   * Parameters
   * ----------
   * style : str
   *     `"solid"`, `"dashed"` ou `"dotted"`.
   *
   * Returns
   * -------
   * str or null
   *     Motif `dashArray` à passer à Leaflet, ou `null` pour un trait continu.
   */
  function routeDashArrayForStyle(style) {
    if (style === "dashed") return "12 8";
    if (style === "dotted") return "2 6";
    return null;
  }

  /**
   * Construire l'attribut `stroke-dasharray` SVG correspondant à un style de trait.
   *
   * Parameters
   * ----------
   * style : str
   *     `"solid"`, `"dashed"` ou `"dotted"`.
   *
   * Returns
   * -------
   * str
   *     Attribut SVG complet (avec l'espace de tête), ou chaîne vide pour un trait continu.
   */
  function svgDashArrayAttribute(style) {
    const dashArray = routeDashArrayForStyle(style);
    return dashArray ? ` stroke-dasharray="${dashArray}"` : "";
  }

  /**
   * Choisir un pas de grille « rond » pour une étendue donnée, en degrés.
   *
   * Vise environ 5 à 6 lignes visibles, avec des valeurs lisibles (0,01°,
   * 0,02°, 0,05°, 0,1°... plutôt qu'un pas quelconque).
   *
   * Parameters
   * ----------
   * spanDegrees : number
   *     Étendue (latitude ou longitude) actuellement visible, en degrés.
   *
   * Returns
   * -------
   * number
   *     Pas de grille en degrés.
   */
  function niceGridStep(spanDegrees) {
    const candidates = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10];
    const rawStep = spanDegrees / 6;
    for (const step of candidates) {
      if (rawStep <= step) return step;
    }
    return 10;
  }

  /**
   * Construire la grille latitude/longitude pour l'emprise actuellement visible.
   *
   * Un calque de plus, reconstruit à chaque activation de la case à
   * cocher plutôt que suivi en direct du déplacement/zoom : suffisant pour
   * une grille de repère visuel, sans la complexité d'un recalcul continu.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte actuellement affichée.
   *
   * Returns
   * -------
   * L.LayerGroup
   *     Calque contenant les lignes et les étiquettes de graduation.
   */
  function buildGrid(map) {
    const bounds = map.getBounds();
    const south = bounds.getSouth();
    const north = bounds.getNorth();
    const west = bounds.getWest();
    const east = bounds.getEast();
    const latStep = niceGridStep(north - south);
    const lonStep = niceGridStep(east - west);
    const group = L.layerGroup();

    const lineStyle = {color: "#ffffff", weight: 1, opacity: 0.7, dashArray: "4 4", interactive: false};

    /** Ajouter une étiquette de graduation à une position donnée. */
    function addLabel(latLng, text) {
      L.marker(latLng, {
        icon: L.divIcon({className: "grid-label", html: text, iconSize: [70, 16]}),
        interactive: false
      }).addTo(group);
    }

    const firstLat = Math.ceil(south / latStep) * latStep;
    for (let lat = firstLat; lat <= north; lat += latStep) {
      L.polyline([[lat, west], [lat, east]], lineStyle).addTo(group);
      addLabel([lat, west], `${lat.toFixed(2)}°`);
    }

    const firstLon = Math.ceil(west / lonStep) * lonStep;
    for (let lon = firstLon; lon <= east; lon += lonStep) {
      L.polyline([[south, lon], [north, lon]], lineStyle).addTo(group);
      addLabel([north, lon], `${lon.toFixed(2)}°`);
    }

    return group;
  }

  /**
   * Basculer l'affichage de la grille latitude/longitude selon la case à cocher.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte actuellement affichée.
   * visible : bool
   *     `true` pour afficher la grille, `false` pour la retirer.
   */
  function toggleGrid(map, visible) {
    if (currentGridLayer) {
      map.removeLayer(currentGridLayer);
      currentGridLayer = null;
    }
    if (visible) {
      currentGridLayer = buildGrid(map);
      currentGridLayer.addTo(map);
    }
  }

  /**
   * Ajouter une barre d'échelle en milles nautiques, en bas à droite de la carte.
   *
   * Leaflet fournit un contrôle d'échelle natif (`L.control.scale`), mais
   * seulement en kilomètres/miles terrestres, jamais en milles nautiques —
   * d'où ce contrôle personnalisé, sur le même principe (mesure la
   * distance réelle visible, choisit une valeur ronde qui tient dans
   * environ un quart de la largeur de la carte).
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte sur laquelle ajouter le contrôle.
   */
  /**
   * Calculer le pas d'échelle « rond » en milles nautiques pour la vue actuelle.
   *
   * Mutualisée entre la barre d'échelle et les graduations des bords de la
   * carte, pour garantir un espacement rigoureusement identique entre les
   * deux (demandé explicitement) — vise une valeur qui tient dans environ
   * un quart de la largeur de la carte.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte actuellement affichée.
   *
   * Returns
   * -------
   * object
   *     `{chosenNm, totalNm, mapWidthPx}` : pas retenu, distance totale
   *     visible en largeur (milles nautiques) et largeur de la carte en
   *     pixels — ces deux dernières valeurs réutilisées pour dessiner la
   *     barre d'échelle elle-même.
   */
  function computeNiceNauticalStep(map) {
    const size = map.getSize();
    const halfHeight = size.y / 2;
    const westPoint = map.containerPointToLatLng([0, halfHeight]);
    const eastPoint = map.containerPointToLatLng([size.x, halfHeight]);
    const totalNm = westPoint.distanceTo(eastPoint) / 1852;
    const targetNm = totalNm * 0.25;
    const niceValues = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200];
    let chosenNm = niceValues[0];
    for (const value of niceValues) {
      if (value <= targetNm) chosenNm = value;
    }
    return {chosenNm, totalNm, mapWidthPx: size.x};
  }

  function addNauticalScaleControl(map) {
    const NauticalScaleControl = L.Control.extend({
      options: {position: "bottomright"},
      onAdd: function (leafletMap) {
        const container = L.DomUtil.create("div", "nautical-scale-control");
        this._leafletMap = leafletMap;
        this._container = container;
        leafletMap.on("moveend zoomend", this._update, this);
        this._update();
        return container;
      },
      onRemove: function (leafletMap) {
        leafletMap.off("moveend zoomend", this._update, this);
      },
      _update: function () {
        const {chosenNm, totalNm, mapWidthPx} = computeNiceNauticalStep(this._leafletMap);
        const widthPx = mapWidthPx * (chosenNm / totalNm);
        this._container.innerHTML = "";
        const bar = document.createElement("div");
        bar.className = "nautical-scale-bar";
        bar.style.width = `${widthPx.toFixed(0)}px`;
        bar.textContent = `${chosenNm} Milles`;
        this._container.appendChild(bar);
      }
    });
    new NauticalScaleControl().addTo(map);
  }

  // Rayon terrestre moyen en mètres, la même valeur que Leaflet utilise en
  // interne (L.CRS.Earth.R) pour ses propres calculs de distance — cohérence
  // avec `distanceTo()` déjà utilisé ci-dessus pour la barre d'échelle.
  const EARTH_RADIUS_METERS = 6371008.8;

  /**
   * Convertir une distance est-ouest en degrés de longitude, à une latitude donnée.
   *
   * Les méridiens se rapprochent aux hautes latitudes : la même distance
   * réelle correspond à un plus grand nombre de degrés de longitude qu'à
   * l'équateur, d'où la division par le cosinus de la latitude.
   *
   * Parameters
   * ----------
   * meters : number
   *     Distance réelle est-ouest, en mètres.
   * atLatitudeDeg : number
   *     Latitude à laquelle la conversion doit rester correcte, en degrés.
   *
   * Returns
   * -------
   * number
   *     Écart de longitude correspondant, en degrés.
   */
  function metersToLongitudeDelta(meters, atLatitudeDeg) {
    const latitudeRad = (atLatitudeDeg * Math.PI) / 180;
    return (meters / (EARTH_RADIUS_METERS * Math.cos(latitudeRad))) * (180 / Math.PI);
  }

  /**
   * Convertir une distance nord-sud en degrés de latitude.
   *
   * Contrairement à la longitude, la conversion ne dépend pas de la
   * position (un degré de latitude représente toujours à peu près la même
   * distance réelle).
   *
   * Parameters
   * ----------
   * meters : number
   *     Distance réelle nord-sud, en mètres.
   *
   * Returns
   * -------
   * number
   *     Écart de latitude correspondant, en degrés.
   */
  function metersToLatitudeDelta(meters) {
    return (meters / EARTH_RADIUS_METERS) * (180 / Math.PI);
  }

  /**
   * Ajouter des graduations en milles nautiques sur les 4 bords de la carte.
   *
   * Espacement rigoureusement identique à la valeur affichée par la barre
   * d'échelle (`computeNiceNauticalStep`, mutualisée) — si la barre affiche
   * « 2 Milles », les graduations se répètent tous les 2 milles nautiques,
   * quelle que soit l'échelle de la carte. Un simple survol visuel, pas un
   * calque de données : reconstruites à chaque déplacement/zoom plutôt que
   * suivies en continu, sur le même principe que la grille latitude/longitude.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte sur laquelle ajouter les graduations.
   */
  function addNauticalTickMarks(map) {
    const NauticalTickMarksControl = L.Control.extend({
      options: {position: "topleft"},
      onAdd: function (leafletMap) {
        // La position « topleft » ci-dessus ne sert qu'à l'enregistrement
        // du contrôle : la taille et la position réelles (toute la carte)
        // sont fixées explicitement ci-dessous, pour couvrir les 4 bords
        // plutôt qu'un seul coin.
        const container = L.DomUtil.create("div", "nautical-tick-overlay");
        this._leafletMap = leafletMap;
        this._container = container;
        leafletMap.on("moveend zoomend resize", this._update, this);
        this._update();
        return container;
      },
      onRemove: function (leafletMap) {
        leafletMap.off("moveend zoomend resize", this._update, this);
      },
      _addTick: function (position, edgeClassName) {
        const tick = document.createElement("div");
        tick.className = `nautical-tick ${edgeClassName}`;
        if (edgeClassName.includes("vertical")) {
          tick.style.left = `${position.toFixed(1)}px`;
        } else {
          tick.style.top = `${position.toFixed(1)}px`;
        }
        this._container.appendChild(tick);
      },
      _update: function () {
        const map = this._leafletMap;
        const {chosenNm} = computeNiceNauticalStep(map);
        const stepMeters = chosenNm * 1852;
        const size = map.getSize();
        const center = map.getCenter();
        const lonDelta = metersToLongitudeDelta(stepMeters, center.lat);
        const latDelta = metersToLatitudeDelta(stepMeters);

        this._container.innerHTML = "";
        this._container.style.width = `${size.x}px`;
        this._container.style.height = `${size.y}px`;

        // Graduations verticales (espacées selon la longitude), sur les
        // bords haut et bas. Limite de sécurité sur le nombre d'itérations :
        // ne devrait jamais être atteinte (chosenNm est toujours positif),
        // mais évite toute boucle infinie en cas de valeur inattendue.
        for (let lon = center.lng, i = 0; i < 200; lon -= lonDelta, i++) {
          const point = map.latLngToContainerPoint([center.lat, lon]);
          if (point.x < 0) break;
          this._addTick(point.x, "nautical-tick-vertical nautical-tick-top");
          this._addTick(point.x, "nautical-tick-vertical nautical-tick-bottom");
        }
        for (let lon = center.lng + lonDelta, i = 0; i < 200; lon += lonDelta, i++) {
          const point = map.latLngToContainerPoint([center.lat, lon]);
          if (point.x > size.x) break;
          this._addTick(point.x, "nautical-tick-vertical nautical-tick-top");
          this._addTick(point.x, "nautical-tick-vertical nautical-tick-bottom");
        }

        // Graduations horizontales (espacées selon la latitude), sur les
        // bords gauche et droite.
        for (let lat = center.lat, i = 0; i < 200; lat -= latDelta, i++) {
          const point = map.latLngToContainerPoint([lat, center.lng]);
          if (point.y > size.y) break;
          this._addTick(point.y, "nautical-tick-horizontal nautical-tick-left");
          this._addTick(point.y, "nautical-tick-horizontal nautical-tick-right");
        }
        for (let lat = center.lat + latDelta, i = 0; i < 200; lat += latDelta, i++) {
          const point = map.latLngToContainerPoint([lat, center.lng]);
          if (point.y < 0) break;
          this._addTick(point.y, "nautical-tick-horizontal nautical-tick-left");
          this._addTick(point.y, "nautical-tick-horizontal nautical-tick-right");
        }
      }
    });
    new NauticalTickMarksControl().addTo(map);
  }

  // État de l'outil de mesure : actif seulement si la case à cocher
  // correspondante est cochée, pour ne jamais entrer en conflit avec le
  // déplacement normal de la carte au clic-glisser.
  let measureModeActive = false;
  let measureStartLatLng = null;
  let measureTempLine = null;
  let lastMeasureText = "";

  const measureDialog = document.getElementById("measure-dialog");

  /**
   * Activer ou désactiver l'outil de mesure sur la carte.
   *
   * En mode mesure, le déplacement normal de la carte au clic-glisser est
   * désactivé : le même geste sert à tracer un segment de mesure plutôt
   * qu'à déplacer le cadre, pour éviter tout conflit entre les deux gestes.
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte actuellement affichée.
   * active : bool
   *     `true` pour activer l'outil de mesure, `false` pour revenir au
   *     déplacement normal de la carte.
   */
  function setMeasureModeActive(map, active) {
    measureModeActive = active;
    if (active) {
      map.dragging.disable();
      map.getContainer().style.cursor = "crosshair";
    } else {
      map.dragging.enable();
      map.getContainer().style.cursor = "";
      if (measureTempLine) {
        map.removeLayer(measureTempLine);
        measureTempLine = null;
      }
      measureStartLatLng = null;
    }
  }

  /**
   * Ouvrir la boîte de dialogue de résultat de mesure et y déplacer le focus.
   *
   * Le focus initial se pose sur le bouton « Copier », pas sur le titre —
   * même principe que la boîte de dialogue « modifications non
   * enregistrées » de l'éditeur : un titre n'est pas un contrôle
   * interactif, et certains lecteurs d'écran ne basculent pas de façon
   * fiable en mode formulaire sinon.
   *
   * Parameters
   * ----------
   * distanceNm : number
   *     Distance du segment mesuré, en milles nautiques.
   * bearingDegrees : number
   *     Cap vrai initial du segment mesuré, en degrés.
   */
  function openMeasureDialog(distanceNm, bearingDegrees) {
    lastMeasureText =
      `Distance : ${distanceNm.toFixed(2).replace(".", ",")} milles nautiques — ` +
      `Cap : ${Math.round(bearingDegrees)}°`;
    document.getElementById("measure-dialog-description").textContent = lastMeasureText;
    measureDialog.hidden = false;
    document.getElementById("measure-dialog-copy").focus();
  }

  /** Fermer la boîte de dialogue de résultat de mesure. */
  function closeMeasureDialog() {
    measureDialog.hidden = true;
  }

  // Piège de focus : tant que la boîte de dialogue est ouverte, Tab et
  // Maj+Tab restent cantonnés à ses deux boutons, et Échap la referme —
  // même comportement que la boîte de dialogue de l'éditeur.
  measureDialog.addEventListener("keydown", event => {
    const buttons = [...measureDialog.querySelectorAll("button")];
    const currentIndex = buttons.indexOf(document.activeElement);
    if (event.key === "Escape") {
      event.preventDefault();
      closeMeasureDialog();
    } else if (event.key === "Tab") {
      if (event.shiftKey && currentIndex <= 0) {
        event.preventDefault();
        buttons[buttons.length - 1].focus();
      } else if (!event.shiftKey && currentIndex === buttons.length - 1) {
        event.preventDefault();
        buttons[0].focus();
      }
    }
  });

  document.getElementById("measure-dialog-close").addEventListener("click", closeMeasureDialog);
  document.getElementById("measure-dialog-copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(lastMeasureText);
      announce("Mesure copiée dans le presse-papiers.");
    } catch (error) {
      announce(`Copie impossible : ${error.message}`);
    }
  });

  const markerInfoDialog = document.getElementById("marker-info-dialog");
  let lastMarkerInfoText = "";

  /**
   * Ouvrir la boîte de dialogue d'informations sur une marque (double-clic) et y déplacer le focus.
   *
   * Même principe que la boîte de dialogue de mesure : focus initial sur
   * le bouton « Copier », pas sur le titre.
   *
   * Parameters
   * ----------
   * name : str
   *     Nom du point ou de la marque.
   * source : str
   *     Provenance : « Point de la route » ou « Marque SHOM environnante ».
   * type : str
   *     Type de balise (Latérale, Cardinale, Danger isolé...), ou une
   *     mention explicite si l'information n'est pas disponible.
   */
  /**
   * Préciser le type d'une marque avec sa direction (cardinale) ou son côté
   * (latérale), déduits du nom de fichier de l'icône déjà résolue côté
   * serveur (voir `shom_icons.py`) plutôt que de la seule catégorie
   * générale (« Cardinale », « Latérale ») — repéré après retour
   * utilisateur : la catégorie seule ne suffisait pas à identifier
   * précisément une marque cardinale ou latérale.
   *
   * Parameters
   * ----------
   * category : str
   *     Catégorie générale de la marque (« Cardinale », « Latérale »...).
   * iconFilename : str or null
   *     Nom du fichier d'icône, s'il a pu être déterminé.
   *
   * Returns
   * -------
   * str
   *     Catégorie précisée si la direction/le côté a pu être déduit du nom
   *     de fichier, sinon la catégorie telle quelle.
   */
  function describeMarkType(category, iconFilename) {
    if (!iconFilename) return category;
    const cardinalDirections = {N: "Nord", E: "Est", S: "Sud", W: "Ouest"};
    const cardinalMatch = iconFilename.match(/^(?:BCNCAR|BOYCAR)_([NESW])/);
    if (cardinalMatch) {
      return `${category} ${cardinalDirections[cardinalMatch[1]]}`;
    }
    const lateralMatch = iconFilename.match(/^(?:BCNLAT|BOYLAT)_([BT])/);
    if (lateralMatch) {
      return `${category} ${lateralMatch[1] === "B" ? "bâbord" : "tribord"}`;
    }
    return category;
  }

  function openMarkerInfoDialog(name, source, type) {
    lastMarkerInfoText = `Nom : ${name}\nType : ${type}\nSource : ${source}`;
    document.getElementById("marker-info-dialog-description").textContent = lastMarkerInfoText;
    markerInfoDialog.hidden = false;
    document.getElementById("marker-info-dialog-copy").focus();
  }

  /** Fermer la boîte de dialogue d'informations sur une marque. */
  function closeMarkerInfoDialog() {
    markerInfoDialog.hidden = true;
  }

  // Piège de focus, identique à celui de la boîte de dialogue de mesure.
  markerInfoDialog.addEventListener("keydown", event => {
    const buttons = [...markerInfoDialog.querySelectorAll("button")];
    const currentIndex = buttons.indexOf(document.activeElement);
    if (event.key === "Escape") {
      event.preventDefault();
      closeMarkerInfoDialog();
    } else if (event.key === "Tab") {
      if (event.shiftKey && currentIndex <= 0) {
        event.preventDefault();
        buttons[buttons.length - 1].focus();
      } else if (!event.shiftKey && currentIndex === buttons.length - 1) {
        event.preventDefault();
        buttons[0].focus();
      }
    }
  });

  document.getElementById("marker-info-dialog-close").addEventListener("click", closeMarkerInfoDialog);
  document.getElementById("marker-info-dialog-copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(lastMarkerInfoText);
      announce("Informations copiées dans le presse-papiers.");
    } catch (error) {
      announce(`Copie impossible : ${error.message}`);
    }
  });

  /**
   * Brancher les gestionnaires de souris de l'outil de mesure sur la carte.
   *
   * Cliquer un premier point, maintenir le bouton enfoncé, glisser vers un
   * second point, relâcher pour afficher la distance et le cap du segment.
   * N'agit que lorsque le mode mesure est actif (voir `setMeasureModeActive`).
   *
   * Parameters
   * ----------
   * map : L.Map
   *     Carte sur laquelle brancher l'outil.
   */
  function setupMeasureTool(map) {
    map.on("mousedown", event => {
      if (!measureModeActive) return;
      measureStartLatLng = event.latlng;
      measureTempLine = L.polyline([event.latlng, event.latlng], {color: "#ffffff", weight: 2, dashArray: "6 4"}).addTo(map);
    });

    map.on("mousemove", event => {
      if (!measureModeActive || !measureStartLatLng || !measureTempLine) return;
      measureTempLine.setLatLngs([measureStartLatLng, event.latlng]);
    });

    map.on("mouseup", event => {
      if (!measureModeActive || !measureStartLatLng) return;
      const startPoint = {latitude: measureStartLatLng.lat, longitude: measureStartLatLng.lng};
      const endPoint = {latitude: event.latlng.lat, longitude: event.latlng.lng};
      if (measureTempLine) {
        map.removeLayer(measureTempLine);
        measureTempLine = null;
      }
      measureStartLatLng = null;
      // Un segment de longueur quasi nulle (simple clic, sans glisser)
      // n'est pas une mesure exploitable : on l'ignore silencieusement.
      const distanceNm = segmentDistanceNm(startPoint, endPoint);
      if (distanceNm < 0.001) return;
      const bearingDegrees = segmentInitialBearing(startPoint, endPoint);
      openMeasureDialog(distanceNm, bearingDegrees);
    });
  }

  document.getElementById("toggle-measure-tool").addEventListener("change", event => {
    if (currentMap) setMeasureModeActive(currentMap, event.target.checked);
  });

  async function initialize() {
    let token;
    try {
      token = readToken();
    } catch (error) {
      routeNameElement.textContent = "Impossible d’afficher la route";
      document.getElementById("map-container").textContent = error.message;
      announce(error.message);
      return;
    }

    await loadDisplayColors();

    try {
      const route = await fetchRoute(token);
      currentRoute = route;
      updateRouteSummary(route);
      currentMap = renderRoute(route.points || []);
      addNauticalScaleControl(currentMap);
      addNauticalTickMarks(currentMap);
      setupMeasureTool(currentMap);
      document.getElementById("export-segments-csv").disabled = false;
      document.getElementById("export-map-svg").disabled = false;
      announce(`Carte affichée pour la route ${route.name || "sans nom"}, ${route.points.length} point(s).`);
    } catch (error) {
      routeNameElement.textContent = "Impossible d’afficher la route";
      document.getElementById("map-container").textContent = error.message;
      announce(error.message);
      return;
    }

    // Le trait de côte est un complément visuel, pas un prérequis : son
    // indisponibilité (réseau, service SHOM, etc.) ne doit jamais empêcher
    // l'affichage déjà réussi des points de la route ci-dessus.
    try {
      const coastline = await fetchCoastline(token);
      currentCoastline = coastline;
      renderCoastline(currentMap, coastline);
    } catch (error) {
      coastlineCreditElement.textContent = `Trait de côte non affiché : ${error.message}`;
    }

    // Même principe pour les marques SHOM : un échec ne doit jamais
    // empêcher l'affichage déjà réussi de la route et du trait de côte.
    try {
      const marks = await fetchMarks(token);
      renderMarks(currentMap, marks);
    } catch (error) {
      announce(`Marques SHOM non affichées : ${error.message}`);
    }
  }

  document.getElementById("export-segments-csv").addEventListener("click", exportSegmentsCsvFromMap);
  document.getElementById("toggle-grid").addEventListener("change", event => {
    if (currentMap) toggleGrid(currentMap, event.target.checked);
  });
  document.getElementById("toggle-mark-labels").addEventListener("change", event => {
    document.getElementById("map-container").classList.toggle("hide-mark-labels", !event.target.checked);
  });
  document.getElementById("toggle-route-labels").addEventListener("change", event => {
    document.getElementById("map-container").classList.toggle("hide-route-labels", !event.target.checked);
  });
  document.getElementById("export-map-svg").addEventListener("click", exportMapSvg);

  /**
   * Fermer la fenêtre de visualisation cartographique.
   *
   * window.close() ne fonctionne que sur une fenêtre ouverte par un
   * script (window.open()) — jamais le cas en mode pywebview, où cette
   * fenêtre est créée côté Python. DesktopApi.close_map_window() est donc
   * requis dans ce mode ; window.close() reste valable en mode navigateur.
   */
  function closeMapWindow() {
    const desktopApi = window.pywebview?.api;
    if (desktopApi) {
      desktopApi.close_map_window();
    } else {
      window.close();
    }
  }

  document.getElementById("close-map-window").addEventListener("click", closeMapWindow);

  // Alt+F4 est normalement pris en charge nativement par Windows sans code
  // applicatif — mais signalé sans effet dans cette fenêtre pywebview,
  // vraisemblablement parce que le contenu web (WebView2) intercepte le
  // raccourci avant qu'il n'atteigne le châssis natif de la fenêtre.
  // Interception explicite en repli, sur le même chemin que le bouton
  // « Fermer ».
  document.addEventListener("keydown", event => {
    if (event.altKey && event.key === "F4") {
      event.preventDefault();
      closeMapWindow();
    }
  });

  initialize();
})();
