# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : run_sara_route_manager
Description : Point d'entrée dédié à la construction de l'exécutable
PyInstaller. `sara_route_manager/__main__.py` utilise des imports relatifs
(`from .app_logging import ...`), qui exigent que le module soit exécuté
comme membre du paquet — jamais directement comme script autonome. Ce
petit fichier importe donc le paquet correctement puis appelle `main()`,
plutôt que de pointer PyInstaller sur `__main__.py` lui-même.

Fonctions présentes :
- Aucune (appelle directement `sara_route_manager.__main__.main`).
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from sara_route_manager.__main__ import main

if __name__ == "__main__":
    main()
