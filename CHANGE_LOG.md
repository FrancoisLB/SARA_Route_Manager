# Journal des modifications

## 0.7.2.0 (suite) — clarification sur la distribution de l'exécutable

- **documentation complétée**, repérée comme manquante après question de l'utilisateur : `docs/SPECIFICATIONS.md` explique désormais que `dist\SARA_Route_Manager.exe` est exclu du dépôt Git (résultat de construction, pas du code source) et détaille les deux façons de le rendre disponible (le reconstruire soi-même, ou l'attacher manuellement à une *Release* GitHub) ;
- mention courte ajoutée dans `README.md`, section Installation, avec lien vers les *Releases* du dépôt ;
- 1 test dédié ajouté.

## 0.7.2.0 — version réelle mise à jour avant publication GitHub

- **incohérence corrigée, repérée par l'utilisateur** : la version interne réelle (`VERSION.txt`, tous les `__version__`) était restée bloquée à `0.7.1.0` depuis le début de cette session, alors que le numéro croissant utilisé dans le nom des archives (`v0.7.1.N`) n'était qu'un simple compteur de livraison interne à nos échanges, jamais la vraie version de l'application — d'où le dossier `SARA_Route_Manager_v0.7.1.0` à l'intérieur d'un zip nommé `...v0.7.1.30.zip` ;
- **version portée à `0.7.2.0`**, reflétant l'ampleur réelle du travail livré depuis `0.7.1.0` (fenêtre carte complète, éditeur refondu, Configuration avec export/import, licence, exécutable...) ;
- mise à jour uniforme : `VERSION.txt`, `__version__`/`__date__` de tous les modules Python (`sara_route_manager/`, `tests/`, `run_sara_route_manager.py`), `__version__`/`__date__` de tous les scripts JavaScript, `ROUTE_MATH_VERSION`/`ROUTE_MATH_DATE` (convention de nommage propre à `route_math.js`), titre de `README.md` ;
- 1 test de cohérence de version mis à jour ;
- **compteur de livraison abandonné à partir de maintenant** : le nom de l'archive suit désormais directement la vraie version de l'application, sans numéro supplémentaire.

## Non publié — rafraîchissement de docs/USER_GUIDE.md

