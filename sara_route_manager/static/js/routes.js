"use strict";

// L'ensemble du fichier est isolé dans une fonction immédiatement
// invoquée (IIFE) : les scripts classiques chargés côté page partagent
// le même environnement global, et cette isolation évite toute collision
// de nom (par exemple __version__/__date__) avec file_dialogs.js ou avec
// un futur script chargé sur la même page.
(function () {
  /**
   * Module : routes.js
   * Description : Page « Bibliothèque » (0.8.0) — une liste unique réunit les
   * routes en ligne (« Mes routes (en partage) » et « Autres routes (en partage) ») et les routes enregistrées
   * sur ce PC. Un filtre à boutons radio et une recherche par nom réduisent
   * la liste ; les actions (ouvrir, exporter, importer, supprimer) portent sur
   * la route sélectionnée, et le menu contextuel ajoute dupliquer, copier et
   * renommer. La route choisie est transmise à l'éditeur via sessionStorage.
   * Fonctions présentes : announce, requestJson, formatDate, originLabel,
   * routeLabel, buildEntries, visibleEntries, renderList, selectedEntry,
   * updateActionStates, hasLocalCopy, downloadAllowed, actionHint, viewMapSelected, openEditor, loadLocalRoute, loadRouteData,
   * downloadSelected, openSelected, duplicateSelected, renameSelected, deleteSelected,
   * exportRoute, exportSelected, importRouteFile,
   * openContextMenu, closeContextMenu, refreshRemoteRoutes,
   * refreshLocalRoutes, refreshAccountState.
   */

  const __version__ = "0.9.4";
  const __date__ = "2026-11-19";

  const statusMessage = document.getElementById("status-message");
  const list = document.getElementById("routes-list");
  const summary = document.getElementById("routes-summary");
  const searchField = document.getElementById("route-search");
  const importInput = document.getElementById("route-import-file");

  // Collections brutes reçues du serveur, une par origine.
  const routeCollections = {mine: [], community: [], local: []};
  // Ordre d'affichage des origines pour départager deux routes de même nom.
  const KIND_ORDER = {mine: 0, local: 1, community: 2};
  // Entrées actuellement affichées (après filtre et recherche).
  let shownEntries = [];
  // Vrai quand le compte SARA est connecté (renseigné par refreshAccountState).
  let accountConnected = false;
  // Réglage « confirmer avant d'écraser un fichier », lu dans la configuration.
  let confirmOverwrite = true;

  /**
   * Annoncer un message dans la zone de statut (lue par les lecteurs d'écran).
   *
   * @param {string} message - Texte à annoncer.
   * @param {boolean} isError - Vrai pour afficher le message comme une erreur.
   */
  function announce(message, isError = false) {
    statusMessage.textContent = "";
    statusMessage.classList.toggle("error", isError);
    // Le court délai force la relecture même si le texte est identique.
    window.setTimeout(() => { statusMessage.textContent = message; }, 20);
  }

  /**
   * Appeler une API JSON locale et lever une erreur lisible en cas d'échec.
   *
   * @param {string} url - Adresse de l'API.
   * @param {object} options - Options transmises à fetch.
   * @returns {Promise<object>} Résultat décodé.
   */
  async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.message || "Erreur inconnue.");
    return result;
  }

  /** Mettre en forme une date SARA AAAA-MM-JJ_HH:MM:SS en JJ/MM/AAAA à HH:MM. */
  function formatDate(value) {
    if (!value) return "date non indiquée";
    const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})_(\d{2}):(\d{2}):(\d{2})$/);
    return match ? `${match[3]}/${match[2]}/${match[1]} à ${match[4]}:${match[5]}` : String(value);
  }

  /** Donner le libellé parlé de l'origine d'une route. */
  function originLabel(kind) {
    if (kind === "mine") return "mes routes en partage";
    if (kind === "community") return "autres routes en partage";
    return "sur ce PC";
  }

  /** Construire le texte d'une ligne : nom, nombre de points, origine, date. */
  function routeLabel(entry) {
    const route = entry.route;
    const count = Number(route.points_count ?? (route.points || []).length ?? 0);
    const countText = `${count} point${count > 1 ? "s" : ""}`;
    const dateText = route.last_update_time ? ` — date de dépôt ${formatDate(route.last_update_time)}` : "";
    return `${route.name} — ${countText} — ${originLabel(entry.kind)}${dateText}`;
  }

  /** Rassembler les trois collections en une liste d'entrées {kind, route}. */
  function buildEntries() {
    const entries = [];
    Object.keys(routeCollections).forEach(kind => {
      routeCollections[kind].forEach(route => entries.push({kind, route}));
    });
    return entries;
  }

  /**
   * Appliquer le filtre radio et la recherche, puis trier par nom.
   *
   * @returns {Array<object>} Entrées à afficher.
   */
  function visibleEntries() {
    const filter = document.querySelector('input[name="route-filter"]:checked').value;
    const needle = searchField.value.trim().toLocaleLowerCase("fr");
    return buildEntries()
      .filter(entry => filter === "all" || entry.kind === filter)
      .filter(entry => !needle || String(entry.route.name).toLocaleLowerCase("fr").includes(needle))
      .sort((a, b) => String(a.route.name).localeCompare(String(b.route.name), "fr", {sensitivity: "base"})
        || KIND_ORDER[a.kind] - KIND_ORDER[b.kind]);
  }

  /** Retourner l'entrée sélectionnée dans la liste, ou null. */
  function selectedEntry() {
    const index = Number(list.value);
    return list.value !== "" && Number.isInteger(index) ? shownEntries[index] || null : null;
  }

  /**
   * Reconstruire la liste en conservant, si possible, la route sélectionnée.
   */
  function renderList() {
    const previous = selectedEntry();
    shownEntries = visibleEntries();
    list.replaceChildren();
    shownEntries.forEach((entry, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = routeLabel(entry);
      list.appendChild(option);
    });
    const found = previous ? shownEntries.findIndex(entry => entry.route === previous.route && entry.kind === previous.kind) : -1;
    if (shownEntries.length > 0) list.selectedIndex = found >= 0 ? found : 0;
    // Le nom du filtre ouvre la phrase : après un changement de bouton radio,
    // on sait ainsi à quel filtre correspond le nombre annoncé.
    const filterName = document.querySelector('input[name="route-filter"]:checked').parentElement.textContent.trim();
    const total = buildEntries().length;
    summary.textContent = total === 0
      ? `${filterName} : aucune route disponible.`
      : `${filterName} : ${shownEntries.length} route${shownEntries.length > 1 ? "s" : ""} affichée${shownEntries.length > 1 ? "s" : ""} sur ${total}.`;
    updateActionStates();
  }

  /** Activer ou désactiver les boutons selon la sélection, et adapter leurs libellés. */
  function updateActionStates() {
    const entry = selectedEntry();
    const openButton = document.getElementById("route-open");
    openButton.textContent = entry && entry.kind === "community" ? "Consulter" : "Éditer";
    openButton.disabled = !entry;
    document.getElementById("route-view").disabled = !entry;
    document.getElementById("route-export").disabled = !entry;
    // « Télécharger » (comme dans SARA Navigation) ne concerne que les routes en ligne,
    // et reste grisé pour une de vos routes déjà enregistrée sur ce PC.
    document.getElementById("route-download").disabled = !entry || !downloadAllowed(entry);
    // Une route partagée appartient à quelqu'un d'autre : elle ne se supprime pas ici.
    document.getElementById("route-delete").disabled = !entry || entry.kind === "community";
    document.getElementById("route-action-hint").textContent = actionHint(entry);
  }

  /**
   * Indiquer si une copie locale de même nom existe déjà sur ce PC.
   *
   * @param {object} entry - Entrée {kind, route}.
   * @returns {boolean} Vrai si une route locale porte le même nom.
   */
  function hasLocalCopy(entry) {
    return routeCollections.local.some(route => route.name === entry.route.name);
  }

  /**
   * Dire si « Télécharger » est proposé pour cette entrée.
   *
   * Une route locale n'a rien à télécharger ; une de vos routes en ligne n'est
   * proposée que si elle n'est pas déjà sur ce PC ; la route d'un autre
   * utilisateur reste téléchargeable (avec confirmation d'écrasement si besoin).
   *
   * @param {object} entry - Entrée {kind, route}.
   * @returns {boolean} Vrai si le téléchargement est proposé.
   */
  function downloadAllowed(entry) {
    if (entry.kind === "local") return false;
    if (entry.kind === "mine") return !hasLocalCopy(entry);
    return true;
  }

  /**
   * Expliquer en une phrase ce que l'on peut faire de la route sélectionnée.
   *
   * @param {object|null} entry - Entrée sélectionnée ou null.
   * @returns {string} Phrase affichée sous les boutons.
   */
  function actionHint(entry) {
    if (!entry) return "Sélectionnez une route pour voir les actions possibles.";
    if (entry.kind === "local") {
      return "Route enregistrée sur ce PC : éditer, voir la carte, renommer, dupliquer, exporter ou supprimer. Pour la mettre en ligne, utilisez « Déposer en ligne » dans l’éditeur.";
    }
    if (entry.kind === "mine") {
      return hasLocalCopy(entry)
        ? "Votre route en partage : « Télécharger » est indisponible car elle est déjà enregistrée sur ce PC."
        : "Votre route en partage : vous pouvez la télécharger sur ce PC, l’éditer, voir la carte, l’exporter ou la supprimer de la liste en partage.";
    }
    return "Route d’un autre utilisateur : consulter, voir la carte, télécharger, copier dans vos routes ou exporter. Elle ne peut pas être supprimée ici.";
  }

  /**
   * Transmettre une route à l'éditeur puis ouvrir celui-ci.
   *
   * @param {object} route - Route au format API.
   * @param {boolean} makeCopy - Vrai pour créer une copie indépendante.
   */
  function openEditor(route, makeCopy = false) {
    const selected = JSON.parse(JSON.stringify(route));
    if (makeCopy) {
      selected.id = "";
      selected.owner = "";
      selected.remote_key = "";
      selected.last_update_time = "";
      selected.own = false;
      selected.name = `${selected.name} - copie`;
    }
    sessionStorage.setItem("sara_editor_route", JSON.stringify(selected));
    window.location.href = "/editor";
  }

  /** Charger le contenu complet d'une route locale depuis le serveur. */
  async function loadLocalRoute(route) {
    return (await requestJson(`/api/routes/local/${encodeURIComponent(route.file)}`)).route;
  }

  /**
   * Obtenir les données complètes d'une entrée, quelle que soit son origine.
   *
   * @param {object} entry - Entrée {kind, route}.
   * @returns {Promise<object>} Route au format API, avec l'indicateur `own`.
   */
  async function loadRouteData(entry) {
    if (entry.kind === "local") return loadLocalRoute(entry.route);
    return {...entry.route, own: entry.kind === "mine"};
  }

  /**
   * Télécharger la route en ligne sélectionnée : l'enregistrer sur ce PC.
   *
   * Même comportement que le bouton « Télécharger » de SARA Navigation : si une
   * route locale porte déjà ce nom, il faut confirmer l'écrasement (sauf si le
   * réglage « confirmer avant d'écraser » est désactivé dans la Configuration).
   */
  async function downloadSelected() {
    const entry = selectedEntry();
    if (!entry) return;
    if (entry.kind === "local") {
      announce("Cette route est déjà enregistrée sur ce PC.", true);
      return;
    }
    try {
      const check = await requestJson("/api/routes/local/exists", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name: entry.route.name})
      });
      if (check.exists && confirmOverwrite && !window.confirm("Une route avec le même nom existe déjà, voulez-vous l’écraser ?")) {
        announce("Téléchargement annulé : la route locale existante est conservée.");
        list.focus();
        return;
      }
      await requestJson("/api/routes/save", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(entry.route)
      });
      await refreshLocalRoutes();
      announce("La route a été téléchargée et sauvegardée avec succès.");
    } catch (error) {
      announce(`Téléchargement impossible : ${error.message}`, true);
    }
    list.focus();
  }

  /** Éditer (ou consulter) la route sélectionnée : ouverture dans l'éditeur. */
  async function openSelected() {
    const entry = selectedEntry();
    if (!entry) return;
    try { openEditor(await loadRouteData(entry)); } catch (error) { announce(error.message, true); }
  }

  /**
   * Afficher la route sélectionnée sur la carte, sans passer par l'éditeur.
   *
   * Reprend le mécanisme de l'éditeur : un jeton temporaire côté serveur
   * transmet la route à la fenêtre carte, qui est réutilisée si elle est déjà
   * ouverte. Comme dans SARA Navigation, il faut au moins 2 points.
   */
  async function viewMapSelected() {
    const entry = selectedEntry();
    if (!entry) return;
    try {
      const route = await loadRouteData(entry);
      const points = route.points || [];
      if (points.length < 2) {
        announce("La route doit contenir au moins deux points pour être affichée sur la carte.", true);
        return;
      }
      const data = await requestJson("/api/map/token", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: route.name, points})
      });
      const url = `${window.location.origin}/map?token=${encodeURIComponent(data.token)}`;
      const desktopApi = window.pywebview?.api;
      if (desktopApi) {
        await desktopApi.open_map_window(url);
      } else {
        window.open(url, "sara_map_window");
      }
      announce(`Carte ouverte : ${route.name}, ${points.length} points.`);
    } catch (error) {
      announce(error.message, true);
    }
  }

  /** Ouvrir l'éditeur sur une copie de la route sélectionnée (dupliquer ou copier). */
  async function duplicateSelected() {
    const entry = selectedEntry();
    if (!entry) return;
    try { openEditor(await loadRouteData(entry), true); } catch (error) { announce(error.message, true); }
  }

  /** Ouvrir la route dans l'éditeur avec le focus sur le champ du nom. */
  async function renameSelected() {
    const entry = selectedEntry();
    if (!entry) return;
    if (entry.kind === "community") {
      announce("La route d’un autre utilisateur doit d’abord être copiée avant d’être renommée.", true);
      return;
    }
    sessionStorage.setItem("sara_editor_focus_name", "1");
    await openSelected();
  }

  /** Supprimer la route sélectionnée (compte SARA ou PC) après confirmation. */
  async function deleteSelected() {
    const entry = selectedEntry();
    if (!entry) return;
    if (entry.kind === "community") {
      announce("La suppression n’est pas autorisée pour la route d’un autre utilisateur.", true);
      return;
    }
    const where = entry.kind === "mine" ? "en ligne" : "de ce PC";
    if (!window.confirm(`Voulez-vous supprimer la route « ${entry.route.name} » ${where} ? Cette action est définitive.`)) {
      announce("Suppression annulée.");
      list.focus();
      return;
    }
    const oldIndex = list.selectedIndex;
    try {
      let result;
      if (entry.kind === "mine") {
        const remoteKey = entry.route.remote_key || entry.route.id || entry.route.key;
        if (!remoteKey) throw new Error("La référence distante de cette route est absente.");
        result = await requestJson("/api/routes/delete", {
          method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({remote_key: remoteKey})
        });
        await refreshRemoteRoutes(false);
      } else {
        result = await requestJson("/api/routes/local/delete", {
          method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({file: entry.route.file})
        });
        await refreshLocalRoutes();
      }
      // Replacer la sélection près de la route supprimée pour ne pas perdre sa position.
      if (list.options.length > 0) list.selectedIndex = Math.min(oldIndex, list.options.length - 1);
      updateActionStates();
      announce(result.message);
    } catch (error) {
      announce(error.message, true);
    }
    list.focus();
  }

  /**
   * Exporter une route dans le format demandé via le dialogue « Enregistrer sous ».
   *
   * @param {object} route - Route au format API.
   * @param {string} formatName - « json », « gpx » ou « csv ».
   */
  async function exportRoute(route, formatName) {
    announce(`Préparation de l’export ${formatName.toUpperCase()} de ${route.name}…`);
    try {
      const response = await fetch(`/api/routes/export/${formatName}`, {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(route)
      });
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.message || "Export impossible.");
      }
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
      const filename = match ? decodeURIComponent(match[1].replace(/\"/g, "")) : `route.${formatName}`;
      const result = await saveBlobWithDialog(blob, filename, exportFileTypes(formatName));

      if (result.cancelled) {
        announce("Export annulé.");
        return;
      }
      if (!result.saved) throw new Error(result.message || "Le fichier n’a pas pu être enregistré.");
      announce(`Route ${route.name} exportée au format ${formatName.toUpperCase()}. Fichier : ${result.path}`);
    } catch (error) { announce(`Export impossible : ${error.message}`, true); }
  }

  // ---------------------------------------------------------------------
  // Export : la boîte de dialogue de choix du format est commune (export_dialog.js)
  // ---------------------------------------------------------------------

  /** Demander le format puis exporter la route sélectionnée. */
  async function exportSelected() {
    const entry = selectedEntry();
    if (!entry) { announce("Aucune route sélectionnée.", true); return; }
    const formatName = await chooseExportFormat(list);
    if (!formatName) { announce("Export annulé."); return; }
    try { await exportRoute(await loadRouteData(entry), formatName); } catch (error) { announce(error.message, true); }
    list.focus();
  }

  // ---------------------------------------------------------------------
  // Import d'une route depuis un fichier JSON, GPX, CSV ou WPT
  // ---------------------------------------------------------------------

  /**
   * Importer un fichier comme route complète et l'enregistrer sur ce PC.
   *
   * La route garde son nom, son sens et ses points. Si une route locale porte
   * déjà le même nom, une confirmation est demandée avant de la remplacer.
   *
   * @param {File} file - Fichier choisi par l'utilisateur.
   */
  async function importRouteFile(file) {
    announce(`Import de ${file.name} en cours…`);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const imported = (await requestJson("/api/routes/import", {method: "POST", body: formData})).route;
      // Une route importée est une route locale neuve : aucune identité distante n'est reprise.
      imported.owner = "";
      imported.remote_key = "";
      imported.last_update_time = "";
      const check = await requestJson("/api/routes/local/exists", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name: imported.name})
      });
      if (check.exists && confirmOverwrite && !window.confirm(`Une route locale nommée « ${imported.name} » existe déjà. La remplacer ?`)) {
        announce("Import annulé : la route existante est conservée.");
        return;
      }
      const saved = await requestJson("/api/routes/save", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(imported)
      });
      await refreshLocalRoutes();
      // Rendre la route importée visible, puis la sélectionner.
      document.querySelector('input[name="route-filter"][value="all"]').checked = true;
      searchField.value = "";
      renderList();
      const index = shownEntries.findIndex(entry => entry.kind === "local" && entry.route.file === saved.file);
      if (index >= 0) list.selectedIndex = index;
      updateActionStates();
      list.focus();
      announce(`Route « ${imported.name} » importée avec ${imported.points.length} point${imported.points.length > 1 ? "s" : ""} et enregistrée sur ce PC.`);
    } catch (error) { announce(`Import impossible : ${error.message}`, true); }
  }

  document.getElementById("route-import").addEventListener("click", () => importInput.click());
  importInput.addEventListener("change", async () => {
    const file = importInput.files[0];
    importInput.value = "";
    if (file) await importRouteFile(file);
    else announce("Import annulé.");
  });

  // ---------------------------------------------------------------------
  // Menu contextuel
  // ---------------------------------------------------------------------
  const contextMenu = document.getElementById("route-context-menu");

  /** Fermer le menu contextuel, en rendant éventuellement le focus à la liste. */
  function closeContextMenu(restoreFocus = false) {
    if (contextMenu.hidden) return;
    contextMenu.hidden = true;
    contextMenu.replaceChildren();
    if (restoreFocus) list.focus();
  }

  /** Créer un élément de menu qui ferme le menu puis exécute l'action. */
  function contextAction(label, handler) {
    const button = document.createElement("button");
    button.type = "button";
    button.role = "menuitem";
    button.textContent = label;
    button.addEventListener("click", () => {
      closeContextMenu(false);
      handler();
    });
    return button;
  }

  /**
   * Ouvrir le menu contextuel de la route sélectionnée.
   *
   * @param {number|null} x - Abscisse du clic droit, ou null pour un appel clavier.
   * @param {number|null} y - Ordonnée du clic droit, ou null pour un appel clavier.
   */
  function openContextMenu(x = null, y = null) {
    const entry = selectedEntry();
    if (!entry) { announce("Aucune route sélectionnée.", true); return; }
    contextMenu.replaceChildren();
    contextMenu.appendChild(contextAction(entry.kind === "community" ? "Consulter" : "Éditer", openSelected));
    contextMenu.appendChild(contextAction("Voir la carte", viewMapSelected));
    if (downloadAllowed(entry)) contextMenu.appendChild(contextAction("Télécharger", downloadSelected));
    if (entry.kind === "community") {
      contextMenu.appendChild(contextAction("Copier dans mes routes", duplicateSelected));
    } else {
      contextMenu.appendChild(contextAction("Renommer", renameSelected));
      contextMenu.appendChild(contextAction("Dupliquer", duplicateSelected));
    }
    contextMenu.appendChild(contextAction("Exporter…", exportSelected));
    if (entry.kind !== "community") contextMenu.appendChild(contextAction("Supprimer", deleteSelected));
    const rect = list.getBoundingClientRect();
    contextMenu.style.left = `${Math.max(8, x ?? rect.left + 24)}px`;
    contextMenu.style.top = `${Math.max(8, y ?? rect.top + 24)}px`;
    contextMenu.hidden = false;
    contextMenu.querySelector("button")?.focus();
    announce("Menu contextuel ouvert.");
  }

  contextMenu.addEventListener("keydown", event => {
    const items = [...contextMenu.querySelectorAll("button:not([disabled])")];
    const index = items.indexOf(document.activeElement);
    if (event.key === "Escape") {
      event.preventDefault();
      closeContextMenu(true);
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

  document.addEventListener("click", event => {
    if (!contextMenu.hidden && !contextMenu.contains(event.target)) closeContextMenu(false);
  });

  // ---------------------------------------------------------------------
  // Récupération des routes
  // ---------------------------------------------------------------------

  /**
   * Récupérer les routes personnelles et partagées du compte SARA.
   *
   * @param {boolean} verbose - Vrai pour annoncer le résultat de la synchronisation.
   */
  async function refreshRemoteRoutes(verbose = true) {
    if (verbose) announce("Récupération des routes SARA en cours…");
    try {
      const result = await requestJson("/api/routes/remote");
      routeCollections.mine = result.mine || [];
      routeCollections.community = result.community || [];
      renderList();
      if (verbose) announce(result.message + (result.warnings.length ? ` ${result.warnings.length} route(s) invalide(s) ignorée(s).` : ""), result.warnings.length > 0);
    } catch (error) { announce(error.message, true); }
  }

  /** Récupérer les routes enregistrées sur ce PC. */
  async function refreshLocalRoutes() {
    try {
      const result = await requestJson("/api/routes/local");
      routeCollections.local = result.routes || [];
      renderList();
    } catch (error) { announce(error.message, true); }
  }

  /** Afficher l'état du compte puis récupérer les routes SARA si connecté. */
  async function refreshAccountState() {
    try {
      const result = await requestJson("/api/status");
      const panel = document.getElementById("account-state");
      accountConnected = Boolean(result.connected);
      if (result.connected) {
        panel.className = "connection-panel connected";
        panel.textContent = `Connecté au compte SARA : ${result.email}.`;
        await refreshRemoteRoutes();
      } else {
        panel.className = "connection-panel disconnected";
        panel.innerHTML = 'Non connecté : seules les routes de ce PC sont affichées. <a href="/">Ouvrir la page Compte SARA</a>.';
      }
    } catch (error) { announce(error.message, true); }
  }

  // ---------------------------------------------------------------------
  // Liaison des commandes
  // ---------------------------------------------------------------------
  document.getElementById("route-open").addEventListener("click", openSelected);
  document.getElementById("route-view").addEventListener("click", viewMapSelected);
  document.getElementById("route-download").addEventListener("click", downloadSelected);
  document.getElementById("route-export").addEventListener("click", exportSelected);
  document.getElementById("route-delete").addEventListener("click", deleteSelected);
  // Un seul bouton : il actualise les routes de ce PC et, si le compte est connecté, celles de SARA.
  document.getElementById("route-refresh").addEventListener("click", async () => {
    await refreshLocalRoutes();
    if (accountConnected) await refreshRemoteRoutes(true);
    else announce(`${routeCollections.local.length} route(s) locale(s). Non connecté au compte SARA.`);
  });

  // Le filtre radio et la recherche réduisent la liste sans quitter leur champ.
  document.querySelectorAll('input[name="route-filter"]').forEach(radio => {
    radio.addEventListener("change", () => renderList());
  });
  searchField.addEventListener("input", () => renderList());

  list.addEventListener("change", updateActionStates);
  // Sans sélection par défaut au premier focus clavier, les flèches
  // haut/bas n'ont aucune position de départ tant qu'un clic souris n'a
  // pas explicitement choisi un premier élément.
  list.addEventListener("focus", () => {
    if (list.selectedIndex === -1 && list.options.length > 0) {
      list.selectedIndex = 0;
      updateActionStates();
    }
  });
  // Double-clic pour ouvrir directement la route sélectionnée.
  list.addEventListener("dblclick", openSelected);
  list.addEventListener("contextmenu", event => {
    event.preventDefault();
    openContextMenu(event.clientX, event.clientY);
  });
  list.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      openSelected();
    } else if (event.key === "F2") {
      event.preventDefault();
      renameSelected();
    } else if (event.key === "Delete") {
      event.preventDefault();
      deleteSelected();
    } else if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
      event.preventDefault();
      openContextMenu();
    } else if (event.key === "Escape") {
      closeContextMenu(true);
    }
  });

  // Lire le réglage de confirmation ; en cas d'échec, la confirmation reste demandée.
  fetch("/api/configuration").then(response => response.json()).then(data => {
    confirmOverwrite = data.configuration?.confirm_before_overwrite !== false;
  }).catch(() => {});

  refreshAccountState();
  refreshLocalRoutes();
  updateActionStates();
})();
