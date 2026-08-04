# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : sara_route_manager.app_logging
Description : Configuration du journal technique de SARA Route Manager.
Classes présentes : aucune.
Fonctions présentes : configure_logging, get_logger.
"""

__version__ = "0.7.2.0"
__date__ = "2026-08-04"

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "sara_route_manager"


def configure_logging(logs_directory: Path) -> Path:
    """Configurer un journal texte avec rotation simple.

    Parameters
    ----------
    logs_directory : pathlib.Path
        Dossier dans lequel le fichier ``journal.txt`` doit être créé.

    Returns
    -------
    pathlib.Path
        Chemin complet du fichier journal actif.
    """
    logs_directory.mkdir(parents=True, exist_ok=True)
    log_file = logs_directory / "journal.txt"
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    # Éviter d'ajouter plusieurs gestionnaires lors des tests ou rechargements Flask.
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_file:
            return log_file

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return log_file


def get_logger() -> logging.Logger:
    """Retourner le journal applicatif partagé.

    Returns
    -------
    logging.Logger
        Journal nommé ``sara_route_manager``.
    """
    return logging.getLogger(_LOGGER_NAME)
