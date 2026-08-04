# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_shom_icons
Description : Vérifie la sélection du fichier SVG officiel du SHOM à partir
des attributs S-57 d'une marque, contre les noms réels confirmés dans le
paquet officiel « Balisage maritime » (53 fichiers inspectés directement).
Classes présentes :
- TestSelectIconFilename : test_cardinal_marks, test_lateral_marks,
  test_lateral_bcnlat_has_no_iala_b_variant_without_topmark,
  test_plain_topmark_codes, test_single_icon_codes, test_landmark,
  test_unknown_code_returns_none, test_missing_category_returns_none.
- TestIsIalaRegionB : test_metropole_is_region_a, test_antilles_is_region_b,
  test_guyane_is_region_b, test_saint_pierre_et_miquelon_is_region_b,
  test_reunion_is_region_a.
- TestIconFilenameForMark : test_lateral_from_english_property_text,
  test_cardinal_from_english_property_text,
  test_topmark_detected_from_linkage_attribute,
  test_topmark_not_detected_when_linkage_empty,
  test_iala_region_b_applied_from_position,
  test_missing_category_property_returns_none.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from sara_route_manager.shom_icons import (
    icon_filename_for_mark,
    is_iala_region_b,
    select_icon_filename,
)


class TestSelectIconFilename:
    """Vérifier la sélection du fichier SVG, contre les noms réels du paquet officiel."""

    def test_cardinal_marks(self) -> None:
        """Vérifier les 4 directions cardinales, sans et avec voyant, balise et bouée."""
        assert select_icon_filename("BCNCAR", catcam=1) == "BCNCAR_N.svg"
        assert select_icon_filename("BCNCAR", catcam=2, has_topmark=True) == "BCNCAR_E_T.svg"
        assert select_icon_filename("BOYCAR", catcam=3) == "BOYCAR_S.svg"
        assert select_icon_filename("BOYCAR", catcam=4, has_topmark=True) == "BOYCAR_W_T.svg"

    def test_lateral_marks(self) -> None:
        """Vérifier bâbord/tribord, sans/avec voyant, et la variante région IALA B."""
        assert select_icon_filename("BCNLAT", catlam=1) == "BCNLAT_B.svg"
        assert select_icon_filename("BCNLAT", catlam=2, has_topmark=True) == "BCNLAT_T_T.svg"
        assert (
            select_icon_filename("BCNLAT", catlam=1, has_topmark=True, iala_region_b=True)
            == "BCNLAT_B_T_IALAB.svg"
        )
        # BOYLAT propose une variante région B même sans voyant, contrairement à BCNLAT.
        assert select_icon_filename("BOYLAT", catlam=2, iala_region_b=True) == "BOYLAT_T_IALAB.svg"
        assert (
            select_icon_filename("BOYLAT", catlam=1, has_topmark=True, iala_region_b=True)
            == "BOYLAT_B_T_IALAB.svg"
        )

    def test_lateral_bcnlat_has_no_iala_b_variant_without_topmark(self) -> None:
        """Vérifier le repli sur la variante région A pour BCNLAT sans voyant en région B.

        Le jeu officiel ne comporte pas de fichier ``BCNLAT_x_IALAB.svg``
        (sans voyant) : seul ``BOYLAT`` propose cette variante.
        """
        assert select_icon_filename("BCNLAT", catlam=1, iala_region_b=True) == "BCNLAT_B.svg"

    def test_plain_topmark_codes(self) -> None:
        """Vérifier danger isolé, eaux saines, marque spéciale (balise et bouée)."""
        assert select_icon_filename("BCNISD") == "BCNISD.svg"
        assert select_icon_filename("BOYISD", has_topmark=True) == "BOYISD_T.svg"
        assert select_icon_filename("BCNSAW") == "BCNSAW.svg"
        assert select_icon_filename("BOYSAW", has_topmark=True) == "BOYSAW_T.svg"
        assert select_icon_filename("BCNSPP") == "BCNSPP.svg"
        assert select_icon_filename("BOYSPP", has_topmark=True) == "BOYSPP_T.svg"

    def test_single_icon_codes(self) -> None:
        """Vérifier les objets à icône unique, sans variante."""
        for code in ("DAYMAR", "NEWOBJ", "OFSPLF", "PILPNT", "SILTNK", "VEGATN", "FORSTC"):
            assert select_icon_filename(code) == f"{code}.svg"

    def test_landmark(self) -> None:
        """Vérifier le repli générique pour un amer (LNDMRK)."""
        assert select_icon_filename("LNDMRK") == "LNDMRK_default.svg"

    def test_unknown_code_returns_none(self) -> None:
        """Vérifier qu'un code inconnu renvoie None plutôt qu'un nom de fichier inventé."""
        assert select_icon_filename("CODE_INCONNU") is None

    def test_missing_category_returns_none(self) -> None:
        """Vérifier qu'une marque cardinale/latérale sans catégorie renvoie None.

        Mieux vaut se replier sur un marqueur générique côté appelant que
        de deviner une direction ou un côté au hasard.
        """
        assert select_icon_filename("BCNCAR") is None
        assert select_icon_filename("BCNLAT") is None


