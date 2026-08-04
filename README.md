# SARA Route Manager 0.7.2.0

SARA Route Manager est une application Windows accessible destinée à préparer, modifier, visualiser, importer, exporter et synchroniser des routes compatibles avec l’application SARA Navigation sur Iphone.

L’application n’est ni un logiciel de navigation, ni une application cartographique. Elle sert juste à faciliter la préparation des routes avant leur utilisation dans l’application SARA Navigation.

## Installation

1. Décompresser entièrement l’archive ZIP.
2. Exécuter `Installer.bat` lors de la première installation.
3. Exécuter `Lancer_SARA_Route_Manager.bat` pour démarrer l’application.

Le mode `Lancer_Mode_Navigateur.bat` est réservé au diagnostic. Dans ce mode, le navigateur gère lui-même le dossier de téléchargement et ne communique pas son chemin exact à l’application.

Un exécutable Windows autonome (`.exe`, sans installation de Python requise) est disponible dans les [*Releases*](../../releases) du dépôt, lorsqu’une a été publiée. À défaut, `Construire_Executable.bat` permet de le construire soi-même depuis les sources (voir `docs/SPECIFICATIONS.md`).

## Fonctions principales

- création et ouverture de routes ;
- import de fichiers GPX, WPT, CSV et JSON ;
- recherche de marques SHOM ;
- composition d’une route avec deux listes accessibles ;
- analyse légère : distance totale et nombre de segments ;
- export GPX, CSV, JSON et export CSV détaillé des segments ;
- synchronisation avec un compte SARA Navigation ;
- bibliothèque de routes personnelles, partagées et locales.

## Nouveautés de la version 0.7.0

- Nouvelle fenêtre de visualisation cartographique de la route active (création ou modification) : rendu Leaflet interactif (zoom à la molette, déplacement au clic-glisser), trait de côte du SHOM (Limite terre-mer avec repli HISTOLITT pour l'outre-mer), export des segments en CSV et export de la carte en SVG.
- Fenêtre principale et fenêtre carte dimensionnées et centrées automatiquement selon des pourcentages configurables de la taille de l'écran.
- Correction d'un défaut d'accessibilité : l'abréviation « NM » (milles nautiques), lue par NVDA comme « nanomètre », a été remplacée par le texte complet partout où une distance est annoncée.

## Nouveautés de la version 0.6.13

- Restructuration de la page « Créer une route » : la création et l'ouverture d'une route ne sont plus mélangées sur le même écran. La création se fait depuis un onglet dédié du menu principal ; l'ouverture d'une route existante se fait uniquement depuis la Bibliothèque. Un lien « Retour à la bibliothèque » est disponible en permanence, avec confirmation en cas de modifications non enregistrées.
- Le titre de la page « Créer une route » reflète désormais réellement le contexte (« Créer une route », « Nouvelle route : *nom* » ou « Modifier : *nom* »).
- Homogénéisation de l'accessibilité sur les 5 pages de l'application : le pattern « zone F6 + titre focusable » s'applique désormais partout, y compris sur les pages Compte, Configuration et À propos qui en étaient dépourvues. La navigation F6 est mutualisée dans un script unique commun à toutes les pages.
- Nettoyage du code : suppression des fichiers orphelins non utilisés, ajout des entêtes standardisés à tous les scripts JavaScript actifs.

## Nouveautés de la version 0.6.12

- L'export CSV des segments ouvre un véritable dialogue **Enregistrer sous**.
- Le nom proposé peut être modifié.
- Le dossier de destination peut être choisi.
- Le dialogue utilise la constante officielle de pywebview au lieu d'une valeur numérique ambiguë.

## Documentation

- `docs/USER_GUIDE.md` : utilisation de l’application ;
- `docs/RACCOURCIS_CLAVIER.md` : commandes clavier et navigation NVDA ;
- `docs/SPECIFICATIONS.md` : comportement fonctionnel et conventions de développement ;
- `docs/ARCHITECTURE.md` : organisation technique (inclut les détails d’implémentation de l’accessibilité) ;
- `docs/THIRD_PARTY_LICENSES.md` : licences des ressources tierces intégrées ;
- `CHANGE_LOG.md` : historique des versions ;
- `LICENSE.md` : licences du code et de la documentation.
