# SARA Route Manager — synthèse du projet

Document recréé le 2026-11-19 (version 0.9.4). Il remplace l'ancienne synthèse, qui n'était plus disponible.

## Objet

Outil Windows (Python, Flask, pywebview, HTML/CSS/JavaScript, Leaflet) pour créer, modifier, importer, exporter et partager des routes de navigation compatibles avec l'application iPhone **SARA Navigation**, destinée aux voiliers de personnes malvoyantes ou aveugles. L'outil est entièrement utilisable avec NVDA et respecte les WCAG.

## Fonctions principales

- Bibliothèque : une liste unique (Sur ce PC, Mes routes (en partage), Autres routes (en partage)), filtre à boutons radio, recherche, Ouvrir/Consulter, Visualiser, Télécharger, Exporter…, Importer une route…, Supprimer.
- Éditeur : composition de la route à partir des marques SHOM, d'un fichier ou de la saisie manuelle ; analyse de la route ; carte ; Enregistrer sur le PC, Déposer en ligne, Exporter… (JSON SARA, GPX, CSV).
- Partage : la mise en ligne dans Firebase vaut partage avec tous les utilisateurs de SARA Navigation ; une route de même nom ne peut être écrasée que par son propriétaire.
- Vocabulaire des actions repris de SARA Navigation. SARA Régate n'est pas prise en charge.

## Historique récent

- 0.8.0 : Bibliothèque simplifiée (liste unique, filtre radio, export avec choix du format, import d'une route complète).
- 0.8.1 à 0.8.2 : homogénéisation des onglets, écrasement et propriété des routes en ligne.
- 0.8.3 : correction du plantage de SARA Navigation à la visualisation d'une route déposée depuis le PC (coordonnées arrondies en Float32 au dépôt uniquement).
- 0.9.0 : noms des actions alignés sur SARA Navigation, bouton Télécharger.
- 0.9.1 : libellés « (en partage) » pour les routes en ligne.
- 0.9.2 : actions et menus adaptés à l'origine de la route.
- 0.9.4 : rechargement unique de la première page pour que NVDA expose ses repères au démarrage.
- 0.9.3 : boutons « Éditer » et « Voir la carte » (carte directe depuis la Bibliothèque).

## Validation de bout en bout (2026-11-19)

Parcours validé en conditions réelles, avec la version 0.9.1 :

1. import d'une route JSON depuis un dossier du PC (chenal de la passe de l'ouest, rade de Lorient) ;
2. dépôt en ligne depuis SARA Route Manager ;
3. récupération de la route par une autre utilisatrice dans SARA Navigation sur sa tablette ;
4. affichage de la liste des points de la route, puis visualisation sur la carte de SARA Navigation, sans plantage.

Ce test confirme la correction Float32 de la 0.8.3 sur un second appareil.

## Points ouverts

- Aucun point bloquant. Le suivi d'un bug signalé par Laurent est abandonné, la validation de bout en bout ayant été faite.
- Alerte GitHub « secret scanning » sur la clé Web Firebase : faux positif à commenter (voir le commentaire dans `firebase_client.py`).
- La 0.9.4 n'a pas encore été essayée sur le PC (tests automatiques seulement).
