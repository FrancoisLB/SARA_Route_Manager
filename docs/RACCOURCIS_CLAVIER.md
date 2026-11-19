# Raccourcis clavier

## Navigation générale

- `Tab` : contrôle suivant ;
- `Maj+Tab` : contrôle précédent ;
- `F6` : zone principale suivante ;
- `Maj+F6` : zone principale précédente ;
- `H` avec NVDA : titre suivant ;
- `Maj+H` avec NVDA : titre précédent.

## Listes

- Flèche haut ou bas : élément précédent ou suivant ;
- Début ou Fin : premier ou dernier élément ;
- Entrée : ouvrir ou valider selon la liste ;
- `F2` : renommer lorsque l’action est autorisée ;
- `Suppr` : supprimer ou retirer lorsque l’action est autorisée ;
- touche Menu ou `Maj+F10` : menu contextuel ;
- Échap : fermer le menu contextuel ou annuler.

## Bibliothèque

- Flèches haut/bas dans le groupe « Afficher » : changer le filtre (Toutes, Mes routes (en partage), Autres routes (en partage), Sur ce PC) ;
- Entrée dans la liste ou double-clic : éditer (ou consulter) la route sélectionnée ;
- `F2` : renommer ; `Suppr` : supprimer (route SARA ou locale) ;
- touche Menu ou `Maj+F10` : menu contextuel adapté à l’origine de la route (Éditer ou Consulter, Voir la carte, Télécharger, Renommer, Dupliquer ou Copier dans mes routes, Exporter…, Supprimer) ;
- dans la boîte « Exporter la route » : flèches pour choisir le format, `Tab` reste dans la boîte, Échap annule.

## Composer une route

- `Alt+Flèche droite` : ajouter le point sélectionné à la route ;
- `Alt+Flèche gauche` : retirer le point sélectionné de la route ;
- `Alt+Flèche haut` : monter le point dans la route ;
- `Alt+Flèche bas` : descendre le point dans la route ;
- `Alt+C` : copier les informations du point sélectionné ;
- `Alt+Maj+C` : copier les coordonnées du point sélectionné ;
- `Alt+E` : sauter directement dans le champ **Nom** du panneau **Informations sur le point** (uniquement si le point sélectionné est déjà ajouté à la route — un point encore dans « Points importés » n'est pas modifiable) ;
- Entrée depuis une liste de points : accéder à **Informations sur le point**.

Les listes **Points importés** et **Points de la route** sont accessibles par `Tab`, `F6` et `Maj+F6`.

### Panneau « Informations sur le point »

Une fois le focus dans le panneau, chaque ligne (un couple libellé/valeur) se parcourt avec les **flèches haut/bas** — pas de bouclage en début/fin de liste. Sur une ligne modifiable (Nom, Latitude, Longitude, Distance de validation — uniquement pour un point déjà ajouté à la route), `Tab` entre dans le champ de texte, encadré d'un trait fin et contrasté ; la modification s'applique à la perte de focus (`Tab` ou clic ailleurs). Une valeur invalide (latitude/longitude hors bornes, rayon hors 1–1000 m) est refusée avec une annonce d'erreur, l'ancienne valeur étant reprise.

## Dialogues d’import et d’export

Les dialogues natifs Windows se parcourent avec les commandes habituelles de l’Explorateur. Après fermeture d’un dialogue d’export, le focus revient au bouton qui l’a ouvert.

## Renommer la route en cours

Une fois une route créée ou ouverte, le champ « Nom de la route » se masque et le titre H2 affiche le nom retenu. Le bouton **Renommer la route** réaffiche le champ, y place le focus et en sélectionne le contenu. La perte de focus (Tab, clic ailleurs) referme le champ et annonce le nom retenu.

## Boîte de dialogue « Modifications non enregistrées »

Si la route en cours contient des modifications non enregistrées, le lien **Retour à la bibliothèque** ouvre une boîte de dialogue à 3 choix plutôt que de naviguer directement :

- **Enregistrer et retourner à la bibliothèque** ;
- **Retourner sans enregistrer** ;
- **Annuler**.

`Tab` et `Maj+Tab` restent cantonnés aux trois boutons tant que la boîte est ouverte. `Échap` équivaut à **Annuler** et rend le focus au lien d’origine.

## Commandes NVDA utiles

- `H` : titre suivant ;
- `K` : lien suivant ;
- `B` : bouton suivant ;
- `F` : champ de formulaire suivant ;
- `T` : tableau suivant.
