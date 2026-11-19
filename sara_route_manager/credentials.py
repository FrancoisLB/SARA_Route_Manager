# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.credentials
Description : Mémorisation sécurisée du compte SARA dans le gestionnaire d’identifiants Windows.
Classes présentes :
- CredentialStore
  - load_email
  - load_password
  - save
  - clear
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import json
from pathlib import Path

import keyring


class CredentialStore:
    """Gérer les identifiants SARA sans écrire le mot de passe dans un fichier.

    Notes
    -----
    L’adresse électronique est conservée dans un petit fichier de paramètres.
    Le mot de passe est confié au gestionnaire d’identifiants du système via
    ``keyring``. Sous Windows, cela utilise normalement le Gestionnaire
    d’identifiants Windows.
    """

    SERVICE_NAME = "SARA Route Manager"

    def __init__(self) -> None:
        """Initialiser le dossier de paramètres utilisateur."""
        self.directory = Path.home() / "Documents" / "SARA Route Manager"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.directory / "settings.json"

    def load_email(self) -> str | None:
        """Lire l’adresse électronique mémorisée.

        Returns
        -------
        str | None
            Adresse mémorisée, ou ``None`` si elle n’existe pas.
        """
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        email = data.get("email") if isinstance(data, dict) else None
        return str(email).strip() if email else None

    def load_password(self, email: str | None) -> str | None:
        """Lire le mot de passe associé depuis le coffre système.

        Parameters
        ----------
        email : str | None
            Adresse du compte à rechercher.

        Returns
        -------
        str | None
            Mot de passe mémorisé, ou ``None``.
        """
        if not email:
            return None
        try:
            return keyring.get_password(self.SERVICE_NAME, email)
        except keyring.errors.KeyringError:
            return None

    def save(self, email: str, password: str) -> None:
        """Mémoriser l’adresse et le mot de passe.

        Parameters
        ----------
        email : str
            Adresse électronique SARA.
        password : str
            Mot de passe à enregistrer dans le coffre système.
        """
        clean_email = email.strip()
        self.settings_path.write_text(
            json.dumps({"email": clean_email}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        keyring.set_password(self.SERVICE_NAME, clean_email, password)

    def clear(self) -> None:
        """Supprimer les identifiants mémorisés."""
        email = self.load_email()
        if email:
            try:
                keyring.delete_password(self.SERVICE_NAME, email)
            except keyring.errors.PasswordDeleteError:
                pass
            except keyring.errors.KeyringError:
                pass
        try:
            self.settings_path.unlink(missing_ok=True)
        except OSError:
            pass
