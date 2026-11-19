# Spécifications

**Rôle :** document de référence unique pour le comportement fonctionnel de l'application et les conventions de développement — fusionné à partir de trois fichiers auparavant distincts (spécifications fonctionnelles, notes de préparation de la fenêtre cartographique, conventions de développement), qui se chevauchaient partiellement.

## Partie 1 — Fonctionnement

### Périmètre

Sont inclus : gestion du compte SARA, bibliothèque, création et modification des routes, synchronisation, SHOM, GPX, WPT, CSV, JSON, saisie manuelle, autre route locale, et une fenêtre de visualisation cartographique en complément strictement visuel.

Sont hors périmètre : routage automatique, météo, marées, AIS et navigation en temps réel. SARA Route Manager n'est ni un logiciel de navigation, ni une application cartographique à part entière — voir le texte d'avertissement affiché dans l'onglet À propos.

### Navigation principale

L'application comporte cinq onglets : Compte, Bibliothèque, Créer une route, Configuration, À propos.

### Précision numérique des envois vers SARA Navigation

SARA Navigation décode latitude, longitude et distance de validation avec `as? Float` : un nombre JSON 64 bits non exactement représentable en 32 bits est refusé, le point perd sa position GPS et la visualisation de la route fait planter l'application. À l'envoi vers Firebase, ces trois valeurs sont donc arrondies à la précision 32 bits (`to_float32`, écart inférieur à 0,5 m), comme le fait l'application iOS elle-même. La sauvegarde locale et les exports gardent les valeurs d'origine.

### Vocabulaire commun avec SARA Navigation

Les noms des actions de partage reprennent ceux de l'application iPhone SARA Navigation (sources `SARANav.xcstrings` et `Localizable.xcstrings` de SARAFramework). SARA Régate, qui parle de « parcours » à « partager » / « départager », n'est pas prise en charge ; le vocabulaire de Navigation fait foi.

| Clé iPhone | Libellé iPhone | Utilisation dans SARA Route Manager |
| --- | --- | --- |
| `upload` | Déposer en ligne | bouton de l'éditeur |
| `download` | Télécharger | bouton de la Bibliothèque (routes en ligne) |
| `my_routes` | Mes routes | filtre et origine des routes que l'on a mises en ligne |
| `other_routes` | Autres routes | filtre et origine des routes des autres utilisateurs |
| `upload_date` | Date de dépôt | date affichée dans la liste |
| `delete` | Supprimer | bouton de la Bibliothèque |
| `visualize` / `map` | Visualiser / carte | **« Voir la carte »** (éditeur et Bibliothèque) : sur iPhone, « Visualiser » ouvre la liste des points et le bouton « carte » bascule vers la carte ; ici la liste des points est dans l'éditeur et la carte est ouverte à part |
| `firebase_success_upload` | La route a été mise en ligne avec succès ! | message après « Déposer en ligne » |
| `firebase_name_exists_owner` | Une de vos routes mises en ligne a le même nom. Voulez-vous l'écraser ? | boîte « Attention », Oui / Non |
| `firebase_name_exists` | Cette route ne peut pas être mise en ligne. Une route avec le même nom appartenant à un autre utilisateur existe déjà. | erreur de mise en ligne |
| `firebase_warning_erase_route_local` | Une route avec le même nom existe déjà, voulez-vous l'écraser ? | confirmation de « Télécharger » |
| `firebase_success_download_save_route` | La route a été téléchargée et sauvegardée avec succès. | message après « Télécharger » |
| `firebase_success_delete_route` | La route a été supprimée avec succès. | message après suppression |

Pour lever toute confusion avec « Sur ce PC », les deux filtres de routes en ligne portent la précision **« (en partage) »** (« Mes routes (en partage) », « Autres routes (en partage) ») : une route déposée en ligne est visible de tous les utilisateurs de SARA Navigation.

#### SARA Navigation et SARA Régate

SARA Route Manager cible **uniquement SARA Navigation** : il lit et écrit les routes de navigation (`/courses` dans Firebase) au format de cette application. SARA Régate est une application distincte, qui manipule des **parcours** de régate avec son propre vocabulaire (« parcours partagé », « partager », « départager ») et ses propres structures de données. Ces parcours ne sont pas pris en charge : ils ne sont ni importés, ni créés, ni déposés en ligne par l'outil. En cas de différence de vocabulaire, celui de SARA Navigation fait foi, et c'est pourquoi les termes « partager » ou « parcours » ne sont pas utilisés pour les noms de boutons.

