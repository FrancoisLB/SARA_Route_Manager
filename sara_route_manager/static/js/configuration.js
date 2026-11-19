"use strict";

// L'ensemble du fichier est isolé dans une fonction immédiatement
// invoquée (IIFE) : les scripts classiques chargés côté page partagent
// le même environnement global, et cette isolation évite toute collision
// de nom (par exemple __version__/__date__) avec file_dialogs.js ou avec
// un futur script chargé sur la même page.
(function () {
  /**
   * Module : configuration.js
   * Description : Page « Configuration » — lecture, modification et remise à
   * zéro des préférences de l'application (répertoire des routes, compte,
   * formats d'import/export, unité SHOM par défaut).
   * Fonctions présentes : announce, requestJson, fillForm, loadConfiguration,
   * openTarget.
   */

  const __version__ = "0.9.4";
  const __date__ = "2026-11-19";

  const statusMessage = document.getElementById("status-message");

  function announce(message, isError = false) {
    statusMessage.textContent = "";
    statusMessage.classList.toggle("error", isError);
    window.setTimeout(() => { statusMessage.textContent = message; }, 20);
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok || result.ok === false) {
      throw new Error(result.message || "Erreur inconnue.");
    }
    return result;
  }

  function fillForm(configuration) {
    document.getElementById("routes-directory").value = configuration.routes_directory;
    document.getElementById("automatic-connection").checked = configuration.automatic_connection;
    document.getElementById("remember-email").checked = configuration.remember_email;
    document.getElementById("default-export-format").value = configuration.default_export_format;
    document.getElementById("csv-separator").value = configuration.csv_separator;
    document.getElementById("confirm-before-overwrite").checked = configuration.confirm_before_overwrite;
    document.getElementById("shom-radius-unit").value = configuration.shom_radius_unit;
    document.getElementById("map-window-width-percent").value = configuration.map_window_width_percent;
    document.getElementById("map-window-height-percent").value = configuration.map_window_height_percent;
    document.getElementById("main-window-width-percent").value = configuration.main_window_width_percent;
    document.getElementById("main-window-height-percent").value = configuration.main_window_height_percent;
    document.getElementById("map-sea-color").value = configuration.map_sea_color;
    document.getElementById("map-land-color").value = configuration.map_land_color;
    document.getElementById("map-route-color").value = configuration.map_route_color;
    document.getElementById("map-route-line-width").value = configuration.map_route_line_width;
    document.getElementById("map-route-line-style").value = configuration.map_route_line_style;
    document.getElementById("map-route-labels-visible").checked = configuration.map_route_labels_visible;
    document.getElementById("map-route-label-font-size").value = configuration.map_route_label_font_size;
    document.getElementById("map-route-label-bordered").checked = configuration.map_route_label_bordered;
    document.getElementById("map-marker-size").value = configuration.map_marker_size;
    document.getElementById("config-file-path").textContent = `Fichier actuel : ${configuration.config_file}`;
  }

  async function loadConfiguration() {
    try {
      const result = await requestJson("/api/configuration");
      fillForm(result.configuration);
      announce("Configuration chargée.");
    } catch (error) {
      announce(error.message, true);
    }
  }

  async function openTarget(target) {
    try {
      const result = await requestJson("/api/open-path", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({target})
      });
      announce(result.message);
    } catch (error) {
      announce(error.message, true);
    }
  }

  document.getElementById("configuration-form").addEventListener("submit", async event => {
    event.preventDefault();
    const data = {
      routes_directory: document.getElementById("routes-directory").value,
      automatic_connection: document.getElementById("automatic-connection").checked,
      remember_email: document.getElementById("remember-email").checked,
      default_export_format: document.getElementById("default-export-format").value,
      csv_separator: document.getElementById("csv-separator").value,
      confirm_before_overwrite: document.getElementById("confirm-before-overwrite").checked,
      shom_radius_unit: document.getElementById("shom-radius-unit").value,
      map_window_width_percent: document.getElementById("map-window-width-percent").value,
      map_window_height_percent: document.getElementById("map-window-height-percent").value,
      main_window_width_percent: document.getElementById("main-window-width-percent").value,
      main_window_height_percent: document.getElementById("main-window-height-percent").value,
      map_sea_color: document.getElementById("map-sea-color").value,
      map_land_color: document.getElementById("map-land-color").value,
      map_route_color: document.getElementById("map-route-color").value,
      map_route_line_width: document.getElementById("map-route-line-width").value,
      map_route_line_style: document.getElementById("map-route-line-style").value,
      map_route_labels_visible: document.getElementById("map-route-labels-visible").checked,
      map_route_label_font_size: document.getElementById("map-route-label-font-size").value,
      map_route_label_bordered: document.getElementById("map-route-label-bordered").checked,
      map_marker_size: document.getElementById("map-marker-size").value
    };

    try {
      const result = await requestJson("/api/configuration", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
      });
      fillForm(result.configuration);
      announce(result.message);
    } catch (error) {
      announce(error.message, true);
    }
  });

  document.getElementById("reset-configuration").addEventListener("click", async () => {
    if (!window.confirm("Rétablir tous les paramètres par défaut ?")) return;
    try {
      const result = await requestJson("/api/configuration/reset", {method: "POST"});
      fillForm(result.configuration);
      announce(result.message);
    } catch (error) {
      announce(error.message, true);
    }
  });

  document.getElementById("open-routes-directory").addEventListener("click", () => openTarget("routes"));
  document.getElementById("open-config-file").addEventListener("click", () => openTarget("config_file"));
  document.getElementById("open-config-directory").addEventListener("click", () => openTarget("config_directory"));

  /**
   * Exporter le fichier de configuration actuel via le dialogue natif d'enregistrement.
   *
   * Dossier initial proposé : « sauvegardes » (`backups`), un export de
   * configuration étant sémantiquement une sauvegarde des réglages —
   * distinct du dossier « routes », utilisé par tous les autres exports.
   */
  document.getElementById("export-configuration").addEventListener("click", async () => {
    try {
      const response = await fetch("/api/configuration/export");
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || "Export impossible.");
      }
      const blob = await response.blob();
      const result = await saveBlobWithDialog(blob, "config.toml", exportFileTypes("toml"), "backups");
      if (result.cancelled) {
        announce("Export annulé.");
        return;
      }
      if (!result.saved) throw new Error(result.message || "Le fichier n’a pas pu être enregistré.");
      announce(`Configuration exportée. Fichier : ${result.path}`);
    } catch (error) {
      announce(`Export impossible : ${error.message}`, true);
    }
  });

  /**
   * Importer un fichier de configuration TOML, en remplaçant les réglages actuels.
   *
   * Une confirmation est demandée avant d'écraser la configuration en
   * cours, sur le même modèle que le bouton « Rétablir la configuration
   * par défaut » déjà présent.
   */
  // Même présentation que l'import de route de la Bibliothèque : un seul
  // bouton « Importer… » qui ouvre directement le choix du fichier.
  document.getElementById("import-configuration-button").addEventListener("click", () => {
    document.getElementById("import-configuration-file").click();
  });
  document.getElementById("import-configuration-file").addEventListener("change", async () => {
    const fileInput = document.getElementById("import-configuration-file");
    const file = fileInput.files[0];
    if (!file) return announce("Import annulé.");
    if (!window.confirm("Remplacer la configuration actuelle par celle du fichier sélectionné ?")) {
      fileInput.value = "";
      return announce("Import annulé : la configuration actuelle est conservée.");
    }
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await requestJson("/api/configuration/import", {method: "POST", body: formData});
      fillForm(result.configuration);
      fileInput.value = "";
      announce(result.message);
    } catch (error) {
      announce(error.message, true);
    }
  });

  document.getElementById("choose-routes-directory").addEventListener("click", async () => {
    try {
      if (window.pywebview?.api) {
        const selected = await window.pywebview.api.choose_routes_directory();
        if (selected) {
          document.getElementById("routes-directory").value = selected;
          announce(`Répertoire sélectionné : ${selected}`);
        }
        return;
      }
      announce("En mode navigateur, saisissez ou collez le chemin complet du répertoire.", true);
    } catch (error) {
      announce(`Sélection impossible : ${error}`, true);
    }
  });

  loadConfiguration();
})();
