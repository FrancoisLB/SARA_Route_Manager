"use strict";

// L'ensemble du fichier est isolé dans une fonction immédiatement
// invoquée (IIFE) : les scripts classiques chargés côté page partagent
// le même environnement global, et cette isolation évite toute collision
// de nom (par exemple __version__/__date__) avec file_dialogs.js ou avec
// un futur script chargé sur la même page.
(function () {
  /**
   * Module : account.js
   * Description : Page « Compte » — connexion, déconnexion et affichage de
   * l'état de synchronisation avec le compte SARA.
   * Fonctions présentes : announce, requestJson, postJson, renderStatus,
   * refreshStatus.
   */

  const __version__ = "0.9.4";
  const __date__ = "2026-11-19";

  const statusMessage = document.getElementById("status-message");
  const connectionPanel = document.getElementById("connection-panel");
  const accountStatusHeading = document.getElementById("account-status-heading");

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

  async function postJson(url, data) {
    return requestJson(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
  }

  function renderStatus(result) {
    const emailInput = document.getElementById("email");
    if (result.remembered_email && !emailInput.value) emailInput.value = result.remembered_email;
    if (result.connected) {
      accountStatusHeading.textContent = "Compte connecté";
      connectionPanel.className = "connection-panel connected";
      connectionPanel.innerHTML = `<strong>Connecté au compte SARA.</strong><br>Compte : ${result.email}<br>${result.credentials_saved ? "Les identifiants sont mémorisés sur ce PC." : "Les identifiants ne sont pas mémorisés."}`;
    } else {
      accountStatusHeading.textContent = "Compte non connecté";
      connectionPanel.className = "connection-panel disconnected";
      connectionPanel.innerHTML = `<strong>Non connecté au compte SARA.</strong><br>${result.credentials_saved ? "Des identifiants sont mémorisés. Utilisez le bouton Se connecter." : "Saisissez vos identifiants ci-dessous."}`;
    }
    if (result.automatic_login_message) announce(result.automatic_login_message, !result.connected);
  }

  async function refreshStatus() {
    try { renderStatus(await requestJson("/api/status")); }
    catch (error) { announce(error.message, true); }
  }

  document.getElementById("login-form").addEventListener("submit", async event => {
    event.preventDefault();
    announce("Connexion au compte SARA en cours…");
    try {
      const result = await postJson("/api/login", {
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
        remember: document.getElementById("remember").checked
      });
      // Le champ n’est volontairement pas effacé : l’état reste lisible comme dans la version 0.1.
      announce(result.message);
      await refreshStatus();
    } catch (error) { announce(error.message, true); }
  });

  document.getElementById("logout-button").addEventListener("click", async () => {
    try {
      const result = await postJson("/api/logout", {forget: false});
      announce(result.message);
      await refreshStatus();
    } catch (error) { announce(error.message, true); }
  });

  document.getElementById("forget-button").addEventListener("click", async () => {
    if (!window.confirm("Supprimer les identifiants SARA mémorisés sur ce PC ?")) return;
    try {
      const result = await postJson("/api/logout", {forget: true});
      document.getElementById("email").value = "";
      document.getElementById("password").value = "";
      announce(`${result.message} Les identifiants mémorisés ont été supprimés.`);
      await refreshStatus();
    } catch (error) { announce(error.message, true); }
  });

  refreshStatus();
})();
