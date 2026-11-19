"use strict";

/**
 * Module : file_dialogs.js
 * Description : Enregistrement de fichiers via le dialogue natif Windows
 * « Enregistrer sous » en mode pywebview, avec repli sur le téléchargement
 * standard du navigateur en mode diagnostic.
 * Fonctions présentes : blobToBase64, saveBlobWithDialog, exportFileTypes.
 */

const __version__ = "0.9.4";
const __date__ = "2026-11-19";

/**
 * Convertir un Blob en Base64 sans préfixe data-URL.
 *
 * @param {Blob} blob - Contenu binaire à transmettre à l'API de bureau.
 * @returns {Promise<string>} Contenu encodé en Base64.
 */
async function blobToBase64(blob) {
  const buffer = await blob.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  let binary = "";

  // Construire la chaîne par blocs pour éviter de dépasser la taille maximale
  // d'arguments de String.fromCharCode sur les fichiers un peu volumineux.
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return window.btoa(binary);
}

/**
 * Enregistrer un Blob avec le dialogue natif commun de l'application.
 *
 * En mode pywebview, l'utilisateur choisit le dossier et le nom du fichier.
 * En mode navigateur de diagnostic, le téléchargement standard du navigateur
 * est conservé comme solution de repli.
 *
 * @param {Blob} blob - Contenu à enregistrer.
 * @param {string} suggestedFilename - Nom de fichier proposé.
 * @param {Array<string>} fileTypes - Filtres du dialogue natif.
 * @param {string} directoryKind - Dossier initial proposé (« routes » par défaut, ou « backups »).
 * @returns {Promise<object>} Résultat contenant saved, cancelled, path et native.
 */
async function saveBlobWithDialog(blob, suggestedFilename, fileTypes = [], directoryKind = "routes") {
  const desktopApi = window.pywebview?.api;

  if (desktopApi?.save_file) {
    const base64Content = await blobToBase64(blob);
    return desktopApi.save_file(suggestedFilename, base64Content, fileTypes, directoryKind);
  }

  // Le mode navigateur ne connaît pas le chemin choisi par le navigateur.
  const link = document.createElement("a");
  const objectUrl = URL.createObjectURL(blob);
  link.href = objectUrl;
  link.download = suggestedFilename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
  return {
    saved: true,
    cancelled: false,
    path: "emplacement choisi par le navigateur",
    native: false
  };
}

/** Déduire les filtres de dialogue à partir d'un format d'export. */
function exportFileTypes(formatName) {
  const types = {
    csv: ["Fichiers CSV (*.csv)", "Tous les fichiers (*.*)"],
    gpx: ["Fichiers GPX (*.gpx)", "Tous les fichiers (*.*)"],
    json: ["Fichiers JSON (*.json)", "Tous les fichiers (*.*)"],
    svg: ["Fichiers SVG (*.svg)", "Tous les fichiers (*.*)"],
    toml: ["Fichiers TOML (*.toml)", "Tous les fichiers (*.*)"]
  };
  return types[String(formatName).toLowerCase()] || ["Tous les fichiers (*.*)"];
}
