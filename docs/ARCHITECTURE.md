# Architecture

**Rôle :** référence technique concise du projet.

## Accessibilité — implémentation

Conçu pour Windows 11 avec le lecteur d’écran NVDA. L’accès au clavier ne constitue pas une solution de remplacement : il fait partie du fonctionnement normal de l’application. Pour l’usage pratique au clavier (raccourcis), voir `RACCOURCIS_CLAVIER.md` — cette section couvre les choix d’implémentation techniques.

**Hiérarchie des titres.** Un seul `H1` par page, toujours focusable (`tabindex="-1"`) ; les grandes zones utilisent `H2` ; les sous-zones (notamment les deux listes de composition de l’éditeur, et les sous-groupes de la page Configuration) utilisent `H3` ; les titres sont reliés à leur zone avec `aria-labelledby` lorsque cela améliore le nom accessible.

Hiérarchie par page :

- **Compte** (`/`) : `H1` Compte ; `H2` Vérification du compte, Connexion, Synchronisation, Messages.
- **Bibliothèque** (`/routes`) : `H1` Bibliothèque des routes ; `H2` Routes personnelles, Routes partagées, Routes enregistrées sur ce PC, Messages.
- **Créer une route** (`/editor`) — le `H1` reflète le contexte réel (« Créer une route », « Nouvelle route : *nom* », « Modifier : *nom* ») : `H2` Route en cours, Choisir des points, Composer la route, Informations sur le point, Analyse de la route, Enregistrement et export, Messages ; `H3` Points importés : nombre, Points de la route : nombre.
- **Configuration** (`/configuration`) : `H1` Configuration ; `H2` Répertoire des routes, Compte SARA, Import et export, Fenêtre principale, Fenêtre de visualisation cartographique, Fichier de configuration, Messages ; `H3` (dans la zone fenêtre carte) Taille de la fenêtre, Couleurs, Tracé de route, Étiquettes des points de route, Marques SHOM.
- **À propos** (`/about`) : `H1` À propos de SARA Route Manager ; `H2` Informations générales, Périmètre, Licence, Avertissement, Référence et remerciements, Documentation, Assistance technique.

**Zones F6.** Toutes les pages appliquent le même motif : chaque grande zone porte la classe `f6-zone` et l’attribut `data-zone-name`, et son titre est focusable. Seule exception, volontaire et identique partout : la zone **Messages** n’est jamais une zone F6 (journal passif consulté au fil de l’eau via `aria-live`, pas une zone de travail à atteindre directement). La navigation F6 elle-même est mutualisée dans `static/js/keyboard_zones.js`, chargé globalement depuis `base.html` : comportement identique sur toutes les pages, sans code dupliqué par page.

**Focus.** Après une action, le focus revient sur l’élément logique : liste concernée, bouton ayant ouvert un dialogue, ou élément nouvellement créé. Une annulation ne doit jamais envoyer le focus au début de la page.

**Messages.** Les messages de succès, d’annulation et d’erreur utilisent une zone `role="status"` avec `aria-live="polite"`. Ils donnent une information exploitable (ex. nombre de segments exportés et chemin complet du fichier).

**Dialogues de fichiers.** Les exports utilisent le dialogue natif Windows **Enregistrer sous**. Le nom proposé est modifiable, le dossier est choisi par l’utilisateur, le chemin complet est annoncé après succès.

**Boîtes de dialogue modales.** Trois existent à ce jour, sur le même motif : « Modifications non enregistrées » (éditeur), résultat de l’outil de mesure et informations sur une marque (fenêtre carte). Toutes partagent : `role="alertdialog"`, `aria-modal="true"`, titre et description reliés par `aria-labelledby`/`aria-describedby` ; à l’ouverture, le focus se pose sur le premier bouton actionnable (jamais sur le titre, qui n’est pas un contrôle interactif — certains lecteurs d’écran ne basculent pas de façon fiable en mode formulaire sinon) ; `Tab`/`Maj+Tab` restent cantonnés aux boutons de la boîte tant qu’elle est ouverte ; `Échap` ferme ou annule, et rend le focus à l’élément qui a ouvert la boîte.

## Organisation

- `sara_route_manager/` : code Python ;
- `templates/` : vues HTML Jinja ;
- `static/` : CSS et JavaScript ;
- `tests/` : tests automatisés ;
- `examples/` : fichiers d’exemple ;
- documents Markdown à la racine : références du projet.

## Composants

- Flask fournit l’interface HTTP locale et les API internes.
- pywebview affiche l’application dans une fenêtre Windows.
- Le stockage local conserve les routes et la configuration.
- Le client Firebase gère le compte et les routes distantes.
- Le module SHOM interroge le service WFS utilisé par SARA Navigation.
- Les modules de formats assurent les imports et exports.

## Modèle commun

