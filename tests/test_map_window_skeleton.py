# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_map_window_skeleton
Description : Vérifie le squelette de la fenêtre de visualisation
cartographique (étape 1) : bouton dans l'éditeur, jeton temporaire côté
serveur, page carte, et méthode pywebview de réutilisation de fenêtre.
Classes présentes :
- MapWindowSkeletonTests : test_visualize_button_present,
  test_visualize_button_toggle, test_map_token_roundtrip,
  test_map_data_enriches_route_points_with_icon,
  test_map_token_requires_two_points, test_map_token_expiry,
  test_map_page_renders, test_open_map_window_js_contract,
  test_desktop_api_open_map_window, test_desktop_api_close_map_window,
  test_map_window_has_js_api, test_map_window_sized_to_screen,
  test_map_window_size_is_configurable, test_main_window_size_is_configurable,
  test_main_window_sized_and_centered, test_map_svg_reserves_margin_for_labels,
  test_map_uses_leaflet_vendored_locally, test_map_background_set_after_init,
  test_map_uses_native_zoom_and_pan, test_map_coastline_endpoint_contract,
  test_map_coastline_failure_does_not_break_page,
  test_map_js_handles_coastline_gracefully, test_histolitt_attribution_requires_logos,
  test_map_container_ignores_forced_colors, test_map_has_real_h1_and_summary,
  test_map_export_segments_csv_button, test_map_export_svg_button,
  test_map_buttons_in_side_column, test_map_page_uses_full_width,
  test_map_page_has_no_redundant_header, test_map_has_breathing_room_around_content,
  test_map_marks_filter_present, test_map_labels_have_reduced_font_size,
  test_map_colors_come_only_from_configuration, test_map_route_color_configurable,
  test_map_route_line_style_configurable, test_map_route_labels_settings_configurable,
  test_map_route_labels_live_toggle_in_addition_to_configuration, test_map_route_label_frame_toggle,
  test_map_grid_toggle,
  test_map_nautical_scale_control, test_map_scale_bar_uses_milles_not_nm,
  test_map_alt_f4_closes_window, test_map_hover_announces_marker_name,
  test_map_marker_size_configurable, test_map_nautical_tick_marks_share_scale_bar_step,
  test_map_nautical_tick_marks_cover_all_four_edges, test_map_mark_labels_toggle,
  test_measure_tool_dialog_present, test_measure_tool_dialog_focus_trap,
  test_measure_tool_disables_dragging_while_active,
  test_measure_tool_uses_shared_route_math, test_measure_tool_ignores_near_zero_segments,
  test_measure_tool_copy_announces_to_nvda,
  test_marker_info_dialog_present_and_accessible, test_double_click_opens_marker_info_dialog,
  test_marker_type_precised_with_direction_or_side,
  test_map_js_renders_marks_with_icons_and_fallback,
  test_map_js_renders_route_points_with_icon_when_available,
  test_shom_icons_vendored_locally,
  test_map_side_buttons_can_wrap_to_two_lines, test_map_title_and_summary_are_close,
  test_sea_color_is_saturated.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path