- **guide utilisateur entièrement rafraîchi**, très en retard (aucune mention de la fenêtre carte, section « Consulter les informations » décrivant encore l'ancienne version en lecture seule) :
  - section « Visualiser la route sur une carte » ajoutée (fond de carte, trait de côte, marques SHOM, outil de mesure, boîte de dialogue d'informations, export) ;
  - section « Consulter et modifier les informations d'un point » réécrite pour refléter le panneau désormais éditable (champs modifiables, `Alt+E`) ;
  - sections « Configuration » et « Licence et avertissement » ajoutées ;
  - référence à `RACCOURCIS_CLAVIER.md` corrigée en `docs/RACCOURCIS_CLAVIER.md`.

**Documentation entièrement à jour et cohérente à ce stade** — dernier point en suspens avant publication GitHub levé.

## Non publié — exécutable PyInstaller confirmé fonctionnel en conditions réelles

- **construction et lancement testés avec succès sur Windows** (version 0.7.1.27) : `Construire_Executable.bat` a produit `dist\SARA_Route_Manager.exe` sans erreur ;
- **les deux inconnues signalées lors de la préparation sont levées** : l'exécutable démarre normalement, la connexion au compte SARA fonctionne (confirme le backend `keyring.backends.Windows`), la recherche/ajout de marques SHOM et la visualisation cartographique fonctionnent (confirme le backend `webview.platforms.edgechromium`) ;
- `sara_route_manager.spec` et `docs/SPECIFICATIONS.md` mis à jour pour refléter cette confirmation, plutôt que la réserve initiale ;
- 1 test mis à jour.

**Groupe 5 (phase E) entièrement achevé et validé en conditions réelles.**

## Non publié — suppression de docs/RELEASE_NOTES.md

- **`docs/RELEASE_NOTES.md` supprimé** : constat décisif en vérifiant — le bouton « Ouvrir le journal des versions » de l'onglet À propos pointe en réalité vers `CHANGE_LOG.md`, jamais vers `RELEASE_NOTES.md`, qui était un fichier orphelin, non relié à l'application. Par ailleurs, redondant avec `CHANGE_LOG.md` (même historique, en version plus soignée mais bien moins détaillée) et arrêté à la version 0.7.0 comme les autres fichiers déjà nettoyés ;
- références retirées de `README.md` et `tests/test_release_completeness.py`.

## Non publié — mise à jour de dépendances (audit avant publication)

- **Flask 3.1.1 → 3.1.3** : la 3.1.2 corrige une faille de sécurité (session mal invalidée sur des opérations qui ne font que consulter les clés) ;
- **requests 2.32.4 → 2.34.2** : rien de cassant identifié pour notre usage (simples GET/POST vers le WFS SHOM) ;
- **waitress** : déjà à jour (3.0.2), inchangé ;
- **pywebview volontairement laissé en 5.4** : un successeur majeur (6.2.1) existe, avec des changements cassants annoncés — notre code semble déjà compatible en lecture (préfère déjà `webview.FileDialog`, n'utilise aucun élément supprimé en 6.0), mais c'est une lecture de code, pas un test réel. Décision de ne pas ajouter cette inconnue supplémentaire avant d'avoir confirmé que l'exécutable PyInstaller fonctionne avec le socle actuel.

## Non publié — groupe 5 (phase E), étape 3/3 : préparation PyInstaller

- **4 nouveaux fichiers préparés** pour la construction d'un exécutable Windows autonome (`--onefile`) :
  - `run_sara_route_manager.py` : point d'entrée dédié, import absolu du paquet — `sara_route_manager/__main__.py` utilise des imports relatifs, qui échoueraient si PyInstaller le pointait directement comme script autonome ;
  - `sara_route_manager.spec` : configuration PyInstaller (gabarits Jinja et fichiers statiques inclus explicitement, non embarqués automatiquement ; imports cachés estimés pour les backends pywebview et keyring, à confirmer sur un poste Windows réel ; sans console, application graphique) ;
  - `requirements-dev.txt` : PyInstaller comme dépendance de construction séparée (`pyinstaller==6.21.0` + `pyinstaller-hooks-contrib`), jamais imposée à un utilisateur lançant l'application depuis les sources ;
  - `Construire_Executable.bat` : automatise la construction dans l'environnement virtuel partagé ;
- `.gitignore` : exception explicite pour `sara_route_manager.spec`, versionné intentionnellement (nécessaire à une construction reproductible), au milieu de l'exclusion générale des `*.spec` ;
- `docs/SPECIFICATIONS.md` complété ;
- 8 tests dédiés ajoutés (vérification de contenu uniquement — la construction et le test de l'exécutable lui-même sont hors de portée de cet environnement de préparation, sans Windows disponible).

**Groupe 5 (phase E) — audit d'hygiène et restructuration entièrement terminés.** Reste, avant publication effective : construire et tester réellement l'exécutable sur un poste Windows (aller-retour de vérification à prévoir).

## Non publié — groupe 5 (phase E), étape 2/3 : environnement virtuel partagé

- **friction de distribution corrigée** : l'environnement virtuel Python est désormais créé et réutilisé à un emplacement partagé et stable (`%LOCALAPPDATA%\SARA Route Manager\venv`), en dehors des dossiers versionnés, plutôt qu'un `.venv` par dossier de livraison que l'utilisateur recopiait manuellement d'une version à l'autre ;
- `Installer.bat` crée l'environnement au premier lancement et le réutilise ensuite (recherche de version Python compatible inchangée, seul l'emplacement change) ; exporte son chemin via la variable `SARA_VENV_PYTHON`, transmise au script appelant (technique `endlocal & set`) ;
- `Lancer_SARA_Route_Manager.bat` et `Lancer_Mode_Navigateur.bat` utilisent cette variable plutôt qu'un chemin local ;
- `.gitignore` et `docs/SPECIFICATIONS.md` mis à jour en conséquence ;
- 5 tests dédiés ajoutés (vérification de contenu, un `.bat` ne s'exécute pas sous Linux).

## Non publié — suppression de ROADMAP.md

- **`ROADMAP.md` supprimé** : à ce stade, ~90 % de son contenu était devenu purement historique (groupes 1 à 4 et versions antérieures, tous marqués « Réalisé », déjà documentés dans le détail par ce même journal) — et les dernières étapes prospectives qui restaient (groupe 5 : `.venv` partagé, préparation PyInstaller) sont sur le point d'être réalisées avant la publication GitHub, ce qui aurait laissé le fichier vide de tout contenu utile ;
- références retirées de `README.md` et `tests/test_release_completeness.py`.

## Non publié — groupe 5 (phase E), audit d'hygiène du dépôt (4/4) : fusion SPECIFICATIONS/DEVELOPPEMENT/NOTES_CARTOGRAPHIE

- **3 fichiers fusionnés en un seul, `docs/SPECIFICATIONS.md`** : l'ancien `SPECIFICATIONS.md` (fonctionnel, très en retard, s'arrêtait à 0.6.8/0.6.12), `docs/DEVELOPPEMENT.md` (conventions de code, procédure de livraison) et `NOTES_CARTOGRAPHIE.md` (en réalité la spécification fonctionnelle de la fenêtre carte, rédigée comme des notes de préparation avant sa construction — la fonctionnalité est maintenant terminée) ;
- **partie « Fonctionnement » entièrement rafraîchie**, avec tout ce qui manquait : fenêtre de visualisation cartographique (fond de carte, trait de côte, marques SHOM, icônes IALA, réglages visuels, grille/échelle/graduations, outil de mesure, boîte de dialogue d'informations sur une marque, export), panneau « Informations sur le point » refondu, page Configuration (titres hiérarchiques, export/import), onglet À propos (licence, avertissement) ;
- **partie « Développement » reprise sans la section structure des dossiers**, déjà présente dans `ARCHITECTURE.md` (duplication retirée) ;
- **contenu de recherche technique très détaillé de `NOTES_CARTOGRAPHIE.md` non repris tel quel** (conventions de nommage des icônes SHOM, points d'accès WFS, structure des attributs S-57...) : déjà documenté à l'endroit le plus utile, directement dans le code source (`sara_route_manager/shom_icons.py`), pas dupliqué dans un document séparé ;
- toutes les références corrigées : `README.md`, `ROADMAP.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md`, `docs/THIRD_PARTY_LICENSES.md`, `tests/test_release_completeness.py`, et les commentaires de code faisant référence à `NOTES_CARTOGRAPHIE.md` (`webapp.py`, `models.py`, `static/js/unified_editor.js`, `static/js/map.js`), redirigés vers `docs/SPECIFICATIONS.md` ;
- paramètre de cache-busting bumpé à `v='0.7.1.25'` sur tous les scripts de toutes les pages (commentaires modifiés dans deux fichiers JS).

**Racine du projet désormais réduite à l'essentiel** : `README.md`, `LICENSE.md`, `CONTRIBUTING.md`, `CHANGE_LOG.md`, `ROADMAP.md`, plus les `.bat` et fichiers de métadonnées. `docs/` contient 6 fichiers : `USER_GUIDE.md`, `SPECIFICATIONS.md`, `ARCHITECTURE.md`, `RACCOURCIS_CLAVIER.md`, `RELEASE_NOTES.md`, `THIRD_PARTY_LICENSES.md`.

## Non publié — groupe 5 (phase E), audit d'hygiène du dépôt (3/3) : restructuration en docs/

- **6 fichiers déplacés vers `docs/`** (rejoignent `docs/USER_GUIDE.md` déjà présent) : `ARCHITECTURE.md`, `DEVELOPPEMENT.md`, `RACCOURCIS_CLAVIER.md`, `SPECIFICATIONS.md`, `THIRD_PARTY_LICENSES.md`, `RELEASE_NOTES.md` — pour ne garder à la racine que ce que GitHub traite spécialement (`README.md`, `LICENSE.md`, `CONTRIBUTING.md`) et ce qui doit rester immédiatement visible/accessible en double-clic pour un utilisateur Windows (les `.bat`), plutôt qu'un mur de 13 fichiers `.md` avant même d'apercevoir le code ;
- `CHANGE_LOG.md` et `ROADMAP.md` restent à la racine (le premier par convention largement répandue, le second en tant que document de pilotage du projet, pas de la documentation utilisateur/contributeur) ;
- toutes les références corrigées : `README.md`, `CONTRIBUTING.md`, `LICENSE.md`, `sara_route_manager/webapp.py` (cible d'ouverture des raccourcis clavier), `sara_route_manager/templates/about.html`, `docs/ARCHITECTURE.md` (référence interne simplifiée en chemin relatif), `tests/test_release_completeness.py` — au passage, une référence oubliée à l'ancien `DELIVERY_MANIFEST.txt` (supprimé précédemment) retirée de `CONTRIBUTING.md`, et une entrée dupliquée de `THIRD_PARTY_LICENSES.md` nettoyée dans la liste des fichiers obligatoires ;
- paramètre de cache-busting bumpé à `v='0.7.1.24'` sur tous les scripts de toutes les pages (modification d'`about.html`).

`NOTES_CARTOGRAPHIE.md` reste à la racine, son sort (suppression envisagée, carnet de travail interne largement dépassé par `ROADMAP.md`) toujours en discussion avec l'utilisateur.

## Non publié — groupe 5 (phase E), audit d'hygiène du dépôt (2/3) : fusion ACCESSIBILITE.md

- **`ACCESSIBILITE.md` supprimé, contenu réparti selon le public concerné** — redondance identifiée avec `RACCOURCIS_CLAVIER.md` sur 3 points (navigation générale, boîte de dialogue modale, panneau d'informations sur le point), et publics différents (l'un utilisateur, l'autre développeur) :
  - contenu pratique déjà couvert par `RACCOURCIS_CLAVIER.md`, rien à y ajouter ;
  - contenu technique/architectural (hiérarchie des titres par page, implémentation des zones F6, motifs ARIA) fusionné dans `ARCHITECTURE.md`, nouvelle section « Accessibilité — implémentation », mise à jour au passage (page Configuration à jour avec ses sous-titres, section « Boîtes de dialogue modales » corrigée : elle affirmait à tort qu'une seule existait, il y en a désormais trois) ;
- 3 références corrigées (`README.md`, `CONTRIBUTING.md`, `tests/test_release_completeness.py`).

## Non publié — groupe 5 (phase E), audit d'hygiène du dépôt (1/3)

- **3 fichiers obsolètes supprimés**, repérés en préparation de la publication GitHub :
  - `DELIVERY_MANIFEST.txt` : instantané de la liste des fichiers figé à la version 0.6.12, redondant avec ce que Git fait déjà nativement ;
  - `TEST_RESULTS.txt` : instantané figé à « 26 tests réussis » (0.6.12, on en est à 207 aujourd'hui), redondant avec `CHANGE_LOG.md` ;
  - `VALIDATION.md` : contenu par ailleurs utile (tests manuels réels sous NVDA), mais jugé sans utilité par l'utilisateur au même titre que les deux précédents ;
- référence à `DELIVERY_MANIFEST.txt` retirée de la procédure décrite dans `DEVELOPPEMENT.md` ;
- aucune donnée personnelle (chemin utilisateur, identifiant) trouvée ailleurs dans le dépôt lors de cet audit.

## Non publié — section « Avertissement » dans l'onglet À propos

- **nouvelle section « Avertissement »**, juste après « Licence » : dégagement de responsabilité (logiciel livré « en l'état », sans procédure qualité formelle), sur un texte rédigé avec l'utilisateur, ton clair et volontairement un peu léger sur la fin ;
- même motif d'accessibilité que les autres sections (zone F6, titre focusable) ;
- paramètre de cache-busting bumpé à `v='0.7.1.23'` sur tous les scripts de toutes les pages ;
- 1 test dédié ajouté.

## Non publié — groupe 4, dernier point : licence

- **fichier `LICENSE.md` créé à la racine du projet**, une seule section pour le code (GPL-3.0-only) et une pour la documentation (CC BY-SA 4.0), texte court avec renvoi vers les textes légaux complets — pas les textes intégraux recopiés (simplifié après discussion : un seul fichier avec deux sections, pas deux fichiers séparés) ;
- **section « Licence » ajoutée dans l'onglet À propos**, même motif d'accessibilité que les autres sections (zone F6, titre focusable) ;
- **textes légaux complets accessibles par bouton**, ouverts dans le navigateur système via `/api/open-path` — jamais par un lien direct `target="_blank"`, qui ouvrirait une fenêtre pywebview sans barre d'adresse ni bouton retour (même contrainte déjà établie pour le lien Orion Brest) ;
- paramètre de cache-busting bumpé à `v='0.7.1.22'` sur tous les scripts de toutes les pages ;
- 6 tests dédiés ajoutés.

**Le groupe 4 est maintenant intégralement terminé (7/7 points).**

## Non publié — correctifs après second test réel de la boîte de dialogue d'informations

- **affichage sur une seule ligne corrigé** : les retours à la ligne du texte (Nom/Type/Source) étaient ignorés par le navigateur, tout s'affichait sur une seule ligne malgré un contenu logique correctement structuré (utilisé tel quel pour la copie presse-papiers). Corrigé avec `white-space: pre-line` sur la zone de description, qui restitue visuellement les 3 lignes ;
- **annonce au survol enrichie** : indique désormais le type précis (direction cardinale, côté latéral), comme la boîte de dialogue au double-clic — signalé après un premier essai incomplet (seul le nom était annoncé) ;
- paramètre de cache-busting bumpé à `v='0.7.1.21'` sur tous les scripts de toutes les pages ;
- 1 test dédié ajouté, 1 test mis à jour.

## Non publié — ajustements de la boîte de dialogue d'informations sur une marque

- **format latéral aligné sur le format cardinal** : « Latérale bâbord »/« Latérale tribord » (sans parenthèses), cohérent avec « Cardinale Nord »/« Cardinale Sud »/« Cardinale Est »/« Cardinale Ouest » ;
- **ordre des lignes réorganisé** : Nom, puis Type, puis Source (demandé explicitement) ;
- paramètre de cache-busting bumpé à `v='0.7.1.20'` sur tous les scripts de toutes les pages ;
- 1 test mis à jour.

## Non publié — correctif : type de marque précisé (direction cardinale, côté latéral)

- **bug corrigé, repéré après retour utilisateur** : la boîte de dialogue d'informations sur une marque affichait seulement la catégorie générale (« Cardinale », « Latérale »), sans la direction (Nord/Est/Sud/Ouest) ni le côté (bâbord/tribord) — l'information la plus utile en pratique manquait. Corrigé en déduisant cette précision du nom de fichier de l'icône déjà résolue côté serveur (`shom_icons.py`), sans requête supplémentaire ;
- s'applique aussi bien aux points de la route qu'aux marques SHOM environnantes ;
- paramètre de cache-busting bumpé à `v='0.7.1.19'` sur tous les scripts de toutes les pages ;
- 1 test dédié ajouté, 1 test mis à jour.

## Non publié — groupe 4 (3/3) : boîte de dialogue au double-clic sur une marque

- **double-clic sur un point de route ou une marque SHOM** : ouvre une boîte de dialogue accessible affichant le nom, la source (« Point de la route » ou « Marque SHOM environnante ») et le type (Latérale, Cardinale, Danger isolé...) — même structure que la boîte de dialogue de mesure déjà en place (`role="alertdialog"`, focus initial sur le bouton « Copier », piège de focus Tab/Maj+Tab, Échap pour fermer) ;
- bouton « Copier » : copie le nom, la source et le type dans le presse-papiers, avec annonce NVDA ;
- paramètre de cache-busting bumpé à `v='0.7.1.18'` sur tous les scripts de toutes les pages ;
- 2 tests dédiés ajoutés.

## Non publié — groupe 4 (2/2) : graduations en milles nautiques sur les bords de la carte

- **graduations sur les 4 bords de la carte** (haut, bas, gauche, droite), espacées en milles nautiques réels — l'espacement est rigoureusement identique à la valeur affichée par la barre d'échelle (calcul du pas mutualisé via `computeNiceNauticalStep`, demandé explicitement) : si la barre affiche « 2 Milles », les graduations se répètent tous les 2 milles, quelle que soit l'échelle de la carte ;
- graduations verticales (haut/bas) espacées selon la longitude, horizontales (gauche/droite) selon la latitude, avec conversion correcte de la distance réelle en degrés à la latitude courante (les méridiens se rapprochant aux hautes latitudes) ;
- reconstruites à chaque déplacement/zoom, comme la grille latitude/longitude déjà en place ; superposition en pointeur désactivé, pour ne jamais gêner le zoom/déplacement natif de la carte ;
- paramètre de cache-busting bumpé à `v='0.7.1.17'` sur tous les scripts de toutes les pages ;
- 2 tests dédiés ajoutés.

## Non publié — groupe 4 (1/2) : NM → Milles, Alt+F4, annonce au survol, taille des icônes

- **« NM » remplacé par « Milles »** sur la barre d'échelle de la fenêtre carte — même défaut que celui déjà corrigé ailleurs (NVDA lit « NM » comme « nanomètre »), ajouté après coup lors de la phase B sans reprendre cette correction ;
- **`Alt+F4` intercepté explicitement** en JavaScript pour fermer la fenêtre carte — signalé sans effet malgré la prise en charge native habituelle de Windows, vraisemblablement parce que le contenu web (WebView2) absorbe le raccourci avant qu'il n'atteigne le châssis natif de la fenêtre. Interception en repli, sur le même chemin que le bouton « Fermer » (factorisé dans `closeMapWindow`) ;
- **annonce vocale au survol d'un marqueur** (points de route et marques SHOM), via la zone `#map-status` déjà en place (`aria-live="polite"`), plutôt que de compter sur la fonction native NVDA « Annoncer l'objet sous la souris » (dépend d'un réglage que l'utilisateur doit activer lui-même) ;
- **taille des icônes SHOM configurable** : nouveau réglage `map_marker_size` en page Configuration (10–60 px, défaut 20), remplaçant la valeur figée en dur (20×40 px) dans `map.js` — hauteur et ancrage calculés automatiquement (rapport 1:2 des fichiers SVG officiels, ancre au centre) ;
- paramètre de cache-busting bumpé à `v='0.7.1.16'` sur tous les scripts de toutes les pages ;
- 4 tests dédiés ajoutés, audit de complétude de la Configuration (groupe 3) mis à jour avec le nouveau champ.

## Non publié — correctif : les anciens fichiers config.toml restaient incomplets indéfiniment

- **bug corrigé, repéré après signalement** : un fichier `config.toml` créé avant l'ajout de réglages plus récents (SHOM, fenêtre carte, couleurs, tracé, étiquettes...) restait incomplet indéfiniment tant qu'un clic explicite sur « Enregistrer » n'avait pas eu lieu dans la page Configuration — `load()` ne réenregistrait automatiquement que si le fichier était totalement absent, jamais pour compléter un fichier existant mais devenu obsolète ;
- corrigé en réenregistrant systématiquement après chargement : un vieux fichier se complète désormais tout seul au prochain démarrage, sans rien perdre de ce qui existait déjà (`save()` préserve toujours l'existant, complète seulement les sections manquantes avec leurs valeurs par défaut) ;
- paramètre de cache-busting bumpé à `v='0.7.1.15'` sur tous les scripts de toutes les pages ;
- 1 test dédié ajouté, avec un fichier reproduisant exactement le cas signalé.

## Non publié — groupe 3 : titres hiérarchiques, audit de complétude, export/import de configuration

- **titres hiérarchiques** : la zone « Fenêtre de visualisation cartographique » (9 champs) est découpée en 4 sous-titres `<h3>` (Taille de la fenêtre, Couleurs, Tracé de route, Étiquettes des points de route), pour naviguer rapidement au clavier (touche H de NVDA) entre ces groupes ;
- **audit de complétude effectué** : les 19 réglages de la page Configuration ont été vérifiés un par un (HTML → JS → Python `to_dict()`/`update_settings()` → TOML) — aucun oubli trouvé. Un test dédié verrouille cette complétude pour l'avenir ;
- **export/import du fichier de configuration** : deux nouveaux boutons, sur le modèle déjà utilisé pour l'import de route (champ de fichier visible + bouton séparé) et pour la confirmation avant remplacement (même motif que « Rétablir la configuration par défaut ») ;
  - export : nouvel endpoint `/api/configuration/export`, sert le fichier réellement enregistré sur disque (pas d'éventuelles modifications du formulaire non encore enregistrées) ;
  - import : nouvel endpoint `/api/configuration/import`, upload multipart, rejette proprement un fichier qui n'est pas du TOML valide ;
  - **dossier « sauvegardes » (`backups_directory`) enfin utilisé** : configuré depuis le début du projet mais jamais exploité jusqu'ici, choisi comme dossier initial des deux dialogues plutôt que « routes » (spécifique aux fichiers de route) — `save_file()` accepte désormais un paramètre `directory_kind` pour ça, avec repli sur le comportement historique (« routes ») pour tous les autres exports ;
- paramètre de cache-busting bumpé à `v='0.7.1.14'` sur tous les scripts de toutes les pages ;
- 9 tests dédiés ajoutés (audit de complétude + export/import + structure de titres).

## Non publié — correctif : Tab entre champs modifiables sautait vers le titre de la page

- **bug corrigé, repéré après un second retour utilisateur précis (relevé NVDA à l'appui)** : poser le focus sur le champ suivant (ex. Latitude) **avant** que la perte de focus du champ actuel (Nom) ne se déclenche provoquait la reconstruction du panneau — détruisant le champ visé, à peine focalisé, avant que le focus ne s'y pose réellement. Le focus se retrouvait nulle part précis, et NVDA annonçait le titre de la page en repli. Corrigé en inversant l'ordre : déclencher explicitement la perte de focus du champ actuel en premier, puis reposer le focus sur le bon champ dans le panneau reconstruit, retrouvé par une nouvelle recherche depuis le conteneur stable `#point-details` plutôt qu'une référence devenue obsolète après reconstruction ;
- 1 test dédié ajouté.

## Non publié — correctifs après test réel du panneau « Informations sur le point »

- **bug corrigé** : Tab depuis un champ modifiable (ex. « Nom ») nécessitait deux appuis pour atteindre réellement le champ suivant, avec une annonce intermédiaire surprenante. Cause probable : l'input avait un tabindex implicite (0), mélangé au tabindex mobile de la ligne (0/-1 selon la ligne active) — un ordre de tabulation ambigu selon le navigateur/lecteur d'écran. Corrigé en gérant Tab explicitement en code plutôt que de compter sur l'ordre naturel du navigateur : l'input est retiré de l'ordre natif (`tabIndex = -1`), Tab depuis un champ modifiable saute directement au suivant (ou sort du panneau si c'est le dernier) ;
- **libellé clarifié** : « Distance de validation » devient « Distance de validation (mètre) », pour préciser l'unité attendue ;
- 2 tests mis à jour, 1 test ajouté.

## Non publié — groupe 2 (phase D) : panneau « Informations sur le point » éditable

Refonte complète du panneau, en détail avec l'utilisateur avant implémentation :

- **navigation par flèches haut/bas, ligne par ligne** : chaque ligne (couple libellé/valeur) est un élément focusable individuellement, avec un `aria-label` couvrant tout le couple — une seule unité de lecture NVDA par ligne, y compris sur une ligne modifiable. Pas de bouclage aux extrémités (reste sur place) ;
- **champs modifiables** (Nom, Latitude, Longitude, Distance de validation), accessibles par `Tab` depuis la ligne, encadrés d'un trait fin et contrasté (`border:1px solid currentColor`) ; NVDA sait déjà nativement y sauter avec la touche « E » en mode navigation (comportement natif des champs de texte, rien à coder pour ça) ;
- **modification uniquement pour les points déjà ajoutés à la route** — un point encore dans « Points importés » n'a pas encore sa place définitive, reste entièrement en lecture seule ;
- **case « Homme à la mer » retirée du plan initial** : n'a pas de sens en composition de route (tranché explicitement avec l'utilisateur) — la Distance de validation reste un simple champ numérique borné 1–1000 m ;
- **validation à la perte de focus** : latitude/longitude hors bornes ou rayon hors 1–1000 m sont refusés (ancienne valeur reprise, annonce d'erreur) plutôt qu'acceptés tels quels ; un nom vide retombe sur « Point sans nom » plutôt que d'être refusé ;
- **raccourci `Alt+E`** ajouté, saute directement dans le champ Nom ;
- **le focus n'est repris sur la première ligne qu'en cas de reconstruction pendant que l'utilisateur naviguait déjà dans le panneau** (nouvelle sélection dans la liste) — jamais lors d'une reconstruction déclenchée par une perte de focus, pour ne pas voler le focus à l'utilisateur ;
- `RACCOURCIS_CLAVIER.md` complété : `Alt+C`/`Alt+Maj+C` étaient déjà codés mais absents de la documentation, ajoutés en même temps que `Alt+E` ;
- paramètre de cache-busting bumpé à `v='0.7.1.11'` sur tous les scripts de toutes les pages ;
- 17 tests dédiés réécrits pour la nouvelle structure.

## Non publié — groupe 1 : navigation clavier dans les listes, ouverture par double-clic

- **bug corrigé** : la navigation par flèches haut/bas ne fonctionnait qu'après un clic souris préalable dans une liste. Cause identifiée : `selectedIndex` restait à -1 (aucune option choisie) tant qu'aucune interaction n'avait eu lieu, privant les flèches de tout point de départ. Corrigé en sélectionnant automatiquement le premier élément au premier focus clavier, si aucune sélection n'existe encore — dans les listes de points de l'éditeur (Points importés, Points de la route) et les 3 listes de routes de la Bibliothèque ;
- **double-clic ajouté** pour ouvrir directement une route depuis la Bibliothèque (personnelle, communautaire, locale), en plus du raccourci clavier Entrée déjà en place (pas besoin de l'ajouter, seul le double-clic manquait) ;
- code du bouton d'ouverture associé à chaque liste factorisé (`openButtonIdFor`), réutilisé par le double-clic et par Entrée ;
- paramètre de cache-busting bumpé à `v='0.7.1.10'` sur tous les scripts de toutes les pages ;
- 4 tests dédiés ajoutés.

## Non publié — réglages du tracé de route et des étiquettes de points

- **5 nouveaux réglages en page Configuration** : épaisseur du tracé (1–10 px), type de trait (continu/tireté/pointillé), affichage par défaut des étiquettes de points de route, taille du texte des étiquettes (8–24 px), encadrement ou non des étiquettes ;
- **case à cocher « Afficher les étiquettes des points de route » ajoutée en direct dans la fenêtre carte**, en plus du réglage par défaut en Configuration — exception volontaire à l'option A, demandée explicitement : le rendu par défaut (texte trop grand, encadrés qui masquent des éléments de la carte) justifiait un accès rapide sans repasser par la Configuration à chaque fois ;
- les étiquettes de points de route ont désormais leur propre classe CSS (`route-point-tooltip`), distincte de celle des marques SHOM (`mark-tooltip`), pour que leur taille et leur encadrement restent réglables indépendamment ;
- mode « sans encadrement » : texte blanc avec contour sombre pour rester lisible sur tous les fonds, plutôt qu'un encadré retiré sans rien pour le remplacer ;
- l'export SVG respecte désormais l'épaisseur, le style, la visibilité et la taille des étiquettes ;
- paramètre de cache-busting bumpé à `v='0.7.1.9'` sur tous les scripts de toutes les pages ;
- 10 tests dédiés ajoutés.

## Non publié — couleur du tracé jaune vif, option A pour l'organisation des couleurs

- **couleur du tracé de route changée pour un jaune vif (`#ffe600`)**, remplaçant l'orange initial signalé insuffisamment contrasté sur le fond de mer — nouveau réglage `map_route_color` en page Configuration, même mécanisme que les couleurs mer/terre existantes ;
- **option A retenue** pour l'organisation des réglages d'affichage de la carte (discutée avec l'utilisateur, 3 options proposées) : les couleurs (mer, terre, tracé) sont des préférences durables, réglables **uniquement en page Configuration** — les deux sélecteurs de couleur qui figuraient un temps directement dans la fenêtre carte sont retirés, pour ne pas la surcharger. La fenêtre carte ne garde que les réglages « à la volée » (grille, outil de mesure, filtre de marques) ;
- paramètre de cache-busting bumpé sur tous les scripts de toutes les pages (`v='0.7.1.8'`), pour éviter toute confusion avec le cache persistant de WebView2 découvert précédemment ;
- 4 tests dédiés ajoutés/mis à jour.

## Non publié — cause probable de plusieurs correctifs « sans effet » : cache disque persistant de WebView2

- **découverte importante** : le paramètre de cache-busting `v=` sur tous les scripts (toutes les pages, pas seulement la carte) était resté figé à `0.7.1.0` depuis la grosse bascule de version, alors que 6 livraisons différentes du code avaient suivi. Contrairement à un onglet de navigateur classique, **WebView2 conserve un cache disque persistant qui survit à la fermeture complète de l'application** — avec une URL de script identique, aucune raison de retélécharger le fichier. Explique vraisemblablement pourquoi certains correctifs (dont celui de la case « Afficher les noms des marques ») semblaient sans effet malgré un code corrigé ;
- **corrigé sur deux plans** : le paramètre `v=` de tous les scripts de toutes les pages bumpé à `0.7.1.7` ; ajout de `SEND_FILE_MAX_AGE_DEFAULT = 0` côté Flask, qui force une revalidation systématique de tous les fichiers statiques (JS, CSS) — une protection structurelle, en complément du paramètre `v=` qu'il reste nécessaire d'incrémenter à chaque modification ;
- 2 tests dédiés ajoutés, vérifiant l'en-tête `Cache-Control: no-cache` sur un script et une feuille de style.

**Si le problème persistait malgré tout** après cette correction, il faudrait envisager de vider manuellement le cache WebView2 de l'application (dossier de données utilisateur du composant WebView2, propre à l'application) en dernier recours.

## Non publié — correction : la case « Afficher les noms des marques » n'avait aucun effet

- **bug corrigé, la vraie cause** : les infobulles des marques SHOM n'étaient pas permanentes (`permanent: true` absent, contrairement aux points de la route), donc jamais visibles par défaut — cocher/décocher la case n'avait alors aucun effet observable, faute de label à masquer. Ajout de `permanent: true` ;
- **second problème corrigé au passage** : la case des noms de marques vivait dans le même `<fieldset>` que les 7 cases de catégorie, et se retrouvait happée sans le vouloir par le sélecteur générique du filtre par catégorie (sans planter grâce à une protection déjà en place, mais un comportement non voulu). Les 7 cases de catégorie reçoivent désormais une classe CSS distincte (`marks-category-checkbox`), et le filtre cible précisément cette classe ;
- 2 tests de non-régression ajoutés.

## Non publié — phase C : outil de mesure distance/cap entre deux points

- **case à cocher « Activer l'outil de mesure »** : une fois activée, désactive le déplacement normal de la carte au clic-glisser (le même geste sert désormais à tracer un segment de mesure) et affiche un curseur en croix ;
- cliquer un premier point, maintenir le bouton enfoncé, glisser vers un second point (un trait pointillé blanc suit la souris), relâcher pour afficher la distance et le cap vrai initial du segment dans une boîte de dialogue accessible (`role="alertdialog"`, focus initial sur le bouton « Copier », piège de focus Tab/Maj+Tab, Échap pour fermer — même motif que la boîte de dialogue « modifications non enregistrées » de l'éditeur) ;
- bouton « Copier » : copie le résultat dans le presse-papiers et l'annonce à NVDA ;
- réutilise `segmentDistanceNm`/`segmentInitialBearing` (`route_math.js`), déjà mutualisées avec l'analyse de route et l'export CSV des segments — pas un second calcul dupliqué ;
- un simple clic sans glisser (segment quasi nul) n'ouvre pas la boîte de dialogue ;
- 6 tests dédiés ajoutés.

## Non publié — phase B : couleurs configurables, grille, échelle, noms de marques (map)

- **couleurs de la carte configurables** : deux nouveaux réglages `map_sea_color`/`map_land_color` en page Configuration (validés au format hexadécimal), plus deux sélecteurs de couleur directement dans la fenêtre carte pour un ajustement en direct sans recharger ;
- **bug anticipé et corrigé au passage** : les champs `type="number"` et `type="color"` héritaient d'une règle CSS générique prévue pour les champs texte (`width:34rem`), le même défaut que celui corrigé pour les cases à cocher lors de la livraison précédente. Tailles dédiées ajoutées avant qu'il ne pose réellement problème ;
- **grille latitude/longitude** : case à cocher « Afficher la grille », pas de « rond » (0,01° à 10°) calculé selon l'étendue visible, avec étiquettes de graduation ; reconstruite à chaque activation plutôt que suivie en direct du déplacement/zoom ;
- **barre d'échelle en milles nautiques**, en bas à droite de la carte : contrôle Leaflet personnalisé, le contrôle natif ne proposant que kilomètres/miles terrestres ;
- **case à cocher « Afficher les noms des marques »** (proposée en cours de route) : masque uniquement les étiquettes des marques SHOM environnantes, jamais celles des points de la route elle-même (toujours nécessaires au repérage) ;
- 12 tests dédiés ajoutés.

## Non publié — correctifs après nouveau test manuel (filtre de marques, densité des étiquettes)

- **bug corrigé, repéré sur capture d'écran réelle** : les cases à cocher du filtre de marques SHOM n'étaient pas visibles — elles héritaient de la règle générique `input{width:34rem}` prévue pour les champs texte, faute d'utiliser la classe `.checkbox` déjà établie dans l'application (voir `configuration.html`). Corrigé en reprenant cette même structure (`<div class="checkbox"><input><label for="..."></label></div>`) ;
- taille des étiquettes de la carte (`.leaflet-tooltip`) et du filtre de marques réduite (respectivement à 0,75 rem et 0,85 rem, contre 1,1 rem hérité), pour limiter le chevauchement dans les secteurs denses — n'élimine pas complètement le chevauchement dans les cas les plus denses, le zoom molette reste nécessaire pour les démêler entièrement ;
- 2 tests de non-régression ajoutés.

## Non publié — persistance du type IALA dans le format de sauvegarde local (phase A, étape 3, option B)

- **`Waypoint`** (`models.py`) a un nouveau champ `object_code`, conservé par `to_local_dict()`/`from_local_dict()` mais **jamais** inclus dans `to_sara_dict()` — le format échangé avec SARA Navigation reste strictement inchangé, par choix de conception assumé (voir `NOTES_CARTOGRAPHIE.md`) ;
- **`SaraRoute.from_local_dict()`** ajoutée, complétant `to_local_dict()` qui existait déjà mais n'était pas exploitée ; **`storage.py`** l'utilise désormais pour charger une route locale, au lieu de `from_sara_dict()` ;
- **client** (`unified_editor.js`) : `normalize()` conserve `object_code`, pour qu'il survive de la sélection d'une marque SHOM jusqu'à l'enregistrement ;
- **fenêtre carte** : `/api/map/data/<jeton>` calcule désormais l'icône IALA de chaque point de la **route elle-même** (pas seulement des marques environnantes affichées en contexte), et `map.js` l'utilise à l'affichage, avec repli sur le cercle rouge générique pour un point sans type d'origine (saisie manuelle, ou route reçue de SARA Navigation — comportement attendu, pas une erreur) ;
- 13 tests dédiés, dont 3 tests d'intégration avec de vrais fichiers sur disque (`test_storage.py`, nouveau).

## Non publié — affichage des marques SHOM sur la carte (phase A, étape 2)

- nouvel endpoint `/api/map/marks/<jeton>` : interroge le WFS Orion sur l'emprise de la route (centre + rayon dérivés des points, marge de contexte de 20 %), indépendamment de ce qui a pu être recherché pendant la composition de la route dans l'éditeur — même principe que le trait de côte, pas de synchronisation d'état entre les deux fenêtres ;
- chaque marque reçoit le nom du fichier d'icône SHOM correspondant (`shom_icons.py`), ou `None` si aucune correspondance fiable n'existe ;
- **53 icônes SVG officielles du SHOM vendues localement** dans `static/vendor/shom_icons/` (Licence Ouverte 2.0, citation « Shom, 2023. Balisage maritime ») ;
- affichage des marques sur la carte Leaflet : icône officielle si disponible, cercle générique gris en repli sinon ; ancrées au centre (200×400 px), pas en bas comme un marqueur classique ;
- **filtre par cases à cocher** (Latérales, Cardinales, Danger isolé, Eaux saines, Marques spéciales, Amers, Autres), un calque Leaflet par catégorie, affiché/masqué sans reconstruire les marqueurs ;
- un échec de cette requête ne bloque jamais l'affichage déjà réussi de la route et du trait de côte — les marques restent un complément visuel ;
- 4 nouveaux tests pour l'endpoint, 3 pour le rendu côté client, réseau entièrement simulé.

**Avertissement important, comme pour le trait de côte** : l'extraction de la catégorie latérale/cardinale et de la présence d'un voyant depuis les propriétés brutes du WFS Orion (`Category of lateral mark`, `Category of cardinal mark`, attribut `topmar`) repose sur des hypothèses de format non vérifiées en direct (accès réseau limité pendant le développement) — voir `shom_icons.py`. À confirmer sur un poste avec accès réseau réel.

## Non publié — module de sélection d'icônes IALA du SHOM (phase A, étape 1)

- nouveau module `shom_icons.py` : sélectionne le nom du fichier SVG officiel du SHOM à partir des attributs S-57 d'une marque (code d'objet, catégorie latérale/cardinale, présence d'un voyant, région IALA) ;
- convention de nommage établie en inspectant directement les 53 fichiers du paquet officiel « Balisage maritime » (voir `NOTES_CARTOGRAPHIE.md`) ;
- renvoie `None` (repli sur un marqueur générique) plutôt que d'inventer un nom de fichier lorsqu'aucune correspondance fiable n'existe — notamment pour une marque cardinale/latérale sans catégorie connue, ou une balise latérale sans voyant en région IALA B (variante absente du jeu officiel) ;
- fonction `is_iala_region_b()` : détection approximative de la région IALA par zone géographique (Antilles, Guyane, Saint-Pierre-et-Miquelon en région B ; reste des territoires français en région A), en repli si l'information n'est pas directement disponible dans les propriétés de la marque ;
- 13 tests dédiés, contre les noms de fichiers réels confirmés.

## 0.7.0 — 30 juillet 2026

### correction d'une coquille : largeur de la fenêtre principale

- la largeur par défaut de la fenêtre principale était fixée à 58 % suite à une erreur de frappe de l'utilisateur dans sa demande initiale ; corrigée à **90 %** (hauteur inchangée à 80 %).

### dimensionnement et centrage réels de la fenêtre principale

- **la fenêtre principale n'avait jusqu'ici aucun dimensionnement configurable ni centrage réel** : taille fixe 1200×850 sans position explicite, malgré ce qui avait été décidé précédemment. Corrigé : mêmes pourcentages configurables que pour la fenêtre carte (nouveaux réglages « Fenêtre principale » dans la page Configuration, 58 % de largeur × 80 % de hauteur par défaut), avec centrage automatique et la même marge de sécurité de 5 % ;
- **hauteur par défaut de la fenêtre carte corrigée à 80 %** (au lieu de 90 %), sur demande explicite de l'utilisateur, en raison du bandeau des tâches Windows ;
- ajout de tests de non-régression dédiés (persistance TOML, bornes 50–100, dimensionnement/centrage) pour les deux fenêtres.

### resserrement de l'espace entre le titre et le résumé

- **bug corrigé, repéré sur capture d'écran réelle** : la marge par défaut du navigateur sur le H1 (habituellement environ 0,67em en haut et en bas) laissait un grand espace visible avant le résumé (nombre de points, distance) juste en dessous. Marge resserrée explicitement ;
- ajout d'un test de non-régression dédié ;
- **taille de fenêtre carte toujours en cours d'investigation** : le débordement à droite/en bas persiste après la marge de 5 % ajoutée précédemment. Hypothèse en cours de vérification avec l'utilisateur : la fenêtre carte a pu être rechargée (`load_url`) plutôt que recréée lors du test (l'application n'aurait alors pas été complètement relancée entre deux tests), auquel cas elle garde la taille de sa toute première ouverture sans recalcul. Résolution reportée en attente de confirmation.

### marge de sécurité proportionnelle et retour à la ligne des boutons

- **la compensation fixe (40 px / 16 px) s'est révélée insuffisante** lors d'un nouveau test réel : la fenêtre débordait encore de l'écran à droite, alors que la mise à l'échelle Windows était confirmée à 100 % (donc pas un problème de DPI). Remplacée par une **marge de sécurité proportionnelle de 5 %** appliquée directement sur les pourcentages configurés, plus simple et qui s'adapte à la taille de l'écran plutôt qu'un nombre de pixels fixe ;
- le texte des boutons de la colonne latérale peut désormais **revenir à la ligne** (`white-space: normal`) si un libellé est trop long pour la largeur de la colonne, plutôt que de risquer un débordement ;
- tests de non-régression mis à jour/ajoutés en conséquence.

### 4 corrections de la fenêtre carte après nouveau test manuel

- **bug corrigé, cause confirmée via la documentation de pywebview** (issue #1432 du dépôt officiel) : sous Windows, `width`/`height` passés à `create_window` correspondent à la zone de contenu de la fenêtre, pas à la fenêtre entière — la barre de titre et les bordures ajoutées par le système ne sont pas comptées. Sans compensation, la fenêtre réelle débordait de l'écran en bas et à droite alors que son coin haut-gauche restait correct, exactement le défaut observé. Ajout d'une compensation estimée (40 px de hauteur, 16 px de largeur), le centrage se basant désormais sur la taille finale visée plutôt que sur la zone de contenu compensée ;
- **colonne de boutons élargie** (12 → 16 rem) avec plus d'espace par rapport à la carte (1 → 1,5 rem) ;
- **bandeau d'en-tête retiré** (« SARA Route Manager » / « Carte de la route ») : cette fenêtre n'a pas de menu de navigation à identifier comme les 5 pages principales, et le titre de la fenêtre Windows porte déjà l'information (déjà annoncé par NVDA). Le H1 (nom de la route) est désormais le premier élément visible, suivi directement du résumé ;
- **petite bande de respiration ajoutée** autour du contenu (1,25 rem de marge intérieure), pour séparer visuellement le cadre de la fenêtre de la carte ;
- ajout de tests de non-régression dédiés pour les 4 points.

### correction visuelle du panneau de détails (2 colonnes)

- **bug corrigé, repéré sur capture d'écran réelle** : sur un libellé long (« Distance de validation »), le texte se coupait juste avant les deux-points, qui se retrouvaient seuls sur une ligne. Remplacé l'espace normale par une espace insécable entre le libellé et les deux-points ;
- confirmation par la même capture que la disposition à 2 colonnes (libellé en gras à gauche, valeur à droite) fonctionne comme prévu ;
- ajout d'un test de non-régression dédié.

### correction de la vraie cause de l'espace perdu

- **bug corrigé, la vraie cause cette fois** : neutraliser `max-width` ne suffisait pas à faire utiliser toute la largeur de la fenêtre carte, confirmé par un test réel montrant un grand espace vide à gauche. Cause : le `margin:auto` de `main.css`, en contexte flexbox (`body` étant `display:flex`), fait qu'un élément se réduit à la largeur de son contenu et se centre au lieu de s'étirer sur toute la largeur disponible — même une fois `max-width` neutralisé. Ajout de `margin:0` et `width:100%` explicites en plus de `max-width:none` ;
- test de non-régression mis à jour pour vérifier les deux propriétés, pas seulement `max-width`.

### quatre correctifs après nouveau test manuel

- **couleur de mer resserrée à un bleu plus soutenu** (`#1f6fa3`, encore plus franc que le `#3f7cb0` précédent) ;
- **panneau « Informations sur le point » restructuré en 2 colonnes visuelles** (libellé à gauche, valeur à droite, alignées) — sans revenir sur le choix d'accessibilité qui réunit libellé et valeur dans un seul `<p>` (une seule unité de lecture NVDA par ligne) : la structure interne utilise deux `<span>` alignés par CSS, pas `dt`/`dd`, qui fragmenterait la lecture en deux annonces distinctes (déjà essayé et abandonné pour cette raison par le passé) ;
- **boutons de la fenêtre carte déplacés à droite** (le côté demandé initialement était une confusion) — géré par CSS `order`, sans changer l'ordre de lecture/tabulation ;
- **pleine largeur de la fenêtre carte restaurée** : la limite `max-width:82rem` de `main.css`, pensée pour la lisibilité des pages de texte, ne s'applique plus à cette fenêtre utilitaire, où l'espace ainsi perdu manquait justement à la carte ;
- ajout de tests de non-régression dédiés pour les quatre points.

### mise en page de la fenêtre carte : boutons en colonne à gauche

- signalé après test : les 3 boutons (export CSV, export SVG, Fermer) étaient parfois masqués en bas de la fenêtre carte, celle-ci étant plus haute que large de contenu ;
- **restructuration en mise en page flexible plein écran** : les 3 boutons sont désormais en colonne à gauche de la carte plutôt qu'empilés en dessous — cohérent avec le fait que les écrans sont en général plus larges que hauts, et laisse à la carte toute la hauteur disponible de la fenêtre ;
- ajout d'un recalcul automatique de la taille de la carte au redimensionnement de la fenêtre (`map.invalidateSize()`), utile maintenant que sa hauteur dépend de la mise en page plutôt que d'une valeur fixe ;
- ajout d'un test de non-régression dédié.

### contraste de la couleur de mer

- couleur de la mer resserrée à un bleu plus soutenu (`#3f7cb0`, auparavant `#dceefb`) sur la carte interactive et l'export SVG, pour un meilleur contraste avec la terre (`#d9c9a3`) — demandé après test visuel ;
- todo list mise à jour dans `NOTES_CARTOGRAPHIE.md` : persistance du type IALA (option B), affichage des marques SHOM sur la carte avec filtre par type, refonte du panneau « Informations sur le point » en tableau à 2 colonnes modifiable, raccourci `Alt+E`.

### résumé de route, unité en toutes lettres, exports CSV/SVG sur la carte

- **bug d'accessibilité corrigé** (repéré sur la fenêtre carte, mais présent aussi dans l'éditeur) : l'abréviation « NM » (milles nautiques) est lue par NVDA comme « nanomètre ». Remplacée par « milles nautiques » en toutes lettres partout où une distance est annoncée (éditeur : « Analyse de la route », étiquettes de points ; carte : nouveau résumé). L'en-tête de colonne CSV `Longueur_NM` reste inchangée (donnée machine, pas lue par un lecteur d'écran) ;
- la fenêtre carte a maintenant un vrai `<h1>` (nom de la route, focusable) au lieu d'un simple paragraphe, avec un résumé juste en dessous : nombre de points et distance totale en milles nautiques ;
- nouveau module partagé `route_math.js` (distance orthodromique, cap initial, construction des segments, lignes CSV), chargé globalement depuis `base.html` : mutualise ce qui existait auparavant en double dans `unified_editor.js`, et le rend disponible pour la fenêtre carte ;
- ajout du bouton « Exporter les segments en CSV » dans la fenêtre carte, identique à celui de l'éditeur ;
- ajout du bouton « Exporter la carte en SVG » dans la fenêtre carte : reconstruit sa propre projection à partir des données déjà en mémoire (points, trait de côte), plutôt que d'extraire le rendu interne de Leaflet — évite toute dépendance aux transformations CSS de positionnement de Leaflet, qui varient selon l'état de défilement ;
- ajout du type de fichier SVG à `file_dialogs.js` (`exportFileTypes`) ;
- ajout de tests de non-régression dédiés.

**Point resté sans réponse ferme, remis en discussion** : la question de savoir si les points de route peuvent conserver une information de type IALA (bâbord/tribord/cardinale...) après enregistrement/réouverture, nécessaire pour l'étape 3 (icônes). Confirmé que le format d'échange avec SARA Navigation (`CoursePoint`) ne prévoit pas ce champ, par choix de conception cohérent avec son usage — piste retenue : étendre uniquement le format de sauvegarde locale (pas celui envoyé à SARA), à trancher avant l'étape 3.

**Autre sujet identifié, non encore traité** : aucune interface ne permet de modifier le seuil de validation (`distance_threshold`) d'un point — toujours 100 m par défaut ou valeur importée telle quelle. Un champ éditable est envisagé (bornes 1–1000 m, avec un contrôle séparé pour le cas spécial « Homme à la mer » à 0 m, plutôt qu'une simple saisie numérique libre).

### protection contre le mode Contraste élevé de Windows

- **confirmé fonctionnel** lors d'un test réel (île de Groix) : la couche Limite terre-mer répond correctement avec les paramètres devinés (nom de couche, `SRSNAME=EPSG:4326`), affichage terre/mer et bandeau de citation corrects du premier coup ;
- ajout de `forced-color-adjust: none` sur le conteneur de la carte : les couleurs de la carte (mer, terre, tracé, points) codent une information réelle et ne doivent pas être remplacées par la palette système lorsque le mode Contraste élevé de Windows est actif — signalé comme exigence par l'utilisateur, qui utilise ce mode ;
- ajout d'un test de non-régression dédié.

### étape 2 (partie 2) : trait de côte via WFS

- nouveau module `coastline.py` : récupération du trait de côte auprès du WFS officiel du SHOM (`services.data.shom.fr/INSPIRE/wfs`), avec repli automatique **Limite terre-mer → HISTOLITT** si la première ne renvoie aucune entité (nécessaire pour l'outre-mer) ;
- nouvel endpoint `/api/map/coastline/<jeton>` : calcule l'emprise géographique de la route (avec une marge de contexte de 20 %) et sert le trait de côte correspondant ;
- affichage du trait de côte en couche superposée sur la carte Leaflet (terre en beige, par-dessus le fond bleu) ;
- bandeau de citation sous la carte, avec le texte exact exigé par la fiche de métadonnées de chaque couche ; pour HISTOLITT, ajout obligatoire des logos IGN et SHOM avec liens, conformément à la licence (contrainte absente pour Limite terre-mer, simple citation textuelle) ;
- **un échec de cette requête ne bloque jamais l'affichage des points de la route**, qui reste l'essentiel : le trait de côte demeure un complément visuel ;
- ajout de tests dédiés (`test_coastline.py`, réseau entièrement simulé — aucun appel WFS réel pendant les tests automatisés).

**Avertissement important** : le nom de la couche « Limite terre-mer » a été vérifié via la fiche de métadonnées officielle du SHOM. Celui d'HISTOLITT (`TCH_FRA:trait_de_cote_histolitt`) est une **meilleure estimation, non confirmée** faute d'accès réseau réel pendant le développement — à vérifier sur un poste ayant un accès réel au service (voir `coastline.py`).

### étape 2 (partie 1) : bascule sur Leaflet

- la fenêtre carte utilise désormais Leaflet.js (1.9.4) pour le rendu, à la place du SVG fait main de l'étape 1 : zoom à la molette et déplacement au clic-glisser sont natifs, sans code supplémentaire ;
- Leaflet est **vendu localement** dans `static/vendor/leaflet/` (JS, CSS, images, licence BSD 2-Clause), récupéré via le paquet npm officiel — jamais chargé depuis un CDN, cohérent avec le principe de ne dépendre d'aucun serveur externe en continu ;
- création de `THIRD_PARTY_LICENSES.md`, qui recense les ressources externes intégrées (Leaflet, et les données/icônes SHOM à venir) avec leur licence et citation exigée ;
- le cadrage automatique sur le tracé utilise `map.fitBounds()` avec une marge asymétrique (plus large à droite, pour les étiquettes de nom), remplaçant le calcul manuel de l'étape 1 ;
- ajout de tests de non-régression dédiés (fichiers Leaflet présents et vendus localement, zoom/déplacement non désactivés).

### pourcentages de la fenêtre carte configurables

- ajout de deux nouveaux paramètres dans la page Configuration : « Largeur (%) » et « Hauteur (%) » de la fenêtre de visualisation cartographique (par défaut 95 % / 90 %) — des valeurs distinctes sont nécessaires car le bandeau des tâches Windows réduit la hauteur utile disponible par rapport à la largeur ;
- `DesktopApi.open_map_window` relit la configuration à chaque ouverture (fichier TOML, lecture peu coûteuse) plutôt que de mettre en cache une valeur figée, pour refléter tout changement fait depuis la page Configuration sans redémarrage ;
- ajout de tests de non-régression dédiés (persistance, bornes 50–100, contrat de l'interface).

### corrections après nouveau test manuel (fenêtre carte)

- **bug corrigé, la vraie cause cette fois** : la fenêtre carte était créée sans `js_api`, donc `window.pywebview.api` n'existait pas à l'intérieur — le bouton « Fermer » croyait être en mode navigateur et retombait sur `window.close()`, qui échoue silencieusement. Ajout de `js_api=self` à la création de la fenêtre carte.
- **évolution** : la fenêtre carte se dimensionne désormais à 95 % de l'écran principal et se centre automatiquement (via `webview.screens`), avec repli sur une taille fixe si cette information n'est pas disponible — elle ne déborde plus sous le bas de l'écran par défaut.
- ajout de 2 tests de non-régression dédiés.

### corrections après test manuel de l'étape 1 (fenêtre carte)

- **bug corrigé** : le bouton « Fermer » de la fenêtre carte ne répondait ni au clic ni à Entrée en mode pywebview. Cause : `window.close()` ne fonctionne que sur une fenêtre ouverte par un script (`window.open()`), jamais le cas de cette fenêtre créée côté Python par `webview.create_window()`. Ajout de `DesktopApi.close_map_window()`, utilisée en mode pywebview ; `window.close()` reste utilisé en mode navigateur.
- **bug corrigé** : le nom du point le plus à droite du tracé pouvait disparaître entièrement (une coordonnée SVG hors du `viewBox` ne s'affiche pas). Ajout d'une marge asymétrique qui réserve la place du texte des étiquettes, écrites à droite de chaque point.
- ajout de 3 tests de non-régression dédiés.

### fenêtre de visualisation cartographique, étape 1 (squelette)

Première étape du chantier 0.7.0 (voir `NOTES_CARTOGRAPHIE.md`), sans dépendance réseau externe :

- ajout du bouton « Visualiser la route » dans la zone « Analyse de la route » de l'éditeur, désactivé tant que la route a moins de 2 points (même règle que l'export des segments) ;
- nouvelle route `/map` (page autonome, sans le menu principal) et mécanisme de jeton temporaire côté serveur (`/api/map/token`, `/api/map/data/<jeton>`) pour transmettre la route active à la fenêtre carte, avec expiration automatique après 10 minutes ;
- ce jeton remplace `sessionStorage` pour ce cas précis : un comportement identique est ainsi garanti en mode pywebview et en mode navigateur, contrairement à `sessionStorage` qui ne se partage pas forcément entre deux fenêtres pywebview créées séparément côté Python ;
- nouvelle méthode `DesktopApi.open_map_window()` : réutilise (recharge) la fenêtre carte déjà ouverte plutôt que d'en empiler une seconde ; en mode navigateur, une cible `window.open()` nommée obtient le même comportement nativement ;
- rendu minimal pour cette étape : points de la route reliés par un trait, sans fond de carte ni trait de côte ni icônes IALA (prévus aux étapes suivantes) ; contenu marqué `role="img"`, strictement illustratif ;
- ajout de tests de non-régression dédiés (`test_map_window_skeleton.py`).

### correction du doublon de confirmation au départ

- corrigé un problème signalé après test manuel : le bouton « Retourner sans enregistrer » de la boîte de dialogue déclenchait en plus l'invite générique « Quitter ce site ? » du navigateur, redondante avec le choix déjà fait explicitement. Le passage par cette boîte neutralise désormais l'invite native pour ce cas précis, sans désactiver ce filet de sécurité pour les autres façons de quitter la page (fermeture de la fenêtre, lien du menu principal, etc.).

### correction du focus initial de la boîte de dialogue

- corrigé un problème signalé après test manuel NVDA : `Tab` n'avait aucun effet perceptible dans la boîte de dialogue « Modifications non enregistrées », alors que les 3 boutons restaient atteignables via la navigation rapide NVDA (`B`). Cause probable : le focus initial se posait sur le titre (`H2`), qui n'est pas un contrôle interactif — certains lecteurs d'écran ne basculent pas de façon fiable en mode formulaire dans ce cas, ce qui rend `Tab` imprévisible. Le focus initial se pose désormais sur le premier bouton (« Enregistrer et retourner à la bibliothèque »).



## 0.6.13 — 29 juillet 2026

### Corrections après test manuel NVDA et comparaison avec le code source iOS

- le bouton de création de route est renommé « Créer cette route » (auparavant « Commencer cette route ») ;
- **bug corrigé** : le bouton de création restait visible et cliquable après la création d'une route, car la classe CSS `.actions` (`display:flex`) neutralisait silencieusement l'attribut `hidden` posé par le script. Ajout de la règle `.actions[hidden]{display:none}` ;
- **bug corrigé (comportement en navigation)**, trouvé en comparant avec le code source réel de SARA Navigation iOS : un point importé avec un seuil de validation à 0 (valeur réservée à un point « Homme à la mer ») n'est plus silencieusement transformé en 100 mètres par l'éditeur ;
- **bug corrigé (identité de la route)**, trouvé lors de la même comparaison : l'identifiant d'une route n'est plus régénéré à chaque enregistrement ou envoi ; il est conservé tant que la route reste la même, et n'est renouvelé que pour une route réellement nouvelle ou une copie explicite ;
- le champ « Nom de la route » et son label se masquent une fois la route active (le nom est déjà annoncé par le titre de la zone) ; un bouton « Renommer la route » les réaffiche à la demande, avec le même comportement que le renommage F2 de la Bibliothèque ;
- remplacement de la confirmation à 2 choix (« Continuer sans enregistrer ? ») par une boîte de dialogue modale accessible à 3 choix avant de quitter l'éditeur avec des modifications non enregistrées : Enregistrer et retourner à la bibliothèque / Retourner sans enregistrer / Annuler. Piège de focus et fermeture par Échap ;
- ajout d'un bouton d'ouverture du site de l'association Orion Brest (`https://orion-brest.com/SARA.html`) dans les remerciements de la page À propos, ouvert dans le navigateur par défaut du PC (comme les autres ressources externes de l'application) plutôt que dans la fenêtre pywebview elle-même ;
- le champ « Fonction » de la page À propos précise maintenant qu'il s'agit de synchroniser avec l'application iOS SARA Navigation depuis un PC Windows ;
- ajout d'un bouton « Copier ces informations » pour la liste Informations générales de la page À propos, qui n'était que sélectionnable (sélection peu fiable dans la fenêtre pywebview) et non copiable jusqu'ici ;
- ajout de tests de non-régression dédiés (`test_start_route_and_about_copy.py`, `test_route_identity_and_credits.py`).

### Restructuration de la page « Créer une route »

- suppression de la zone « Commencer une autre route » : l'ouverture d'une route existante se fait désormais uniquement depuis la Bibliothèque ;
- fusion des deux champs de nom (route en cours / nouvelle route) en un seul champ, activé par le bouton « Commencer cette route » ;
- ajout d'un lien « Retour à la bibliothèque », avec confirmation si des modifications ne sont pas enregistrées ;
- renommage de l'onglet de menu « Routes » en « Créer une route », qui ouvre désormais l'éditeur sans route préchargée ;
- ajout de `aria-current="page"` sur le lien de navigation actif ;
- retrait du bouton « Créer une nouvelle route personnelle » de la page Bibliothèque, devenu redondant avec le nouvel onglet ;
- suppression de la route Flask `/shom`, doublon exact et orphelin de `/editor` ;
- le H1 (et le titre d'onglet du navigateur) reflète maintenant réellement le contexte : « Créer une route » par défaut, « Nouvelle route : X » après création, « Modifier : X » lors de l'ouverture d'une route existante — au lieu du texte générique figé « Créer ou modifier une route » qui restait affiché dans tous les cas.

### Homogénéisation de l'accessibilité

- le pattern « zone F6 + titre focusable », auparavant limité aux pages Bibliothèque et Éditeur, s'applique désormais aux 5 pages de l'application (Compte, Bibliothèque, Créer une route, Configuration, À propos) ;
- la zone Messages reste, de façon identique sur toutes les pages, volontairement exclue de ce pattern ;
- chaque `H1` de page est désormais focusable (`tabindex="-1"`), comme les titres de zone ;
- la navigation clavier F6 / Maj+F6, auparavant dupliquée dans `routes.js` et `unified_editor.js`, est mutualisée dans un nouveau script commun `keyboard_zones.js`, chargé globalement depuis `base.html` ;
- ajout d'un test de non-régression dédié (`test_zone_homogeneity.py`) qui verrouille ce pattern pour l'avenir ;
- mise à jour de `ACCESSIBILITE.md`, `ARCHITECTURE.md`, `SPECIFICATIONS.md` et `docs/USER_GUIDE.md` pour refléter la structure réelle des 5 pages.

### Nettoyage du code

- suppression des fichiers orphelins non servis par aucune route Flask : `templates/index.html`, `templates/shom.html`, `static/js/app.js`, `static/js/shom.js`, `static/js/editor.js` ;
- retrait du test devenu obsolète associé (`test_shom_rows`) ;
- ajout de l'entête standardisé (nom de module, description, fonctions présentes, `__version__`, `__date__`) à tous les scripts JavaScript actifs, y compris `about.js` et `account.js` qui n'avaient jamais eu de paramètre de version pour le cache-busting ;
- isolation de chaque script de page dans une fonction immédiatement invoquée (IIFE) pour éviter toute collision de nom entre scripts chargés sur la même page ;
- vérification de la syntaxe de tous les scripts avec Node.js, y compris en combinaison avec `file_dialogs.js` et `keyboard_zones.js`.

## 0.6.12 — 28 juillet 2026

- Correction du type de dialogue utilisé pour tous les exports natifs.
- L'export des segments ouvre désormais un véritable dialogue « Enregistrer sous ».
- Le nom de fichier proposé peut être modifié avant l'enregistrement.
- Le dossier de destination peut être choisi dans le même dialogue.
- Utilisation de `webview.FileDialog.SAVE` avec compatibilité `webview.SAVE_DIALOG`.
- Ajout d'un test de non-régression dédié au type de dialogue.



## 0.6.12 — 28 juillet 2026

- correction du chemin renvoyé sous forme de chaîne par le dialogue Windows « Enregistrer sous » ;
- suppression de la cause probable de l’erreur « Permission denied » lors d’un export vers Documents ;
- messages d’erreur d’écriture enrichis avec le chemin et une indication exploitable ;
- zone de messages de l’éditeur transformée en journal en lecture seule, sélectionnable et copiable ;
- ajout du bouton « Copier le message ».

## Version 0.6.12 — 28 juillet 2026

### Configuration et exports

- ouverture des dialogues d’export dans le répertoire des routes configuré ;
- relecture de la configuration au moment de chaque export ;
- prise en compte du séparateur CSV pour les routes et pour le relevé des segments ;
- réimportation des CSV séparés par point-virgule, virgule ou tabulation ;
- contrôle de la préférence de confirmation avant écrasement ;
- ajout du réglage de l’unité SHOM par défaut dans la page Configuration.

### Qualité

- 33 tests automatisés réussis ;
- contrôle de syntaxe Python et JavaScript ;
- documentation et notes de publication mises à jour.

## Version 0.6.8 — 28 juillet 2026

- titres `H3` dynamiques **Points importés : nombre** et **Points de la route : nombre** ;
- accès aux deux listes par `Tab`, `F6` et `Maj+F6` ;
- zone `H2` **Analyse de la route** ;
- calcul de la distance totale et du nombre de segments ;
- export CSV UTF-8 du détail des segments.

## Version 0.6.7 — 28 juillet 2026

- titre `H2` accessible **Informations sur le point** ;
- association de la section avec `aria-labelledby` ;
- intégration au parcours `F6` et `Maj+F6`.

## Version 0.6.6 — 28 juillet 2026

- homogénéisation des commandes clavier des listes ;
- prise en charge de `Entrée`, `F2`, `Suppr`, touche Menu et `Maj+F10` ;
- menus contextuels accessibles et restauration du focus.

## Version 0.6.5 — 28 juillet 2026

- chaque ligne du panneau de détails expose le couple complet `libellé : valeur` à NVDA ;
- correction appliquée aux informations de points et aux métadonnées SHOM.

## Version 0.6.4 — 28 juillet 2026

- restauration de `requirements.txt` et de `RACCOURCIS_CLAVIER.md` ;
- liens vers la documentation depuis l’onglet **À propos**.

## Versions 0.6.1 à 0.6.3 — 28 juillet 2026

- filtres et tris SHOM compacts ;
- identification de la route en cours ;
- séparation de la création et de l’ouverture ;
- bibliothèque sous forme de listes ;
- consolidation initiale de la documentation.
