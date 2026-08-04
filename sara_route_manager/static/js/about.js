"use strict";

// L'ensemble du fichier est isolé dans une fonction immédiatement
// invoquée (IIFE) : les scripts classiques chargés côté page partagent
// le même environnement global, et cette isolation évite toute collision
// de nom (par exemple __version__/__date__) avec file_dialogs.js ou avec
// un futur script chargé sur la même page.
(function () {
  /**
   * Module : about.js
   * Description : Assistance technique et ouverture de la documentation depuis
   * la page « À propos » (copie des informations techniques, ouverture du
   * guide utilisateur, des raccourcis clavier et du journal des versions).
   * Fonctions présentes : announce, requestJson, formatInformation, openDocument.
   */

  const __version__ = "0.7.2.0";
  const __date__ = "2026-08-04";

  const statusMessage = document.getElementById("status-message");

  function announce(message, isError = false) {
    statusMessage.textContent = "";
    statusMessage.classList.toggle("error", isError);
    setTimeout(() => { statusMessage.textContent = message; }, 20);
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok || result.ok === false) {
      throw new Error(result.message || "Erreur inconnue.");
    }
    return result;
  }

  function formatInformation(information) {
    return [
      information.application,
      `Version : ${information.version}`,
      `Python : ${information.python}`,
      `Système : ${information.operating_system}`,
      `Flask : ${information.flask}`,
      `pywebview : ${information.pywebview}`,
      `Moteur WebView : ${information.webview_engine}`,
      `Répertoire des routes : ${information.routes_directory}`,
      `Répertoire de configuration : ${information.configuration_directory}`,
      `Fichier de configuration : ${information.configuration_file}`,
      `Répertoire des journaux : ${information.logs_directory}`,
      `Fichier journal : ${information.log_file}`
    ].join("\n");
  }

  /**
   * Construire le texte « Libellé : valeur » de la liste Informations
   * générales, à partir des paires `dt`/`dd` du DOM plutôt que d'une copie
   * codée en dur, pour rester fidèle à ce que la page affiche réellement.
   */
  function formatGeneralInformation() {
    const list = document.getElementById("about-general-list");
    const terms = [...list.querySelectorAll("dt")];
    const definitions = [...list.querySelectorAll("dd")];
    return terms.map((term, index) => `${term.textContent} : ${definitions[index].textContent}`).join("\n");
  }

  document.getElementById("copy-general-information").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(formatGeneralInformation());
      announce("Informations générales copiées dans le presse-papiers.");
    } catch (error) {
      announce(`Copie impossible : ${error.message}`, true);
    }
  });

  document.getElementById("copy-information").addEventListener("click", async () => {
    try {
      const result = await requestJson("/api/technical-information");
      await navigator.clipboard.writeText(formatInformation(result.information));
      announce("Informations techniques copiées dans le presse-papiers.");
    } catch (error) {
      announce(`Copie impossible : ${error.message}`, true);
    }
  });

  document.getElementById("open-log-file").addEventListener("click", async () => {
    try {
      const result = await requestJson("/api/open-path", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({target: "log_file"})
      });
      announce(result.message);
    } catch (error) {
      announce(error.message, true);
    }
  });

  async function openDocument(target, successMessage) {
    try {
      const result = await requestJson("/api/open-path", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({target})
      });
      announce(successMessage || result.message);
    } catch (error) {
      announce(error.message, true);
    }
  }

  document.getElementById("open-user-guide").addEventListener("click", () => {
    openDocument("user_guide", "Ouverture du guide utilisateur.");
  });

  document.getElementById("open-keyboard-shortcuts").addEventListener("click", () => {
    openDocument("keyboard_shortcuts", "Ouverture des raccourcis clavier.");
  });

  document.getElementById("open-release-notes").addEventListener("click", () => {
    openDocument("change_log", "Ouverture du journal des versions.");
  });

  document.getElementById("open-orion-brest-website").addEventListener("click", () => {
    openDocument("orion_brest_website", "Ouverture du site d’Orion Brest dans le navigateur.");
  });

  document.getElementById("open-gpl-license-text").addEventListener("click", () => {
    openDocument("gpl_license_url", "Ouverture du texte légal de la GPL-3.0 dans le navigateur.");
  });

  document.getElementById("open-cc-by-sa-license-text").addEventListener("click", () => {
    openDocument("cc_by_sa_license_url", "Ouverture du texte légal de la CC BY-SA 4.0 dans le navigateur.");
  });
})();
