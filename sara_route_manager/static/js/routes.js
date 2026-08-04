"use strict";

// L'ensemble du fichier est isolé dans une fonction immédiatement
// invoquée (IIFE) : les scripts classiques chargés côté page partagent
// le même environnement global, et cette isolation évite toute collision
// de nom (par exemple __version__/__date__) avec file_dialogs.js ou avec
// un futur script chargé sur la même page.
(function () {
  /**
   * Module : routes.js
   * Description : Page « Bibliothèque » — consultation des routes
   * personnelles, partagées et locales, avec leurs actions (modifier,
   * dupliquer, copier, exporter, supprimer) et transmission de la route
   * choisie vers l'éditeur via sessionStorage.
   * Fonctions présentes : announce, requestJson, formatDate, routeLabel,
   * renderList, selectedRoute, openEditor, loadLocalRoute, exportRoute,
   * updateActionStates, listKindFromId, focusSelectedOption,
   * renameSelectedRoute, deleteSelectedPersonalRoute.
   */

  const __version__ = "0.7.2.0";
  const __date__ = "2026-08-04";

  const statusMessage = document.getElementById("status-message");
  const routeCollections = {mine: [], community: [], local: []};

  function announce(message, isError = false) {
    statusMessage.textContent = "";
    statusMessage.classList.toggle("error", isError);
    window.setTimeout(() => { statusMessage.textContent = message; }, 20);
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.message || "Erreur inconnue.");
    return result;
  }

  function formatDate(value) {
    if (!value) return "date non indiquée";
    const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})_(\d{2}):(\d{2}):(\d{2})$/);
    return match ? `${match[3]}/${match[2]}/${match[1]} à ${match[4]}:${match[5]}` : String(value);
  }

  function routeLabel(route) {
    const count = Number(route.points_count ?? (route.points || []).length ?? 0);
    const countText = `${count} point${count > 1 ? "s" : ""}`;
    const dateText = route.last_update_time ? ` — modifiée le ${formatDate(route.last_update_time)}` : "";
    return `${route.name} — ${countText}${dateText}`;
  }

  function renderList(id, routes) {
    const list = document.getElementById(id);
    list.replaceChildren();
    routes.forEach((route, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = routeLabel(route);
      list.appendChild(option);
    });
    if (routes.length > 0) list.selectedIndex = 0;
    updateActionStates();
  }

  function selectedRoute(kind) {
    const list = document.getElementById(`${kind === "mine" ? "my" : kind}-routes-list`);
    const index = Number(list.value);
    return Number.isInteger(index) && index >= 0 ? routeCollections[kind][index] : null;
  }

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

  async function loadLocalRoute(route) {
    return (await requestJson(`/api/routes/local/${encodeURIComponent(route.file)}`)).route;
  }

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

  function updateActionStates() {
    const groups = [
      ["mine", ["my-open", "my-duplicate", "my-export-gpx", "my-export-csv", "my-export-json", "my-delete"]],
      ["community", ["community-open", "community-copy", "community-export-gpx", "community-export-csv", "community-export-json"]],
      ["local", ["local-open", "local-export-gpx", "local-export-csv", "local-export-json"]]
    ];
    groups.forEach(([kind, ids]) => {
      const disabled = !selectedRoute(kind);
      ids.forEach(id => { document.getElementById(id).disabled = disabled; });
    });
  }


  function listKindFromId(id) {
    if (id === "my-routes-list") return "mine";
    if (id === "community-routes-list") return "community";
    return "local";
  }

  function focusSelectedOption(list) {
    if (list.options.length > 0 && list.selectedIndex < 0) list.selectedIndex = 0;
    list.focus();
    updateActionStates();
  }

  function renameSelectedRoute(kind) {
    const route = selectedRoute(kind);
    if (!route) return;
    if (kind === "community") {
      announce("Une route partagée doit d’abord être copiée avant d’être renommée.", true);
      return;
    }
    sessionStorage.setItem("sara_editor_focus_name", "1");
    if (kind === "local") {
      loadLocalRoute(route).then(loaded => openEditor(loaded)).catch(error => announce(error.message, true));
    } else {
      openEditor({...route, own: true});
    }
  }

  async function deleteSelectedPersonalRoute() {
    const route = selectedRoute("mine");
    if (!route) return;
    const remoteKey = route.remote_key || route.id || route.key;
    if (!remoteKey) {
      announce("La référence distante de cette route est absente.", true);
      return;
    }
    if (!window.confirm(`Supprimer définitivement la route « ${route.name} » de votre compte SARA ?`)) {
      announce("Suppression annulée.");
      document.getElementById("my-routes-list").focus();
      return;
    }
    try {
      const result = await requestJson("/api/routes/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({remote_key: remoteKey})
      });
      const list = document.getElementById("my-routes-list");
      const oldIndex = list.selectedIndex;
      announce(result.message);
      await refreshRemoteRoutes();
      list.selectedIndex = Math.min(oldIndex, Math.max(0, list.options.length - 1));
      focusSelectedOption(list);
    } catch (error) {
      announce(error.message, true);
      document.getElementById("my-routes-list").focus();
    }
  }

  const contextMenu = document.getElementById("route-context-menu");
  let contextSourceList = null;

  function closeContextMenu(restoreFocus = false) {
    if (contextMenu.hidden) return;
    contextMenu.hidden = true;
    contextMenu.replaceChildren();
    if (restoreFocus && contextSourceList) contextSourceList.focus();
  }

  function contextAction(label, handler, disabled = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.role = "menuitem";
    button.textContent = label;
    button.disabled = disabled;
    button.addEventListener("click", () => {
      closeContextMenu(false);
      handler();
    });
    return button;
  }

  function openContextMenu(list, x = null, y = null) {
    const kind = listKindFromId(list.id);
    const route = selectedRoute(kind);
    if (!route) {
      announce("Aucune route sélectionnée.", true);
      return;
    }
    contextSourceList = list;
    contextMenu.replaceChildren();
    const prefix = kind === "mine" ? "my" : kind;
    const openButtonId = `${prefix}-open`;
    contextMenu.appendChild(contextAction(kind === "community" ? "Consulter" : "Ouvrir", () => document.getElementById(openButtonId).click()));
    if (kind === "mine") {
      contextMenu.appendChild(contextAction("Renommer", () => renameSelectedRoute(kind)));
      contextMenu.appendChild(contextAction("Dupliquer", () => document.getElementById("my-duplicate").click()));
    } else if (kind === "community") {
      contextMenu.appendChild(contextAction("Copier dans mes routes", () => document.getElementById("community-copy").click()));
    } else {
      contextMenu.appendChild(contextAction("Renommer dans l’éditeur", () => renameSelectedRoute(kind)));
    }
    ["gpx", "csv", "json"].forEach(formatName => {
      contextMenu.appendChild(contextAction(`Exporter ${formatName.toUpperCase()}`, () => document.getElementById(`${prefix}-export-${formatName}`).click()));
    });
    if (kind === "mine") {
      contextMenu.appendChild(contextAction("Supprimer", deleteSelectedPersonalRoute));
    }
    const rect = list.getBoundingClientRect();
    contextMenu.style.left = `${Math.max(8, x ?? rect.left + 24)}px`;
    contextMenu.style.top = `${Math.max(8, y ?? rect.top + 24)}px`;
    contextMenu.hidden = false;
    const first = contextMenu.querySelector("button:not([disabled])");
    first?.focus();
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

  async function refreshRemoteRoutes() {
    announce("Récupération des routes SARA en cours…");
    try {
      const result = await requestJson("/api/routes/remote");
      routeCollections.mine = result.mine || [];
      routeCollections.community = result.community || [];
      renderList("my-routes-list", routeCollections.mine);
      renderList("community-routes-list", routeCollections.community);
      document.getElementById("my-routes-summary").textContent = `${routeCollections.mine.length} route(s) personnelle(s).`;
      document.getElementById("community-routes-summary").textContent = `${routeCollections.community.length} route(s) partagée(s).`;
      announce(result.message + (result.warnings.length ? ` ${result.warnings.length} route(s) invalide(s) ignorée(s).` : ""), result.warnings.length > 0);
    } catch (error) { announce(error.message, true); }
  }

  async function refreshLocalRoutes() {
    try {
      const result = await requestJson("/api/routes/local");
      routeCollections.local = result.routes || [];
      renderList("local-routes-list", routeCollections.local);
      document.getElementById("local-routes-summary").textContent = `${routeCollections.local.length} route(s) locale(s).`;
    } catch (error) { announce(error.message, true); }
  }

  async function refreshAccountState() {
    try {
      const result = await requestJson("/api/status");
      const panel = document.getElementById("account-state");
      if (result.connected) {
        panel.className = "connection-panel connected";
        panel.textContent = `Connecté au compte SARA : ${result.email}.`;
        await refreshRemoteRoutes();
      } else {
        panel.className = "connection-panel disconnected";
        panel.innerHTML = 'Non connecté. <a href="/">Ouvrir la page Compte SARA</a>.';
        announce("Vous devez vous connecter pour récupérer les routes SARA.", true);
      }
    } catch (error) { announce(error.message, true); }
  }

  function bind(id, handler) {
    document.getElementById(id).addEventListener("click", handler);
  }

  bind("my-open", () => { const route = selectedRoute("mine"); if (route) openEditor({...route, own: true}); });
  bind("my-duplicate", () => { const route = selectedRoute("mine"); if (route) openEditor({...route, own: true}, true); });
  bind("community-open", () => { const route = selectedRoute("community"); if (route) openEditor({...route, own: false}); });
  bind("community-copy", () => { const route = selectedRoute("community"); if (route) openEditor({...route, own: false}, true); });
  bind("local-open", async () => { const route = selectedRoute("local"); if (route) openEditor(await loadLocalRoute(route)); });
  bind("my-delete", deleteSelectedPersonalRoute);

  [["mine", "my"], ["community", "community"]].forEach(([kind, prefix]) => {
    ["gpx", "csv", "json"].forEach(formatName => bind(`${prefix}-export-${formatName}`, () => {
      const route = selectedRoute(kind); if (route) exportRoute(route, formatName);
    }));
  });
  ["gpx", "csv", "json"].forEach(formatName => bind(`local-export-${formatName}`, async () => {
    const route = selectedRoute("local"); if (route) exportRoute(await loadLocalRoute(route), formatName);
  }));

  /**
   * Retrouver l'identifiant du bouton « Ouvrir » associé à une liste de routes.
   *
   * @param {str} listId - Identifiant de la liste (`my-routes-list`, etc.).
   * @returns {str} Identifiant du bouton d'ouverture correspondant.
   */
  function openButtonIdFor(listId) {
    if (listId === "my-routes-list") return "my-open";
    if (listId === "community-routes-list") return "community-open";
    return "local-open";
  }

  ["my-routes-list", "community-routes-list", "local-routes-list"].forEach(id => {
    const list = document.getElementById(id);
    list.addEventListener("change", updateActionStates);
    // Sans sélection par défaut au premier focus clavier, les flèches
    // haut/bas n'ont aucune position de départ tant qu'un clic souris n'a
    // pas explicitement choisi un premier élément — repéré après
    // signalement, corrigé ici et dans l'éditeur (points disponibles/route).
    list.addEventListener("focus", () => {
      if (list.selectedIndex === -1 && list.options.length > 0) {
        list.selectedIndex = 0;
        updateActionStates();
      }
    });
    // Double-clic pour ouvrir directement la route sélectionnée, en plus
    // du raccourci clavier Entrée déjà en place ci-dessous.
    list.addEventListener("dblclick", () => {
      document.getElementById(openButtonIdFor(id)).click();
    });
    list.addEventListener("contextmenu", event => {
      event.preventDefault();
      openContextMenu(list, event.clientX, event.clientY);
    });
    list.addEventListener("keydown", event => {
      const kind = listKindFromId(id);
      if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById(openButtonIdFor(id)).click();
      } else if (event.key === "F2") {
        event.preventDefault();
        renameSelectedRoute(kind);
      } else if (event.key === "Delete") {
        event.preventDefault();
        if (kind === "mine") deleteSelectedPersonalRoute();
        else announce("La suppression n’est pas autorisée dans cette liste.", true);
      } else if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
        event.preventDefault();
        openContextMenu(list);
      } else if (event.key === "Escape") {
        closeContextMenu(true);
      }
    });
  });

  bind("refresh-remote-button", refreshRemoteRoutes);
  bind("refresh-local-button", refreshLocalRoutes);
  refreshAccountState();
  refreshLocalRoutes();
  updateActionStates();
})();
