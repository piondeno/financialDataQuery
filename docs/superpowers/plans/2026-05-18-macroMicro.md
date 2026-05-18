# MacroMicro Data Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add MacroMicro (macromicro.me) as a financial data source with user-managed symbol-to-URL mapping.

**Architecture:** A single `macroMicro.py` module contains both the `MacroMicroFetcher` class and `macroMicroSymbolLinkConnect()` function. Symbol mappings are stored in `.macroMicro_links.json` in the project root. The function auto-updates README.md using marker comments.

**Tech Stack:** `undetected-chromedriver`, `selenium`, `pandas`, Highcharts JS extraction via `execute_script`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/financial_data_query/sources/macroMicro.py` | Create | Symbol link JSON helpers, README updater, `macroMicroSymbolLinkConnect()`, `MacroMicroFetcher` |
| `src/financial_data_query/sources/__init__.py` | Modify | Register `MacroMicroFetcher` |
| `README.md` | Modify | Add MacroMicro section with marker comments |
| `.gitignore` | Modify | Add `.macroMicro_links.json` |
| `tests/test_macroMicro.py` | Create | Tests for all functionality |

---

### Task 1: Symbol link JSON read/write helpers

**Files:**
- Create: `src/financial_data_query/sources/macroMicro.py`
- Test: `tests/test_macroMicro.py`

- [ ] **Step 1: Write the failing test for loading links**

```python
# tests/test_macroMicro.py
import json
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestLoadLinks -v`
Expected: FAIL with `ImportError` (module doesn't exist yet)

- [ ] **Step 3: Write minimal implementation**

```python
# src/financial_data_query/sources/macroMicro.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestLoadLinks -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write test for save_links**

Add to `tests/test_macroMicro.py`:

```python
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
```

- [ ] **Step 6: Run save_links tests**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestSaveLinks -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Commit**

```bash
git add src/financial_data_query/sources/macroMicro.py tests/test_macroMicro.py
git commit -m "feat: add symbol link JSON read/write helpers for MacroMicro"
```

---

### Task 2: README update mechanism

**Files:**
- Modify: `src/financial_data_query/sources/macroMicro.py`
- Test: `tests/test_macroMicro.py`

- [ ] **Step 1: Write failing test for README update**

Add to `tests/test_macroMicro.py`:

```python
from financial_data_query.sources.macroMicro import _update_readme_symbols


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestUpdateReadmeSymbols -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write implementation**

Add to `src/financial_data_query/sources/macroMicro.py`:

```python
README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "README.md")
MACROMICRO_START_MARKER = "<!-- MACROMICRO_SYMBOLS_START -->"
MACROMICRO_END_MARKER = "<!-- MACROMICRO_SYMBOLS_END -->"


def _update_readme_symbols(links: dict, readme_path: str | None = None) -> None:
    path = readme_path or README_PATH
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    table_lines = ["| Symbol | 說明 |", "|--------|------|"]
    for symbol in sorted(links.keys()):
        desc = links[symbol].get("description", "")
        table_lines.append(f"| `{symbol}` | {desc} |")
    table_block = "\n".join(table_lines)

    if MACROMICRO_START_MARKER in content and MACROMICRO_END_MARKER in content:
        start_idx = content.index(MACROMICRO_START_MARKER) + len(MACROMICRO_START_MARKER)
        end_idx = content.index(MACROMICRO_END_MARKER)
        content = content[:start_idx] + "\n" + table_block + "\n" + content[end_idx:]
    else:
        new_section = f"\n## MacroMicro (`\"macroMicro\"`)\n\n{MACROMICRO_START_MARKER}\n{table_block}\n{MACROMICRO_END_MARKER}\n"
        content = content.rstrip() + new_section

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestUpdateReadmeSymbols -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/financial_data_query/sources/macroMicro.py tests/test_macroMicro.py
git commit -m "feat: add README auto-update for MacroMicro symbol table"
```

---

### Task 3: `macroMicroSymbolLinkConnect` function

**Files:**
- Modify: `src/financial_data_query/sources/macroMicro.py`
- Test: `tests/test_macroMicro.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_macroMicro.py`:

```python
from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect


