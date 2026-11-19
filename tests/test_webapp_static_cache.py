# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_webapp_static_cache
Description : Vérifie que les fichiers statiques (JS, CSS) sont servis
avec une revalidation systématique, pour éviter qu'un script modifié reste
indéfiniment servi depuis le cache disque persistant de WebView2 — qui,
contrairement à un onglet de navigateur classique, survit à la fermeture
complète de l'application.
Classes présentes :
- TestStaticFileCaching : test_static_js_not_cached,
  test_static_css_not_cached.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from sara_route_manager.webapp import create_app


class TestStaticFileCaching:
    """Vérifier que les fichiers statiques ne sont jamais mis en cache durablement."""

    def test_static_js_not_cached(self) -> None:
        """Vérifier l'en-tête Cache-Control d'un script JavaScript.

        Repéré après signalement : un correctif dans `map.js` semblait
        sans effet, alors que le code était correct — la cause réelle
        était le cache disque persistant de WebView2, combiné à un
        paramètre `v=` de cache-busting resté identique sur plusieurs
        livraisons successives.
        """
        client = create_app().test_client()
        response = client.get("/static/js/map.js")
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-cache" in cache_control

    def test_static_css_not_cached(self) -> None:
        """Vérifier l'en-tête Cache-Control d'une feuille de style."""
        client = create_app().test_client()
        response = client.get("/static/css/main.css")
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-cache" in cache_control