Les corrections d'orthographe de l'iPhone (« téléchargé » → « téléchargée », « Une de vos route » → « Une de vos routes ») sont appliquées. Les actions sans équivalent sur iPhone (Importer une route…, Exporter…, Enregistrer sur le PC, Actualiser la liste, filtre « Sur ce PC ») gardent leurs noms propres.

### Bibliothèque

Depuis la version 0.8.0, la Bibliothèque présente **une liste unique** qui réunit les routes personnelles SARA, les routes partagées et les routes enregistrées sur le PC. Chaque ligne annonce son origine (« mes routes », « autres routes » ou « sur ce PC »).

- **Filtre** : groupe de boutons radio « Afficher » (Toutes, Mes routes (en partage), Autres routes (en partage), Sur ce PC) et champ de recherche par nom, qui réduisent la liste au fil de la saisie. Un résumé « *Filtre* : n routes affichées sur m » est annoncé (`role="status"`), le nom du filtre en tête pour lever toute ambiguïté après un changement de bouton radio.
- **Actions** (un seul jeu de boutons, portant sur la route sélectionnée) : **Éditer** (libellé **Consulter** pour une route de « Autres routes (en partage) »), **Voir la carte**, **Télécharger**, **Exporter…**, **Importer une route…**, **Supprimer**. Leur disponibilité dépend de l'origine de la route (tableau ci-dessous) et une phrase d'aide (`#route-action-hint`) rappelle ce qu'il est possible de faire.
- **Exporter…** ouvre une boîte de dialogue (`alertdialog`, piège de focus, Échap pour annuler) avec le choix du format en boutons radio : JSON SARA (par défaut), GPX ou CSV, puis le dialogue natif « Enregistrer sous ».
- **Importer une route…** ouvre le dialogue de choix de fichier (JSON, GPX, CSV, WPT). La route est importée **en entier** (nom, sens, points) et enregistrée sur le PC ; si une route locale porte déjà ce nom, une confirmation est demandée. Les clés non reconnues d'un fichier JSON (par exemple un bloc `metadonnees`) sont ignorées. Cet import est distinct de la source « Fichier » de l'éditeur, qui ne récupère que les points.
- **Menu contextuel** (touche Menu, `Maj+F10` ou clic droit), adapté à l'origine de la route (voir tableau ci-dessous).

| Action | Sur ce PC | Mes routes (en partage) | Autres routes (en partage) |
| --- | --- | --- | --- |
| Éditer / Consulter | Éditer | Éditer | Consulter |
| Voir la carte | oui (2 points minimum) | oui (2 points minimum) | oui (2 points minimum) |
| Télécharger | absent | actif seulement si aucune route locale de même nom ; sinon grisé et absent du menu | oui (confirmation d'écrasement si une copie locale existe) |
| Renommer | oui | oui | absent |
| Dupliquer | oui | oui | « Copier dans mes routes » |
| Exporter… | oui | oui | oui |
| Supprimer | oui | oui (retire la route de la liste en partage) | absent |

- **Voir la carte** (0.9.3) : ouvre directement la fenêtre carte avec la trace de la route, sans passer par l'éditeur (jeton `/api/map/token`, fenêtre réutilisée si elle est déjà ouverte) et annonce le nom et le nombre de points. Il faut au moins 2 points, comme pour « Visualiser » dans SARA Navigation. La carte reste un complément visuel : le nom et le nombre de points sont aussi annoncés en texte.
- **Format pré-coché** : celui du réglage « Format d'export par défaut » de la page Configuration.
- **Actualisation** : un seul bouton « Actualiser la liste » (routes du PC, et routes SARA si connecté).
- **Boîte de dialogue d'export commune** (`export_dialog.js`, gabarit `_export_dialog.html`) : la Bibliothèque et l'éditeur l'utilisent toutes deux, avec le même bouton **Exporter…** ; l'éditeur n'a plus de boutons d'export par format.
- **Déposer en ligne** (éditeur) : comme dans SARA Navigation, une route d'un autre utilisateur de même nom bloque la mise en ligne (API : 409, `owned_by_other: true`, simple message d'erreur) ; l'une de ses propres routes en ligne de même nom propose l'écrasement (API : 409, `exists: true`, boîte « Attention » Oui / Non).
- La suppression d'une route locale supprime son fichier JSON du dossier des routes, après confirmation.
- Ouverture directe d'une route par double-clic ou Entrée sur un élément de la liste.

