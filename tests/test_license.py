# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_license
Description : Vérifie le fichier LICENSE.md unique (code GPL-3.0-only,
documentation CC BY-SA 4.0), la section « Licence » de la page À propos et
l'ouverture des textes légaux dans le navigateur système (groupe 4, dernier
point).
Classes présentes :
- TestLicense : test_license_file_exists_at_project_root,
  test_license_file_covers_code_and_documentation,
  test_about_page_has_license_section,
  test_about_page_license_section_follows_f6_zone_pattern,
  test_license_buttons_open_in_system_browser_not_pywebview_window,
  test_about_js_wires_license_buttons, test_about_page_has_disclaimer_section.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestLicense:
    """Vérifier le fichier de licence unique et son affichage dans À propos."""

    def test_license_file_exists_at_project_root(self) -> None:
        """Vérifier qu'un seul fichier LICENSE.md existe, à la racine du projet.

        À la racine (pas dans un sous-dossier) : convention quasi
        universelle (GitHub, GitLab, outils d'analyse de licence), cohérente
        avec tous les autres documents du projet. Un seul fichier avec deux
        sections, pas deux fichiers séparés (simplifié après discussion).
        """
        assert (ROOT / "LICENSE.md").is_file()
        assert not (ROOT / "LICENSE-DOCUMENTATION.md").exists()
        assert not (ROOT / "licence").exists()

    def test_license_file_covers_code_and_documentation(self) -> None:
        """Vérifier les deux sections (code GPL-3.0-only, documentation CC BY-SA 4.0) et leurs liens."""
        content = (ROOT / "LICENSE.md").read_text(encoding="utf-8")
        assert "GPL-3.0-only" in content
        assert "https://www.gnu.org/licenses/gpl-3.0.fr.html" in content
        assert "CC BY-SA 4.0" in content
        assert "https://creativecommons.org/licenses/by-sa/4.0/deed.fr" in content
        # Texte court avec renvoi vers les textes légaux complets, pas les
        # textes légaux intégraux recopiés (demandé explicitement).
        assert len(content) < 3000

    def test_about_page_has_license_section(self) -> None:
        """Vérifier la présence de la section Licence dans la page À propos."""
        about = (ROOT / "sara_route_manager/templates/about.html").read_text(encoding="utf-8")
        assert "GPL-3.0-only" in about
        assert "CC BY-SA 4.0" in about
        assert "LICENSE.md" in about

    def test_about_page_license_section_follows_f6_zone_pattern(self) -> None:
        """Vérifier que la section Licence garde les raccourcis d'accessibilité déjà établis.

        Même motif que les autres sections de la page (zone F6, titre
        focusable) — demandé explicitement.
        """
        about = (ROOT / "sara_route_manager/templates/about.html").read_text(encoding="utf-8")
        assert (
            '<section class="f6-zone" data-zone-name="Licence" aria-labelledby="license-heading">'
            in about
        )
        assert '<h2 id="license-heading" tabindex="-1">Licence</h2>' in about

    def test_license_buttons_open_in_system_browser_not_pywebview_window(self) -> None:
        """Vérifier que les textes légaux s'ouvrent via le navigateur système, pas un lien direct.

        Un `<a target="_blank">` ouvrirait une fenêtre pywebview sans barre
        d'adresse ni bouton retour (contrainte déjà établie pour le lien
        Orion Brest) — mêmes boutons + `/api/open-path` + `os.startfile`,
        pas de lien direct dans cette page.
        """
        about = (ROOT / "sara_route_manager/templates/about.html").read_text(encoding="utf-8")
        assert 'id="open-gpl-license-text"' in about
        assert 'id="open-cc-by-sa-license-text"' in about
        assert 'target="_blank"' not in about
        webapp = (ROOT / "sara_route_manager/webapp.py").read_text(encoding="utf-8")
        assert '"gpl_license_url": "https://www.gnu.org/licenses/gpl-3.0.fr.html"' in webapp
        assert (
            '"cc_by_sa_license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.fr"'
            in webapp
        )

    def test_about_js_wires_license_buttons(self) -> None:
        """Vérifier que les deux boutons appellent bien openDocument() avec la bonne cible."""
        script = (ROOT / "sara_route_manager/static/js/about.js").read_text(encoding="utf-8")
        assert 'openDocument("gpl_license_url",' in script
        assert 'openDocument("cc_by_sa_license_url",' in script

    def test_about_page_has_disclaimer_section(self) -> None:
        """Vérifier la section « Avertissement » (dégagement de responsabilité), ajoutée après la licence.

        Même motif d'accessibilité que les autres sections (zone F6, titre
        focusable), placée juste après la section Licence.
        """
        about = (ROOT / "sara_route_manager/templates/about.html").read_text(encoding="utf-8")
        assert (
            '<section class="f6-zone" data-zone-name="Avertissement" aria-labelledby="disclaimer-heading">'
            in about
        )
        assert '<h2 id="disclaimer-heading" tabindex="-1">Avertissement</h2>' in about
        assert "aucune réclamation" in about.lower()