Tous les points sont convertis vers un modèle commun comportant notamment : identifiant, nom, latitude, longitude, seuil de validation, source et métadonnées. L’éditeur ne dépend donc pas directement du format d’origine. Une sélection logique unique identifie le point actif et alimente à la fois le panneau de détails et les actions de copie.

## Principes de conception

- **Screen Reader First** : structure logique avant présentation visuelle.
- **Un éditeur unique** : toutes les sources alimentent la même interface.
- **Listes avant cartouches** : présentation compacte et prévisible.
- **Contexte stable** : la route active et l’état restent visibles.
- **Heading + F6** : titres et zones fonctionnelles se correspondent.
- **Périmètre maîtrisé** : aucune fonction cartographique hors scope.
- **Source unique de vérité** : une information n’est documentée qu’à un seul endroit.

## Décisions principales

1. Navigation à cinq onglets.
2. Éditeur de routes unique.
3. Bibliothèque sous forme de listes compactes.
4. Modèle de point unifié.
5. Accessibilité clavier et NVDA intégrée dès la conception.

## Service commun de dialogue de fichiers — version 0.6.12

Le fichier `static/js/file_dialogs.js` fournit `saveBlobWithDialog`. Il convertit le contenu à enregistrer et appelle `DesktopApi.save_file` exposé par pywebview.

`DesktopApi.save_file` ouvre le dialogue natif, écrit le fichier choisi et renvoie un résultat sérialisable avec le chemin complet. Le mode navigateur de diagnostic conserve un téléchargement standard comme solution de repli.

## Navigation F6 mutualisée — non publiée

Le fichier `static/js/keyboard_zones.js` est chargé globalement depuis `base.html`, comme `file_dialogs.js`. Il fournit la logique F6 / Maj+F6 de parcours des zones (`.f6-zone`) commune à toutes les pages, ce qui évite toute duplication entre scripts de page et garantit que le pattern « zone F6 + titre focusable » se comporte de façon identique partout, y compris sur les pages qui n'avaient historiquement aucune zone (Compte, Configuration, À propos).

## Fenêtre de visualisation cartographique — 0.7.0, étape 1

La page `/map` (`templates/map.html`, `static/js/map.js`) est une page autonome, sans le menu principal : c'est une fenêtre utilitaire ouverte à part depuis l'éditeur, pas une page de navigation normale.

La route active lui est transmise par un **jeton temporaire côté serveur** (`POST /api/map/token`, `GET /api/map/data/<jeton>`, stockage en mémoire dans `ApplicationState.map_tokens` avec expiration après 10 minutes) plutôt que par `sessionStorage`. Ce choix garantit un comportement identique en mode pywebview et en mode navigateur : `sessionStorage` se partage automatiquement entre onglets ouverts par `window.open()` en navigateur, mais pas nécessairement entre deux fenêtres pywebview créées séparément côté Python.

`DesktopApi.open_map_window(url)` réutilise la fenêtre carte déjà ouverte (rechargement via `load_url`) plutôt que d'en créer une seconde ; en mode navigateur, une cible `window.open()` nommée (`sara_map_window`) obtient nativement le même comportement. Aucun bouton de rafraîchissement n'existe dans la fenêtre carte elle-même : c'est le bouton « Visualiser la route » de l'éditeur qui joue ce rôle, en rechargeant la fenêtre existante avec un nouvel instantané.

Rendu initial minimal à l'étape 1 (points reliés par un trait, sans fond de carte ni trait de côte) ; fond de carte, trait de côte, icônes IALA officielles et export SVG ajoutés aux étapes suivantes — comportement fonctionnel complet documenté dans `SPECIFICATIONS.md`, section « Fenêtre de visualisation cartographique ».

## Calculs de route mutualisés — 0.7.0

Le fichier `static/js/route_math.js` est chargé globalement depuis `base.html`, comme `file_dialogs.js` et `keyboard_zones.js`. Il fournit les calculs de géométrie de route (distance orthodromique, cap initial, construction des segments, lignes CSV) utilisés à la fois par l'éditeur et par la fenêtre carte, évitant toute duplication. Comme `file_dialogs.js`, ses fonctions restent de vraies fonctions globales (pas d'IIFE) pour rester appelables depuis les autres scripts ; ses constantes de version portent donc un nom spécifique (`ROUTE_MATH_VERSION`/`ROUTE_MATH_DATE`) plutôt que `__version__`/`__date__`, pour ne pas entrer en collision avec celles de `file_dialogs.js` sur les pages qui chargent les deux.

La fenêtre carte (`map.html`, `map.js`) charge désormais aussi `file_dialogs.js`, prévu depuis l'étape 1 pour l'export SVG : l'export reconstruit sa propre projection à partir des données déjà en mémoire (points, trait de côte), plutôt que d'extraire le rendu interne de Leaflet — celui-ci est positionné par des transformations CSS relatives à l'état de défilement en cours, peu adaptées à un export autonome et correct dans tous les cas.
