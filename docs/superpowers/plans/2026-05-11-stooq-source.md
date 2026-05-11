# Stooq 資料來源實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 Stooq 資料來源，透過 undetected_chromedriver 操作網頁下載 CSV 資料並回傳 pandas DataFrame。

**Architecture:** 單一 `StooqFetcher` 類別繼承 `DataSourceFetcher`，內部建立瀏覽器 → 操作頁面 → 下載 CSV → 解析 → 清理。

**Tech Stack:** undetected-chromedriver, selenium, pandas

---

### Task 1: 新增 stooq optional dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 新增 stooq optional dependency**

在 `pyproject.toml` 的 `[project.optional-dependencies]` 區段新增 stooq：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.10",
    "responses>=0.25",
]
stooq = [
    "undetected-chromedriver>=3.5",
    "selenium>=4.0",
]
```

- [ ] **Step 2: 提交**

```bash
git add pyproject.toml
git commit -m "feat: add stooq optional dependency for browser-based data fetching"
```

---

### Task 2: 建立 StooqFetcher 基礎結構和 CSV 解析

**Files:**
- Create: `src/financial_data_query/sources/stooq.py`
- Test: `tests/test_stooq.py`

- [ ] **Step 1: 寫測試 — CSV 解析**

```python
# tests/test_stooq.py
import pytest
import pandas as pd
import io
from unittest import mock
from financial_data_query.sources.stooq import StooqFetcher
from financial_data_query.errors import FetchError


