# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.__main__
Description : Démarrage du serveur local et de la fenêtre Windows pywebview, avec dialogues de fichiers configurables.
Classes présentes :
- LocalServer : start, stop.
- DesktopApi : _set_window, save_file, choose_routes_directory, open_map_window, close_map_window.
Fonctions présentes : find_free_port, install_first_page_refresh, main.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import argparse
import base64
import socket
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from waitress import create_server

from .app_logging import configure_logging, get_logger
from .configuration import AppConfiguration
from .webapp import create_app


class DesktopApi:
    """Exposer au JavaScript uniquement les dialogues natifs nécessaires.

    Notes
    -----
    La référence à la fenêtre pywebview est volontairement privée. Pywebview
    inspecte récursivement les attributs publics de ``js_api``. Une référence
    publique vers la fenêtre conduirait alors à l'exploration des objets .NET
    internes et à une erreur ``System.Drawing.Rectangle`` sous Windows.
    """

    def __init__(self) -> None:
        """Créer l'API avant son association à la fenêtre pywebview."""
        self._window: Any | None = None
        # Fenêtre secondaire de visualisation cartographique : conservée pour
        # être réutilisée (rechargée) plutôt que dupliquée à chaque clic sur
        # « Voir la carte ».
        self._map_window: Any | None = None

    def _set_window(self, window: Any) -> None:
        """Associer en interne la fenêtre pywebview.

        Parameters
        ----------
        window : Any
            Fenêtre principale créée par ``webview.create_window``.
        """
        self._window = window

    def save_file(
        self,
        suggested_filename: str,
        base64_content: str,
        file_types: list[str] | None = None,
        directory_kind: str = "routes",
    ) -> dict[str, Any]:
        """Afficher le dialogue natif « Enregistrer sous » et écrire le fichier.

        Parameters
        ----------
        suggested_filename : str
            Nom proposé dans la boîte de dialogue.
        base64_content : str
            Contenu du fichier encodé en Base64 par le navigateur.
        file_types : list[str] or None, optional
            Filtres de fichiers compatibles avec pywebview.
        directory_kind : str, default="routes"
            Dossier initial proposé : ``"routes"`` (comportement historique,
            utilisé par tous les exports de route) ou ``"backups"`` (dossier
            « sauvegardes », réservé jusqu'ici et utilisé pour l'export de
            la configuration — un export de configuration est une sauvegarde
            des réglages, sémantiquement à sa place dans ce dossier).

        Returns
        -------
        dict[str, Any]
            Résultat sérialisable indiquant si le fichier a été enregistré ou
            si l'utilisateur a annulé, ainsi que le chemin complet choisi.
        """
        if self._window is None:
            return {"saved": False, "cancelled": False, "path": "", "native": True,
                    "message": "La fenêtre de l’application n’est pas disponible."}

        safe_name = Path(str(suggested_filename)).name or "export.dat"
        filters = tuple(str(item) for item in (file_types or ["Tous les fichiers (*.*)"]))

        # Recharger la configuration à chaque export afin que les changements
        # enregistrés depuis la page Configuration soient appliqués sans
        # redémarrage de l’application.
        configuration = AppConfiguration.load()
        initial_directory = str(
            configuration.backups_directory if directory_kind == "backups" else configuration.routes_directory
        )

        # Utiliser la constante officielle de pywebview. La valeur numérique 20
        # correspond au dialogue de sélection de dossier dans certaines
        # versions ; elle ne doit donc jamais être codée en dur pour un export.
        # Avec pywebview 5.4, l'API recommandée est ``FileDialog.SAVE``.
        import webview

        file_dialog_enum = getattr(webview, "FileDialog", None)
        if file_dialog_enum is not None and hasattr(file_dialog_enum, "SAVE"):
            save_dialog_type = file_dialog_enum.SAVE
        else:
            # Compatibilité avec les anciennes versions de pywebview.
            save_dialog_type = webview.SAVE_DIALOG

        try:
            # Les arguments nommés préservent le nom proposé et le dossier
            # initial tout en ouvrant un véritable dialogue « Enregistrer sous ».
            result = self._window.create_file_dialog(
                save_dialog_type,
                directory=initial_directory,
                allow_multiple=False,
                save_filename=safe_name,
                file_types=filters,
            )
        except TypeError:
            # Compatibilité défensive avec certaines variantes anciennes.
            result = self._window.create_file_dialog(
                save_dialog_type, initial_directory, False, safe_name, filters
            )

        if not result:
            return {"saved": False, "cancelled": True, "path": "", "native": True}

        # Selon la version de pywebview et le moteur Windows utilisé, le
        # dialogue peut renvoyer soit une chaîne, soit une liste/tuple. Ne pas
        # indexer directement une chaîne : ``result[0]`` ne donnerait alors
        # que la lettre du lecteur (par exemple ``C``), ce qui peut provoquer
        # une erreur « Permission denied » lors de l’écriture.
        if isinstance(result, (str, Path)):
            selected_value = str(result)
        elif isinstance(result, (list, tuple)) and result:
            selected_value = str(result[0])
        else:
            return {
                "saved": False,
                "cancelled": False,
                "path": "",
                "native": True,
                "message": "Le dialogue d’enregistrement a renvoyé un chemin inutilisable.",
            }

        selected_path = Path(selected_value).expanduser()

        # Lorsque l’option est active, demander une confirmation explicite
        # avant de remplacer un fichier existant. Certains dialogues Windows
        # demandent déjà cette confirmation ; ce contrôle garantit toutefois
        # le respect de la préférence dans les variantes de pywebview.
        if selected_path.exists() and configuration.confirm_before_overwrite:
            confirmation_method = getattr(self._window, "create_confirmation_dialog", None)
            if callable(confirmation_method):
                confirmed = confirmation_method(
                    "Confirmer le remplacement",
                    f"Le fichier existe déjà :\n{selected_path}\n\nLe remplacer ?",
                )
                if not confirmed:
                    return {
                        "saved": False,
                        "cancelled": True,
                        "path": str(selected_path),
                        "native": True,
                    }

        try:
            selected_path.parent.mkdir(parents=True, exist_ok=True)
            content = base64.b64decode(base64_content.encode("ascii"), validate=True)
            selected_path.write_bytes(content)
        except PermissionError as exc:
            return {
                "saved": False,
                "cancelled": False,
                "path": str(selected_path),
                "native": True,
                "message": (
                    "Accès refusé lors de l’enregistrement.\n"
                    f"Chemin : {selected_path}\n"
                    "Vérifiez que le fichier n’est pas déjà ouvert et que le dossier est accessible. "
                    f"Détail système : {exc}"
                ),
            }
        except (OSError, ValueError) as exc:
            return {
                "saved": False,
                "cancelled": False,
                "path": str(selected_path),
                "native": True,
                "message": (
                    "Impossible d’enregistrer le fichier.\n"
                    f"Chemin : {selected_path}\n"
                    f"Détail système : {exc}"
                ),
            }

        return {
            "saved": True,
            "cancelled": False,
            "path": str(selected_path.resolve()),
            "native": True,
        }

    def choose_routes_directory(self) -> str:
        """Afficher le sélecteur natif d'un répertoire Windows.

        Returns
        -------
        str
            Chemin choisi, ou chaîne vide après annulation.
        """
        if self._window is None:
            return ""
        import webview

        file_dialog_enum = getattr(webview, "FileDialog", None)
        if file_dialog_enum is not None and hasattr(file_dialog_enum, "FOLDER"):
            folder_dialog_type = file_dialog_enum.FOLDER
        else:
            folder_dialog_type = webview.FOLDER_DIALOG

        result = self._window.create_file_dialog(folder_dialog_type, allow_multiple=False)
        if not result:
            return ""
        if isinstance(result, (str, Path)):
            return str(result)
        return str(result[0])

    def open_map_window(self, url: str) -> None:
        """Ouvrir ou réutiliser la fenêtre de visualisation cartographique.

        Un deuxième clic sur « Voir la carte » alors que la fenêtre
        est déjà ouverte recharge cette même fenêtre avec le nouvel
        instantané, plutôt que d'en empiler une seconde : c'est le bouton
        « Voir la carte » de l'éditeur qui joue le rôle de
        rafraîchissement, pas un bouton dédié dans la fenêtre carte.

        Parameters
        ----------
        url : str
            Adresse locale complète de la page carte, avec son jeton
            (``http://127.0.0.1:<port>/map?token=...``).
        """
        import webview

        if self._map_window is not None:
            try:
                self._map_window.load_url(url)
                return
            except Exception:
                # La fenêtre a pu être fermée sans que l'évènement de
                # fermeture n'ait encore été traité : on en recrée une.
                self._map_window = None

        # Dimensionner la fenêtre selon les pourcentages configurés (page
        # Configuration) et la centrer, pour éviter qu'une taille fixe ne
        # déborde sous le bas de l'écran. La configuration est relue à
        # chaque ouverture (fichier TOML, lecture peu coûteuse) plutôt que
        # mise en cache, pour refléter tout changement fait entre-temps par
        # l'utilisateur sans avoir à synchroniser deux instances distinctes.
        # Repli sur une taille fixe raisonnable si la liste des écrans
        # n'est pas disponible.
        #
        # Sous Windows, `width`/`height` correspondent à la zone de contenu
        # de la fenêtre, pas à la fenêtre entière : la barre de titre et les
        # bordures ajoutées par le système ne sont pas comptées dedans
        # (comportement documenté, voir l'issue #1432 du dépôt pywebview).
        # Une première compensation en pixels fixes (40 px / 16 px) s'est
        # révélée insuffisante lors d'un test réel (fenêtre encore un peu
        # trop grande). Remplacée par une marge de sécurité proportionnelle
        # de 5 % en largeur et en hauteur : plus simple, et qui s'adapte
        # naturellement à la taille de l'écran plutôt qu'un nombre de
        # pixels fixe.
        SAFETY_MARGIN_FACTOR = 0.95

        width, height, x, y = 1000, 750, None, None
        screens = getattr(webview, "screens", None)
        if screens:
            configuration = AppConfiguration.load()
            screen = screens[0]
            width = int(screen.width * configuration.map_window_width_percent / 100 * SAFETY_MARGIN_FACTOR)
            height = int(screen.height * configuration.map_window_height_percent / 100 * SAFETY_MARGIN_FACTOR)
            x = int((screen.width - width) / 2)
            y = int((screen.height - height) / 2)

        map_window = webview.create_window(
            "Carte de la route — SARA Route Manager",
            url,
            width=width,
            height=height,
            x=x,
            y=y,
            min_size=(700, 500),
            text_select=True,
            # Sans ce js_api, window.pywebview.api serait absent de cette
            # fenêtre : le bouton « Fermer » de map.js croirait alors être en
            # mode navigateur et retomberait sur window.close(), qui échoue
            # silencieusement (une fenêtre créée côté Python, pas par un
            # script, ne peut pas se fermer elle-même de cette façon).
            js_api=self,
        )

        def _on_map_window_closed() -> None:
            self._map_window = None

        map_window.events.closed += _on_map_window_closed
        self._map_window = map_window

    def close_map_window(self) -> None:
        """Fermer la fenêtre de visualisation cartographique.

        Notes
        -----
        `window.close()` côté JavaScript ne fonctionne que sur une fenêtre
        ouverte par un script (`window.open()`) — ce qui n'est jamais le cas
        de la fenêtre carte en mode pywebview, créée côté Python par
        `webview.create_window()`. Sans cette méthode, le bouton « Fermer »
        échouerait silencieusement au clic comme au clavier (Entrée).
        """
        if self._map_window is not None:
            self._map_window.destroy()
            self._map_window = None