class TestIsIalaRegionB:
    """Vérifier la détection approximative de la région IALA par zone géographique."""

    def test_metropole_is_region_a(self) -> None:
        """Vérifier qu'un point en métropole (Lorient) n'est pas classé région B."""
        assert is_iala_region_b(47.75, -3.37) is False

    def test_antilles_is_region_b(self) -> None:
        """Vérifier que la Martinique est classée région B."""
        assert is_iala_region_b(14.6, -61.0) is True

    def test_guyane_is_region_b(self) -> None:
        """Vérifier que la Guyane française est classée région B."""
        assert is_iala_region_b(4.9, -52.3) is True

    def test_saint_pierre_et_miquelon_is_region_b(self) -> None:
        """Vérifier que Saint-Pierre-et-Miquelon est classé région B."""
        assert is_iala_region_b(46.78, -56.18) is True

    def test_reunion_is_region_a(self) -> None:
        """Vérifier que La Réunion (région IALA A comme la métropole) n'est pas classée région B."""
        assert is_iala_region_b(-21.1, 55.3) is False


class TestIconFilenameForMark:
    """Vérifier l'extraction des attributs depuis les propriétés WFS brutes."""

    def test_lateral_from_english_property_text(self) -> None:
        """Vérifier la reconnaissance du texte anglais habituel (port/starboard)."""
        assert (
            icon_filename_for_mark(
                "BCNLAT", {"Category of lateral mark": "port hand"}, 47.7, -3.4
            )
            == "BCNLAT_B.svg"
        )
        assert (
            icon_filename_for_mark(
                "BCNLAT", {"Category of lateral mark": "starboard hand"}, 47.7, -3.4
            )
            == "BCNLAT_T.svg"
        )

    def test_cardinal_from_english_property_text(self) -> None:
        """Vérifier la reconnaissance des 4 directions cardinales en anglais."""
        assert (
            icon_filename_for_mark("BCNCAR", {"Category of cardinal mark": "north cardinal"}, 47.7, -3.4)
            == "BCNCAR_N.svg"
        )
        assert (
            icon_filename_for_mark("BOYCAR", {"Category of cardinal mark": "south cardinal"}, 47.7, -3.4)
            == "BOYCAR_S.svg"
        )

    def test_topmark_detected_from_linkage_attribute(self) -> None:
        """Vérifier la détection du voyant depuis un attribut de liaison non vide."""
        assert (
            icon_filename_for_mark(
                "BCNLAT",
                {"Category of lateral mark": "port hand", "topmar": "FR000006300300001"},
                47.7,
                -3.4,
            )
            == "BCNLAT_B_T.svg"
        )

    def test_topmark_not_detected_when_linkage_empty(self) -> None:
        """Vérifier qu'un attribut de liaison vide n'est pas pris pour un voyant présent."""
        assert (
            icon_filename_for_mark(
                "BCNLAT", {"Category of lateral mark": "port hand", "topmar": ""}, 47.7, -3.4
            )
            == "BCNLAT_B.svg"
        )

    def test_iala_region_b_applied_from_position(self) -> None:
        """Vérifier que la région IALA est déduite de la position de la marque."""
        assert (
            icon_filename_for_mark(
                "BOYLAT",
                {"Category of lateral mark": "starboard hand"},
                14.6,
                -61.0,  # Martinique
            )
            == "BOYLAT_T_IALAB.svg"
        )

    def test_missing_category_property_returns_none(self) -> None:
        """Vérifier qu'une propriété absente renvoie None plutôt qu'une supposition."""
        assert icon_filename_for_mark("BCNLAT", {}, 47.7, -3.4) is None
