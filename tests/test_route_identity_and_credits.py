# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_route_identity_and_credits
Description : Vérifie la préservation du seuil MOB, la stabilité de l'id de
route entre deux enregistrements, le masquage du champ nom une fois la route
active, le lien vers le site d'Orion Brest, et la boîte de dialogue à 3 choix
avant de quitter l'éditeur avec des modifications non enregistrées.
Classes présentes :
- RouteIdentityAndCreditsTests : test_mob_threshold_preserved,
  test_route_id_sent_in_payload, test_route_name_field_hideable,
  test_rename_button_present, test_orion_brest_link,
  test_leave_route_dialog_markup, test_leave_route_dialog_behaviour,
  test_modal_dialog_css_hidden_rule.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RouteIdentityAndCreditsTests(unittest.TestCase):
    """Contrôler les corrections issues de la comparaison avec le code iOS."""

    def test_mob_threshold_preserved(self) -> None:
        """Vérifier qu'un seuil à 0 (point MOB) n'est plus remplacé par 100."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function normalizeDistanceThreshold", script)
        self.assertNotIn("distance_threshold: Number(point.distance_threshold || 100)", script)
        self.assertIn("distance_threshold: normalizeDistanceThreshold(point.distance_threshold)", script)

    def test_route_id_sent_in_payload(self) -> None:
        """Vérifier que l'id de la route active est transmis, pas régénéré à chaque envoi."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("let routeId = null;", script)
        self.assertIn("routeId = id || crypto.randomUUID();", script)
        self.assertIn("return {id: routeId, name:", script)

    def test_route_name_field_hideable(self) -> None:
        """Vérifier que le champ nom peut être masqué et révélé à la demande."""
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="route-name-field"', editor)
        self.assertIn('id="rename-route-action" class="actions" hidden', editor)
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('$("route-name-field").hidden = routeActive && !renamingRoute;', script)
        self.assertIn("function startRenamingRoute", script)
        self.assertIn("function stopRenamingRoute", script)

    def test_rename_button_present(self) -> None:
        """Vérifier la présence et le câblage du bouton Renommer la route."""
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="rename-route" type="button" class="secondary">Renommer la route</button>', editor)
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('$("rename-route").onclick = startRenamingRoute;', script)

    def test_orion_brest_link(self) -> None:
        """Vérifier le bouton d'ouverture du site d'Orion Brest et sa cible serveur."""
        about = (ROOT / "sara_route_manager/templates/about.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="open-orion-brest-website"', about)
        webapp = (ROOT / "sara_route_manager/webapp.py").read_text(encoding="utf-8")
        self.assertIn('"orion_brest_website": "https://orion-brest.com/SARA.html"', webapp)

    def test_leave_route_dialog_markup(self) -> None:
        """Vérifier la structure accessible de la boîte de dialogue à 3 choix."""
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="leave-route-dialog" class="modal-dialog" role="alertdialog" aria-modal="true"', editor)
        for button_id in ("leave-route-save", "leave-route-discard", "leave-route-cancel"):
            self.assertIn(f'id="{button_id}"', editor)

    def test_leave_route_dialog_behaviour(self) -> None:
        """Vérifier l'ouverture conditionnelle, le piège de focus et Échap."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function openLeaveRouteDialog", script)
        self.assertIn("function closeLeaveRouteDialog", script)
        # Le focus initial doit se poser sur un bouton, pas sur le titre : un
        # titre n'est pas un contrôle interactif et certains lecteurs d'écran
        # ne basculent pas de façon fiable en mode formulaire sinon.
        self.assertIn('$("leave-route-save").focus();', script)
        self.assertIn('if (event.key === "Escape")', script)
        self.assertIn("if (!routeDirty) return;", script)
        self.assertNotIn("window.confirm(", script)
        self.assertIn("$(\"leave-route-save\").onclick", script)
        self.assertIn("$(\"leave-route-discard\").onclick", script)
        self.assertIn("$(\"leave-route-cancel\").onclick", script)
        # Le choix « Retourner sans enregistrer » ne doit pas redéclencher
        # l'invite générique « Quitter ce site ? » du navigateur : l'utilisateur
        # vient déjà de confirmer explicitement l'abandon dans notre propre
        # boîte de dialogue.
        self.assertIn("routeDirty = false;\n    window.location.href = \"/routes\";", script)

    def test_modal_dialog_css_hidden_rule(self) -> None:
        """Vérifier que .modal-dialog[hidden] restaure bien display:none."""
        css = (ROOT / "sara_route_manager/static/css/main.css").read_text(
            encoding="utf-8"
        )
        self.assertIn(".modal-dialog[hidden]", css)


if __name__ == "__main__":
    unittest.main()