class LocalServer:
    """Exécuter Flask avec Waitress dans un fil local contrôlé."""

    def __init__(self, host: str, port: int) -> None:
        """Préparer le serveur local sans le démarrer.

        Parameters
        ----------
        host : str
            Adresse locale d'écoute.
        port : int
            Port TCP disponible.
        """
        self._server = create_server(create_app(), host=host, port=port, threads=4)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self) -> None:
        """Démarrer le serveur local."""
        self._thread.start()

    def stop(self) -> None:
        """Arrêter proprement le serveur local."""
        self._server.close()


def find_free_port() -> int:
    """Trouver un port TCP libre sur l'interface locale.

    Returns
    -------
    int
        Numéro d'un port local disponible.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


# Délai (en secondes) entre la fin du premier chargement et le rechargement
# unique de la page d'accueil (voir `install_first_page_refresh`).
FIRST_PAGE_REFRESH_DELAY = 1.0


def install_first_page_refresh(window: Any, start_url: str, delay: float = FIRST_PAGE_REFRESH_DELAY) -> None:
    """Recharger une seule fois la première page, pour exposer ses repères à NVDA.

    Constat (version 0.9.3) : au tout premier chargement dans la fenêtre
    Edge WebView2, NVDA n'affiche aucun repère (bannière, navigation,
    principal, pied de page) dans sa liste NVDA+F7, alors que ces repères
    existent bien dans le HTML et apparaissent dès qu'une page est chargée
    par un clic sur la navigation. La première page est chargée avant que
    le lecteur d'écran n'ait été détecté, et l'arborescence d'accessibilité
    n'est alors pas construite. Recharger cette page une fois, quelques
    instants après son chargement, produit le même résultat qu'un clic sur
    « Compte ».

    Le rechargement n'a lieu que si l'utilisateur est toujours sur la page
    de départ (il n'a pas déjà navigué), et une seule fois : un drapeau
    empêche toute boucle, l'événement ``loaded`` étant émis à nouveau après
    chaque chargement.

    Parameters
    ----------
    window : Any
        Fenêtre pywebview (``events.loaded``, ``get_current_url``,
        ``load_url``).
    start_url : str
        Adresse de la page de départ, sans barre oblique finale.
    delay : float, default=FIRST_PAGE_REFRESH_DELAY
        Attente avant le rechargement, en secondes.
    """
    state = {"done": False}

    def refresh() -> None:
        # Laisser le temps au lecteur d'écran de se connecter à la fenêtre.
        time.sleep(delay)
        try:
            current = str(window.get_current_url() or "").rstrip("/")
            if current == start_url.rstrip("/"):
                window.load_url(start_url)
        except Exception:
            # Un échec ne doit jamais gêner l'application : la page reste
            # utilisable, et un clic sur la navigation reconstruit les repères.
            get_logger().exception("Rechargement de la première page impossible")

    def on_loaded() -> None:
        if state["done"]:
            return
        state["done"] = True
        threading.Thread(target=refresh, name="first-page-refresh", daemon=True).start()

    window.events.loaded += on_loaded


def main() -> None:
    """Démarrer pywebview par défaut ou le navigateur en mode diagnostic."""
    parser = argparse.ArgumentParser(description="Gestionnaire de routes SARA Navigation")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Mode de diagnostic : ouvrir dans le navigateur par défaut.",
    )
    args = parser.parse_args()

    configuration = AppConfiguration.load()
    log_file = configure_logging(configuration.logs_directory)
    logger = get_logger()
    logger.info("Démarrage de SARA Route Manager %s", __version__)
    logger.info("Journal actif : %s", log_file)

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    server = LocalServer("127.0.0.1", port)
    server.start()

    if args.browser:
        logger.warning("Démarrage en mode navigateur de diagnostic")
        webbrowser.open(url)
        try:
            input("Mode diagnostic. Appuyez sur Entrée pour arrêter le serveur... ")
        finally:
            server.stop()
            logger.info("Arrêt du mode navigateur")
        return

    try:
        import webview

        # Dimensionner la fenêtre principale selon les pourcentages
        # configurés (page Configuration) et la centrer — même principe et
        # même marge de sécurité de 5 % que pour la fenêtre de
        # visualisation cartographique (`DesktopApi.open_map_window`), pour
        # absorber la barre de titre et les bordures Windows non comptées
        # dans `width`/`height` (voir l'issue #1432 du dépôt pywebview).
        # Repli sur une taille fixe raisonnable si la liste des écrans
        # n'est pas disponible.
        SAFETY_MARGIN_FACTOR = 0.95
        main_width, main_height, main_x, main_y = 1200, 850, None, None
        screens = getattr(webview, "screens", None)
        if screens:
            screen = screens[0]
            main_width = int(screen.width * configuration.main_window_width_percent / 100 * SAFETY_MARGIN_FACTOR)
            main_height = int(screen.height * configuration.main_window_height_percent / 100 * SAFETY_MARGIN_FACTOR)
            main_x = int((screen.width - main_width) / 2)
            main_y = int((screen.height - main_height) / 2)

        desktop_api = DesktopApi()
        window = webview.create_window(
            f"SARA Route Manager {__version__}",
            url,
            width=main_width,
            height=main_height,
            x=main_x,
            y=main_y,
            min_size=(800, 650),
            text_select=True,
            js_api=desktop_api,
        )
        # L'attribut privé évite que pywebview parcoure les objets .NET internes.
        desktop_api._set_window(window)
        install_first_page_refresh(window, url)
        logger.info("Ouverture de la fenêtre pywebview avec Edge WebView2")
        webview.start(gui="edgechromium", debug=False)
    except Exception:
        logger.exception("Échec du démarrage de pywebview")
        raise
    finally:
        server.stop()
        logger.info("Arrêt de SARA Route Manager")


if __name__ == "__main__":
    main()
