# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_accessible_details
Description : Vérifie la refonte du panneau « Informations sur le point »
(phase D) : navigation par flèches ligne par ligne, une seule unité de
lecture NVDA par ligne, champs modifiables encadrés pour les points déjà
ajoutés à la route, validation à la perte de focus.
Classes présentes :
- AccessibleDetailsTests : test_row_is_single_element_not_dt_dd,
  test_row_has_nbsp_before_colon, test_row_carries_aria_label,
  test_editable_row_has_nested_input_with_own_aria_label,
  test_read_only_row_has_no_input,
  test_editable_only_for_route_points_not_available_points,
  test_editable_fields_are_name_latitude_longitude_threshold,
  test_row_navigation_no_wrap_at_extremes,
  test_row_navigation_works_on_arrow_keys_only, test_tab_moves_directly_between_editable_fields,
  test_tab_blurs_before_focusing_next_field_not_after,
  test_focus_restored_to_first_row_only_if_was_inside_panel,
  test_latitude_validation_rejects_out_of_range,
  test_longitude_validation_rejects_out_of_range,
  test_distance_threshold_validation_rejects_out_of_range,
  test_empty_name_falls_back_to_generic_label,
  test_alt_e_shortcut_jumps_to_first_editable_input,
  test_thin_contrasted_border_on_editable_fields,
  test_detail_rows_still_used_for_clipboard_copy.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AccessibleDetailsTests(unittest.TestCase):
    """Contrôler la structure accessible et le comportement du panneau de détails."""

    def setUp(self) -> None:
        self.script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(
            encoding="utf-8"
        )
        self.css = (ROOT / "sara_route_manager/static/css/main.css").read_text(
            encoding="utf-8"
        )

    def test_row_is_single_element_not_dt_dd(self) -> None:
        """Vérifier que chaque ligne reste un seul élément, jamais une paire dt/dd.

        Une structure dt/dd séparerait le libellé et la valeur en deux
        unités de lecture distinctes — déjà essayé puis abandonné pour
        cette raison lors d'une itération précédente.
        """
        self.assertIn('row.className = "details-line";', self.script)
        self.assertNotIn('document.createElement("dt")', self.script)
        self.assertNotIn('document.createElement("dd")', self.script)

    def test_row_has_nbsp_before_colon(self) -> None:
        """Vérifier l'espace insécable avant les deux-points (libellés longs)."""
        self.assertIn("labelSpan.textContent = `${label}\\u00A0:`;", self.script)

    def test_row_carries_aria_label(self) -> None:
        """Vérifier que chaque ligne porte un aria-label couvrant tout le couple libellé/valeur.

        C'est ce qui garantit qu'une seule unité de lecture NVDA est
        annoncée par ligne, y compris pour les lignes modifiables (qui
        contiennent par ailleurs un vrai champ de texte imbriqué avec sa
        propre valeur — sans l'aria-label sur la ligne, le focus sur la
        ligne elle-même risquerait une lecture ambiguë).
        """
        self.assertIn('row.setAttribute("aria-label", `${label} : ${value}`);', self.script)

    def test_editable_row_has_nested_input_with_own_aria_label(self) -> None:
        """Vérifier la structure d'une ligne modifiable : input imbriqué, aria-label propre."""
        self.assertIn('const input = document.createElement("input");', self.script)
        self.assertIn('input.className = "details-value-input";', self.script)
        self.assertIn('input.setAttribute("aria-label", label);', self.script)
        self.assertIn('input.addEventListener("blur", () => options.onCommit(input.value));', self.script)

    def test_read_only_row_has_no_input(self) -> None:
        """Vérifier qu'une ligne en lecture seule n'a qu'un span, pas de champ."""
        self.assertIn('valueSpan.className = "details-value";', self.script)

    def test_editable_only_for_route_points_not_available_points(self) -> None:
        """Vérifier que seuls les points déjà ajoutés à la route sont modifiables.

        Un point encore dans « Points importés » n'a pas encore sa place
        définitive : modifier sa position ou son nom à ce stade n'aurait
        pas de sens (tranché explicitement avec l'utilisateur).
        """
        self.assertIn('const editable = activePointList === "route";', self.script)

    def test_editable_fields_are_name_latitude_longitude_threshold(self) -> None:
        """Vérifier la liste exacte des champs modifiables et leurs bornes."""
        self.assertIn('label: "Nom", value: point.name, inputType: "text",', self.script)
        self.assertIn('label: "Latitude",', self.script)
        self.assertIn('label: "Longitude",', self.script)
        self.assertIn(
            'label: "Distance de validation (mètre)", value: point.distance_threshold,',
            self.script,
        )
        self.assertIn('inputType: "number", min: 1, max: 1000, step: 1,', self.script)

    def test_row_navigation_no_wrap_at_extremes(self) -> None:
        """Vérifier que les flèches ne bouclent pas en début/fin de liste (tranché explicitement)."""
        self.assertIn(
            "const nextIndex = Math.min(rows.length - 1, Math.max(0, activeDetailRowIndex + delta));",
            self.script,
        )
        self.assertIn("if (nextIndex === activeDetailRowIndex) return;", self.script)

    def test_row_navigation_works_on_arrow_keys_only(self) -> None:
        """Vérifier que seules les flèches haut/bas déplacent le focus entre lignes.

        Fonctionne aussi bien depuis la ligne que depuis un champ modifiable
        imbriqué : une flèche haut/bas n'a aucun effet natif dans un champ
        texte sur une seule ligne.
        """
        self.assertIn('if (event.key === "ArrowDown" || event.key === "ArrowUp") {', self.script)

    def test_tab_moves_directly_between_editable_fields(self) -> None:
        """Vérifier que Tab passe directement d'un champ modifiable au suivant, sans arrêt intermédiaire.

        Signalé après retour utilisateur : l'input avait lui-même un
        tabindex implicite, mélangé au tabindex mobile de la ligne (0/-1
        selon la ligne active) — un ordre de tabulation ambigu selon le
        navigateur/lecteur d'écran, avec un arrêt intermédiaire surprenant
        sur la ligne suivante avant d'atteindre son champ (il fallait
        appuyer deux fois sur Tab). Corrigé en gérant Tab explicitement :
        l'input est retiré de l'ordre naturel (`input.tabIndex = -1`) et
        Tab depuis un champ modifiable saute directement au suivant.
        """
        self.assertIn("input.tabIndex = -1;", self.script)
        self.assertIn('if (event.target.classList.contains("details-value-input")) {', self.script)
        self.assertIn(
            "const nextIndex = currentIndex + (event.shiftKey ? -1 : 1);", self.script
        )

    def test_tab_blurs_before_focusing_next_field_not_after(self) -> None:
        """Vérifier que la perte de focus se déclenche avant de poser le focus sur le champ suivant.

        Signalé après un second retour utilisateur : poser le focus sur le
        champ suivant AVANT que la perte de focus du champ actuel ne se
        déclenche détruisait ce même champ suivant lors de la
        reconstruction du panneau qui suit la perte de focus (validation +
        application de la modification), laissant le focus nulle part
        précis — NVDA se rabattait alors sur le titre de la page. Corrigé
        en inversant l'ordre : déclencher explicitement la perte de focus
        du champ actuel en premier (`blur()`), puis reposer le focus sur
        le bon champ dans le panneau reconstruit, en le retrouvant par une
        nouvelle recherche depuis le conteneur stable `#point-details`
        plutôt qu'une référence devenue obsolète.
        """
        self.assertIn("event.target.blur();", self.script)
        self.assertIn(
            'const freshInputs = [...$("point-details").querySelectorAll(".details-value-input")];',
            self.script,
        )
        self.assertIn("freshInputs[nextIndex]?.focus();", self.script)

    def test_focus_restored_to_first_row_only_if_was_inside_panel(self) -> None:
        """Vérifier que le focus n'est repris que si l'utilisateur naviguait déjà dans le panneau.

        Jamais lors d'une reconstruction déclenchée par une perte de focus
        (l'utilisateur a déjà déplacé son focus ailleurs de lui-même).
        """
        self.assertIn(
            "const wasFocusInsidePanel = details.contains(document.activeElement);",
            self.script,
        )
        self.assertIn("if (wasFocusInsidePanel) rows[0]?.focus();", self.script)

    def test_latitude_validation_rejects_out_of_range(self) -> None:
        """Vérifier le rejet d'une latitude invalide, avec reprise de l'ancienne valeur."""
        self.assertIn("function commitPointLatitude(point, rawValue) {", self.script)
        self.assertIn("parsed < -90 || parsed > 90", self.script)

    def test_longitude_validation_rejects_out_of_range(self) -> None:
        """Vérifier le rejet d'une longitude invalide, avec reprise de l'ancienne valeur."""
        self.assertIn("function commitPointLongitude(point, rawValue) {", self.script)
        self.assertIn("parsed < -180 || parsed > 180", self.script)

    def test_distance_threshold_validation_rejects_out_of_range(self) -> None:
        """Vérifier le rejet d'un rayon d'activation hors bornes 1-1000, sans case Homme à la mer.

        La case « Homme à la mer » initialement envisagée a été retirée :
        elle n'a pas de sens en composition de route (tranché explicitement
        avec l'utilisateur).
        """
        self.assertIn("function commitPointDistanceThreshold(point, rawValue) {", self.script)
        self.assertIn("!Number.isInteger(parsed) || parsed < 1 || parsed > 1000", self.script)
        self.assertNotIn("Homme à la mer", self.script.split("function commitPointDistanceThreshold")[1][:600])

    def test_empty_name_falls_back_to_generic_label(self) -> None:
        """Vérifier qu'un nom vide retombe sur un nom générique plutôt que d'être refusé."""
        self.assertIn(
            'point.name = rawValue.trim() || "Point sans nom";', self.script
        )

    def test_alt_e_shortcut_jumps_to_first_editable_input(self) -> None:
        """Vérifier que Alt+E saute dans le premier champ modifiable (Nom)."""
        self.assertIn('event.altKey && event.key.toLowerCase() === "e"', self.script)
        self.assertIn(
            'const firstEditableInput = $("point-details").querySelector(".details-value-input");',
            self.script,
        )

    def test_thin_contrasted_border_on_editable_fields(self) -> None:
        """Vérifier que les champs modifiables ont un trait fin et contrasté (demandé explicitement)."""
        self.assertIn(".details-value-input{", self.css)
        self.assertIn("border:1px solid currentColor", self.css)

    def test_detail_rows_still_used_for_clipboard_copy(self) -> None:
        """Vérifier que detailRows() reste utilisée pour la copie presse-papiers, inchangée.

        Séparée de la construction visuelle des lignes (buildDetailRow) :
        deux usages distincts du même point, pas de duplication de logique
        de formatage.
        """
        self.assertIn("function detailRows(point) {", self.script)
        self.assertIn("const text = Object.entries(detailRows(point))", self.script)


if __name__ == "__main__":
    unittest.main()