### Éditeur de routes

L'éditeur affiche toujours la route active : nom, nombre de points et état des modifications. Le titre de la page reflète le contexte (« Créer une route », « Nouvelle route : *nom* » ou « Modifier : *nom* »).

La création et l'ouverture d'une route ne sont pas mélangées sur le même écran :

- **Créer une route** : accessible depuis l'onglet dédié du menu principal, l'éditeur s'ouvre vide avec un seul champ de nom et un bouton **Créer cette route** ;
- **Modifier une route existante** : uniquement depuis la Bibliothèque, qui transmet la route choisie à l'éditeur.

Un lien **Retour à la bibliothèque** reste disponible en permanence. Le remplacement ou l'abandon d'une route modifiée sans être enregistrée demande toujours confirmation (boîte de dialogue à 3 choix : Enregistrer et retourner, Retourner sans enregistrer, Annuler).

L'éditeur repose sur deux listes — points disponibles, points de la route — navigables par flèches haut/bas dès le premier focus clavier (sélection automatique du premier élément), avec menu contextuel (touche Menu ou Maj+F10) pour les actions courantes.

### Panneau « Informations sur le point »

Reflète toujours la sélection logique la plus récente, qu'elle provienne de la liste **Points disponibles** ou de la liste **Points de la route**. Navigable ligne par ligne avec les flèches haut/bas (pas de bouclage aux extrémités), une seule unité de lecture NVDA par ligne (couple libellé/valeur).

