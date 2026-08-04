"use strict";

// L'ensemble du fichier est isolé dans une fonction immédiatement
// invoquée (IIFE) : les scripts classiques chargés côté page partagent
// le même environnement global, et cette isolation évite toute collision
// de nom (par exemple __version__/__date__) avec file_dialogs.js ou avec
// un futur script chargé sur la même page.
(function () {
  /**
   * Module : unified_editor.js
   * Description : Page « Créer une route » — composition d'une route par
   * double liste (points disponibles / points de la route), import depuis
   * SHOM, fichier ou saisie manuelle, réorganisation, analyse des segments,
   * enregistrement local, envoi vers SARA et export GPX/CSV/JSON.
   * Fonctions présentes (principales) : announce, copyStatusMessage,
   * activateRoute, transfer, move, render, buildRouteSegments,
   * exportSegmentsCsv, exportFormat, loadLocals, loadLocalInto, initialize.
   */

  const __version__ = "0.7.2.0";
  const __date__ = "2026-08-04";

  let available = [];
  let routePoints = [];
  let localRoutes = [];
  let availableItemName = "point";
  let routeActive = false;
  let routeDirty = false;
  let routeId = null;
  let renamingRoute = false;
  let activePointList = null;
  let activePointId = null;

  const $ = id => document.getElementById(id);
  const status = $("status-message");

  function announce(message, isError = false) {
    status.classList.toggle("error", isError);

    // La zone de messages est un champ en lecture seule afin que NVDA et le
    // clavier permettent de sélectionner puis copier le texte sans difficulté.
    status.value = "";
    window.setTimeout(() => { status.value = String(message); }, 20);
  }

  /** Copier intégralement le message actuellement affiché. */
  async function copyStatusMessage() {
    const message = status.value || "";
    if (!message) {
      announce("Aucun message à copier.", true);
      return;
    }

    try {
      await navigator.clipboard.writeText(message);
      status.focus();
      status.select();
    } catch (_error) {
      // Solution de repli compatible avec les moteurs WebView plus anciens.
      status.focus();
      status.select();
      document.execCommand("copy");
    }
  }

  async function json(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.message || "Erreur");
    return data;
  }

  /**
   * Normaliser le seuil de validation d'un point, en préservant la valeur 0.
   *
   * Dans SARA Navigation, un seuil à 0 désigne un point « Homme à la mer »
   * (MOB) : il n'est jamais validé automatiquement en approche, contrairement
   * à un point normal. Un simple `point.distance_threshold || 100` traiterait
   * à tort 0 comme une valeur absente (0 est « falsy » en JavaScript) et
   * transformerait silencieusement un point MOB importé en point normal.
   * Seules les valeurs réellement absentes, vides ou non numériques doivent
   * retomber sur la valeur par défaut de 100 m.
   */
  function normalizeDistanceThreshold(rawValue) {
    if (rawValue === undefined || rawValue === null || rawValue === "") return 100;
    const numericValue = Number(rawValue);
    return Number.isFinite(numericValue) ? numericValue : 100;
  }

  function normalize(point, source = "unknown") {
    return {
      id: point.id || crypto.randomUUID(),
      gps_id: point.gps_id || crypto.randomUUID(),
      name: point.name || "Point sans nom",
      latitude: Number(point.latitude),
      longitude: Number(point.longitude),
      distance_threshold: normalizeDistanceThreshold(point.distance_threshold),
      distance_nm: Number(point.distance_nm ?? Infinity),
      type: point.type || point.category || source,
      // Code d'objet S-57 d'origine (ex. "BCNLAT"), distinct de la
      // catégorie affichée ci-dessus : sert uniquement à retrouver l'icône
      // IALA correcte à l'affichage sur la carte. Conservé uniquement dans
      // la sauvegarde locale, jamais envoyé à SARA Navigation (option B,
      // voir docs/SPECIFICATIONS.md).
      object_code: point.object_code || "",
      source: point.source || source,
      properties: point.properties || {}
    };
  }

  function pointLabel(point, index, isRoute = false) {
    const position = isRoute ? `${index + 1}. ` : "";
    const distance = Number.isFinite(point.distance_nm) ? ` — ${point.distance_nm.toFixed(2)} milles nautiques` : "";
    return `${position}${point.name} — ${point.type || point.source}${distance}`;
  }

  /**
   * Construire la liste ordonnée des segments de la route active.
   *
   * @returns {Array<object>} Segments avec numéro, extrémités, longueur et cap.
   */
  function buildActiveRouteSegments() {
    return buildRouteSegments(routePoints);
  }

  /** Mettre à jour le résumé léger de l’analyse de la route. */
  function updateRouteAnalysis() {
    const segments = buildActiveRouteSegments();
    const totalDistance = segments.reduce((total, segment) => total + segment.distanceNm, 0);
    $("total-distance").textContent = `Distance totale : ${totalDistance.toFixed(2).replace(".", ",")} milles nautiques`;
    $("segment-count").textContent = `Nombre de segments : ${segments.length}`;
    $("export-segments-csv").disabled = segments.length === 0;
    $("visualize-route").disabled = segments.length === 0;
  }

  /** Charger les préférences utiles à l’export sans bloquer l’éditeur. */
  async function loadExportConfiguration() {
    try {
      const response = await json("/api/configuration");
      return response.configuration;
    } catch (_error) {
      return {csv_separator: ";"};
    }
  }

  /** Produire puis enregistrer le relevé détaillé des segments au format CSV UTF-8. */
  async function exportSegmentsCsv() {
    const segments = buildActiveRouteSegments();
    if (segments.length === 0) {
      announce("Impossible d’exporter : la route ne contient aucun segment.", true);
      return;
    }

    const configuration = await loadExportConfiguration();
    const separator = configuration.csv_separator === "TAB" ? "\t" : configuration.csv_separator;
    const rows = buildSegmentsCsvRows(segments, separator);

    const routeName = ($("route-name").value.trim() || "route")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[<>:"/\\|?*]+/g, "_")
      .replace(/\s+/g, "_");
    const filename = `${routeName}_segments.csv`;
    const blob = new Blob(["\uFEFF", rows.join("\r\n"), "\r\n"], {type: "text/csv;charset=utf-8"});

    try {
      const result = await saveBlobWithDialog(blob, filename, exportFileTypes("csv"));
      if (result.cancelled) {
        announce("Export annulé.");
        $("export-segments-csv").focus();
        return;
      }
      if (!result.saved) throw new Error(result.message || "Le fichier n’a pas pu être enregistré.");

      const plural = segments.length > 1;
      announce(
        `Export terminé. ${segments.length} segment${plural ? "s" : ""} `
        + `enregistré${plural ? "s" : ""}. Fichier : ${result.path}`
      );
      $("export-segments-csv").focus();
    } catch (error) {
      announce(`Export impossible : ${error.message}`, true);
      $("export-segments-csv").focus();
    }
  }

  function updateRouteContext() {
    const name = $("route-name").value.trim();
    $("current-route-heading").textContent = routeActive
      ? `Route en cours : ${name || "route non nommée"}`
      : "Route en cours : aucune route";
    $("current-route-summary").textContent = routeActive
      ? `${routePoints.length} point${routePoints.length > 1 ? "s" : ""}. ${routeDirty ? "Modifications non enregistrées." : "Aucune modification non enregistrée."}`
      : "Aucune route n’est ouverte. Saisissez un nom puis choisissez « Créer cette route », ou ouvrez une route existante depuis la Bibliothèque.";
    // Avant l'activation d'une route, seuls le champ nom et le bouton de
    // création sont utiles. Une fois la route en cours, le nom est déjà
    // annoncé par le H2 ci-dessus : le champ ne réapparaît que sur demande,
    // via « Renommer la route », pour éviter la redondance visuelle.
    $("route-name-field").hidden = routeActive && !renamingRoute;
    $("start-route-action").hidden = routeActive;
    $("rename-route-action").hidden = !routeActive || renamingRoute;
  }

  /** Révéler le champ nom pour le modifier, sur le modèle du renommage F2 de la Bibliothèque. */
  function startRenamingRoute() {
    renamingRoute = true;
    updateRouteContext();
    $("route-name").focus();
    $("route-name").select();
  }

  /** Refermer le champ nom après une saisie, en conservant le nom éventuellement modifié. */
  function stopRenamingRoute() {
    if (!renamingRoute) return;
    renamingRoute = false;
    updateRouteContext();
  }

  function markDirty() {
    if (!routeActive) return;
    routeDirty = true;
    updateRouteContext();
  }

  function setActivePoint(listName, pointId = null) {
    activePointList = listName;
    activePointId = pointId;

    // Une seule liste possède la sélection logique active. Cette règle évite
    // qu'une ancienne sélection de la liste de gauche masque la sélection de droite.
    const otherList = listName === "available" ? $("route-list") : $("available-list");
    if (otherList) otherList.selectedIndex = -1;

    showDetails();
    updateButtons();
  }

  function getActivePoint() {
    if (!activePointList || !activePointId) return null;
    const points = activePointList === "available" ? available : routePoints;
    return points.find(point => point.id === activePointId) || null;
  }

  function render() {
    const sortBy = $("sort-by").value;
    const sortOrder = $("sort-order").value;
    const typeFilter = $("type-filter").value;
    const displayed = available.filter(point => typeFilter === "all" || point.type === typeFilter);

    displayed.sort((a, b) => {
      let comparison;
      if (sortBy === "name") comparison = a.name.localeCompare(b.name, "fr", {sensitivity: "base"});
      else if (sortBy === "latitude") comparison = a.latitude - b.latitude;
      else comparison = a.distance_nm - b.distance_nm;
      return sortOrder === "desc" ? -comparison : comparison;
    });

    $("available-list").innerHTML = displayed.map((point, index) =>
      `<option value="${point.id}">${pointLabel(point, index)}</option>`).join("");
    $("route-list").innerHTML = routePoints.map((point, index) =>
      `<option value="${point.id}">${pointLabel(point, index, true)}</option>`).join("");

    $("available-heading").textContent = `Points importés : ${available.length}`;
    $("available-empty-message").hidden = available.length !== 0;
    $("available-empty-message").textContent = "Aucun point importé.";

    $("route-points-heading").textContent = `Points de la route : ${routePoints.length}`;
    $("route-empty-message").hidden = routePoints.length !== 0;
    $("route-empty-message").textContent = "Aucun point dans la route.";
    updateRouteAnalysis();

    // Restaurer uniquement la sélection logique active si l'élément reste visible.
    const activeList = activePointList === "available" ? $("available-list") : $("route-list");
    if (activeList && activePointId && [...activeList.options].some(option => option.value === activePointId)) {
      activeList.value = activePointId;
    } else if (activePointId) {
      activePointList = null;
      activePointId = null;
    }

    updateRouteContext();
    showDetails();
    updateButtons();
  }

  function selected(list, array) {
    return array.find(point => point.id === list.value);
  }

  function detailRows(point) {
    return {
      Nom: point.name,
      Latitude: Number.isFinite(point.latitude) ? point.latitude.toFixed(6) : point.latitude,
      Longitude: Number.isFinite(point.longitude) ? point.longitude.toFixed(6) : point.longitude,
      Type: point.type,
      Source: point.source,
      "Distance de validation": `${point.distance_threshold} m`,
      ...(point.properties || {})
    };
  }

  // Index de la ligne actuellement « armée » (tabindex 0) dans le panneau
  // de détails, pour la navigation par flèches haut/bas entre les lignes.
  let activeDetailRowIndex = 0;

  /**
   * Construire une ligne du panneau « Informations sur le point ».
   *
   * Chaque ligne est un élément unique, focusable individuellement
   * (navigation par flèches, pas Tab), avec un `aria-label` couvrant tout
   * le couple libellé/valeur : une seule unité de lecture NVDA par ligne,
   * qu'elle soit modifiable ou non. Sur une ligne modifiable, un vrai
   * `<input>` est imbriqué à l'intérieur — Tab depuis la ligne y entre
   * naturellement, et NVDA sait déjà nativement y sauter avec la touche
   * « E » en mode navigation, comme sur n'importe quel champ de texte.
   *
   * Parameters
   * ----------
   * label : str
   *     Libellé affiché et annoncé.
   * value : str
   *     Valeur actuelle, affichée et annoncée.
   * options : object, optional
   *     `editable` (bool), `inputType`, `min`, `max`, `step`, `onCommit`
   *     (fonction appelée avec la valeur brute saisie, à la perte de focus).
   *
   * Returns
   * -------
   * HTMLElement
   *     Élément de ligne prêt à insérer dans le panneau.
   */
  function buildDetailRow(label, value, options = {}) {
    const row = document.createElement("div");
    row.className = "details-line";
    row.tabIndex = -1;
    row.setAttribute("aria-label", `${label} : ${value}`);

    const labelSpan = document.createElement("span");
    labelSpan.className = "details-label";
    // Espace insécable avant les deux-points : sans elle, un libellé long
    // (« Distance de validation ») peut se couper juste avant, laissant
    // les deux-points seuls sur une ligne.
    labelSpan.textContent = `${label}\u00A0:`;
    row.appendChild(labelSpan);

    if (options.editable) {
      const input = document.createElement("input");
      input.type = options.inputType || "text";
      input.className = "details-value-input";
      input.value = value;
      // Retiré de l'ordre de tabulation naturel du navigateur (voir
      // wireDetailRowNavigation) : la mécanique implicite « tabindex 0 par
      // défaut sur l'input, mélangée au tabindex mobile de la ligne »
      // produisait un ordre ambigu selon le navigateur/lecteur d'écran,
      // avec un arrêt intermédiaire surprenant sur la ligne suivante.
      input.tabIndex = -1;
      if (options.min !== undefined) input.min = String(options.min);
      if (options.max !== undefined) input.max = String(options.max);
      if (options.step !== undefined) input.step = String(options.step);
      input.setAttribute("aria-label", label);
      input.addEventListener("blur", () => options.onCommit(input.value));
      row.appendChild(document.createTextNode(" "));
      row.appendChild(input);
    } else {
      const valueSpan = document.createElement("span");
      valueSpan.className = "details-value";
      valueSpan.textContent = String(value);
      row.appendChild(document.createTextNode(" "));
      row.appendChild(valueSpan);
    }
    return row;
  }

  /**
   * Brancher la navigation par flèches haut/bas entre les lignes d'un panneau.
   *
   * Reste sur place aux extrémités (pas de bouclage). Les flèches
   * fonctionnent aussi bien depuis la ligne elle-même que depuis un champ
   * modifiable imbriqué : une flèche haut/bas n'a aucun effet natif dans
   * un champ texte sur une seule ligne, la réutiliser ici pour la
   * navigation entre lignes ne prive donc l'utilisateur de rien.
   *
   * Parameters
   * ----------
   * container : HTMLElement
   *     Élément englobant les lignes `.details-line`.
   */
  function wireDetailRowNavigation(container) {
    container.addEventListener("keydown", event => {
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        const rows = [...container.querySelectorAll(".details-line")];
        if (rows.length === 0) return;
        const delta = event.key === "ArrowDown" ? 1 : -1;
        const nextIndex = Math.min(rows.length - 1, Math.max(0, activeDetailRowIndex + delta));
        if (nextIndex === activeDetailRowIndex) return;
        event.preventDefault();
        rows[activeDetailRowIndex].tabIndex = -1;
        rows[nextIndex].tabIndex = 0;
        activeDetailRowIndex = nextIndex;
        rows[nextIndex].focus();
        return;
      }

      if (event.key !== "Tab") return;

      // Un champ modifiable a lui-même un tabindex retiré de l'ordre
      // naturel (voir buildDetailRow) : sans cette gestion explicite, Tab
      // depuis un champ atterrirait sur la ligne suivante (tabindex -1,
      // donc ignorée) puis sur son propre champ, obligeant à appuyer deux
      // fois sur Tab pour passer réellement au champ suivant — corrigé
      // après signalement.
      if (event.target.classList.contains("details-line")) {
        if (event.shiftKey) return;
        const input = event.target.querySelector(".details-value-input");
        if (input) {
          event.preventDefault();
          input.focus();
        }
        return;
      }

      if (event.target.classList.contains("details-value-input")) {
        const inputs = [...container.querySelectorAll(".details-value-input")];
        const currentIndex = inputs.indexOf(event.target);
        const nextIndex = currentIndex + (event.shiftKey ? -1 : 1);
        // En dehors des bornes (avant le premier champ, après le dernier) :
        // laisser Tab sortir naturellement du panneau, sans intercepter.
        if (nextIndex >= 0 && nextIndex < inputs.length) {
          event.preventDefault();
          // Poser le focus sur le champ suivant AVANT que la perte de focus
          // du champ actuel ne se déclenche appliquerait la modification et
          // reconstruirait tout le panneau (nouvelles lignes, nouveaux
          // champs) — détruisant alors le champ visé, à peine focalisé, et
          // laissant le focus nulle part précis. Il faut inverser l'ordre :
          // déclencher explicitement la perte de focus (et la
          // reconstruction qui en découle) en premier, puis reposer le
          // focus sur le bon champ dans le panneau reconstruit. Repéré
          // après retour utilisateur (NVDA annonçait le titre de la page).
          event.target.blur();
          const freshInputs = [...$("point-details").querySelectorAll(".details-value-input")];
          freshInputs[nextIndex]?.focus();
        }
      }
    });
  }

  /** Appliquer une modification du nom d'un point de route (vide toléré, repli sur un nom générique). */
  function commitPointName(point, rawValue) {
    point.name = rawValue.trim() || "Point sans nom";
    markDirty();
    render();
  }

  /** Appliquer une modification de latitude, avec repli sur l'ancienne valeur si invalide. */
  function commitPointLatitude(point, rawValue) {
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed) || parsed < -90 || parsed > 90) {
      announce("Latitude invalide : elle doit être un nombre entre -90 et 90. Valeur reprise.", true);
      render();
      return;
    }
    point.latitude = parsed;
    markDirty();
    render();
  }

  /** Appliquer une modification de longitude, avec repli sur l'ancienne valeur si invalide. */
  function commitPointLongitude(point, rawValue) {
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed) || parsed < -180 || parsed > 180) {
      announce("Longitude invalide : elle doit être un nombre entre -180 et 180. Valeur reprise.", true);
      render();
      return;
    }
    point.longitude = parsed;
    markDirty();
    render();
  }

  /** Appliquer une modification du rayon d'activation, avec repli sur l'ancienne valeur si invalide. */
  function commitPointDistanceThreshold(point, rawValue) {
    const parsed = Number(rawValue);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > 1000) {
      announce("Le rayon d’activation doit être un nombre entier entre 1 et 1000 mètres. Valeur reprise.", true);
      render();
      return;
    }
    point.distance_threshold = parsed;
    markDirty();
    render();
  }

  function showDetails() {
    const point = getActivePoint();
    const details = $("point-details");
    // Ne remet le focus sur la première ligne qu'en cas de reconstruction
    // pendant que l'utilisateur naviguait déjà dans le panneau (nouvelle
    // sélection dans la liste des points de la route) — jamais lorsque la
    // reconstruction vient d'une perte de focus (l'utilisateur a déjà
    // déplacé son focus ailleurs de lui-même, ne pas le lui reprendre).
    const wasFocusInsidePanel = details.contains(document.activeElement);

    if (!point) {
      details.textContent = "Sélectionnez un point.";
      activeDetailRowIndex = 0;
      return;
    }

    // Seuls les points déjà ajoutés à la route sont modifiables : un point
    // encore dans « Points importés » n'a pas encore sa place définitive,
    // modifier sa position ou son nom à ce stade n'aurait pas de sens.
    const editable = activePointList === "route";

    const list = document.createElement("div");
    list.className = "details-list";

    const editableFields = [
      {
        label: "Nom", value: point.name, inputType: "text",
        onCommit: raw => commitPointName(point, raw)
      },
      {
        label: "Latitude",
        value: Number.isFinite(point.latitude) ? point.latitude.toFixed(6) : point.latitude,
        inputType: "text",
        onCommit: raw => commitPointLatitude(point, raw)
      },
      {
        label: "Longitude",
        value: Number.isFinite(point.longitude) ? point.longitude.toFixed(6) : point.longitude,
        inputType: "text",
        onCommit: raw => commitPointLongitude(point, raw)
      },
      {
        label: "Distance de validation (mètre)", value: point.distance_threshold,
        inputType: "number", min: 1, max: 1000, step: 1,
        onCommit: raw => commitPointDistanceThreshold(point, raw)
      }
    ];
    editableFields.forEach(field => {
      list.appendChild(buildDetailRow(field.label, field.value, {
        editable,
        inputType: field.inputType,
        min: field.min,
        max: field.max,
        step: field.step,
        onCommit: field.onCommit
      }));
    });

    const readOnlyRows = {Type: point.type, Source: point.source, ...(point.properties || {})};
    Object.entries(readOnlyRows)
      .filter(([, value]) => value !== null && value !== undefined && value !== "")
      .forEach(([key, value]) => {
        list.appendChild(buildDetailRow(key, value, {editable: false}));
      });

    details.replaceChildren(list);

    activeDetailRowIndex = 0;
    const rows = [...list.querySelectorAll(".details-line")];
    rows.forEach((row, index) => { row.tabIndex = index === 0 ? 0 : -1; });
    wireDetailRowNavigation(list);

    if (wasFocusInsidePanel) rows[0]?.focus();
  }

  function updateButtons() {
    const availableIndex = $("available-list").selectedIndex;
    const routeIndex = $("route-list").selectedIndex;
    const hasActivePoint = Boolean(getActivePoint());
    $("add-point").disabled = availableIndex < 0 || !routeActive;
    $("remove-point").disabled = routeIndex < 0 || !routeActive;
    $("move-up").disabled = routeIndex <= 0 || !routeActive;
    $("move-down").disabled = routeIndex < 0 || routeIndex >= routePoints.length - 1 || !routeActive;
    $("copy-info").disabled = !hasActivePoint;
    $("copy-coordinates").disabled = !hasActivePoint;
  }

  const leaveRouteDialog = $("leave-route-dialog");

  /** Ouvrir la boîte de dialogue « modifications non enregistrées » et y déplacer le focus.
   *
   * Le focus initial se pose sur le premier bouton, pas sur le titre : un
   * titre n'est pas un contrôle interactif, et certains lecteurs d'écran ne
   * basculent pas de façon fiable en mode formulaire si le focus initial
   * d'une boîte de dialogue n'atterrit pas sur un élément actionnable.
   */
  function openLeaveRouteDialog() {
    leaveRouteDialog.hidden = false;
    $("leave-route-save").focus();
  }

  /** Fermer la boîte de dialogue et, si demandé, rendre le focus au lien d'origine. */
  function closeLeaveRouteDialog(restoreFocus) {
    leaveRouteDialog.hidden = true;
    if (restoreFocus) $("back-to-library").focus();
  }

  // Piège de focus : tant que la boîte de dialogue est ouverte, Tab et
  // Maj+Tab restent cantonnés à ses trois boutons, et Échap équivaut à
  // « Annuler ». C'est le comportement attendu d'une boîte de dialogue
  // modale au clavier et avec NVDA.
  leaveRouteDialog.addEventListener("keydown", event => {
    const buttons = [...leaveRouteDialog.querySelectorAll("button")];
    const currentIndex = buttons.indexOf(document.activeElement);
    if (event.key === "Escape") {
      event.preventDefault();
      closeLeaveRouteDialog(true);
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

  $("leave-route-save").onclick = async () => {
    closeLeaveRouteDialog(false);
    if (await saveRouteLocally()) window.location.href = "/routes";
  };
  $("leave-route-discard").onclick = () => {
    // L'utilisateur vient de choisir explicitement d'abandonner les
    // modifications dans notre propre boîte de dialogue : inutile de le lui
    // redemander via l'invite générique « Quitter ce site ? » du navigateur.
    routeDirty = false;
    window.location.href = "/routes";
  };
  $("leave-route-cancel").onclick = () => closeLeaveRouteDialog(true);

  function activateRoute(name, points = [], isDirty = false, isNew = false, id = null) {
    routeActive = true;
    routePoints = points;
    routeDirty = isDirty;
    // Un id transmis (route chargée depuis la Bibliothèque) est conservé tel
    // quel, pour que l'identité de la route reste stable d'un enregistrement
    // à l'autre. Une route sans id (nouvelle route, ou copie explicite dont
    // routes.js vide volontairement l'id) reçoit un identifiant frais.
    routeId = id || crypto.randomUUID();
    renamingRoute = false;
    $("route-name").value = name || "";
    activePointList = points.length ? "route" : null;
    activePointId = points.length ? points[0].id : null;
    // Le H1 annonce le contexte réel de la page : une route nouvellement
    // créée n'est pas présentée comme « en modification », et inversement.
    const label = isNew ? `Nouvelle route : ${name}` : `Modifier : ${name}`;
    $("editor-title").textContent = label;
    document.title = `${label} — SARA Route Manager`;
    render();
    $("current-route-heading").focus();
  }

  function transfer(add) {
    if (!routeActive) {
      announce("Créez ou ouvrez d’abord une route.", true);
      return;
    }
    if (add) {
      const point = selected($("available-list"), available);
      if (!point) return;
      const addedPoint = {...point, id: crypto.randomUUID(), gps_id: crypto.randomUUID()};
      routePoints.push(addedPoint);
      activePointList = "route";
      activePointId = addedPoint.id;
    } else {
      const index = $("route-list").selectedIndex;
      if (index < 0) return;
      routePoints.splice(index, 1);
      const replacement = routePoints[Math.min(index, routePoints.length - 1)] || null;
      activePointList = replacement ? "route" : null;
      activePointId = replacement ? replacement.id : null;
    }
    markDirty();
    render();
    announce(add ? "Point ajouté à la route." : "Point retiré de la route.");
  }

  function move(delta) {
    if (!routeActive) return;
    const index = $("route-list").selectedIndex;
    const target = index + delta;
    if (index < 0 || target < 0 || target >= routePoints.length) return;
    [routePoints[index], routePoints[target]] = [routePoints[target], routePoints[index]];
    activePointList = "route";
    activePointId = routePoints[target].id;
    markDirty();
    render();
    announce(`Point déplacé en position ${target + 1}.`);
  }

  async function loadLocals() {
    // Cette liste alimente uniquement le choix « Autre route » comme source de
    // points : l'ouverture d'une route à modifier se fait depuis la Bibliothèque.
    const data = await json("/api/routes/local");
    localRoutes = data.routes || [];
    $("source-route-list").innerHTML = '<option value="">Choisir une route locale</option>' +
      localRoutes.map(route => `<option value="${route.file}">${route.name}</option>`).join("");
  }

  async function loadLocalInto(select) {
    if (!select.value) {
      announce("Choisissez une route.", true);
      return;
    }
    const data = await json(`/api/routes/local/${encodeURIComponent(select.value)}`);
    const points = data.route.points.map(point => normalize(point, "route"));
    available = points;
    availableItemName = "point";
    $("type-filter").value = "all";
    render();
    announce(`${points.length} point(s) chargés.`);
  }

  $("source-type").addEventListener("change", event => {
    document.querySelectorAll(".source-panel").forEach(panel => { panel.hidden = true; });
    $(`${event.target.value}-source`).hidden = false;
  });

  $("search-shom").onclick = async () => {
    try {
      announce("Recherche SHOM en cours…");
      const data = await json("/api/shom/search", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          center_latitude: $("center-latitude").value,
          center_longitude: $("center-longitude").value,
          radius: $("radius").value,
          unit: $("unit").value,
          categories: []
        })
      });
      available = data.marks.map(point => normalize(point, "SHOM"));
      availableItemName = "marque";
      $("type-filter").value = "all";
      render();
      $("available-heading").focus();
      announce(`Importation terminée. ${available.length} marques importées.`);
    } catch (error) { announce(error.message, true); }
  };

  $("import-file").onclick = async () => {
    const file = $("point-file").files[0];
    if (!file) return announce("Sélectionnez un fichier.", true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const data = await json("/api/routes/import", {method: "POST", body: formData});
      available = data.route.points.map(point => normalize(point, file.name.split(".").pop()));
      availableItemName = "point";
      $("type-filter").value = "all";
      render();
      $("available-heading").focus();
      announce(`${available.length} points importés.`);
    } catch (error) { announce(error.message, true); }
  };

  $("add-manual-source").onclick = () => {
    available.push(normalize({
      name: $("manual-name").value,
      latitude: $("manual-lat").value,
      longitude: $("manual-lon").value
    }, "manual"));
    availableItemName = "point";
    render();
    announce("Point manuel ajouté aux points disponibles.");
  };

  $("start-route").onclick = () => {
    const name = $("route-name").value.trim();
    if (!name) {
      announce("Saisissez d’abord le nom de la route.", true);
      $("route-name").focus();
      return;
    }
    activateRoute(name, [], true, true);
    announce(`Route ${name} créée. Choisissez maintenant une source de points.`);
  };

  $("load-source-route").onclick = () => loadLocalInto($("source-route-list"), "available");

  $("rename-route").onclick = startRenamingRoute;

  // Un changement du nom pendant qu'une route est active la marque comme
  // modifiée ; avant activation, ce champ ne fait que préparer la création.
  // La perte de focus referme le champ une fois la saisie terminée, qu'elle
  // vienne du bouton « Renommer la route » ou de l'ouverture depuis la
  // Bibliothèque (F2) : dans les deux cas, on annonce le nom retenu.
  $("route-name").addEventListener("input", () => { if (routeActive) markDirty(); });
  $("route-name").addEventListener("blur", () => {
    if (!routeActive || !renamingRoute) return;
    const name = $("route-name").value.trim();
    stopRenamingRoute();
    announce(name ? `Route renommée ${name}.` : "Le nom de la route est vide.", !name);
  });

  $("back-to-library").addEventListener("click", event => {
    if (!routeDirty) return;
    event.preventDefault();
    openLeaveRouteDialog();
  });
  $("add-point").onclick = () => transfer(true);
  $("remove-point").onclick = () => transfer(false);
  $("move-up").onclick = () => move(-1);
  $("move-down").onclick = () => move(1);
  [
    [$("available-list"), "available"],
    [$("route-list"), "route"]
  ].forEach(([list, listName]) => {
    const updateSelection = () => setActivePoint(listName, list.value || null);
    list.addEventListener("change", updateSelection);
    list.addEventListener("input", updateSelection);
    list.addEventListener("focus", () => {
      // Sans sélection par défaut au premier focus clavier, les flèches
      // haut/bas n'ont aucune position de départ tant qu'un clic souris
      // n'a pas explicitement choisi un premier élément — repéré après
      // signalement, corrigé ici et dans la Bibliothèque (listes de routes).
      if (list.selectedIndex === -1 && list.options.length > 0) {
        list.selectedIndex = 0;
      }
      if (list.value) setActivePoint(listName, list.value);
    });
  });
  $("type-filter").onchange = render;
  $("sort-by").onchange = render;
  $("sort-order").onchange = render;

  function payload() {
    return {id: routeId, name: $("route-name").value.trim(), points: routePoints, reversed: false};
  }

  function validateActiveRoute() {
    if (!routeActive) {
      announce("Créez ou ouvrez d’abord une route.", true);
      return false;
    }
    if (!$("route-name").value.trim()) {
      announce("Le nom de la route est obligatoire.", true);
      $("route-name").focus();
      return false;
    }
    return true;
  }

  /**
   * Ouvrir (ou recharger) la fenêtre de visualisation cartographique de la
   * route active.
   *
   * Un jeton temporaire côté serveur transmet la route, pour un
   * comportement identique en mode pywebview et en mode navigateur —
   * plutôt que `sessionStorage`, qui ne se partage pas forcément entre deux
   * fenêtres pywebview créées séparément côté Python.
   */
  async function openMapWindow() {
    if (!routeActive) {
      announce("Créez ou ouvrez d’abord une route.", true);
      return;
    }
    try {
      const data = await json("/api/map/token", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload())
      });
      const url = `${window.location.origin}/map?token=${encodeURIComponent(data.token)}`;
      const desktopApi = window.pywebview?.api;
      if (desktopApi) {
        // La fenêtre pywebview gère elle-même la réutilisation plutôt que
        // la duplication (voir DesktopApi.open_map_window côté serveur).
        await desktopApi.open_map_window(url);
      } else {
        // Une cible nommée identique réutilise le même onglet en mode
        // navigateur, pour un comportement équivalent au mode pywebview.
        window.open(url, "sara_map_window");
      }
      announce("Fenêtre de visualisation ouverte.");
    } catch (error) {
      announce(error.message, true);
    }
  }

  /**
   * Enregistrer la route active sur le PC.
   *
   * Factorisée pour être utilisée à la fois par le bouton « Enregistrer sur
   * le PC » et par la boîte de dialogue affichée avant de quitter l'éditeur
   * avec des modifications non enregistrées.
   *
   * @returns {Promise<boolean>} `true` si l'enregistrement a réussi.
   */
  async function saveRouteLocally() {
    if (!validateActiveRoute()) return false;
    try {
      const data = await json("/api/routes/save", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload())
      });
      routeDirty = false;
      updateRouteContext();
      announce(data.message);
      await loadLocals();
      return true;
    } catch (error) {
      announce(error.message, true);
      return false;
    }
  }

  $("save-route").onclick = saveRouteLocally;

  $("upload-route").onclick = async () => {
    if (!validateActiveRoute()) return;
    try {
      const data = await json("/api/routes/upload", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload())
      });
      routeDirty = false;
      updateRouteContext();
      announce(data.message);
    } catch (error) { announce(error.message, true); }
  };

  async function exportFormat(formatName) {
    if (!validateActiveRoute()) return;
    const exportButton = $(`export-${formatName}`);
    try {
      announce(`Préparation de l’export ${formatName.toUpperCase()}…`);
      const response = await fetch(`/api/routes/export/${formatName}`, {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload())
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || "Export impossible.");
      }

      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
      const filename = match
        ? decodeURIComponent(match[1].replace(/\"/g, ""))
        : `${$("route-name").value || "route"}.${formatName}`;
      const result = await saveBlobWithDialog(blob, filename, exportFileTypes(formatName));

      if (result.cancelled) {
        announce("Export annulé.");
        exportButton.focus();
        return;
      }
      if (!result.saved) throw new Error(result.message || "Le fichier n’a pas pu être enregistré.");

      announce(`Export ${formatName.toUpperCase()} terminé. Fichier : ${result.path}`);
      exportButton.focus();
    } catch (error) {
      announce(`Export impossible : ${error.message}`, true);
      exportButton.focus();
    }
  }

  ["gpx", "csv", "json"].forEach(formatName => {
    $(`export-${formatName}`).onclick = () => exportFormat(formatName);
  });

  $("export-segments-csv").onclick = exportSegmentsCsv;
  $("visualize-route").onclick = openMapWindow;
  $("copy-status-message").onclick = copyStatusMessage;

  $("copy-info").onclick = async () => {
    const point = getActivePoint();
    if (!point) return announce("Sélectionnez un point.", true);
    const text = Object.entries(detailRows(point))
      .filter(([, value]) => value !== null && value !== undefined && value !== "")
      .map(([key, value]) => `${key} : ${value}`)
      .join("\n");
    await navigator.clipboard.writeText(text);
    announce("Informations copiées.");
  };

  $("copy-coordinates").onclick = async () => {
    const point = getActivePoint();
    if (!point) return announce("Sélectionnez un point.", true);
    await navigator.clipboard.writeText(`${point.latitude}, ${point.longitude}`);
    announce("Coordonnées copiées.");
  };


  const pointContextMenu = $("point-context-menu");
  let pointContextSource = null;

  function focusActivePointList() {
    const list = activePointList === "available" ? $("available-list") : $("route-list");
    if (list) list.focus();
  }

  function closePointContextMenu(restoreFocus = false) {
    if (pointContextMenu.hidden) return;
    pointContextMenu.hidden = true;
    pointContextMenu.replaceChildren();
    if (restoreFocus && pointContextSource) pointContextSource.focus();
  }

  function pointMenuAction(label, handler, disabled = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.role = "menuitem";
    button.textContent = label;
    button.disabled = disabled;
    button.addEventListener("click", () => {
      closePointContextMenu(false);
      handler();
    });
    return button;
  }

  function openPointContextMenu(list, x = null, y = null) {
    const listName = list === $("available-list") ? "available" : "route";
    setActivePoint(listName, list.value || null);
    const point = getActivePoint();
    if (!point) return announce("Aucun point sélectionné.", true);
    pointContextSource = list;
    pointContextMenu.replaceChildren();
    if (listName === "available") {
      pointContextMenu.appendChild(pointMenuAction("Ajouter à la route", () => transfer(true), !routeActive));
    } else {
      pointContextMenu.appendChild(pointMenuAction("Retirer de la route", () => transfer(false), !routeActive));
      pointContextMenu.appendChild(pointMenuAction("Monter", () => move(-1), list.selectedIndex <= 0 || !routeActive));
      pointContextMenu.appendChild(pointMenuAction("Descendre", () => move(1), list.selectedIndex < 0 || list.selectedIndex >= routePoints.length - 1 || !routeActive));
    }
    pointContextMenu.appendChild(pointMenuAction("Afficher les informations", () => $("details-heading").focus()));
    pointContextMenu.appendChild(pointMenuAction("Copier les informations", () => $("copy-info").click()));
    pointContextMenu.appendChild(pointMenuAction("Copier les coordonnées", () => $("copy-coordinates").click()));
    const rect = list.getBoundingClientRect();
    pointContextMenu.style.left = `${Math.max(8, x ?? rect.left + 24)}px`;
    pointContextMenu.style.top = `${Math.max(8, y ?? rect.top + 24)}px`;
    pointContextMenu.hidden = false;
    pointContextMenu.querySelector("button:not([disabled])")?.focus();
    announce("Menu contextuel du point ouvert.");
  }

  pointContextMenu.addEventListener("keydown", event => {
    const items = [...pointContextMenu.querySelectorAll("button:not([disabled])")];
    const index = items.indexOf(document.activeElement);
    if (event.key === "Escape") {
      event.preventDefault();
      closePointContextMenu(true);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      items[(index + 1) % items.length]?.focus();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      items[(index - 1 + items.length) % items.length]?.focus();
    } else if (event.key === "Home") {
      event.preventDefault();
      items[0]?.focus();
    } else if (event.key === "End") {
      event.preventDefault();
      items.at(-1)?.focus();
    }
  });

  [$("available-list"), $("route-list")].forEach(list => {
    list.addEventListener("contextmenu", event => {
      event.preventDefault();
      openPointContextMenu(list, event.clientX, event.clientY);
    });
    list.addEventListener("keydown", event => {
      if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
        event.preventDefault();
        openPointContextMenu(list);
      } else if (event.key === "Delete" && list === $("route-list")) {
        event.preventDefault();
        transfer(false);
        focusActivePointList();
      } else if (event.key === "Escape") {
        closePointContextMenu(true);
      }
    });
  });

  document.addEventListener("click", event => {
    if (!pointContextMenu.hidden && !pointContextMenu.contains(event.target)) closePointContextMenu(false);
  });

  document.addEventListener("keydown", event => {
    if (event.altKey && event.key === "ArrowRight") { event.preventDefault(); transfer(true); }
    if (event.altKey && event.key === "ArrowLeft") { event.preventDefault(); transfer(false); }
    if (event.altKey && event.key === "ArrowUp") { event.preventDefault(); move(-1); }
    if (event.altKey && event.key === "ArrowDown") { event.preventDefault(); move(1); }
    if (event.altKey && event.key.toLowerCase() === "c") {
      event.preventDefault();
      (event.shiftKey ? $("copy-coordinates") : $("copy-info")).click();
    }
    if (event.altKey && event.key.toLowerCase() === "e") {
      event.preventDefault();
      const firstEditableInput = $("point-details").querySelector(".details-value-input");
      if (firstEditableInput) {
        firstEditableInput.focus();
      } else {
        announce("Aucun champ modifiable : sélectionnez d’abord un point déjà ajouté à la route.", true);
      }
    }
    if (event.key === "Enter" && (document.activeElement === $("available-list") || document.activeElement === $("route-list"))) {
      event.preventDefault();
      const listName = document.activeElement === $("available-list") ? "available" : "route";
      setActivePoint(listName, document.activeElement.value || null);
      $("details-heading").focus();
    }
  });

  window.addEventListener("beforeunload", event => {
    if (!routeDirty) return;
    event.preventDefault();
    event.returnValue = "";
  });

  async function initialize() {
    await loadLocals();
    const stored = sessionStorage.getItem("sara_editor_route");
    if (stored) {
      sessionStorage.removeItem("sara_editor_route");
      const route = JSON.parse(stored);
      activateRoute(route.name || "Route", (route.points || []).map(point => normalize(point, "route")), false, false, route.id || null);
      if (sessionStorage.getItem("sara_editor_focus_name") === "1") {
        sessionStorage.removeItem("sara_editor_focus_name");
        startRenamingRoute();
        announce(`Route ${route.name || "sans nom"} ouverte. Modifiez son nom puis enregistrez.`);
      } else {
        announce(`Route ${route.name || "sans nom"} ouverte.`);
      }
    } else {
      render();
    }
  }

  initialize().catch(error => announce(error.message, true));
})();
