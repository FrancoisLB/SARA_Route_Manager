"use strict";

// Isolé dans une IIFE : file_dialogs.js déclare déjà __version__ et __date__
// au niveau global, et un second script classique ne peut pas les redéclarer.
(function () {
  /**
   * Module : export_dialog.js
   * Description : Boîte de dialogue commune « Exporter la route » (0.8.0),
   * utilisée par la Bibliothèque et par l'éditeur pour que l'export se
   * présente partout de la même façon : un seul bouton « Exporter… », puis le
   * choix du format (JSON SARA, GPX ou CSV) en boutons radio.
   * Fonctions présentes : chooseExportFormat (exposée sur window).
   */

  const __version__ = "0.9.4";
  const __date__ = "2026-11-19";

  /**
   * Demander le format d'export à l'utilisateur.
   *
   * La page doit inclure le gabarit `_export_dialog.html`. Le focus se pose
   * sur le format coché, reste piégé dans la boîte tant qu'elle est ouverte
   * (Tab, Maj+Tab), Échap équivaut à « Annuler », et le focus est rendu à
   * l'élément d'origine à la fermeture.
   *
   * @param {HTMLElement} returnFocus - Élément qui reprend le focus à la fermeture.
   * Le format pré-coché est celui de la page Configuration (« Format d'export par défaut »).
   *
   * @returns {Promise<string|null>} « json », « gpx », « csv », ou null si annulé.
   */
  async function chooseExportFormat(returnFocus) {
    const dialog = document.getElementById("export-dialog");
    if (!dialog) return null;
    // Pré-cocher le format choisi dans Configuration (« Format d'export par
    // défaut ») ; en cas d'échec de lecture, le format coché par le gabarit reste.
    try {
      const response = await fetch("/api/configuration");
      const configuration = (await response.json()).configuration || {};
      const preferred = dialog.querySelector(`input[name="export-format"][value="${configuration.default_export_format}"]`);
      if (preferred) preferred.checked = true;
    } catch (_error) { /* on garde le format déjà coché */ }
    return new Promise(resolve => {
      const confirmButton = document.getElementById("export-confirm");
      const cancelButton = document.getElementById("export-cancel");

      // Fermer la boîte, retirer les écouteurs et transmettre le résultat.
      function finish(result) {
        dialog.hidden = true;
        dialog.removeEventListener("keydown", onKeydown);
        confirmButton.removeEventListener("click", onConfirm);
        cancelButton.removeEventListener("click", onCancel);
        if (returnFocus) returnFocus.focus();
        resolve(result);
      }
      function onConfirm() {
        finish(dialog.querySelector('input[name="export-format"]:checked').value);
      }
      function onCancel() { finish(null); }
      function onKeydown(event) {
        if (event.key === "Escape") {
          event.preventDefault();
          finish(null);
          return;
        }
        if (event.key !== "Tab") return;
        // Piège de focus : la tabulation boucle entre le premier et le dernier contrôle.
        const items = [...dialog.querySelectorAll("input, button")];
        const first = items[0];
        const last = items.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }

      dialog.addEventListener("keydown", onKeydown);
      confirmButton.addEventListener("click", onConfirm);
      cancelButton.addEventListener("click", onCancel);
      dialog.hidden = false;
      // Focus sur un contrôle actionnable, comme les autres boîtes de dialogue.
      dialog.querySelector('input[name="export-format"]:checked').focus();
    });
  }

  window.chooseExportFormat = chooseExportFormat;
})();