import re
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MapWindowSkeletonTests(unittest.TestCase):
    """Contrôler le squelette de la fenêtre de visualisation cartographique."""

    def test_visualize_button_present(self) -> None:
        """Vérifier la présence du bouton dans la zone Analyse de la route."""
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="visualize-route" type="button" class="secondary" disabled', editor)

    def test_visualize_button_toggle(self) -> None:
        """Vérifier que le bouton suit le même état que l'export des segments."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('$("visualize-route").disabled = segments.length === 0;', script)
        self.assertIn('$("visualize-route").onclick = openMapWindow;', script)

    def test_map_token_roundtrip(self) -> None:
        """Vérifier la création puis la lecture d'un jeton de route."""
        from sara_route_manager.webapp import create_app

        client = create_app().test_client()
        payload = {
            "name": "Route de test",
            "points": [
                {"name": "Départ", "latitude": 47.7, "longitude": -3.4},
                {"name": "Arrivée", "latitude": 47.75, "longitude": -3.35},
            ],
        }
        created = client.post("/api/map/token", json=payload)
        self.assertEqual(created.status_code, 200)
        token = created.get_json()["token"]

        fetched = client.get(f"/api/map/data/{token}")
        self.assertEqual(fetched.status_code, 200)
        route = fetched.get_json()["route"]
        self.assertEqual(route["name"], "Route de test")
        self.assertEqual(len(route["points"]), 2)

        missing = client.get("/api/map/data/jeton-inconnu")
        self.assertEqual(missing.status_code, 404)

    def test_map_data_enriches_route_points_with_icon(self) -> None:
        """Vérifier que /api/map/data ajoute l'icône IALA de chaque point de route (option B).

        Un point avec un `object_code` connu (marque SHOM ajoutée en
        session, ou route rouverte depuis une sauvegarde locale) reçoit son
        icône ; un point générique (saisie manuelle) reçoit `None`, sans
        que ce soit une erreur.
        """
        from sara_route_manager.webapp import create_app

        client = create_app().test_client()
        payload = {
            "name": "Route de test",
            "points": [
                {
                    "name": "Balise",
                    "latitude": 47.7,
                    "longitude": -3.4,
                    "object_code": "BCNLAT",
                    "properties": {"Category of lateral mark": "port hand"},
                },
                {"name": "Point manuel", "latitude": 47.75, "longitude": -3.35, "object_code": "", "properties": {}},
            ],
        }
        token = client.post("/api/map/token", json=payload).get_json()["token"]
        response = client.get(f"/api/map/data/{token}")
        points = response.get_json()["route"]["points"]
        self.assertEqual(points[0]["icon_filename"], "BCNLAT_B.svg")
        self.assertIsNone(points[1]["icon_filename"])

    def test_map_token_requires_two_points(self) -> None:
        """Vérifier qu'une route à un seul point est refusée."""
        from sara_route_manager.webapp import create_app

        client = create_app().test_client()
        response = client.post(
            "/api/map/token",
            json={"name": "Route", "points": [{"latitude": 1, "longitude": 1}]},
        )
        self.assertEqual(response.status_code, 400)

    def test_map_token_expiry(self) -> None:
        """Vérifier que la purge retire bien les jetons expirés."""
        from sara_route_manager.webapp import ApplicationState, _prune_map_tokens

        state = ApplicationState()
        state.map_tokens["ancien"] = {"data": {}, "created_at": time.time() - 9999}
        state.map_tokens["recent"] = {"data": {}, "created_at": time.time()}
        _prune_map_tokens(state)
        self.assertNotIn("ancien", state.map_tokens)
        self.assertIn("recent", state.map_tokens)

    def test_map_page_renders(self) -> None:
        """Vérifier que la page carte se charge et référence son script."""
        from sara_route_manager.webapp import create_app

        client = create_app().test_client()
        response = client.get("/map")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("js/map.js", html)
        self.assertIn('id="close-map-window"', html)
        self.assertIn('role="img"', html)

    def test_open_map_window_js_contract(self) -> None:
        """Vérifier la logique de choix pywebview/navigateur côté client."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("window.pywebview?.api", script)
        self.assertIn("desktopApi.open_map_window(url)", script)
        self.assertIn('window.open(url, "sara_map_window");', script)

    def test_desktop_api_open_map_window(self) -> None:
        """Vérifier que DesktopApi expose bien la réutilisation de fenêtre."""
        script = (ROOT / "sara_route_manager/__main__.py").read_text(encoding="utf-8")
        self.assertIn("def open_map_window(self, url: str) -> None:", script)
        self.assertIn("self._map_window.load_url(url)", script)
        self.assertIn("map_window.events.closed += _on_map_window_closed", script)

    def test_desktop_api_close_map_window(self) -> None:
        """Vérifier la fermeture réelle de la fenêtre carte en mode pywebview.

        window.close() côté JavaScript ne fonctionne que sur une fenêtre
        ouverte par un script (window.open()) — jamais le cas de la fenêtre
        carte en mode pywebview, créée côté Python. Sans DesktopApi.close_map_window,
        le bouton « Fermer » échouait silencieusement au clic comme au clavier.
        """
        script = (ROOT / "sara_route_manager/__main__.py").read_text(encoding="utf-8")
        self.assertIn("def close_map_window(self) -> None:", script)
        self.assertIn("self._map_window.destroy()", script)
        map_script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("desktopApi.close_map_window();", map_script)

    def test_map_window_has_js_api(self) -> None:
        """Vérifier que la fenêtre carte reçoit bien un js_api.

        Sans `js_api=self` sur ce `create_window`, `window.pywebview.api`
        serait absent à l'intérieur de la fenêtre carte : le bouton
        « Fermer » croirait alors être en mode navigateur et retomberait sur
        `window.close()`, qui échoue silencieusement pour une fenêtre créée
        côté Python plutôt que par un script.
        """
        script = (ROOT / "sara_route_manager/__main__.py").read_text(encoding="utf-8")
        create_window_call = script.split("map_window = webview.create_window(")[1].split(")\n\n")[0]
        self.assertIn("js_api=self,", create_window_call)

    def test_map_window_sized_to_screen(self) -> None:
        """Vérifier que la fenêtre carte se dimensionne selon la configuration et se centre.

        Une marge de sécurité proportionnelle de 5 % complète les
        pourcentages configurés, pour absorber la barre de titre et les
        bordures Windows non comptées dans width/height (voir l'issue
        #1432 du dépôt pywebview) — remplace une première compensation en
        pixels fixes, insuffisante d'après un test réel.
        """
        script = (ROOT / "sara_route_manager/__main__.py").read_text(encoding="utf-8")
        self.assertIn("configuration = AppConfiguration.load()", script)
        self.assertIn("SAFETY_MARGIN_FACTOR = 0.95", script)
        self.assertIn(
            "width = int(screen.width * configuration.map_window_width_percent / 100 * SAFETY_MARGIN_FACTOR)",
            script,
        )
        self.assertIn(
            "height = int(screen.height * configuration.map_window_height_percent / 100 * SAFETY_MARGIN_FACTOR)",
            script,
        )
        self.assertIn("x = int((screen.width - width) / 2)", script)
        self.assertIn("y = int((screen.height - height) / 2)", script)

    def test_map_window_size_is_configurable(self) -> None:
        """Vérifier que les pourcentages de la fenêtre carte sont configurables.

        Des pourcentages distincts pour la largeur et la hauteur sont
        nécessaires car le bandeau des tâches Windows réduit la hauteur
        utile disponible par rapport à la largeur.
        """
        config_script = (ROOT / "sara_route_manager/configuration.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("map_window_width_percent: int = 95", config_script)
        self.assertIn("map_window_height_percent: int = 80", config_script)
        page = (ROOT / "sara_route_manager/templates/configuration.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="map-window-width-percent"', page)
        self.assertIn('id="map-window-height-percent"', page)

    def test_main_window_size_is_configurable(self) -> None:
        """Vérifier que les pourcentages de la fenêtre principale sont configurables.

        Réglage distinct et complémentaire de celui de la fenêtre de
        visualisation cartographique : 90 % de largeur, 80 % de hauteur,
        demandés explicitement par l'utilisateur pour la fenêtre principale
        au démarrage de l'application.
        """
        config_script = (ROOT / "sara_route_manager/configuration.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("main_window_width_percent: int = 90", config_script)
        self.assertIn("main_window_height_percent: int = 80", config_script)
        page = (ROOT / "sara_route_manager/templates/configuration.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="main-window-width-percent"', page)
        self.assertIn('id="main-window-height-percent"', page)

    def test_main_window_sized_and_centered(self) -> None:
        """Vérifier que la fenêtre principale se dimensionne et se centre, comme la carte.

        Même principe et même marge de sécurité de 5 % que pour la fenêtre
        de visualisation cartographique — la fenêtre principale n'avait
        jusqu'ici aucun dimensionnement configurable ni centrage réel
        (taille fixe 1200x850 sans position explicite).
        """
        script = (ROOT / "sara_route_manager/__main__.py").read_text(encoding="utf-8")
        main_section = script.split("def main() -> None:")[1]
        self.assertIn(
            "main_width = int(screen.width * configuration.main_window_width_percent / 100 * SAFETY_MARGIN_FACTOR)",
            main_section,
        )
        self.assertIn(
            "main_height = int(screen.height * configuration.main_window_height_percent / 100 * SAFETY_MARGIN_FACTOR)",
            main_section,
        )
        self.assertIn("main_x = int((screen.width - main_width) / 2)", main_section)
        self.assertIn("main_y = int((screen.height - main_height) / 2)", main_section)
        self.assertIn("x=main_x,", main_section)
        self.assertIn("y=main_y,", main_section)

    def test_map_svg_reserves_margin_for_labels(self) -> None:
        """Vérifier que le cadrage Leaflet réserve une marge asymétrique pour les étiquettes.

        Sans cette marge, le nom du point le plus à droite du tracé pouvait
        sortir du cadre visible, les étiquettes étant affichées à droite de
        chaque point.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("paddingBottomRight: [160, 40]", script)

    def test_map_uses_leaflet_vendored_locally(self) -> None:
        """Vérifier que Leaflet est chargé depuis les fichiers vendus localement, pas un CDN."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("vendor/leaflet/leaflet.css", page)
        self.assertIn("vendor/leaflet/leaflet.js", page)
        self.assertNotIn("unpkg.com", page)
        self.assertNotIn("cdn.", page)
        leaflet_js = ROOT / "sara_route_manager/static/vendor/leaflet/leaflet.js"
        leaflet_css = ROOT / "sara_route_manager/static/vendor/leaflet/leaflet.css"
        leaflet_license = ROOT / "sara_route_manager/static/vendor/leaflet/LEAFLET_LICENSE.txt"
        self.assertTrue(leaflet_js.exists())
        self.assertTrue(leaflet_css.exists())
        self.assertTrue(leaflet_license.exists())

    def test_map_background_set_after_init(self) -> None:
        """Vérifier que le fond de carte est fixé après l'initialisation Leaflet.

        Un simple `style=""` posé sur le `<div>` avant l'existence de la
        carte peut être écrasé par le style que Leaflet applique lui-même à
        son conteneur au démarrage — d'où un fond noir constaté au lieu du
        bleu clair prévu. Fixer la couleur après `L.map(...)` garantit
        qu'elle s'applique en dernier. La couleur elle-même est désormais
        une variable (`currentSeaColor`), configurable, plutôt qu'une
        valeur hexadécimale figée.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        init_index = script.index("L.map(\"map-container\"")
        background_index = script.index("map.getContainer().style.background = currentSeaColor;")
        self.assertGreater(background_index, init_index)


    def test_map_uses_native_zoom_and_pan(self) -> None:
        """Vérifier que le zoom/déplacement natifs de Leaflet ne sont pas désactivés."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertNotIn("scrollWheelZoom: false", script)
        self.assertNotIn("dragging: false", script)
        self.assertIn("L.map(", script)
        self.assertIn("map.fitBounds(", script)

    def test_map_coastline_endpoint_contract(self) -> None:
        """Vérifier le contrat de l'endpoint de trait de côte, réseau simulé."""
        from unittest.mock import patch
        from sara_route_manager.webapp import create_app

        client = create_app().test_client()
        payload = {
            "name": "Route de test",
            "points": [
                {"name": "Départ", "latitude": 47.7, "longitude": -3.4},
                {"name": "Arrivée", "latitude": 47.75, "longitude": -3.35},
            ],
        }
        token = client.post("/api/map/token", json=payload).get_json()["token"]

        fake_result = {
            "geojson": {"type": "FeatureCollection", "features": []},
            "layer": "limite_terre_mer",
            "attribution": "Shom-IGN, 2021.",
        }
        with patch("sara_route_manager.webapp.fetch_coastline", return_value=fake_result) as mocked:
            response = client.get(f"/api/map/coastline/{token}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["layer"], "limite_terre_mer")

        # L'emprise transmise doit englober les deux points avec une marge.
        call_args = mocked.call_args[0]
        min_lat, max_lat, min_lon, max_lon = call_args
        self.assertLess(min_lat, 47.7)
        self.assertGreater(max_lat, 47.75)
        self.assertLess(min_lon, -3.4)
        self.assertGreater(max_lon, -3.35)

        missing = client.get("/api/map/coastline/jeton-inconnu")
        self.assertEqual(missing.status_code, 404)

    def test_map_coastline_failure_does_not_break_page(self) -> None:
        """Vérifier qu'un échec du trait de côte reste une erreur 502 gracieuse."""
        from unittest.mock import patch
        from sara_route_manager.webapp import create_app
        from sara_route_manager.coastline import CoastlineError

        client = create_app().test_client()
        payload = {"name": "Route", "points": [{"latitude": 1, "longitude": 1}, {"latitude": 2, "longitude": 2}]}
        token = client.post("/api/map/token", json=payload).get_json()["token"]

        with patch("sara_route_manager.webapp.fetch_coastline", side_effect=CoastlineError("réseau indisponible")):
            response = client.get(f"/api/map/coastline/{token}")
        self.assertEqual(response.status_code, 502)
        self.assertFalse(response.get_json()["ok"])

    def test_map_js_handles_coastline_gracefully(self) -> None:
        """Vérifier que map.js n'interrompt jamais l'affichage des points si le trait de côte échoue."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function renderCoastline", script)
        self.assertIn("function fetchCoastline", script)
        # Le bloc try/catch du trait de côte doit être séparé de celui des
        # points, pour qu'une erreur ici n'empêche jamais l'affichage déjà
        # réussi de la route elle-même.
        coastline_block = script.split("// Le trait de côte est un complément visuel")[1]
        self.assertIn("catch (error)", coastline_block)
        self.assertIn("coastlineCreditElement.textContent", coastline_block)

    def test_histolitt_attribution_requires_logos(self) -> None:
        """Vérifier que la citation HISTOLITT inclut bien les logos IGN et SHOM exigés.

        Contrairement à Limite terre-mer (simple citation textuelle), la
        licence d'HISTOLITT exige les logos IGN et SHOM avec liens dès lors
        que la donnée est représentée sur une interface.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn('coastline.layer === "histolitt"', script)
        self.assertIn("www.ign.fr", script)
        self.assertIn("www.shom.fr", script)

    def test_map_container_ignores_forced_colors(self) -> None:
        """Vérifier que le mode Contraste élevé de Windows n'altère pas les couleurs de la carte.

        Les couleurs de la carte (mer, terre, tracé, points) codent une
        information réelle et doivent rester lisibles telles que définies,
        y compris pour les utilisateurs qui activent ce mode.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("forced-color-adjust:none", page)

    def test_map_has_real_h1_and_summary(self) -> None:
        """Vérifier que la carte a un vrai H1 (nom de route) et un résumé (points, distance).

        L'unité est écrite en toutes lettres (« milles nautiques »), jamais
        abrégée en « NM » : NVDA lit cette abréviation comme « nanomètre ».
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('<h1 id="map-route-name" tabindex="-1">', page)
        self.assertIn('id="map-route-summary"', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function updateRouteSummary", script)
        self.assertIn("milles nautiques", script)

    def test_map_export_segments_csv_button(self) -> None:
        """Vérifier la présence du bouton d'export CSV des segments, identique à l'éditeur."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="export-segments-csv" type="button" class="secondary" disabled', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function exportSegmentsCsvFromMap", script)
        self.assertIn("buildSegmentsCsvRows(segments, separator)", script)

    def test_map_export_svg_button(self) -> None:
        """Vérifier la présence et le câblage du bouton d'export SVG de la carte."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="export-map-svg" type="button" class="secondary" disabled', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function exportMapSvg", script)
        self.assertIn("function buildMapSvgString", script)
        self.assertIn('exportFileTypes("svg")', script)
        file_dialogs_script = (ROOT / "sara_route_manager/static/js/file_dialogs.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("svg: [", file_dialogs_script)

    def test_map_buttons_in_side_column(self) -> None:
        """Vérifier que les 3 boutons sont en colonne à droite de la carte, pas empilés en dessous.

        Les écrans sont en général plus larges que hauts : une colonne
        latérale laisse à la carte toute la hauteur disponible, plutôt
        que de risquer de pousser les boutons hors champ sur une fenêtre
        haute mais peu large. Le côté (droite, pas gauche) est géré par
        CSS `order`, pas par l'ordre du DOM, pour ne pas changer l'ordre
        de lecture/tabulation.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('class="map-layout"', page)
        self.assertIn('class="map-side-actions"', page)
        self.assertIn("order: 2", page)
        self.assertIn("order: 1", page)
        # Les 3 boutons doivent se trouver à l'intérieur de la colonne d'actions.
        side_actions_block = page.split('class="map-side-actions"')[1].split("</div>")[0]
        for button_id in ("export-segments-csv", "export-map-svg", "close-map-window"):
            self.assertIn(f'id="{button_id}"', side_actions_block)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn('map.invalidateSize()', script)

    def test_map_page_uses_full_width(self) -> None:
        """Vérifier que la fenêtre carte utilise bien toute la largeur disponible.

        Deux corrections nécessaires, pas une seule : `main.css` limite
        `<main>` à 82rem (pensé pour la lisibilité des pages de texte, pas
        pertinent ici) — mais neutraliser seulement `max-width` ne suffit
        pas. Le `margin:auto` de main.css, en contexte flexbox (body étant
        `display:flex`), fait que l'élément se réduit à la largeur de son
        contenu et se centre au lieu de s'étirer, même sans `max-width`.
        Repéré après un test réel montrant un grand espace vide à gauche.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("max-width: none", page)
        self.assertIn("margin: 0; width: 100%", page)

    def test_map_page_has_no_redundant_header(self) -> None:
        """Vérifier que le bandeau d'en-tête redondant a été retiré.

        Cette fenêtre n'a pas de menu de navigation à identifier comme les
        5 pages principales, et le titre de la fenêtre Windows porte déjà
        l'information — répéter « SARA Route Manager » / « Carte de la
        route » dans le contenu n'apporte rien et coûte de la place. Le H1
        (nom de la route) doit être le premier élément visible.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertNotIn('<header class="site-header">', page)
        self.assertNotIn('<p class="app-name">SARA Route Manager</p>', page)
        main_content = page.split('<main id="main-content"')[1]
        self.assertTrue(main_content.lstrip().startswith('tabindex="-1" role="main">\n    <h1 id="map-route-name"'))

    def test_map_has_breathing_room_around_content(self) -> None:
        """Vérifier qu'une petite bande sépare le cadre de la fenêtre du contenu (dont la carte)."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("padding: 1.25rem", page)

    def test_map_marks_filter_present(self) -> None:
        """Vérifier la présence du filtre par catégorie de marques SHOM.

        Chaque case doit utiliser la classe `.checkbox` déjà établie dans
        l'application (voir `configuration.html`) : sans elle, la case
        hérite de la règle générique `input{width:34rem}` prévue pour les
        champs texte, la rendant démesurée et effectivement invisible dans
        la colonne étroite — constaté sur capture d'écran réelle.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="marks-filter"', page)
        for category in (
            "Latérale", "Cardinale", "Danger isolé", "Eaux saines",
            "Marque spéciale", "Amer", "Autre",
        ):
            self.assertIn(f'value="{category}"', page)
        self.assertEqual(page.count('class="checkbox">'), 11)

    def test_map_labels_have_reduced_font_size(self) -> None:
        """Vérifier que les étiquettes de la carte et du filtre ont une taille réduite.

        Les étiquettes héritaient de la taille de texte générale de
        l'application (1,1rem), contribuant au chevauchement dans les
        secteurs denses de la carte — constaté sur capture d'écran réelle.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn(".leaflet-tooltip { font-size: 0.75rem; }", page)
        self.assertIn("#marks-filter { border: 1px solid currentColor; border-radius: 0.25rem; padding: 0.5rem 0.75rem; margin: 0; font-size: 0.85rem; }", page)

    def test_map_colors_come_only_from_configuration(self) -> None:
        """Vérifier que les couleurs (mer, terre, tracé) sont des préférences durables.

        Option A retenue après discussion : réglables uniquement en page
        Configuration, pas d'ajustement en direct dans la fenêtre carte —
        pour ne pas la surcharger. Les sélecteurs de couleur qui y
        figuraient un temps ont été retirés.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertNotIn('id="sea-color-picker"', page)
        self.assertNotIn('id="land-color-picker"', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("async function loadDisplayColors", script)
        self.assertIn("currentRouteColor = data.configuration.map_route_color || currentRouteColor;", script)
        self.assertIn("map.getContainer().style.background = currentSeaColor;", script)
        self.assertIn("fillColor: currentLandColor", script)
        self.assertIn("color: currentRouteColor", script)

    def test_map_route_color_configurable(self) -> None:
        """Vérifier que la couleur du tracé de route est configurable, jaune vif par défaut.

        Signalé après test réel : l'orange initialement utilisé n'offrait
        pas un contraste suffisant sur le fond de mer.
        """
        config_script = (ROOT / "sara_route_manager/configuration.py").read_text(encoding="utf-8")
        self.assertIn('map_route_color: str = "#ffe600"', config_script)
        page = (ROOT / "sara_route_manager/templates/configuration.html").read_text(encoding="utf-8")
        self.assertIn('id="map-route-color" type="color"', page)

    def test_map_route_line_style_configurable(self) -> None:
        """Vérifier que l'épaisseur et le type de trait du tracé sont configurables."""
        config_script = (ROOT / "sara_route_manager/configuration.py").read_text(encoding="utf-8")
        self.assertIn('map_route_line_width: int = 3', config_script)
        self.assertIn('map_route_line_style: str = "solid"', config_script)
        page = (ROOT / "sara_route_manager/templates/configuration.html").read_text(encoding="utf-8")
        self.assertIn('id="map-route-line-width" type="number" min="1" max="10"', page)
        self.assertIn('id="map-route-line-style"', page)
        for option in ("solid", "dashed", "dotted"):
            self.assertIn(f'value="{option}"', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function routeDashArrayForStyle", script)
        self.assertIn("weight: currentRouteLineWidth,", script)

    def test_map_route_labels_settings_configurable(self) -> None:
        """Vérifier les réglages de taille et d'encadrement des étiquettes de points de route."""
        config_script = (ROOT / "sara_route_manager/configuration.py").read_text(encoding="utf-8")
        self.assertIn("map_route_labels_visible: bool = True", config_script)
        self.assertIn("map_route_label_font_size: int = 12", config_script)
        self.assertIn("map_route_label_bordered: bool = True", config_script)
        page = (ROOT / "sara_route_manager/templates/configuration.html").read_text(encoding="utf-8")
        self.assertIn('id="map-route-labels-visible" type="checkbox"', page)
        self.assertIn('id="map-route-label-font-size" type="number" min="8" max="24"', page)
        self.assertIn('id="map-route-label-bordered" type="checkbox"', page)

    def test_map_route_labels_live_toggle_in_addition_to_configuration(self) -> None:
        """Vérifier la case à cocher en direct pour les étiquettes de points de route.

        Demandée explicitement en plus du réglage par défaut en
        Configuration : le rendu par défaut (texte trop grand, encadrés qui
        masquent des éléments de la carte) justifiait un accès rapide,
        sans repasser par la Configuration à chaque fois — contrairement
        aux couleurs (option A, Configuration uniquement).
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="toggle-route-labels" type="checkbox"', page)
        self.assertIn("#map-container.hide-route-labels .route-point-tooltip { display: none; }", page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn(
            'document.getElementById("map-container").classList.toggle("hide-route-labels", !event.target.checked);',
            script,
        )
        self.assertIn('className: "route-point-tooltip"', script)
        self.assertIn("tooltipElement.style.fontSize = `${currentRouteLabelFontSize}px`;", script)

    def test_map_route_label_frame_toggle(self) -> None:
        """Vérifier que l'absence d'encadrement garde le texte lisible (contour sombre)."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("#map-container.route-label-no-frame .route-point-tooltip {", page)
        self.assertIn("text-shadow: 0 0 3px #000, 0 0 3px #000;", page)

    def test_map_grid_toggle(self) -> None:
        """Vérifier la case à cocher et les fonctions de construction de la grille latitude/longitude."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="toggle-grid" type="checkbox"', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function niceGridStep", script)
        self.assertIn("function buildGrid", script)
        self.assertIn("function toggleGrid", script)

    def test_map_nautical_scale_control(self) -> None:
        """Vérifier l'ajout d'une échelle en milles nautiques, absente du contrôle natif de Leaflet."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function addNauticalScaleControl", script)
        self.assertIn('position: "bottomright"', script)
        self.assertIn("/ 1852", script)  # conversion mètres -> milles nautiques
        self.assertIn("addNauticalScaleControl(currentMap);", script)

    def test_map_scale_bar_uses_milles_not_nm(self) -> None:
        """Vérifier que la barre d'échelle affiche « Milles » et non « NM ».

        Même défaut que celui déjà corrigé ailleurs dans l'application
        (NVDA lit « NM » comme « nanomètre ») — ajouté après coup (phase B)
        sans reprendre cette correction, repéré après signalement.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("bar.textContent = `${chosenNm} Milles`;", script)
        self.assertNotIn("bar.textContent = `${chosenNm} NM`;", script)

    def test_map_alt_f4_closes_window(self) -> None:
        """Vérifier que Alt+F4 est intercepté explicitement pour fermer la fenêtre carte.

        Signalé sans effet malgré la prise en charge native habituelle de
        Windows — interception explicite en repli, sur le même chemin que
        le bouton « Fermer » (factorisé dans `closeMapWindow`).
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function closeMapWindow() {", script)
        self.assertIn('document.getElementById("close-map-window").addEventListener("click", closeMapWindow);', script)
        self.assertIn('if (event.altKey && event.key === "F4") {', script)

    def test_map_hover_announces_marker_name(self) -> None:
        """Vérifier l'annonce vocale au survol d'un marqueur (route et marques SHOM).

        Via la zone `#map-status` déjà en place, plutôt que de compter sur
        la fonction native NVDA « Annoncer l'objet sous la souris »
        (dépend d'un réglage que l'utilisateur doit activer lui-même).
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn(
            'const preciseType = describeMarkType(point.type || point.source || "Inconnu", point.icon_filename);',
            script,
        )
        self.assertIn('announce(`${label} — ${preciseType}`);', script)
        self.assertIn(
            'announce(`${mark.name || category} — ${describeMarkType(category, mark.icon_filename)}`);',
            script,
        )

    def test_map_marker_size_configurable(self) -> None:
        """Vérifier que la taille des icônes SHOM est configurable, pas figée en dur."""
        config_script = (ROOT / "sara_route_manager/configuration.py").read_text(encoding="utf-8")
        self.assertIn("map_marker_size: int = 20", config_script)
        page = (ROOT / "sara_route_manager/templates/configuration.html").read_text(encoding="utf-8")
        self.assertIn('id="map-marker-size" type="number" min="10" max="60"', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("currentMarkerSize = data.configuration.map_marker_size || currentMarkerSize;", script)
        self.assertIn("iconSize: [currentMarkerSize, currentMarkerSize * 2],", script)

    def test_map_nautical_tick_marks_share_scale_bar_step(self) -> None:
        """Vérifier que les graduations des bords utilisent le même pas que la barre d'échelle.

        Demandé explicitement : si la barre d'échelle affiche « 2 Milles »,
        les graduations doivent se répéter tous les 2 milles nautiques, à
        toute échelle — d'où la mutualisation du calcul du pas
        (`computeNiceNauticalStep`) entre les deux fonctions.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function computeNiceNauticalStep(map) {", script)
        self.assertIn("const {chosenNm, totalNm, mapWidthPx} = computeNiceNauticalStep(this._leafletMap);", script)
        self.assertIn("const {chosenNm} = computeNiceNauticalStep(map);", script)
        self.assertIn("function addNauticalTickMarks(map) {", script)
        self.assertIn("addNauticalTickMarks(currentMap);", script)

    def test_map_nautical_tick_marks_cover_all_four_edges(self) -> None:
        """Vérifier que les graduations couvrent bien les 4 bords de la carte (haut/bas/gauche/droite)."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        for edge_class in (
            "nautical-tick-vertical nautical-tick-top",
            "nautical-tick-vertical nautical-tick-bottom",
            "nautical-tick-horizontal nautical-tick-left",
            "nautical-tick-horizontal nautical-tick-right",
        ):
            self.assertIn(f'"{edge_class}"', script)
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn(".nautical-tick-overlay { position: absolute; top: 0; left: 0; pointer-events: none; }", page)

    def test_map_mark_labels_toggle(self) -> None:
        """Vérifier la case à cocher pour afficher/masquer uniquement les noms des marques SHOM.

        Les étiquettes des points de la route elle-même ne doivent jamais
        être masquables par ce bouton (nécessaires au repérage) — seules
        celles des marques SHOM environnantes, identifiées par la classe
        CSS dédiée `mark-tooltip`.

        Corrigé après signalement : les infobulles des marques n'étaient
        pas permanentes (`permanent: true` absent), donc jamais visibles
        par défaut — cocher/décocher la case n'avait alors aucun effet
        observable, faute de label à masquer.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="toggle-mark-labels" type="checkbox" checked', page)
        self.assertIn("#map-container.hide-mark-labels .mark-tooltip { display: none; }", page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn('className: "mark-tooltip"', script)
        self.assertIn('classList.toggle("hide-mark-labels", !event.target.checked)', script)
        self.assertIn(
            'marker.bindTooltip(mark.name || category, {permanent: true, direction: "top", offset: [0, -10], className: "mark-tooltip"});',
            script,
        )

    def test_marks_category_filter_does_not_catch_labels_toggle(self) -> None:
        """Vérifier que le filtre par catégorie ne capture pas la case des noms de marques.

        La case « Afficher les noms des marques » vit dans le même
        `<fieldset>` que les 7 cases de catégorie : sans une classe
        distincte, le sélecteur générique du filtre par catégorie
        l'attrapait aussi par erreur (sans planter grâce à une protection
        déjà en place, mais un comportement non voulu).
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("marks-category-checkbox"), 7)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("#marks-filter .marks-category-checkbox", script)
        self.assertNotIn('#marks-filter input[type="checkbox"]', script)

    def test_measure_tool_dialog_present(self) -> None:
        """Vérifier la présence de la boîte de dialogue de résultat de mesure.

        Même structure accessible que la boîte de dialogue « modifications
        non enregistrées » de l'éditeur : role="alertdialog", focus initial
        sur un bouton (pas le titre), piège de focus, Échap pour fermer.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="measure-dialog" class="modal-dialog" role="alertdialog" aria-modal="true"', page)
        self.assertIn('id="measure-dialog-copy" type="button"', page)
        self.assertIn('id="measure-dialog-close" type="button" class="secondary"', page)
        self.assertIn('id="toggle-measure-tool" type="checkbox"', page)

    def test_measure_tool_dialog_focus_trap(self) -> None:
        """Vérifier le piège de focus et le focus initial sur un bouton, pas le titre."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn('document.getElementById("measure-dialog-copy").focus();', script)
        self.assertIn('measureDialog.addEventListener("keydown"', script)
        self.assertIn('event.key === "Escape"', script)
        self.assertIn('event.key === "Tab"', script)

    def test_measure_tool_disables_dragging_while_active(self) -> None:
        """Vérifier que le mode mesure désactive le déplacement normal de la carte.

        Sans ça, le même geste de clic-glisser servirait à la fois à
        déplacer le cadre et à mesurer un segment, ce qui serait ambigu.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("map.dragging.disable();", script)
        self.assertIn("map.dragging.enable();", script)

    def test_measure_tool_uses_shared_route_math(self) -> None:
        """Vérifier que la mesure réutilise segmentDistanceNm/segmentInitialBearing.

        Ce sont les mêmes fonctions mutualisées (`route_math.js`) que celles
        utilisées pour l'analyse de route et l'export CSV des segments —
        pas un second calcul de distance/cap dupliqué.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("const distanceNm = segmentDistanceNm(startPoint, endPoint);", script)
        self.assertIn("const bearingDegrees = segmentInitialBearing(startPoint, endPoint);", script)

    def test_measure_tool_ignores_near_zero_segments(self) -> None:
        """Vérifier qu'un simple clic (sans glisser) n'ouvre pas la boîte de dialogue."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("if (distanceNm < 0.001) return;", script)

    def test_measure_tool_copy_announces_to_nvda(self) -> None:
        """Vérifier que le bouton Copier annonce le résultat à NVDA après la copie."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("await navigator.clipboard.writeText(lastMeasureText);", script)
        self.assertIn('announce("Mesure copiée dans le presse-papiers.");', script)


    def test_marker_info_dialog_present_and_accessible(self) -> None:
        """Vérifier la présence de la boîte de dialogue d'informations sur une marque.

        Même structure accessible que la boîte de dialogue de mesure :
        role="alertdialog", focus initial sur le bouton « Copier » (pas le
        titre), piège de focus Tab/Maj+Tab, Échap pour fermer.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn('id="marker-info-dialog" class="modal-dialog" role="alertdialog" aria-modal="true"', page)
        self.assertIn('id="marker-info-dialog-copy" type="button"', page)
        self.assertIn('id="marker-info-dialog-close" type="button" class="secondary"', page)
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn('document.getElementById("marker-info-dialog-copy").focus();', script)
        self.assertIn('markerInfoDialog.addEventListener("keydown"', script)
        self.assertIn('event.key === "Escape"', script)

    def test_marker_info_dialog_displays_three_separate_lines(self) -> None:
        """Vérifier que le texte s'affiche sur 3 lignes distinctes, pas sur une seule.

        Signalé après retour utilisateur : sans cette règle, les retours à
        la ligne (\\n) du texte étaient ignorés par le navigateur et tout
        s'affichait sur une seule ligne, bien que le contenu logique (pour
        la copie presse-papiers) reste correctement structuré en 3 lignes.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("#marker-info-dialog-description { white-space: pre-line; }", page)

    def test_double_click_opens_marker_info_dialog(self) -> None:
        """Vérifier que le double-clic ouvre la boîte de dialogue, pour un point de route et une marque SHOM.

        Affiche le type de source (route ou SHOM) et le type de balise,
        demandé explicitement.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn(
            'const preciseType = describeMarkType(point.type || point.source || "Inconnu", point.icon_filename);',
            script,
        )
        self.assertIn('openMarkerInfoDialog(label, "Point de la route", preciseType);', script)
        self.assertIn(
            'openMarkerInfoDialog(mark.name || category, "Marque SHOM environnante", describeMarkType(category, mark.icon_filename));',
            script,
        )
        self.assertIn("function openMarkerInfoDialog(name, source, type) {", script)
        self.assertIn(
            "lastMarkerInfoText = `Nom : ${name}\\nType : ${type}\\nSource : ${source}`;", script
        )

    def test_marker_type_precised_with_direction_or_side(self) -> None:
        """Vérifier que le type précis (direction cardinale ou côté latéral) est déduit de l'icône.

        Signalé après retour utilisateur : la catégorie générale
        (« Cardinale », « Latérale ») ne suffisait pas à identifier
        précisément une marque — la direction (Nord/Est/Sud/Ouest) ou le
        côté (bâbord/tribord) manquait. Déduits du nom de fichier de
        l'icône déjà résolue côté serveur (`shom_icons.py`), sans requête
        supplémentaire.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function describeMarkType(category, iconFilename) {", script)
        self.assertIn('const cardinalDirections = {N: "Nord", E: "Est", S: "Sud", W: "Ouest"};', script)
        self.assertIn(
            'const lateralMatch = iconFilename.match(/^(?:BCNLAT|BOYLAT)_([BT])/);', script
        )
        self.assertIn('lateralMatch[1] === "B" ? "bâbord" : "tribord"', script)


    def test_map_js_renders_marks_with_icons_and_fallback(self) -> None:
        """Vérifier le rendu des marques : icône SHOM si disponible, cercle générique sinon."""
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("function fetchMarks", script)
        self.assertIn("function renderMarks", script)
        self.assertIn("/static/vendor/shom_icons/${mark.icon_filename}", script)
        self.assertIn("iconAnchor: [currentMarkerSize / 2, currentMarkerSize]", script)
        self.assertIn("L.circleMarker([mark.latitude, mark.longitude]", script)
        # Un échec de récupération des marques ne doit jamais bloquer
        # l'affichage déjà réussi de la route et du trait de côte.
        marks_block = script.split("// Même principe pour les marques SHOM")[1]
        self.assertIn("catch (error)", marks_block)

    def test_map_js_renders_route_points_with_icon_when_available(self) -> None:
        """Vérifier que les points de la route eux-mêmes utilisent leur icône IALA si disponible.

        C'est le pendant, pour les points de la route, de ce qui existe
        déjà pour les marques SHOM environnantes (option B) : l'icône est
        déjà résolue côté serveur (`/api/map/data`), il ne reste qu'à
        l'utiliser côté client.
        """
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        self.assertIn("/static/vendor/shom_icons/${point.icon_filename}", script)
        self.assertIn("L.marker([point.latitude, point.longitude], {icon})", script)
        # Le repli générique (cercle rouge) doit rester disponible pour un
        # point sans type d'origine (saisie manuelle, ou route reçue de
        # SARA Navigation).
        self.assertIn("fillColor: \"#d40000\"", script)

    def test_shom_icons_vendored_locally(self) -> None:
        """Vérifier que les 53 icônes officielles du SHOM sont bien vendues localement."""
        icons_dir = ROOT / "sara_route_manager/static/vendor/shom_icons"
        svg_files = list(icons_dir.glob("*.svg"))
        self.assertEqual(len(svg_files), 53)

    def test_map_side_buttons_can_wrap_to_two_lines(self) -> None:
        """Vérifier que le texte des boutons de la colonne latérale peut revenir à la ligne.

        Les boutons sont empilés verticalement avec de la place en dessous :
        un libellé long qui passe sur 2 lignes reste lisible, plutôt que de
        risquer un débordement si la colonne s'avère un peu étroite.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("white-space: normal", page)

    def test_map_title_and_summary_are_close(self) -> None:
        """Vérifier que l'espace entre le H1 et le résumé de route est resserré.

        La marge par défaut du navigateur sur un H1 (habituellement environ
        0,67em en haut et en bas) laissait un grand espace visible avant le
        résumé juste en dessous, constaté sur capture d'écran réelle.
        """
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        self.assertIn("#map-route-name { margin-bottom: 0.3rem; }", page)
        self.assertIn("#map-route-summary { margin-top: 0; }", page)

    def test_sea_color_is_saturated(self) -> None:
        """Vérifier que la couleur de la mer reste un bleu franc, pas un pastel clair."""
        page = (ROOT / "sara_route_manager/templates/map.html").read_text(encoding="utf-8")
        script = (ROOT / "sara_route_manager/static/js/map.js").read_text(encoding="utf-8")
        for source in (page, script):
            self.assertIn("#1f6fa3", source)
            self.assertNotIn("#dceefb", source)
            self.assertNotIn("#3f7cb0", source)


if __name__ == "__main__":
    unittest.main()
