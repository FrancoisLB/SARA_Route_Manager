# Ressources tierces intégrées

Ce fichier recense les ressources externes intégrées à SARA Route Manager, avec leur licence d'origine et la citation ou attribution exigée.

## Leaflet.js

- **Usage** : moteur de rendu de la fenêtre de visualisation cartographique (`static/vendor/leaflet/`), à partir de la version 0.7.0.
- **Version** : 1.9.4.
- **Licence** : BSD 2-Clause. Texte complet conservé dans `static/vendor/leaflet/LEAFLET_LICENSE.txt`.
- **Provenance** : paquet officiel `leaflet` sur npm (https://www.npmjs.com/package/leaflet).
- **Intégration** : fichiers copiés localement (JS, CSS, images), pas chargés depuis un CDN — cohérent avec le principe de l'application de ne dépendre d'aucun serveur externe en continu.

## Données et icônes du SHOM

Ressources intégrées pour la fenêtre de visualisation cartographique (voir `SPECIFICATIONS.md`, section « Fenêtre de visualisation cartographique ») :

- **Balisage maritime (icônes IALA et données)** : Licence Ouverte 2.0 (Etalab). Citation exigée : *« Shom, 2023. Balisage maritime »*. Icônes intégrées dans `static/vendor/shom_icons/` (53 fichiers SVG, certains adaptés de la bibliothèque ouverte OpenSeaMap par le SHOM lui-même).
- **Limite terre-mer** (trait de côte, métropole) : Licence Ouverte 2.0 (Etalab). Citation exigée : *« Shom-IGN, 2021. https://dx.doi.org/10.17183/LIMTM »*.
- **Trait de Côte HISTOLITT®** (trait de côte, outre-mer) : Licence Ouverte 2.0 (Etalab). Citation exigée : *« © IGN-Shom 2009 »*, **avec logos IGN et SHOM obligatoires** (liens vers www.ign.fr et www.shom.fr) dès lors que la donnée est représentée sur une interface.
