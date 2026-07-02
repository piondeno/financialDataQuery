import json
import os
import pytest
from unittest.mock import patch, MagicMock

import pandas as pd

from financial_data_query.sources.macroMicro import _load_links, _save_links, _update_readme_symbols, _symbol_from_url, _parse_title, macroMicroSymbolLinkConnect, MacroMicroFetcher
from financial_data_query.errors import FetchError


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


class TestUpdateReadmeSymbols:
    def test_update_existing_markers(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Test\n<!-- MACROMICRO_SYMBOLS_START -->\n| old |\n<!-- MACROMICRO_SYMBOLS_END -->\nEnd")
        links = {"sym1": {"url": "http://a.com", "description": "Desc 1"}}
        _update_readme_symbols(links, str(readme))
        content = readme.read_text()
        assert "<!-- MACROMICRO_SYMBOLS_START -->" in content
        assert "<!-- MACROMICRO_SYMBOLS_END -->" in content
        assert "`sym1`" in content
        assert "Desc 1" in content
        assert "old" not in content

    def test_add_markers_when_missing(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("## MacroMicro\n\nsome text\n")
        links = {"sym1": {"url": "http://a.com", "description": "Desc 1"}}
        _update_readme_symbols(links, str(readme))
        content = readme.read_text()
        assert "<!-- MACROMICRO_SYMBOLS_START -->" in content
        assert "<!-- MACROMICRO_SYMBOLS_END -->" in content
        assert "`sym1`" in content

    def test_table_format_correct(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("<!-- MACROMICRO_SYMBOLS_START --><!-- MACROMICRO_SYMBOLS_END -->")
        links = {
            "sym1": {"url": "http://a.com", "description": "First"},
            "sym2": {"url": "http://b.com", "description": "Second"}
        }
        _update_readme_symbols(links, str(readme))
        content = readme.read_text()
        assert "| Symbol | 說明 |" in content
        assert "|--------|------|" in content
        assert "| `sym1` | First |" in content
        assert "| `sym2` | Second |" in content


class TestSymbolFromUrl:
    def test_extract_last_segment(self):
        assert _symbol_from_url("https://www.macromicro.me/series/5899/cn-dr007") == "cn-dr007"

    def test_extract_with_trailing_slash(self):
        assert _symbol_from_url("https://www.macromicro.me/series/5899/cn-dr007/") == "cn-dr007"

    def test_simple_url(self):
        assert _symbol_from_url("http://example.com/sym1") == "sym1"


class TestParseTitle:
    def test_remove_macromicro_suffix(self):
        assert _parse_title("中國-逆回購利率(日數據)-7天期 - MacroMicro") == "中國-逆回購利率(日數據)-7天期"

    def test_pipe_separator(self):
        assert _parse_title("Some Title | MacroMicro") == "Some Title"

    def test_no_suffix(self):
        assert _parse_title("Plain Title") == "Plain Title"


class TestMacroMicroSymbolLinkConnect:
    def test_missing_dependency_raises(self, tmp_path):
        with patch("financial_data_query.sources.macroMicro._check_uc_installed",
                   side_effect=FetchError("undetected-chromedriver 未安裝")):
            with pytest.raises(FetchError, match="undetected-chromedriver"):
                macroMicroSymbolLinkConnect("https://www.macromicro.me/series/5899/cn-dr007")

    def test_create_link_from_url(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        readme_file = str(tmp_path / "README.md")
        readme = tmp_path / "README.md"
        readme.write_text("")

        mock_driver = MagicMock()
        mock_driver.title = "中國-逆回購利率(日數據)-7天期 - MacroMicro"

        with patch("financial_data_query.sources.macroMicro._create_uc_driver", return_value=mock_driver):
            with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
                with patch("financial_data_query.sources.macroMicro.README_PATH", readme_file):
                    with patch("time.sleep"):
                        macroMicroSymbolLinkConnect("https://www.macromicro.me/series/5899/cn-dr007")

        with open(json_file, "r", encoding="utf-8") as f:
            links = json.load(f)
        assert "cn-dr007" in links
        assert links["cn-dr007"]["url"] == "https://www.macromicro.me/series/5899/cn-dr007"
        assert links["cn-dr007"]["description"] == "中國-逆回購利率(日數據)-7天期"

    def test_updates_readme(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        readme_file = str(tmp_path / "README.md")
        readme = tmp_path / "README.md"
        readme.write_text("")

        mock_driver = MagicMock()
        mock_driver.title = "Test Symbol - MacroMicro"

        with patch("financial_data_query.sources.macroMicro._create_uc_driver", return_value=mock_driver):
            with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
                with patch("financial_data_query.sources.macroMicro.README_PATH", readme_file):
                    with patch("time.sleep"):
                        macroMicroSymbolLinkConnect("https://www.macromicro.me/series/123/test-sym")

        content = readme.read_text()
        assert "`test-sym`" in content
        assert "Test Symbol" in content


class TestMacroMicroFetcher:
    def test_source_name(self):
        assert MacroMicroFetcher.source_name == "macroMicro"

    def test_fetch_missing_dependency_raises(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        with open(json_file, "w") as f:
            json.dump({"sym1": {"url": "http://a.com", "description": "T"}}, f)
        with patch("financial_data_query.sources.macroMicro._check_uc_installed",
                   side_effect=FetchError("undetected-chromedriver 未安裝")):
            with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
                fetcher = MacroMicroFetcher()
                with pytest.raises(FetchError, match="undetected-chromedriver"):
                    fetcher.fetch("sym1")

    def test_fetch_symbol_not_in_links_raises(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        with open(json_file, "w") as f:
            json.dump({"other": {"url": "http://a.com", "description": "T"}}, f)
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            fetcher = MacroMicroFetcher()
            with pytest.raises(FetchError, match="找不到 symbol"):
                fetcher.fetch("sym1")

    def test_fetch_returns_dataframe(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        with open(json_file, "w") as f:
            json.dump({"sym1": {"url": "http://a.com", "description": "T"}}, f)

        mock_driver = MagicMock()
        mock_driver.execute_script.return_value = [
            {"x": 1704153600000, "y": 1.8},
            {"x": 1704240000000, "y": 1.9}
        ]

        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            with patch.object(MacroMicroFetcher, "_create_driver", return_value=mock_driver):
                with patch("time.sleep"):
                    fetcher = MacroMicroFetcher()
                    df = fetcher.fetch("sym1")
        assert isinstance(df, pd.DataFrame)
        assert "value" in df.columns
        assert len(df) == 2
        assert list(df["value"]) == [1.8, 1.9]


class TestMacroMicroBatchFetch:
    def test_batch_fetch_uses_single_driver(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        with open(json_file, "w") as f:
            json.dump({
                "sym1": {"url": "http://a.com", "description": "T"},
                "sym2": {"url": "http://b.com", "description": "T"}
            }, f)

        mock_driver = MagicMock()
        mock_driver.execute_script.return_value = [
            {"x": 1704153600000, "y": 1.0}
        ]

        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            with patch.object(MacroMicroFetcher, "_create_driver", return_value=mock_driver) as mock_create:
                with patch("time.sleep"):
                    fetcher = MacroMicroFetcher()
                    results = fetcher.batch_fetch(["sym1", "sym2"])
        assert "sym1" in results
        assert "sym2" in results
        assert mock_create.call_count == 1
        assert mock_driver.get.call_count == 2


class TestMacroMicroRegistration:
    def test_macroMicro_is_registered(self):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("macroMicro")
