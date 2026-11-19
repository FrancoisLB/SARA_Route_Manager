# SARA Route Manager — synthèse du projet
Document recréé le 2026-11-19, mis à jour après la publication de la version 0.9.4. Il remplace l'ancienne synthèse, qui n'était plus disponible.
## Objet
Outil Windows (Python, Flask, pywebview, HTML/CSS/JavaScript, Leaflet) pour créer, modifier, importer, exporter et partager des routes de navigation compatibles avec l'application iPhone **SARA Navigation**, destinée aux voiliers de personnes malvoyantes ou aveugles. L'outil est entièrement utilisable avec NVDA et respecte les WCAG.
## Fonctions principales
- Bibliothèque : une liste unique (Sur ce PC, Mes routes (en partage), Autres routes (en partage)), filtre à boutons radio, recherche, Éditer (Consulter pour la route d'un autre utilisateur), Voir la carte, Télécharger, Exporter…, Importer une route…, Supprimer.
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
- 0.9.3 : boutons « Éditer » et « Voir la carte » (carte directe depuis la Bibliothèque).
- 0.9.4 : rechargement unique de la première page pour que NVDA expose ses repères au démarrage.
## Validation de bout en bout (2026-11-19)
Parcours validé en conditions réelles, avec la version 0.9.1 :
1. import d'une route JSON depuis un dossier du PC (chenal de la passe de l'ouest, rade de Lorient) ;
2. dépôt en ligne depuis SARA Route Manager ;
3. récupération de la route par une autre utilisatrice dans SARA Navigation sur sa tablette ;
4. affichage de la liste des points de la route, puis visualisation sur la carte de SARA Navigation, sans plantage.
Ce test confirme la correction Float32 de la 0.8.3 sur un second appareil.
## Validation de la 0.9.4 (2026-11-19)
Les repères NVDA (bannière, navigation, principal, pied de page) n'apparaissaient pas dans NVDA+F7 sur la page de départ tant qu'on ne cliquait pas sur la navigation. Avec le rechargement unique de la première page, introduit en 0.9.4, l'utilisateur a confirmé que cela fonctionne : « ça marche ».
## Publication (2026-11-19)
- Dépôt : `FrancoisLB/SARA_Route_Manager`. La branche `version-0.9.4` a été fusionnée dans `main` (commit de fusion `ec5e931`).
- Étiquette `v0.9.4` et release GitHub « SARA Route Manager 0.9.4 », avec l'archive `SARA_Route_Manager_v0.9.4.zip` jointe. La version publiée auparavant était la 0.7.2.0.
- Alerte « secret scanning » n° 1 (clé Web Firebase) : fermée comme faux positif, avec un commentaire expliquant qu'il s'agit d'une clé Web publique.
## Points ouverts
- Aucun point bloquant. Le suivi d'un bug signalé par Laurent est abandonné, la validation de bout en bout ayant été faite.
- Les boutons « Éditer » et « Voir la carte » (0.9.3) sont inclus dans la version publiée ; leur essai sur PC n'a pas fait l'objet d'une validation formelle.
- Un vrai mode lecture seule pour « Consulter » n'existe pas : l'éditeur s'ouvre normalement.
- Branche `version-0.9.4` supprimée.