class TestStooqFetcher:
    @pytest.fixture
    def fetcher(self):
        return StooqFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "stooq"

    def test_parse_csv_returns_dataframe(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000\n2024-01-02,100.5,102,100,101.5,1200"
        df = fetcher._parse_csv(csv_content)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert isinstance(df.index, pd.DatetimeIndex)
        assert "Close" in df.columns
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `pytest tests/test_stooq.py -v`
Expected: FAIL with "ModuleNotFoundError" or "AttributeError"

- [ ] **Step 3: 實作 StooqFetcher 基礎和 CSV 解析**

```python
# src/financial_data_query/sources/stooq.py
import pandas as pd
import io
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


class StooqFetcher(DataSourceFetcher):
    source_name = "stooq"

    def _parse_csv(self, csv_content: str) -> pd.DataFrame:
        df = pd.read_csv(io.StringIO(csv_content))
        if df.empty:
            raise FetchError("Stooq returned empty data")
        df.columns = [c.strip() for c in df.columns]
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError("fetch not yet implemented")
```

- [ ] **Step 4: 執行測試確認通過**

Run: `pytest tests/test_stooq.py::TestStooqFetcher::test_parse_csv_returns_dataframe -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/financial_data_query/sources/stooq.py tests/test_stooq.py
git commit -m "feat: add StooqFetcher base class and CSV parsing"
```

---

### Task 3: 實作 frequency 參數驗證和選擇器映射

**Files:**
- Modify: `src/financial_data_query/sources/stooq.py`
- Modify: `tests/test_stooq.py`

- [ ] **Step 1: 寫測試 — frequency 驗證**

在 `tests/test_stooq.py` 的 `TestStooqFetcher` 類別中加入：

```python
    def test_frequency_map_contains_all_intervals(self, fetcher):
        assert "1d" in fetcher._FREQUENCY_MAP
        assert "1wk" in fetcher._FREQUENCY_MAP
        assert "1mo" in fetcher._FREQUENCY_MAP
        assert "3mo" in fetcher._FREQUENCY_MAP
        assert "1y" in fetcher._FREQUENCY_MAP

    def test_validate_frequency_valid(self, fetcher):
        for freq in ["1d", "1wk", "1mo", "3mo", "1y"]:
            assert fetcher._validate_frequency(freq) is True

    def test_validate_frequency_invalid_raises(self, fetcher):
        with pytest.raises(FetchError, match="Invalid frequency"):
            fetcher._validate_frequency("5m")
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `pytest tests/test_stooq.py::TestStooqFetcher::test_frequency_map_contains_all_intervals -v`
Expected: FAIL

- [ ] **Step 3: 實作 frequency 映射和驗證**

在 `StooqFetcher` 類別中加入：

```python
    _FREQUENCY_MAP = {
        "1d": 1,
        "1wk": 2,
        "1mo": 3,
        "3mo": 4,
        "1y": 5,
    }

    def _validate_frequency(self, frequency: str) -> bool:
        if frequency not in self._FREQUENCY_MAP:
            raise FetchError(
                f"Invalid frequency '{frequency}'. "
                f"Must be one of: {', '.join(self._FREQUENCY_MAP.keys())}"
            )
        return True
```

- [ ] **Step 4: 執行測試確認通過**

Run: `pytest tests/test_stooq.py::TestStooqFetcher::test_frequency_map_contains_all_intervals tests/test_stooq.py::TestStooqFetcher::test_validate_frequency_valid tests/test_stooq.py::TestStooqFetcher::test_validate_frequency_invalid_raises -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/financial_data_query/sources/stooq.py tests/test_stooq.py
git commit -m "feat: add frequency validation and selector mapping for Stooq"
```

---

### Task 4: 實作完整的 fetch 方法（瀏覽器操作）

**Files:**
- Modify: `src/financial_data_query/sources/stooq.py`
- Modify: `tests/test_stooq.py`

- [ ] **Step 1: 寫測試 — fetch 流程（mock WebDriver）**

在 `tests/test_stooq.py` 中加入：

```python
    def test_fetch_returns_dataframe(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000"
        csv_url = "https://stooq.com/q/d/l?d20240101&t20240101&s=dx.c"
        with mock.patch("financial_data_query.sources.stooq.undetected_chromedriver.Chrome") as MockChrome:
            mock_driver = mock.MagicMock()
            MockChrome.return_value = mock_driver
            mock_driver.save_creds.return_value = None
            mock_csv_link = mock.MagicMock()
            mock_csv_link.get_attribute.return_value = csv_url
            mock_driver.find_element.return_value = mock_csv_link
            mock_driver.current_url = "https://stooq.com/q/d/?s=dx.c"

            with mock.patch("financial_data_query.sources.stooq.requests.get") as mock_req:
                mock_req.return_value.text = csv_content
                result = fetcher.fetch("dx.c")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        MockChrome.assert_called_once()
        mock_driver.quit.assert_called_once()

    def test_fetch_with_frequency(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000"
        csv_url = "https://stooq.com/q/d/l?s=dx.c"
        with mock.patch("financial_data_query.sources.stooq.undetected_chromedriver.Chrome") as MockChrome:
            mock_driver = mock.MagicMock()
            MockChrome.return_value = mock_driver
            mock_csv_link = mock.MagicMock()
            mock_csv_link.get_attribute.return_value = csv_url
            mock_driver.find_element.return_value = mock_csv_link
            mock_driver.current_url = "https://stooq.com/q/d/?s=dx.c"

            with mock.patch("financial_data_query.sources.stooq.requests.get") as mock_req:
                mock_req.return_value.text = csv_content
                result = fetcher.fetch("dx.c", frequency="1wk")
        assert isinstance(result, pd.DataFrame)
        mock_driver.find_element.assert_called()

    def test_fetch_with_date_range(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-06-01,100,101,99,100.5,1000"
        csv_url = "https://stooq.com/q/d/l?s=dx.c"
        with mock.patch("financial_data_query.sources.stooq.undetected_chromedriver.Chrome") as MockChrome:
            mock_driver = mock.MagicMock()
            MockChrome.return_value = mock_driver
            mock_csv_link = mock.MagicMock()
            mock_csv_link.get_attribute.return_value = csv_url
            mock_driver.find_element.return_value = mock_csv_link
            mock_driver.current_url = "https://stooq.com/q/d/?s=dx.c"

            with mock.patch("financial_data_query.sources.stooq.requests.get") as mock_req:
                mock_req.return_value.text = csv_content
                result = fetcher.fetch("dx.c", start="2024-06-01", end="2024-12-31")
        assert isinstance(result, pd.DataFrame)

    def test_fetch_empty_data_raises(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume"
        csv_url = "https://stooq.com/q/d/l?s=dx.c"
        with mock.patch("financial_data_query.sources.stooq.undetected_chromedriver.Chrome") as MockChrome:
            mock_driver = mock.MagicMock()
            MockChrome.return_value = mock_driver
            mock_csv_link = mock.MagicMock()
            mock_csv_link.get_attribute.return_value = csv_url
            mock_driver.find_element.return_value = mock_csv_link
            mock_driver.current_url = "https://stooq.com/q/d/?s=dx.c"

            with mock.patch("financial_data_query.sources.stooq.requests.get") as mock_req:
                mock_req.return_value.text = csv_content
                with pytest.raises(FetchError):
                    fetcher.fetch("INVALID")

    def test_fetch_closes_browser_on_error(self, fetcher):
        with mock.patch("financial_data_query.sources.stooq.undetected_chromedriver.Chrome") as MockChrome:
            mock_driver = mock.MagicMock()
            MockChrome.return_value = mock_driver
            mock_driver.get.side_effect = Exception("Page load failed")

            with pytest.raises(Exception):
                fetcher.fetch("dx.c")
            mock_driver.quit.assert_called_once()
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `pytest tests/test_stooq.py::TestStooqFetcher::test_fetch_returns_dataframe -v`
Expected: FAIL with "NotImplementedError"

- [ ] **Step 3: 實作完整 fetch 方法**

替換 `StooqFetcher.fetch` 的 NotImplementedError 為：

```python
    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC

        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

            driver = uc.Chrome(options=options)
            driver.save_creds()

            url = f"https://stooq.com/q/d/?s={symbol}"
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table1"))
            )

            if frequency:
                self._validate_frequency(frequency)
                btn_index = self._FREQUENCY_MAP[frequency]
                freq_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"table.table1 tr td:nth-child(2) input:nth-of-type({btn_index})")
                    )
                )
                freq_btn.click()

            if start or end:
                self._set_date_range(driver, start, end)

            update_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "table.table1 tr td:nth-child(1) input[type='submit']")
                )
            )
            update_btn.click()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table2"))
            )

            csv_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "center b font a")
                )
            )
            csv_url = csv_link.get_attribute("href")
            if not csv_url:
                raise FetchError("Could not retrieve CSV download URL")

            import requests
            resp = requests.get(csv_url, timeout=30)
            resp.raise_for_status()
            csv_content = resp.text

            df = self._parse_csv(csv_content)

            if sub_field and sub_field in df.columns:
                df = df[[sub_field]]

            return df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"Stooq fetch failed: {e}") from e
        finally:
            if driver is not None:
                driver.quit()
```

同時加入 `_set_date_range` 方法：

```python
    def _set_date_range(
        self,
        driver,
        start: str | None,
        end: str | None,
    ) -> None:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC

        date_td = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table.table1 > tbody > tr > td:nth-child(1)")
            )
        )

        date_inputs = date_td.find_elements(By.CSS_SELECTOR, "input[type='text']")
        date_selects = date_td.find_elements(By.CSS_SELECTOR, "select")

        if start:
            year, month, day = start.split("-")
            Select(date_selects[0]).select_by_visible_text(month.zfill(2))
            date_inputs[0].clear()
            date_inputs[0].send_keys(day)
            date_inputs[1].clear()
            date_inputs[1].send_keys(year)

        if end:
            year, month, day = end.split("-")
            Select(date_selects[1]).select_by_visible_text(month.zfill(2))
            date_inputs[2].clear()
            date_inputs[2].send_keys(day)
            date_inputs[3].clear()
            date_inputs[3].send_keys(year)
```

- [ ] **Step 4: 執行測試確認通過**

Run: `pytest tests/test_stooq.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/financial_data_query/sources/stooq.py tests/test_stooq.py
git commit -m "feat: implement StooqFetcher browser-based fetch with CSV download"
```

---

### Task 5: 註冊 StooqFetcher 到 Registry

**Files:**
- Modify: `src/financial_data_query/sources/__init__.py`

- [ ] **Step 1: 註冊 StooqFetcher**

修改 `src/financial_data_query/sources/__init__.py`：

```python
from financial_data_query.registry import Registry
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.sources.fred import FredFetcher

try:
    from financial_data_query.sources.stooq import StooqFetcher
    Registry.register(StooqFetcher)
except ImportError:
    pass

Registry.register(YahooFetcher)
Registry.register(FredFetcher)
```

- [ ] **Step 2: 寫測試 — 註冊檢查**

在 `tests/test_stooq.py` 中加入：

```python
    def test_fetcher_is_registered(self, fetcher):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("stooq")
```

- [ ] **Step 3: 執行測試確認通過**

Run: `pytest tests/test_stooq.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/financial_data_query/sources/__init__.py tests/test_stooq.py
git commit -m "feat: register StooqFetcher in source registry with graceful import"
```

---

### Task 6: 驗證完整流程

**Files:**
- Test: `tests/test_stooq.py`

- [ ] **Step 1: 執行所有測試**

Run: `pytest tests/ -v`
Expected: 所有測試通過

- [ ] **Step 2: 提交**

```bash
git add -A
git commit -m "test: verify all tests pass with StooqFetcher integration"
```
