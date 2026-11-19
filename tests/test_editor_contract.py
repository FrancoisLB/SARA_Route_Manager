# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_editor_contract
Description : Vérifie les contrats statiques essentiels de l'éditeur unifié.
Classes présentes :
- EditorContractTests : test_active_point_contract, test_normalize_preserves_object_code,
  test_documented_version.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EditorContractTests(unittest.TestCase):
    """Contrôler les éléments structurants de l'éditeur et de la livraison."""

    def test_active_point_contract(self) -> None:
        """Vérifier que détails et copie utilisent la sélection logique unique."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function getActivePoint()", script)
        self.assertIn("function setActivePoint(", script)
        self.assertGreaterEqual(script.count("const point = getActivePoint();"), 3)
        self.assertIn('$("copy-info").disabled = !hasActivePoint;', script)
        self.assertIn('$("copy-coordinates").disabled = !hasActivePoint;', script)

    def test_normalize_preserves_object_code(self) -> None:
        """Vérifier que normalize() conserve object_code (option B).

        Sans ce champ, une marque SHOM ajoutée à une route perdait son
        type d'origine dès la composition côté client, avant même
        d'atteindre le serveur — l'option B ne peut fonctionner que si ce
        champ survit à cette étape.
        """
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('object_code: point.object_code || "",', script)

    def test_documented_version(self) -> None:
        """Vérifier la cohérence du numéro de version principal."""
        self.assertEqual((ROOT / "VERSION.txt").read_text(encoding="utf-8").strip(), "0.9.4")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("SARA Route Manager 0.9.4", readme)


if __name__ == "__main__":
    unittest.main()
