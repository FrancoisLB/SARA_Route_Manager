# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_library_unified
Description : Vérifie la Bibliothèque simplifiée de la version 0.8.0 : liste
unique avec filtre à boutons radio, bouton Exporter avec choix du format,
import d'une route complète, et suppression d'une route locale.
Classes présentes :
- TestLibraryMarkup : test_single_list_and_filter, test_single_action_set,
  test_export_dialog_markup, test_old_per_format_buttons_removed.
- TestImportCompleteRoute : test_import_json_with_unknown_metadata_keys.
- TestLocalStorageDeletion : test_exists_matches_save_naming, test_delete_removes_file,
  test_delete_refuses_missing_or_non_json, test_delete_cannot_leave_directory.
- TestSaraNavigationVocabulary, TestUploadOwnership (0.9.0).
- TestActionsByOrigin (0.9.2, 0.9.3) : boutons Éditer / Voir la carte, Télécharger selon l'origine, menu adapté.
- TestLocalRouteEndpoints : test_delete_endpoint_requires_file,
  test_delete_endpoint_reports_missing_file.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import io
import json
from pathlib import Path

import pytest

from sara_route_manager.models import SaraRoute, Waypoint
from sara_route_manager.storage import LocalRouteStorage
from sara_route_manager.webapp import create_app

ROOT = Path(__file__).resolve().parents[1]

# Fichier réel fourni par l'utilisateur : clés d'import simplifié + bloc
# `metadonnees` que l'application doit ignorer sans erreur.
LORIENT_JSON = {
    "name": "Lorient - Passe de l'Ouest - entrant - à valider",
    "reversed": False,
    "points": [
        {"name": "Laisser A2 à bâbord", "latitude": 47.6821118, "longitude": -3.4162025, "distance_threshold": 30.0},
        {"name": "Laisser A4 à bâbord", "latitude": 47.6861984, "longitude": -3.4017751, "distance_threshold": 30.0},
        {"name": "Laisser A7 à tribord", "latitude": 47.6952541, "longitude": -3.3778378, "distance_threshold": 30.0},
    ],
    "metadonnees": {"zone": "rade de Lorient", "statut": "à valider"},
}


class TestLibraryMarkup:
    """Contrôler statiquement la page Bibliothèque."""

    def _page(self) -> str:
        return (ROOT / "sara_route_manager/templates/routes.html").read_text(encoding="utf-8")

    def test_single_list_and_filter(self) -> None:
        """Une seule liste, un filtre à boutons radio et un champ de recherche."""
        page = self._page()
        assert page.count("<select") == 1 and 'id="routes-list"' in page
        for value in ("all", "mine", "community", "local"):
            assert f'name="route-filter" value="{value}"' in page
        assert 'id="route-search"' in page

    def test_single_action_set(self) -> None:
        """Les quatre actions principales sont présentes une seule fois."""
        page = self._page()
        for button_id in ("route-open", "route-download", "route-export", "route-import", "route-delete"):
            assert page.count(f'id="{button_id}"') == 1

    def test_export_dialog_markup(self) -> None:
        """La boîte d'export est un alertdialog avec trois formats en boutons radio."""
        # Le dialogue vit dans un gabarit partagé par la Bibliothèque et l'éditeur.
        page = (ROOT / "sara_route_manager/templates/_export_dialog.html").read_text(encoding="utf-8")
        assert 'id="export-dialog"' in page and 'role="alertdialog"' in page
        for value in ("json", "gpx", "csv"):
            assert f'name="export-format" value="{value}"' in page

    def test_old_per_format_buttons_removed(self) -> None:
        """Les anciens boutons d'export par format et les trois listes ont disparu."""
        page = self._page()
        for old_id in ("my-export-gpx", "community-export-csv", "local-export-json", "my-routes-list", "local-open"):
            assert old_id not in page

    def test_export_dialog_is_shared_with_editor(self) -> None:
        """La Bibliothèque et l'éditeur incluent le même gabarit de dialogue d'export."""
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(encoding="utf-8")
        assert '{% include "_export_dialog.html" %}' in self._page()
        assert '{% include "_export_dialog.html" %}' in editor
        assert 'id="export-route"' in editor
        for old_id in ("export-gpx", "export-csv", "export-json"):
            assert f'id="{old_id}"' not in editor
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(encoding="utf-8")
        assert "chooseExportFormat" in script

    def test_filter_labels_and_summary_start_with_filter_name(self) -> None:
        """Les filtres sont explicites et le résumé annonce d'abord le nom du filtre."""
        page = self._page()
        assert " Mes routes (en partage)</label>" in page
        assert " Autres routes (en partage)</label>" in page
        script = (ROOT / "sara_route_manager/static/js/routes.js").read_text(encoding="utf-8")
        assert "`${filterName} : ${shownEntries.length}" in script


