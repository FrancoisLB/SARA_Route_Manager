# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Module : tests.test_logging
Description : Tests du journal technique.
Classes présentes :
- LoggingTests : test_log_file_creation.
"""

__version__ = "0.9.4"
__date__ = "2026-11-19"

import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sara_route_manager.app_logging import configure_logging, get_logger


class LoggingTests(unittest.TestCase):
    """Vérifier la création et l'écriture du journal."""

    def test_log_file_creation(self) -> None:
        """Créer journal.txt et y écrire une ligne."""
        with TemporaryDirectory() as directory:
            path = configure_logging(Path(directory))
            logger = get_logger()
            logger.info("test journal")
            for handler in logger.handlers:
                handler.flush()
            self.assertTrue(path.exists())
            self.assertIn("test journal", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
