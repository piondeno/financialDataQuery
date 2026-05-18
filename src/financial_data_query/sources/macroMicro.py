import json
import os
from pathlib import Path

import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError

LINKS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".macroMicro_links.json")


def _load_links() -> dict:
    if not os.path.exists(LINKS_FILE_PATH):
        return {}
    try:
        with open(LINKS_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_links(links: dict) -> None:
    with open(LINKS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
