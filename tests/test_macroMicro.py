import json
import os
import pytest
from unittest.mock import patch, MagicMock

import pandas as pd

from financial_data_query.sources.macroMicro import _load_links, _save_links


class TestLoadLinks:
    def test_load_links_returns_dict(self, tmp_path):
        json_file = tmp_path / ".macroMicro_links.json"
        json_file.write_text(json.dumps({"sym1": {"url": "http://a.com", "description": "Desc"}}))
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", str(json_file)):
            result = _load_links()
        assert result == {"sym1": {"url": "http://a.com", "description": "Desc"}}

    def test_load_links_missing_file_returns_empty(self, tmp_path):
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", str(tmp_path / ".macroMicro_links.json")):
            result = _load_links()
        assert result == {}

    def test_load_links_invalid_json_returns_empty(self, tmp_path):
        json_file = tmp_path / ".macroMicro_links.json"
        json_file.write_text("not valid json")
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", str(json_file)):
            result = _load_links()
        assert result == {}


class TestSaveLinks:
    def test_save_links_writes_json(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        test_links = {"sym1": {"url": "http://a.com", "description": "Desc"}}
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            _save_links(test_links)
        with open(json_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == test_links

    def test_save_links_overwrites(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({"old": {"url": "http://old.com", "description": "Old"}}, f)
        new_links = {"new": {"url": "http://new.com", "description": "New"}}
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            _save_links(new_links)
        with open(json_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == new_links
        assert "old" not in saved
