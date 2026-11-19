# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_first_page_refresh
Description : Vérifie le rechargement unique de la première page (0.9.4), qui
rend ses repères visibles dans NVDA+F7 au démarrage de l'application.
Classes présentes :
- FakeEvent, FakeEvents, FakeWindow : doublures minimales de pywebview.
- TestFirstPageRefresh : test_reload_once_on_start_page,
  test_no_reload_if_user_already_navigated, test_no_loop_on_second_loaded_event,
  test_failure_is_swallowed.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import time

from sara_route_manager.__main__ import install_first_page_refresh


class FakeEvent:
    """Imiter un événement pywebview auquel on s'abonne avec ``+=``."""

    def __init__(self) -> None:
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def fire(self) -> None:
        for handler in list(self.handlers):
            handler()


class FakeEvents:
    """Regrouper les événements de la fausse fenêtre."""

    def __init__(self) -> None:
        self.loaded = FakeEvent()


class FakeWindow:
    """Fenêtre minimale : adresse courante et historique des chargements."""

    def __init__(self, current: str, fail: bool = False) -> None:
        self.events = FakeEvents()
        self.current = current
        self.fail = fail
        self.loaded_urls = []

    def get_current_url(self) -> str:
        return self.current

    def load_url(self, url: str) -> None:
        if self.fail:
            raise RuntimeError("échec simulé")
        self.loaded_urls.append(url)


START = "http://127.0.0.1:5000"


class TestFirstPageRefresh:
    """Contrôler le comportement du rechargement unique."""

    def test_reload_once_on_start_page(self) -> None:
        """La page de départ est rechargée une fois après son chargement."""
        window = FakeWindow(START + "/")
        install_first_page_refresh(window, START, delay=0.01)
        window.events.loaded.fire()
        time.sleep(0.2)
        assert window.loaded_urls == [START]

    def test_no_reload_if_user_already_navigated(self) -> None:
        """Pas de rechargement si l'utilisateur a déjà changé de page."""
        window = FakeWindow(START + "/routes")
        install_first_page_refresh(window, START, delay=0.01)
        window.events.loaded.fire()
        time.sleep(0.2)
        assert window.loaded_urls == []

    def test_no_loop_on_second_loaded_event(self) -> None:
        """L'événement émis après le rechargement ne déclenche rien de plus."""
        window = FakeWindow(START)
        install_first_page_refresh(window, START, delay=0.01)
        window.events.loaded.fire()
        window.events.loaded.fire()
        time.sleep(0.2)
        assert window.loaded_urls == [START]

    def test_failure_is_swallowed(self) -> None:
        """Une erreur de chargement n'interrompt pas l'application."""
        window = FakeWindow(START, fail=True)
        install_first_page_refresh(window, START, delay=0.01)
        window.events.loaded.fire()
        time.sleep(0.2)
        assert window.loaded_urls == []
