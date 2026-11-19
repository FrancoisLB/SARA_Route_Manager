# Guide utilisateur

## Démarrer l’application

Exécuter `Lancer_SARA_Route_Manager.bat`. La navigation principale propose : Compte, Bibliothèque, Créer une route, Configuration et À propos.

## Créer ou ouvrir une route

Pour **créer** une route, ouvrir l’onglet **Créer une route** : l’éditeur s’ouvre vide, avec un champ pour saisir le nom puis un bouton **Créer cette route**.

Pour **modifier** une route existante (personnelle, partagée ou enregistrée localement), passer par la page **Bibliothèque**, sélectionner la route dans la liste unique et activer **Éditer** (**Consulter** pour une route de « Autres routes (en partage) ») — ou double-cliquer directement sur la route dans la liste : l’éditeur s’ouvre alors avec cette route chargée.

Dans les deux cas, la zone **Route en cours** indique le nom, le nombre de points et l’état d’enregistrement, et le titre de la page reflète le contexte (« Créer une route », « Nouvelle route : *nom* » ou « Modifier : *nom* »). Une fois la route créée ou ouverte, le champ de nom se masque : le bouton **Renommer la route** le réaffiche à la demande.

Un lien **Retour à la bibliothèque** permet de revenir en arrière à tout moment. S’il y a des modifications non enregistrées, une boîte de dialogue propose trois choix : enregistrer et revenir, revenir sans enregistrer, ou annuler.

## Utiliser la Bibliothèque

La Bibliothèque affiche **une seule liste** de routes : vos routes SARA, les routes partagées et celles enregistrées sur ce PC. Chaque ligne indique le nombre de points et l’origine de la route.

1. **Filtrer** : dans le groupe « Afficher », choisir Toutes, Mes routes (en partage), Autres routes (en partage) ou Sur ce PC avec les flèches. Le champ « Rechercher par nom » réduit la liste au fil de la saisie.
2. **Éditer** : sélectionner une route puis **Éditer** (ou Entrée, ou double-clic) ouvre l’éditeur. Pour une route d’un autre utilisateur, le bouton s’appelle **Consulter**.
3. **Voir la carte** : ouvre directement la fenêtre carte avec la trace de la route, sans passer par l’éditeur (2 points minimum). Le nom de la route et son nombre de points sont annoncés. La carte est un complément visuel ; la liste des points se lit dans l’éditeur.
4. **Télécharger** : pour une route en ligne, **Télécharger** l’enregistre sur ce PC, comme le bouton du même nom dans SARA Navigation. Il est grisé pour une route déjà enregistrée sur ce PC et, dans « Mes routes (en partage) », lorsqu’une copie du même nom existe déjà sur le PC. Pour une route d’un autre utilisateur, si une route locale porte déjà ce nom, la question « Une route avec le même nom existe déjà, voulez-vous l’écraser ? » est posée.
5. **Exporter** : **Exporter…** ouvre une boîte de dialogue pour choisir le format (JSON SARA, GPX ou CSV ; le format pré-coché est celui du réglage « Format d’export par défaut » de la Configuration), puis l’emplacement du fichier. **Actualiser la liste** recharge les routes du PC et, si vous êtes connecté, celles de SARA.
6. **Importer une route** : **Importer une route…** ouvre le choix d’un fichier JSON, GPX, CSV ou WPT. La route est enregistrée sur ce PC avec son nom, son sens et tous ses points, puis sélectionnée dans la liste. Si une route locale porte déjà ce nom, une confirmation est demandée. Les informations supplémentaires d’un fichier JSON (par exemple un bloc `metadonnees`) ne sont pas conservées.
7. **Dupliquer, copier, renommer** : ouvrir le menu contextuel avec la touche Applications ou `Maj+F10` (ou `F2` pour renommer). Le menu et les boutons s’adaptent à l’origine de la route ; une phrase sous les boutons indique ce qui est possible pour la route sélectionnée.
8. **Déposer en ligne** : dans l’éditeur, **Déposer en ligne** (nom repris de SARA Navigation) met la route en ligne ; il n’existe pas de mise en ligne privée. Elle apparaît ensuite dans « Mes routes (en partage) » pour vous, et dans « Autres routes (en partage) » pour les autres utilisateurs de SARA Navigation, qui peuvent la télécharger. Si l’une de vos routes en ligne porte déjà ce nom, la question « Une de vos routes mises en ligne a le même nom. Voulez-vous l’écraser ? » est posée (Oui / Non). Si la route appartient à un autre utilisateur, la mise en ligne est refusée : « Cette route ne peut pas être mise en ligne. Une route avec le même nom appartenant à un autre utilisateur existe déjà. »
9. **Supprimer** : **Supprimer** (ou `Suppr`) retire une route de votre compte SARA ou de ce PC, après confirmation. Une route de « Autres routes (en partage) » ne peut pas être supprimée.

## SARA Navigation et SARA Régate

SARA Route Manager fonctionne avec **SARA Navigation** (routes de navigation). Il ne gère pas SARA Régate, dont les « parcours » de régate, partagés ou départagés, sont d’une autre nature. Les noms des boutons suivent donc le vocabulaire de SARA Navigation : « Déposer en ligne », « Télécharger », « Mes routes », « Autres routes ».

## Enregistrer, envoyer et exporter une route

Dans l’éditeur, la zone **Enregistrer et exporter** propose **Enregistrer sur le PC**, **Déposer en ligne** et **Exporter…**. Ce dernier ouvre la même boîte de dialogue que dans la Bibliothèque (JSON SARA, GPX ou CSV). Si une route du même nom existe déjà sur SARA, **Déposer en ligne** demande confirmation avant d’écraser l’une de vos routes en ligne du même nom.

