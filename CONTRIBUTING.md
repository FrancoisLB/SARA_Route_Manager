# Contribution

Toute contribution doit préserver l’accessibilité clavier et NVDA décrite dans `docs/ARCHITECTURE.md` (section « Accessibilité — implémentation ») et `docs/RACCOURCIS_CLAVIER.md`.

Avant modification, repartir du dernier ZIP validé. Ne supprimer aucun fichier sans décision explicite. Les nouvelles fonctions d’export doivent réutiliser `static/js/file_dialogs.js`.

Les modules Python respectent les conventions décrites dans `docs/SPECIFICATIONS.md` (partie « Développement ») : UTF-8, `from __future__ import annotations`, cartouche de module, `__version__`, `__date__`, docstrings NumPy et commentaires clairs.

Avant livraison : exécuter la suite de tests, contrôler les fichiers JavaScript, mettre à jour la documentation et vérifier l’intégrité du ZIP.