class TestImportCompleteRoute:
    """Vérifier que l'import renvoie la route complète."""

    def test_import_json_with_unknown_metadata_keys(self) -> None:
        """Le fichier Lorient s'importe avec nom et sens ; `metadonnees` est ignoré."""
        client = create_app().test_client()
        payload = json.dumps(LORIENT_JSON, ensure_ascii=False).encode("utf-8")
        response = client.post(
            "/api/routes/import",
            data={"file": (io.BytesIO(payload), "chenal_Lorient.json")},
            content_type="multipart/form-data",
        )
        data = response.get_json()
        assert response.status_code == 200 and data["ok"] is True
        assert data["route"]["name"] == LORIENT_JSON["name"]
        assert data["route"]["reversed"] is False
        assert len(data["route"]["points"]) == 3
        assert data["route"]["points"][0]["distance_threshold"] == 30.0
        assert "metadonnees" not in json.dumps(data["route"])


def _route(name: str = "Essai") -> SaraRoute:
    """Créer une route valide minimale pour les tests de stockage."""
    return SaraRoute(
        name=name,
        points=[Waypoint.from_form({"name": "A", "latitude": 47.0, "longitude": -3.0}),
                Waypoint.from_form({"name": "B", "latitude": 47.1, "longitude": -3.1})],
    )