## Importer des points

Choisir une source : marques SHOM, fichier, saisie manuelle ou autre route locale. La source « fichier » ne récupère que les **points** du fichier ; pour importer une route complète (nom, sens, points), utiliser **Importer une route…** dans la Bibliothèque. Après import, le titre **Points importés : nombre** indique le nombre de points disponibles.

## Composer la route

La liste de gauche contient les points importés. La liste de droite contient les points de la route en cours. Les boutons fléchés ajoutent, retirent ou déplacent les points. Les raccourcis sont détaillés dans `docs/RACCOURCIS_CLAVIER.md`.

## Consulter et modifier les informations d’un point

La zone **Informations sur le point** suit la sélection la plus récente dans l’une des deux listes. Chaque ligne est un couple `Libellé : valeur`, parcourue avec les flèches haut/bas.

**Pour un point déjà ajouté à la route**, quatre champs sont modifiables — Nom, Latitude, Longitude et Distance de validation (en mètres) — reconnaissables à leur encadrement. Appuyer sur `Tab` depuis une ligne pour entrer dans son champ, modifier la valeur, puis `Tab` ou cliquer ailleurs pour valider : la modification s’applique immédiatement. Une valeur invalide (coordonnées hors limites, distance hors 1–1000 m) est refusée, avec l’ancienne valeur reprise. Le raccourci `Alt+E` saute directement dans le champ Nom.

Les autres informations (Type, Source, propriétés SHOM d’origine) restent en lecture seule. Un point encore dans **Points importés**, pas encore ajouté à la route, n’est pas modifiable : sa place n’est pas encore définitive.

## Analyser la route

La zone **Analyse de la route** affiche :

- la distance totale cumulée en milles nautiques ;
- le nombre de segments.

Un segment relie deux points successifs.

## Voir la route sur une carte

Le bouton **Voir la carte**, dans la zone « Analyse de la route », ouvre une fenêtre séparée affichant la route sur une carte (actif dès que la route contient au moins 2 points). C’est un complément visuel : tout ce que la carte montre reste par ailleurs disponible sous forme textuelle dans l’éditeur.

La carte affiche un instantané de la route au moment du clic — elle ne se met pas à jour toute seule. Pour voir des modifications récentes, cliquer de nouveau sur **Voir la carte** : la fenêtre déjà ouverte se recharge avec la nouvelle version, plutôt que d’en ouvrir une deuxième.

**Ce qu’elle affiche** :

- le tracé de la route, avec les icônes officielles du SHOM pour les points d’origine connue (marque latérale, cardinale...) ;
- le trait de côte ;
- les marques SHOM environnantes, avec des cases à cocher par catégorie (latérales, cardinales, danger isolé, eaux saines, spéciales, amers, autres) pour choisir lesquelles afficher ;
- une grille latitude/longitude activable ;
- une barre d’échelle en milles nautiques, et des graduations sur les 4 bords de la carte, espacées selon cette même échelle.

**Interactions** :

- survoler un point ou une marque à la souris annonce son nom et son type précis (par exemple « Cardinale Nord » ou « Latérale bâbord ») ;
- double-cliquer sur un point ou une marque ouvre une boîte de dialogue avec le nom, le type et la source, et un bouton pour copier ces informations ;
- l’outil de mesure (case à cocher) permet de cliquer-glisser-relâcher entre deux points de la carte pour obtenir la distance et le cap, avec un bouton Copier.

**Export** : les segments en CSV et la carte elle-même en SVG, via les boutons dédiés — même mécanisme d’enregistrement que les autres exports de l’application.

Les couleurs, l’épaisseur du tracé, la taille des étiquettes et des icônes se règlent dans la page **Configuration** — pas directement dans la fenêtre carte, à l’exception de l’affichage des étiquettes (case à cocher en direct, pour les dégager rapidement si elles gênent la lecture).

## Exporter le détail des segments

Le bouton **Exporter les segments en CSV** ouvre la boîte Windows **Enregistrer sous**. Le nom proposé est basé sur le nom de la route, mais il peut être modifié. L’utilisateur choisit le dossier.

Le fichier comporte les colonnes :

`Numero_segment;Marque_debut;Marque_fin;Longueur_NM;Cap_degres`

Après succès, l’application annonce le nombre de segments et le chemin complet du fichier. Après annulation, elle annonce simplement **Export annulé**.

## Autres exports

Les exports GPX, CSV et JSON utilisent le même dialogue et le même comportement que l’export des segments.

## Configuration

La page **Configuration** regroupe les réglages durables de l’application (répertoire des routes, compte SARA, formats d’import/export, apparence et taille des fenêtres, réglages de la fenêtre carte). Deux boutons permettent d’**exporter** l’ensemble de ces réglages dans un fichier, ou d’en **importer** un précédemment exporté — utile pour transférer sa configuration d’un poste à l’autre.

## Licence et avertissement

L’onglet **À propos** affiche la licence du logiciel (code source et documentation) ainsi qu’un avertissement : l’application est fournie sans garantie, sans procédure qualité formelle. Toute remarque sur son fonctionnement reste la bienvenue.

## Mode navigateur de diagnostic

Dans ce mode, le navigateur gère les téléchargements. L’application ne peut donc pas annoncer un chemin local exact. Le fonctionnement normal sous Windows utilise la fenêtre pywebview.