Champs modifiables — **uniquement pour un point déjà ajouté à la route** (un point encore dans « Points importés » n'a pas de place définitive) :

- **Nom, Latitude, Longitude** : champs de texte libre, encadrés d'un trait fin et contrasté, modification appliquée à la perte de focus ;
- **Distance de validation (mètre)** : champ numérique borné 1–1000 m.

Une valeur invalide (latitude/longitude hors bornes, rayon hors 1–1000 m) est refusée avec une annonce d'erreur, l'ancienne valeur étant reprise. Un nom vide retombe sur « Point sans nom ».

Champs en lecture seule, même mise en page : Type, Source, propriétés SHOM d'origine (nombre variable selon le point).

Raccourci `Alt+E` pour sauter directement dans le champ Nom. Les boutons **Copier les informations** et **Copier les coordonnées** agissent sur le point actif, quelle que soit sa liste ou sa source.

### Filtrage et tri

Les points disponibles peuvent être filtrés par type de balisage SHOM. Le filtrage et le tri sont indépendants. Le compteur indique le nombre affiché et le nombre total.

### Fenêtre de visualisation cartographique

Fenêtre séparée (pas un panneau intégré à l'éditeur), ouverte par le bouton **« Voir la carte »** de la zone « Analyse de la route », désactivé tant que la route contient moins de 2 points. C'est un **complément strictement visuel**, jamais un canal d'information exclusif : tout ce qu'elle montre reste disponible par ailleurs sous forme textuelle. La carte reste neutre pour NVDA (`role="img"`), sans jamais porter une information qui n'existerait qu'à cet endroit.

**Instantané, pas de synchronisation en direct** : la carte affiche la route telle qu'elle était au moment du clic sur « Voir la carte ». Un nouveau clic alors que la fenêtre est déjà ouverte la recharge avec un nouvel instantané, plutôt que d'en ouvrir une deuxième.

**Rendu** : Leaflet.js, vendu localement (pas de CDN, pas de dépendance réseau permanente). Fond plat (rectangle de couleur pour la mer, polygones pour les terres émergées), sans tuiles externes — cohérent avec SARA Navigation elle-même, qui utilise Apple MapKit en mode standard sans rendu nautique détaillé.

**Trait de côte** : récupéré via le flux WFS du SHOM, deux couches possibles choisies dynamiquement selon la zone — « Limite terre-mer » (métropole) en priorité, repli automatique sur « Trait de Côte HISTOLITT® » (outre-mer) si la première ne renvoie aucune entité. Attribution affichée selon la couche utilisée (HISTOLITT exige en plus les logos IGN et SHOM).

**Marques SHOM environnantes** : interrogées indépendamment de ce qui a été chargé pendant la composition de la route, avec une bbox dérivée du tracé. Icônes officielles du SHOM (bibliothèque SVG du produit « Balisage maritime », Licence Ouverte 2.0), sélectionnées à partir des attributs S-57 de chaque marque — voir `sara_route_manager/shom_icons.py` pour le détail de la convention de nommage et le mécanisme de sélection. Repli sur un marqueur générique (cercle) si aucune correspondance fiable n'est trouvée. Case à cocher par catégorie (latérales, cardinales, danger isolé, eaux saines, spéciales, amers, autres) pour choisir quelles marques afficher. Taille des icônes configurable (page Configuration, 10–60 px).

**Persistance du type IALA** (option B) : le format de sauvegarde local (pas celui échangé avec SARA Navigation) conserve le code d'objet S-57 d'origine, pour que les icônes IALA des points de route survivent à un enregistrement/réouverture.

**Réglages visuels**, tous en page Configuration (préférences durables, pas d'ajustement en direct dans la fenêtre carte, sauf exception ci-dessous) : couleurs mer/terre/tracé, épaisseur et style du tracé (continu/tireté/pointillé), taille et encadrement des étiquettes de points de route, taille des icônes SHOM, taille et centrage de la fenêtre. Exception délibérée : case à cocher en direct pour l'affichage des étiquettes de points de route et des noms de marques, car les encadrés peuvent masquer des éléments de la carte.

**Grille et échelle** : grille latitude/longitude activable (pas de rond, graduations selon l'étendue visible), barre d'échelle en milles nautiques (toujours affichée, coin inférieur droit, texte en toutes lettres « Milles » plutôt que l'abréviation « NM » lue par NVDA comme « nanomètre »), graduations en milles nautiques sur les 4 bords de la carte (espacement rigoureusement identique à la valeur affichée par la barre d'échelle).

**Outil de mesure** : case à cocher qui désactive le déplacement normal de la carte au clic-glisser ; cliquer-glisser-relâcher entre deux points affiche une boîte de dialogue accessible (distance en milles nautiques, cap vrai initial), avec boutons Copier et Fermer.

**Informations sur une marque** : double-clic sur un point de route ou une marque SHOM affiche une boîte de dialogue (Nom, Type précisé avec direction cardinale ou côté latéral, Source), avec boutons Copier et Fermer. Annonce vocale équivalente au survol à la souris.

**Export** : segments en CSV et carte en SVG, tous deux générés côté serveur/navigateur à partir des mêmes données ayant servi à construire la carte (pas une capture d'écran), réutilisant le mécanisme d'enregistrement commun (`saveBlobWithDialog`).

### Configuration

Page organisée en zones F6, chacune avec ses propres sous-titres `H3` quand elle regroupe plusieurs réglages logiques (ex. la zone fenêtre carte : taille, couleurs, tracé, étiquettes, marques SHOM). Export et import du fichier de configuration complet (dossier « sauvegardes » proposé par défaut), en plus de la réinitialisation aux valeurs par défaut déjà existante. Un fichier de configuration antérieur à l'ajout de nouveaux réglages se complète automatiquement au chargement, sans perdre les réglages déjà présents.

### Accessibilité

- un seul `H1` par page, toujours focusable ;
- hiérarchie de titres sans saut de niveau ;
- chaque zone atteignable avec `F6` commence par un titre focusable ;
- `F6` et `Maj+F6` parcourent les zones fonctionnelles (zone Messages exclue, journal passif) ;
- les changements importants sont annoncés par une zone `aria-live` ;
- le contexte actif ne disparaît pas après une action, le focus revient sur l'élément logique ;
- toutes les fonctions essentielles sont utilisables au clavier.

Détail de l'implémentation (structure des titres par page, motifs ARIA des boîtes de dialogue modales) : voir `ARCHITECTURE.md`. Raccourcis clavier complets : voir `RACCOURCIS_CLAVIER.md`.

### Onglet À propos

Affiche la version, le périmètre, la licence (GPL-3.0-only pour le code, CC BY-SA 4.0 pour la documentation, textes légaux complets ouverts dans le navigateur système), un avertissement (absence de garantie), les remerciements à Orion Brest, et les informations de diagnostic. Permet d'ouvrir le guide utilisateur, le document des raccourcis clavier et le journal des versions.

### Export homogène

Tous les exports de fichiers utilisent un mécanisme commun (`static/js/file_dialogs.js`). Dans l'application de bureau, une boîte native **Enregistrer sous** permet de choisir le dossier et de modifier le nom proposé. Après succès, le message indique le format, le contenu exporté lorsque pertinent et le chemin complet. Après annulation, le message est « Export annulé. », sans erreur signalée. Le focus revient sur le bouton ayant ouvert le dialogue.

L'export des segments utilise le nom proposé `Nom_de_la_route_segments.csv` avec les colonnes `Numero_segment;Marque_debut;Marque_fin;Longueur_NM;Cap_degres` (cap vrai initial du segment).

## Partie 2 — Développement

### Environnement cible

- Windows 11 ;
- Python 3.12 ou version compatible ;
- Flask, Waitress et pywebview avec Edge WebView2 ;
- NVDA pour la validation d'accessibilité.

**Environnement virtuel Python** : créé et réutilisé à un emplacement partagé et stable (`%LOCALAPPDATA%\SARA Route Manager\venv`), en dehors des dossiers versionnés — plutôt qu'un `.venv` par dossier de livraison, recopié manuellement d'une version à l'autre (friction de distribution corrigée). `Installer.bat` le crée au premier lancement et le réutilise ensuite ; `Lancer_SARA_Route_Manager.bat` et `Lancer_Mode_Navigateur.bat` le retrouvent via la variable `SARA_VENV_PYTHON`, exportée par `Installer.bat`.

### Conventions Python

Tout module commence par la déclaration UTF-8, `from __future__ import annotations`, un cartouche de module, puis `__version__` et `__date__`. Les fonctions et méthodes utilisent des docstrings détaillées au format NumPy et des commentaires explicites. Structure des dossiers : voir `ARCHITECTURE.md`.

### Dialogues communs

`static/js/file_dialogs.js` centralise l'enregistrement des fichiers. En mode bureau, il appelle `DesktopApi.save_file`. En mode navigateur de diagnostic, il conserve un téléchargement standard sans promettre de chemin précis. Toute nouvelle fonction d'export doit réutiliser ce mécanisme commun.

### Construction de l'exécutable Windows autonome

`Construire_Executable.bat` construit un exécutable `--onefile` avec PyInstaller, dans l'environnement virtuel partagé (`Installer.bat`). PyInstaller n'est jamais imposé à un utilisateur lançant l'application depuis les sources : c'est une dépendance de construction séparée (`requirements-dev.txt`), pas dans `requirements.txt`.

Le point d'entrée est `run_sara_route_manager.py`, distinct de `sara_route_manager/__main__.py` : ce dernier utilise des imports relatifs, qui échoueraient si PyInstaller le pointait directement comme script autonome. Configuration détaillée dans `sara_route_manager.spec` (fichier `.spec` versionné intentionnellement, exception explicite dans `.gitignore`), qui inclut notamment les gabarits Jinja et les fichiers statiques — non embarqués automatiquement par PyInstaller — ainsi que des imports cachés estimés (backends pywebview et keyring) à confirmer sur un poste Windows réel.

**Construction et test confirmés en conditions réelles sur Windows** (4 août 2026) : exécutable construit avec succès, lancé normalement, connexion au compte SARA (backend `keyring.backends.Windows`), recherche et ajout de marques SHOM, et visualisation cartographique (backend `webview.platforms.edgechromium`) tous vérifiés fonctionnels.

**Distribution de l'exécutable construit** : `dist\SARA_Route_Manager.exe` est un résultat de construction, exclu du dépôt Git (comme `build\`) — il ne fait jamais partie du code source suivi, ni de ce qui est poussé sur GitHub. Deux façons de le rendre disponible à un utilisateur qui ne veut pas le construire lui-même :

- le reconstruire depuis les sources avec `Construire_Executable.bat` ;
- l'attacher manuellement à une *Release* GitHub (page du dépôt → *Releases* → *Create a new release*, choisir un tag correspondant à la version, joindre le fichier `.exe` construit avant de publier) — usage standard sur GitHub pour distribuer un binaire construit à partir du code source, le dépôt et l'exécutable restant deux choses distinctes.

### Préparation d'une version ZIP

1. repartir du dernier ZIP validé ;
2. appliquer uniquement les modifications prévues ;
3. mettre à jour les versions et la documentation ;
4. exécuter les tests Python et les contrôles JavaScript ;
5. comparer les fichiers avec la version précédente ;
6. créer puis tester l'intégrité du ZIP.

Aucun fichier antérieur ne doit disparaître sans décision explicite documentée.
