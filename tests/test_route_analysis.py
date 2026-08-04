# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_route_analysis
Description : Vérifie les titres accessibles, les compteurs et l’export des segments.
Classes présentes :
- RouteAnalysisTests
  - test_list_headings_and_f6_zones
  - test_route_analysis_section
  - test_segment_csv_contract
  - test_route_math_loaded_globally
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RouteAnalysisTests(unittest.TestCase):
    """Contrôler le contrat HTML et JavaScript de l’analyse de route."""

    def test_list_headings_and_f6_zones(self) -> None:
        """Vérifier les titres H3, compteurs et zones F6 des deux listes."""
        template = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="available-heading" tabindex="-1">Points importés : 0</h3>', template)
        self.assertIn('id="route-points-heading" tabindex="-1">Points de la route : 0</h3>', template)
        self.assertIn('data-zone-name="Points importés"', template)
        self.assertIn('data-zone-name="Points de la route"', template)
        self.assertIn('id="available-list"', template)
        self.assertIn('id="route-list"', template)

    def test_route_analysis_section(self) -> None:
        """Vérifier la présence de la synthèse et du bouton d’export."""
        template = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="route-analysis-heading"', template)
        # L'unité est écrite en toutes lettres (pas "NM") : NVDA lit
        # l'abréviation comme "nanomètre", pas "milles nautiques".
        self.assertIn('Distance totale : 0,00 milles nautiques', template)
        self.assertIn('Nombre de segments : 0', template)
        self.assertIn('id="export-segments-csv"', template)

    def test_segment_csv_contract(self) -> None:
        """Vérifier les calculs et l’ordre des colonnes du CSV de segments.

        Les fonctions de calcul (segmentDistanceNm, segmentInitialBearing,
        buildRouteSegments) sont mutualisées dans route_math.js depuis la
        0.7.0, pour être réutilisables par la fenêtre de visualisation
        cartographique — elles ne sont donc plus dans unified_editor.js.
        """
        math_script = (ROOT / "sara_route_manager/static/js/route_math.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function segmentDistanceNm", math_script)
        self.assertIn("function segmentInitialBearing", math_script)
        self.assertIn("function buildRouteSegments", math_script)
        self.assertIn("function buildSegmentsCsvRows", math_script)
        for column_name in (
            "Numero_segment",
            "Marque_debut",
            "Marque_fin",
            "Longueur_NM",
            "Cap_degres",
        ):
            self.assertIn(column_name, math_script)

        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function exportSegmentsCsv", script)
        self.assertIn("buildSegmentsCsvRows(segments, separator)", script)
        self.assertIn("configuration.csv_separator", script)
        self.assertIn('new Blob(["\\uFEFF"', script)

    def test_route_math_loaded_globally(self) -> None:
        """Vérifier que route_math.js est chargé depuis base.html, pour toutes les pages."""
        base = (ROOT / "sara_route_manager/templates/base.html").read_text(encoding="utf-8")
        self.assertIn("js/route_math.js", base)


if __name__ == "__main__":
    unittest.main()