class TestLocalStorageDeletion:
    """Vérifier `exists` et `delete` du stockage local."""

    def test_exists_matches_save_naming(self, tmp_path: Path) -> None:
        """`exists` utilise la même règle de nom de fichier que `save`."""
        storage = LocalRouteStorage(tmp_path)
        assert storage.exists("Lorient - Passe d'Ouest à valider") is False
        storage.save(_route("Lorient - Passe d'Ouest à valider"))
        assert storage.exists("Lorient - Passe d'Ouest à valider") is True

    def test_delete_removes_file(self, tmp_path: Path) -> None:
        """`delete` supprime le fichier JSON demandé."""
        storage = LocalRouteStorage(tmp_path)
        path = storage.save(_route())
        storage.delete(path.name)
        assert not path.exists()

    def test_delete_refuses_missing_or_non_json(self, tmp_path: Path) -> None:
        """Un fichier absent ou non JSON n'est jamais supprimé."""
        storage = LocalRouteStorage(tmp_path)
        (tmp_path / "note.txt").write_text("à garder", encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            storage.delete("absent.json")
        with pytest.raises(FileNotFoundError):
            storage.delete("note.txt")
        assert (tmp_path / "note.txt").exists()

    def test_delete_cannot_leave_directory(self, tmp_path: Path) -> None:
        """Un chemin avec « .. » est réduit à son nom : le dossier parent est intact."""
        folder = tmp_path / "routes"
        folder.mkdir()
        outside = tmp_path / "secret.json"
        outside.write_text("{}", encoding="utf-8")
        storage = LocalRouteStorage(folder)
        with pytest.raises(FileNotFoundError):
            storage.delete("../secret.json")
        assert outside.exists()


class TestLocalRouteEndpoints:
    """Vérifier la validation des nouveaux endpoints, sans rien écrire sur le disque."""

    def test_delete_endpoint_requires_file(self) -> None:
        """Sans nom de fichier, l'API répond 400."""
        response = create_app().test_client().post("/api/routes/local/delete", json={})
        assert response.status_code == 400 and response.get_json()["ok"] is False

    def test_delete_endpoint_reports_missing_file(self) -> None:
        """Un fichier inexistant produit un message d'erreur lisible."""
        response = create_app().test_client().post(
            "/api/routes/local/delete", json={"file": "inexistante_sara_test_0_8_0.json"}
        )
        assert response.status_code == 400
        assert "introuvable" in response.get_json()["message"]


class TestUploadOverwriteContract:
    """Vérifier le dialogue de remplacement à l'envoi vers SARA."""

    def test_upload_returns_409_when_route_exists(self, monkeypatch) -> None:
        """Un nom déjà pris renvoie 409 avec `exists: true`, exploitable par l'éditeur."""
        from sara_route_manager import webapp
        from sara_route_manager.firebase_client import SaraRouteExistsError

        app = create_app()

        def refuse(self, route, overwrite=False):
            raise SaraRouteExistsError("Une de vos routes mises en ligne a le même nom. Voulez-vous l’écraser ?")

        monkeypatch.setattr(webapp.FirebaseSession, "upload_route", refuse)
        payload = {
            "name": "Essai",
            "points": [
                {"name": "A", "latitude": 47.0, "longitude": -3.0},
                {"name": "B", "latitude": 47.1, "longitude": -3.1},
            ],
        }
        response = app.test_client().post("/api/routes/upload", json=payload)
        assert response.status_code == 409
        assert response.get_json()["exists"] is True

    def test_editor_offers_replacement(self) -> None:
        """L'éditeur renvoie la requête avec overwrite après confirmation."""
        script = (ROOT / "sara_route_manager/static/js/unified_editor.js").read_text(encoding="utf-8")
        assert "response.status === 409 && data.exists" in script
        assert "send(true)" in script
        # Aucune invite native : la confirmation passe par un alertdialog de la page.
        assert "confirmReplaceRoute" in script and "window.confirm(" not in script
        editor = (ROOT / "sara_route_manager/templates/editor.html").read_text(encoding="utf-8")
        assert 'id="replace-route-dialog"' in editor and 'role="alertdialog"' in editor


class TestHomogeneousTabs:
    """Vérifier l'harmonisation des onglets (0.8.2)."""

    def _read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_single_refresh_button(self) -> None:
        """La Bibliothèque n'a plus qu'un seul bouton d'actualisation."""
        page = self._read("sara_route_manager/templates/routes.html")
        assert 'id="route-refresh"' in page
        assert "refresh-remote-button" not in page and "refresh-local-button" not in page

    def test_export_dialog_uses_configured_default_format(self) -> None:
        """La boîte d'export pré-coche le format de la Configuration."""
        script = self._read("sara_route_manager/static/js/export_dialog.js")
        assert "default_export_format" in script

    def test_library_honours_overwrite_setting(self) -> None:
        """L'import de la Bibliothèque respecte « confirmer avant d'écraser »."""
        script = self._read("sara_route_manager/static/js/routes.js")
        assert "confirm_before_overwrite" in script and "confirmOverwrite &&" in script

    def test_configuration_import_is_single_button(self) -> None:
        """L'import de configuration suit le modèle « un bouton ouvre le choix du fichier »."""
        page = self._read("sara_route_manager/templates/configuration.html")
        assert "Importer la configuration…" in page
        assert "Fichier de configuration à importer" not in page
        script = self._read("sara_route_manager/static/js/configuration.js")
        assert 'getElementById("import-configuration-file").click()' in script

    def test_no_nm_abbreviation_in_configuration(self) -> None:
        """NVDA lit « NM » comme « nanomètre » : le libellé est écrit en toutes lettres."""
        page = self._read("sara_route_manager/templates/configuration.html")
        assert "(NM)" not in page and "Milles nautiques" in page

    def test_about_has_standard_messages_zone(self) -> None:
        """L'À propos a la même zone Messages que les autres onglets."""
        page = self._read("sara_route_manager/templates/about.html")
        assert 'aria-labelledby="messages-heading"' in page and 'id="messages-heading"' in page


class TestSaraNavigationVocabulary:
    """Vérifier que les libellés de partage reprennent ceux de SARA Navigation (iPhone).

    Sources : `SARANav.xcstrings` et `Localizable.xcstrings` (SARAFramework) —
    clés `upload`, `download`, `my_routes`, `other_routes`, `upload_date`,
    `firebase_success_upload`, `firebase_name_exists_owner`, `firebase_name_exists`,
    `firebase_warning_erase_route_local`, `firebase_success_download_save_route`.
    """

    def _read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_editor_button_is_deposer_en_ligne(self) -> None:
        """Le bouton de mise en ligne s'appelle « Déposer en ligne », comme sur iPhone."""
        editor = self._read("sara_route_manager/templates/editor.html")
        assert ">Déposer en ligne</button>" in editor
        assert "Envoyer vers SARA" not in editor

    def test_overwrite_dialog_uses_ios_wording(self) -> None:
        """La boîte d'écrasement reprend le titre, le texte et les réponses Oui/Non de l'iPhone."""
        editor = self._read("sara_route_manager/templates/editor.html")
        assert ">Attention</h2>" in editor
        assert "Une de vos routes mises en ligne a le même nom. Voulez-vous l’écraser ?" in editor
        assert 'id="replace-route-confirm" type="button">Oui<' in editor
        assert 'id="replace-route-cancel" type="button" class="secondary">Non<' in editor

    def test_library_has_telecharger_button(self) -> None:
        """La Bibliothèque propose « Télécharger », réservé aux routes en ligne."""
        page = self._read("sara_route_manager/templates/routes.html")
        script = self._read("sara_route_manager/static/js/routes.js")
        assert 'id="route-download"' in page and ">Télécharger</button>" in page
        assert 'entry.kind === "local"' in script and "async function downloadSelected()" in script
        assert "Une route avec le même nom existe déjà, voulez-vous l’écraser ?" in script
        assert "La route a été téléchargée et sauvegardée avec succès." in script

    def test_origin_and_date_wording(self) -> None:
        """Origines « mes routes » / « autres routes » et « date de dépôt »."""
        script = self._read("sara_route_manager/static/js/routes.js")
        assert 'return "mes routes en partage";' in script and 'return "autres routes en partage";' in script
        assert "date de dépôt" in script

    def test_success_messages_match_ios(self) -> None:
        """Messages serveur de mise en ligne et de suppression comme sur iPhone."""
        source = self._read("sara_route_manager/webapp.py")
        assert "La route a été mise en ligne avec succès !" in source
        assert "La route a été supprimée avec succès." in source


class TestUploadOwnership:
    """Distinguer, comme SARA Navigation, une route à soi d'une route d'un autre utilisateur."""

    @staticmethod
    def _session(monkeypatch, existing):
        """Créer une session simulée ; `existing` est le JSON renvoyé pour le nom demandé."""
        from sara_route_manager import firebase_client

        class FakeResponse:
            ok = True
            status_code = 200
            text = ""

            def __init__(self, data):
                self._data = data

            def json(self):
                return self._data

        calls = {"put": 0}
        monkeypatch.setattr(firebase_client.requests, "get", lambda *a, **k: FakeResponse(existing))

        def fake_put(*args, **kwargs):
            calls["put"] += 1
            return FakeResponse({})

        monkeypatch.setattr(firebase_client.requests, "put", fake_put)
        session = firebase_client.FirebaseSession()
        session.id_token, session.local_id = "token", "moi"
        return session, calls

    @staticmethod
    def _route():
        return SaraRoute(
            name="Essai",
            points=[Waypoint.from_form({"name": "A", "latitude": 47.0, "longitude": -3.0}),
                    Waypoint.from_form({"name": "B", "latitude": 47.1, "longitude": -3.1})],
        )

    def test_other_owner_blocks_upload_even_with_overwrite(self, monkeypatch) -> None:
        """Une route d'un autre utilisateur bloque toujours la mise en ligne."""
        from sara_route_manager.firebase_client import SaraRouteOwnedByOtherError

        session, calls = self._session(monkeypatch, {"owner": "autre", "name": "Essai"})
        for overwrite in (False, True):
            with pytest.raises(SaraRouteOwnedByOtherError) as error:
                session.upload_route(self._route(), overwrite=overwrite)
            assert "appartenant à un autre utilisateur" in str(error.value)
        assert calls["put"] == 0

    def test_own_route_needs_confirmation_then_overwrites(self, monkeypatch) -> None:
        """Sa propre route demande d'abord confirmation, puis peut être écrasée."""
        from sara_route_manager.firebase_client import SaraRouteExistsError

        session, calls = self._session(monkeypatch, {"owner": "moi", "name": "Essai"})
        with pytest.raises(SaraRouteExistsError):
            session.upload_route(self._route(), overwrite=False)
        assert calls["put"] == 0
        session.upload_route(self._route(), overwrite=True)
        assert calls["put"] == 1

    def test_new_name_uploads_directly(self, monkeypatch) -> None:
        """Un nom libre est mis en ligne sans confirmation."""
        session, calls = self._session(monkeypatch, None)
        session.upload_route(self._route())
        assert calls["put"] == 1

    def test_endpoint_reports_other_owner_without_overwrite_offer(self, monkeypatch) -> None:
        """L'API signale « autre propriétaire » sans proposer d'écrasement."""
        from sara_route_manager import webapp
        from sara_route_manager.firebase_client import SaraRouteOwnedByOtherError

        def refuse(self, route, overwrite=False):
            raise SaraRouteOwnedByOtherError("Cette route ne peut pas être mise en ligne.")

        monkeypatch.setattr(webapp.FirebaseSession, "upload_route", refuse)
        payload = {"name": "Essai", "points": [
            {"name": "A", "latitude": 47.0, "longitude": -3.0},
            {"name": "B", "latitude": 47.1, "longitude": -3.1}]}
        response = create_app().test_client().post("/api/routes/upload", json=payload)
        data = response.get_json()
        assert response.status_code == 409 and data["owned_by_other"] is True and data["exists"] is False


class TestActionsByOrigin:
    """Vérifier (0.9.2) que boutons et menu dépendent de l'origine de la route."""

    @pytest.fixture()
    def script(self) -> str:
        return Path("sara_route_manager/static/js/routes.js").read_text(encoding="utf-8")

    @pytest.fixture()
    def page(self) -> str:
        return Path("sara_route_manager/templates/routes.html").read_text(encoding="utf-8")

    def test_view_button_and_hint_present(self, page: str) -> None:
        """Les boutons Éditer et Voir la carte et la phrase d'aide existent."""
        assert 'id="route-open"' in page and ">Éditer</button>" in page
        assert 'id="route-view"' in page and ">Voir la carte</button>" in page
        assert 'id="route-action-hint"' in page

    def test_download_rules(self, script: str) -> None:
        """Télécharger est grisé pour le local et pour « mes routes » déjà copiées."""
        assert 'if (entry.kind === "local") return false;' in script
        assert 'if (entry.kind === "mine") return !hasLocalCopy(entry);' in script
        assert "if (downloadAllowed(entry)) contextMenu.appendChild" in script

    def test_view_in_context_menu_and_listener(self, script: str) -> None:
        """Voir la carte est branché sur le bouton et sur le menu contextuel."""
        assert 'contextAction("Voir la carte", viewMapSelected)' in script
        assert '"route-view").addEventListener("click", viewMapSelected)' in script
        assert '"/api/map/token"' in script and "open_map_window" in script

    def test_editor_has_no_view_mode_and_renamed_map_button(self) -> None:
        """L'éditeur n'a plus de mode Visualiser ; son bouton s'appelle Voir la carte."""
        editor = Path("sara_route_manager/static/js/unified_editor.js").read_text(encoding="utf-8")
        html = Path("sara_route_manager/templates/editor.html").read_text(encoding="utf-8")
        assert "sara_editor_view" not in editor
        assert 'id="visualize-route" type="button" class="secondary" disabled>Voir la carte</button>' in html

    def test_editor_help_uses_shared_label(self) -> None:
        """L'aide de l'éditeur cite le libellé complet du filtre."""
        html = Path("sara_route_manager/templates/editor.html").read_text(encoding="utf-8")
        assert "« Autres routes (en partage) »" in html
