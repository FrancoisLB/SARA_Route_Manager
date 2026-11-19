"use strict";

/**
 * Module : keyboard_zones.js
 * Description : Navigation clavier F6 / Maj+F6 entre les zones principales
 * (éléments portant la classe « f6-zone ») d'une page. Chargé globalement
 * depuis base.html, ce script s'applique de façon identique à toutes les
 * pages de l'application, qu'elles définissent ou non des zones : si une
 * page n'a aucune zone « f6-zone », la touche F6 n'est simplement pas
 * interceptée et conserve son comportement natif du navigateur.
 * Fonctions présentes : announceZone.
 */

(function () {
  const __version__ = "0.9.4";
  const __date__ = "2026-11-19";

  /**
   * Annoncer le nom de la zone atteinte dans la zone de messages de la page.
   *
   * La zone de messages peut être un `<textarea readonly>` (pages Bibliothèque
   * et Éditeur, pour permettre la sélection et la copie) ou un `<div>` à
   * contenu texte (autres pages) : les deux cas sont pris en charge.
   *
   * Parameters
   * ----------
   * zone : Element
   *     Élément portant la classe « f6-zone » et l'attribut
   *     `data-zone-name` à annoncer.
   */
  function announceZone(zone) {
    const status = document.getElementById("status-message");
    if (!status || !zone.dataset.zoneName) return;
    const message = `Zone ${zone.dataset.zoneName}.`;
    if ("value" in status) {
      status.value = "";
      window.setTimeout(() => { status.value = message; }, 20);
    } else {
      status.textContent = "";
      window.setTimeout(() => { status.textContent = message; }, 20);
    }
  }

  document.addEventListener("keydown", event => {
    if (event.key !== "F6") return;
    const zones = [...document.querySelectorAll(".f6-zone")];
    if (!zones.length) return;
    event.preventDefault();
    const activeZone = document.activeElement.closest?.(".f6-zone") || null;
    const current = zones.indexOf(activeZone);
    const next = event.shiftKey
      ? (current <= 0 ? zones.length - 1 : current - 1)
      : (current + 1) % zones.length;
    (zones[next].querySelector("h2,h3,input,select,button,a") || zones[next]).focus();
    announceZone(zones[next]);
  });
})();