class TestMacroMicroSymbolLinkConnect:
    def test_create_new_link(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        readme_file = str(tmp_path / "README.md")
        readme = tmp_path / "README.md"
        readme.write_text("")
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            with patch("financial_data_query.sources.macroMicro.README_PATH", readme_file):
                macroMicroSymbolLinkConnect("sym1", "http://example.com", "Test Symbol")
        links = _load_links()
        assert links["sym1"]["url"] == "http://example.com"
        assert links["sym1"]["description"] == "Test Symbol"

    def test_update_existing_link(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        readme_file = str(tmp_path / "README.md")
        readme = tmp_path / "README.md"
        readme.write_text("")
        with open(json_file, "w") as f:
            json.dump({"sym1": {"url": "http://old.com", "description": "Old"}}, f)
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            with patch("financial_data_query.sources.macroMicro.README_PATH", readme_file):
                macroMicroSymbolLinkConnect("sym1", "http://new.com", "New")
        links = _load_links()
        assert links["sym1"]["url"] == "http://new.com"
        assert links["sym1"]["description"] == "New"

    def test_updates_readme(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        readme_file = str(tmp_path / "README.md")
        readme = tmp_path / "README.md"
        readme.write_text("")
        with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
            with patch("financial_data_query.sources.macroMicro.README_PATH", readme_file):
                macroMicroSymbolLinkConnect("sym1", "http://a.com", "Test")
        content = readme.read_text()
        assert "`sym1`" in content
        assert "Test" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroSymbolLinkConnect -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write implementation**

Add to `src/financial_data_query/sources/macroMicro.py`:

```python
def macroMicroSymbolLinkConnect(symbol: str, url: str, description: str) -> None:
    links = _load_links()
    links[symbol] = {"url": url, "description": description}
    _save_links(links)
    _update_readme_symbols(links)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroSymbolLinkConnect -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/financial_data_query/sources/macroMicro.py tests/test_macroMicro.py
git commit -m "feat: add macroMicroSymbolLinkConnect function"
```

---

### Task 4: `MacroMicroFetcher.fetch` with Highcharts extraction

**Files:**
- Modify: `src/financial_data_query/sources/macroMicro.py`
- Test: `tests/test_macroMicro.py`

- [ ] **Step 1: Write failing test for fetch**

Add to `tests/test_macroMicro.py`:

```python
from financial_data_query.sources.macroMicro import MacroMicroFetcher
from financial_data_query.errors import FetchError


class TestMacroMicroFetcher:
    def test_source_name(self):
        assert MacroMicroFetcher.source_name == "macroMicro"

    def test_fetch_missing_dependency_raises(self, tmp_path):
        json_file = str(tmp_path / ".macroMicro_links.json")
        with open(json_file, "w") as f:
            json.dump({"sym1": {"url": "http://a.com", "description": "T"}}, f)
        with patch("financial_data_query.sources.macroMicro.uc", None):
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
        mock_uc = MagicMock()
        mock_uc.Chrome.return_value = mock_driver

        with patch("financial_data_query.sources.macroMicro.uc", mock_uc):
            with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
                with patch("time.sleep"):
                    fetcher = MacroMicroFetcher()
                    df = fetcher.fetch("sym1")
        assert isinstance(df, pd.DataFrame)
        assert "value" in df.columns
        assert len(df) == 2
        assert list(df["value"]) == [1.8, 1.9]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroFetcher -v`
Expected: FAIL (class doesn't exist yet or incomplete)

- [ ] **Step 3: Write implementation**

Add to `src/financial_data_query/sources/macroMicro.py`:

```python
try:
    import undetected_chromedriver as uc
    import time
except ImportError:
    uc = None
    time = None


class MacroMicroFetcher(DataSourceFetcher):
    source_name = "macroMicro"

    def _create_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return uc.Chrome(options=options)

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        if not uc:
            raise FetchError(
                "undetected-chromedriver 未安裝。"
                "請執行: pip install financial-data-query[stooq]"
            )

        links = _load_links()
        if symbol not in links:
            raise FetchError(
                f"找不到 symbol '{symbol}'。請先執行 macroMicroSymbolLinkConnect() 建立映射"
            )

        url = links[symbol]["url"]
        driver = self._create_driver()
        try:
            driver.get(url)
            time.sleep(3)
            data_points = driver.execute_script(
                "return Highcharts.charts[0].series[0].data.map(function(point) {"
                "  return {x: point.x, y: point.y};"
                "});"
            )
            if not data_points:
                raise FetchError("頁面中找不到 Highcharts 圖表資料")

            base_time = pd.Timestamp("1970-01-01", tz="UTC")
            rows = []
            for point in data_points:
                dt = base_time + pd.Timedelta(milliseconds=point["x"])
                dt_twt = dt.tz_convert("Asia/Taipei").tz_localize(None)
                rows.append((dt_twt, point["y"]))

            df = pd.DataFrame(rows, columns=["date", "value"])
            df.set_index("date", inplace=True)

            if start:
                df = df[df.index >= pd.Timestamp(start)]
            if end:
                df = df[df.index <= pd.Timestamp(end)]

            return df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"無法存取 MacroMicro 頁面: {url}: {e}") from e
        finally:
            driver.quit()
```

Also add `from unittest.mock import MagicMock` to test file imports.

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroFetcher -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/financial_data_query/sources/macroMicro.py tests/test_macroMicro.py
git commit -m "feat: implement MacroMicroFetcher.fetch with Highcharts extraction"
```

---

### Task 5: `batch_fetch` with shared browser

**Files:**
- Modify: `src/financial_data_query/sources/macroMicro.py`
- Test: `tests/test_macroMicro.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_macroMicro.py`:

```python
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
        mock_uc = MagicMock()
        mock_uc.Chrome.return_value = mock_driver

        with patch("financial_data_query.sources.macroMicro.uc", mock_uc):
            with patch("financial_data_query.sources.macroMicro.LINKS_FILE_PATH", json_file):
                with patch("time.sleep"):
                    fetcher = MacroMicroFetcher()
                    results = fetcher.batch_fetch(["sym1", "sym2"])
        assert "sym1" in results
        assert "sym2" in results
        assert mock_uc.Chrome.call_count == 1
        assert mock_driver.get.call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroBatchFetch -v`
Expected: FAIL (batch_fetch uses default base impl which creates new driver per symbol)

- [ ] **Step 3: Write implementation**

Add to `MacroMicroFetcher` class:

```python
    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        if not uc:
            raise FetchError(
                "undetected-chromedriver 未安裝。"
                "請執行: pip install financial-data-query[stooq]"
            )

        links = _load_links()
        driver = self._create_driver()
        results = {}
        try:
            for symbol in symbols:
                if symbol not in links:
                    raise FetchError(
                        f"找不到 symbol '{symbol}'。請先執行 macroMicroSymbolLinkConnect() 建立映射"
                    )
                url = links[symbol]["url"]
                driver.get(url)
                time.sleep(3)
                data_points = driver.execute_script(
                    "return Highcharts.charts[0].series[0].data.map(function(point) {"
                    "  return {x: point.x, y: point.y};"
                    "});"
                )
                if not data_points:
                    raise FetchError(f"頁面中找不到 Highcharts 圖表資料: {url}")

                base_time = pd.Timestamp("1970-01-01", tz="UTC")
                rows = []
                for point in data_points:
                    dt = base_time + pd.Timedelta(milliseconds=point["x"])
                    dt_twt = dt.tz_convert("Asia/Taipei").tz_localize(None)
                    rows.append((dt_twt, point["y"]))

                df = pd.DataFrame(rows, columns=["date", "value"])
                df.set_index("date", inplace=True)

                if start:
                    df = df[df.index >= pd.Timestamp(start)]
                if end:
                    df = df[df.index <= pd.Timestamp(end)]

                results[symbol] = df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"MacroMicro batch fetch failed: {e}") from e
        finally:
            driver.quit()
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroBatchFetch -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/financial_data_query/sources/macroMicro.py tests/test_macroMicro.py
git commit -m "feat: implement MacroMicroFetcher.batch_fetch with shared browser"
```

---

### Task 6: Register MacroMicroFetcher

**Files:**
- Modify: `src/financial_data_query/sources/__init__.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_macroMicro.py`:

```python
from financial_data_query.registry import Registry


class TestMacroMicroRegistration:
    def test_macroMicro_is_registered(self):
        assert Registry.is_registered("macroMicro")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroRegistration -v`
Expected: FAIL (not registered yet)

- [ ] **Step 3: Add registration to `__init__.py`**

Add to `src/financial_data_query/sources/__init__.py` before the final `Registry.register` calls:

```python
try:
    from financial_data_query.sources.macroMicro import MacroMicroFetcher
    Registry.register(MacroMicroFetcher)
except ImportError:
    pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/test_macroMicro.py::TestMacroMicroRegistration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/financial_data_query/sources/__init__.py tests/test_macroMicro.py
git commit -m "feat: register MacroMicroFetcher in sources"
```

---

### Task 7: Add MacroMicro section to README

**Files:**
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Add MacroMicro section to README**

Add after the NCD 台灣 PMI section (after line ~284), before `## 設定`:

```markdown
### MacroMicro (`"macroMicro"`)

- 底層:`undetected_chromedriver` + Selenium 網頁爬蟲
- 免 API key，需要 Chrome 瀏覽器
- 資料來源：MacroMicro (https://www.macromicro.me)
- 使用前需先執行 `macroMicroSymbolLinkConnect()` 建立 symbol 映射

**建立 symbol 映射：**

```python
from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect

macroMicroSymbolLinkConnect(
    "china-reverse-repo-rate-7-day",
    "https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day",
    "中國7天期逆回購利率"
)
```

**Symbols：**

<!-- MACROMICRO_SYMBOLS_START -->
<!-- MACROMICRO_SYMBOLS_END -->

```python
# 安裝額外依賴
pip install -e ".[stooq]"

# 查詢
result = query("macroMicro", "china-reverse-repo-rate-7-day")

# 批量查詢
result = query("macroMicro", ["sym1", "sym2"])
```
```

- [ ] **Step 2: Update source list in README API table**

In the `source` parameter description (line ~37), add `"macroMicro"` to the list.

- [ ] **Step 3: Add `.macroMicro_links.json` to `.gitignore`**

Add line `.macroMicro_links.json` to `.gitignore`.

- [ ] **Step 4: Commit**

```bash
git add README.md .gitignore
git commit -m "docs: add MacroMicro section to README and gitignore"
```

---

### Task 8: Full test run and verification

**Files:**
- Test: all tests

- [ ] **Step 1: Run all tests**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -m pytest tests/ -v`
Expected: All tests PASS (original 100 + new ~15 = ~115)

- [ ] **Step 2: Verify import works**

Run: `/home/piondeno/uvEnv/baseEnv/bin/python -c "from financial_data_query import list_sources; print(list_sources())"`
Expected: Output includes `"macroMicro"`

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: MacroMicro data source implementation complete" || true
```

---

## Self-Review

**Spec coverage:**
- [x] Symbol link JSON read/write (Task 1)
- [x] README update mechanism (Task 2)
- [x] `macroMicroSymbolLinkConnect` function (Task 3)
- [x] `MacroMicroFetcher.fetch` with Highcharts (Task 4)
- [x] `batch_fetch` with shared browser (Task 5)
- [x] Registration in `__init__.py` (Task 6)
- [x] README section (Task 7)
- [x] Tests for all components (throughout)
- [x] Error handling: missing dependency, symbol not found, empty chart, invalid JSON (Tasks 1, 4)
- [x] UTC+8 timezone conversion (Task 4)
- [x] `.gitignore` entry (Task 7)

**Placeholder scan:** No TBD, TODO, or vague instructions. All code blocks are complete.

**Type consistency:** `LINKS_FILE_PATH`, `_load_links()`, `_save_links()`, `_update_readme_symbols()`, `macroMicroSymbolLinkConnect()`, `MacroMicroFetcher` all consistently named across tasks. DataFrame column is always `"value"`. Source name is always `"macroMicro"`.
