"""
Logger — نظام السجلات
"""
import logging
import os
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "data" / "logs"


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "trading.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("CryptoAI")
