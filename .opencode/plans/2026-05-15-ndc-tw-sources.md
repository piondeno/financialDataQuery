# NDC 台湾经济指标资料来源实作计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `TwEcoFetcher` 和 `TwPmiFetcher` 两个资料来源，透过 undetected_chromedriver 操作 NDC 台湾景气指标网站，抓取 HTML 表格资料并回传 pandas DataFrame。

**Architecture:** 抽象基类 `NdcFetcher` 处理共同 Selenium 操作流程（全选、年度滑块、月份、表格视图、解析），两个子类 `TwEcoFetcher` 和 `TwPmiFetcher` 仅覆写 `base_url` 和 `source_name`。

**Tech Stack:** undetected-chromedriver, selenium, pandas

---

### File Structure

| File | Type | Responsibility |
|------|------|----------------|
| `src/financial_data_query/sources/tw_ndc.py` | Create | `NdcFetcher` base + `TwEcoFetcher` + `TwPmiFetcher` |
| `src/financial_data_query/sources/__init__.py` | Modify | Register both fetchers |
| `tests/test_tw_ndc.py` | Create | Unit tests with mocked WebDriver |

---

### Task 1: 建立 NdcFetcher 基础结构和表格解析

**Files:**
- Create: `src/financial_data_query/sources/tw_ndc.py`
- Test: `tests/test_tw_ndc.py`

- [ ] **Step 1: 写测试 — 来源名称与表格解析**

```python
# tests/test_tw_ndc.py
import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.tw_ndc import NdcFetcher, TwEcoFetcher, TwPmiFetcher
from financial_data_query.errors import FetchError


class TestTwEcoFetcher:
    @pytest.fixture
    def fetcher(self):
        return TwEcoFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "tw_eco"

    def test_base_url(self, fetcher):
        assert "eco" in fetcher.base_url


class TestTwPmiFetcher:
    @pytest.fixture
    def fetcher(self):
        return TwPmiFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "tw_pmi"

    def test_base_url(self, fetcher):
        assert "PMI" in fetcher.base_url


class TestNdcParseTable:
    @pytest.fixture
    def fetcher(self):
        return TwEcoFetcher()

    def test_parse_table_basic(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>扩散指数</th><th>景气指标</th></tr>
          <tr><td>2024/01</td><td>50.1</td><td>102.3</td></tr>
          <tr><td>2024/02</td><td>51.2</td><td>103.4</td></tr>
        </table>
        """
        df = fetcher._parse_table(html)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert isinstance(df.index, pd.DatetimeIndex)
        assert "扩散指数" in df.columns
        assert "景气指标" in df.columns

    def test_parse_table_filters_symbol(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>扩散指数</th><th>景气指标</th></tr>
          <tr><td>2024/01</td><td>50.1</td><td>102.3</td></tr>
          <tr><td>2024/02</td><td>51.2</td><td>103.4</td></tr>
        </table>
        """
        df = fetcher._parse_table(html, symbol="扩散指数")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["扩散指数"]

    def test_parse_table_symbol_not_found_raises(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>扩散指数</th></tr>
          <tr><td>2024/01</td><td>50.1</td></tr>
        </table>
        """
        with pytest.raises(FetchError, match="找不到"):
            fetcher._parse_table(html, symbol="不存在的指标")

    def test_parse_table_empty_raises(self, fetcher):
        html = "<table><tr><th>月份</th></tr></table>"
        with pytest.raises(FetchError):
            fetcher._parse_table(html, symbol="任何指标")

    def test_parse_table_date_filtering(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>扩散指数</th></tr>
          <tr><td>2020/01</td><td>45.0</td></tr>
          <tr><td>2022/06</td><td>50.0</td></tr>
          <tr><td>2024/12</td><td>55.0</td></tr>
        </table>
        """
        df = fetcher._parse_table(html, symbol="扩散指数", start="2021-01-01", end="2023-12-31")
        assert len(df) == 1
        assert df.index[0].year == 2022
```

- [ ] **Step 2: 执行测试确认失败**

Run: `pytest tests/test_tw_ndc.py -v`
Expected: FAIL with "ModuleNotFoundError" or import errors

- [ ] **Step 3: 实作 NdcFetcher 基类基础与表格解析**

```python
# src/financial_data_query/sources/tw_ndc.py
from abc import ABC
import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
except ImportError:
    uc = None
    By = None
    WebDriverWait = None
    EC = None
    Keys = None


class NdcFetcher(DataSourceFetcher, ABC):
    base_url: str = ""

    def _parse_table(
        self,
        html: str,
        symbol: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        dfs = pd.read_html(html)
        if not dfs:
            raise FetchError("无法解析表格: HTML 中找不到表格")

        df = dfs[0]
        if df.empty:
            raise FetchError("表格为空")

        first_col = df.columns[0]
        df[first_col] = df[first_col].astype(str).str.strip()
        df = df[df[first_col] != ""]
        df[first_col] = pd.to_datetime(df[first_col], format="%Y/%m", errors="coerce")
        df = df.dropna(subset=[first_col])
        df.set_index(first_col, inplace=True)

        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if symbol:
            if symbol not in df.columns:
                raise FetchError(
                    f"找不到指标 '{symbol}'。可用的指标: {list(df.columns)}"
                )
            df = df[[symbol]]

        if start:
            df = df[df.index >= pd.Timestamp(start)]
        if end:
            df = df[df.index <= pd.Timestamp(end)]

        return df

    def _interact_page(self, driver) -> str:
        select_all_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#select_all_1"))
        )
        select_all_btn.click()

        slider_handle = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".ui-slider-handle.ui-corner-all.ui-state-default")
            )
        )
        slider_handle.click()

        for _ in range(10):
            slider_handle.send_keys(Keys.PAGE_DOWN)

        month_start = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@title, '月 起')]")
            )
        )
        month_start.click()

        month_end = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@title, '月 迄')]")
            )
        )
        month_end.click()

        table_view = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "table__view"))
        )
        table_view.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        return driver.page_source

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
                "undetected-chromedriver 未安装。"
                "请运行: pip install financial-data-query[stooq]"
            )

        driver = None
        try:
            driver = self._create_driver()
            driver.get(self.base_url)
            WebDriverWait(driver, 30).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "#select_all_1")
            )

            page_source = self._interact_page(driver)

            import re
            table_match = re.search(
                r"<table[^>]*>.*?</table>", page_source, re.DOTALL
            )
            if not table_match:
                raise FetchError("页面中找不到表格元素")

            return self._parse_table(
                table_match.group(0), symbol=symbol, start=start, end=end
            )
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"NDC fetch failed: {e}") from e
        finally:
            if driver is not None:
                driver.quit()


class TwEcoFetcher(NdcFetcher):
    source_name = "tw_eco"
    base_url = "https://index.ndc.gov.tw/n/zh_tw/data/eco#/"


class TwPmiFetcher(NdcFetcher):
    source_name = "tw_pmi"
    base_url = "https://index.ndc.gov.tw/n/zh_tw/data/PMI#/"
```

- [ ] **Step 4: 执行测试确认通过**

Run: `pytest tests/test_tw_ndc.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/financial_data_query/sources/tw_ndc.py tests/test_tw_ndc.py
git commit -m "feat: add NdcFetcher base class with TwEcoFetcher and TwPmiFetcher"
```

---

### Task 2: 注册 Fetchers 到 Registry

**Files:**
- Modify: `src/financial_data_query/sources/__init__.py`
- Modify: `tests/test_tw_ndc.py`

- [ ] **Step 1: 注册 TwEcoFetcher 和 TwPmiFetcher**

修改 `src/financial_data_query/sources/__init__.py`:

```python
from financial_data_query.registry import Registry
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.sources.fred import FredFetcher

try:
    from financial_data_query.sources.stooq import StooqFetcher
    Registry.register(StooqFetcher)
except ImportError:
    pass

try:
    from financial_data_query.sources.tw_ndc import TwEcoFetcher, TwPmiFetcher
    Registry.register(TwEcoFetcher)
    Registry.register(TwPmiFetcher)
except ImportError:
    pass

Registry.register(YahooFetcher)
Registry.register(FredFetcher)
```

- [ ] **Step 2: 写测试 — 注册检查**

在 `tests/test_tw_ndc.py` 中加入:

```python
class TestNdcRegistration:
    def test_tw_eco_is_registered(self):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("tw_eco")

    def test_tw_pmi_is_registered(self):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("tw_pmi")

    def test_tw_eco_fetcher_inherits_base(self):
        from financial_data_query.base import DataSourceFetcher
        fetcher = TwEcoFetcher()
        assert isinstance(fetcher, DataSourceFetcher)

    def test_tw_pmi_fetcher_inherits_base(self):
        from financial_data_query.base import DataSourceFetcher
        fetcher = TwPmiFetcher()
        assert isinstance(fetcher, DataSourceFetcher)
```

- [ ] **Step 3: 执行测试确认通过**

Run: `pytest tests/test_tw_ndc.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/financial_data_query/sources/__init__.py tests/test_tw_ndc.py
git commit -m "feat: register TwEcoFetcher and TwPmiFetcher in source registry"
```

---

### Task 3: 添加 Mock 测试验证完整 fetch 流程

**Files:**
- Modify: `tests/test_tw_ndc.py`

- [ ] **Step 1: 写测试 — fetch 流程（mock WebDriver）**

在 `tests/test_tw_ndc.py` 中加入:

```python
class TestNdcFetchFlow:
    @pytest.fixture
    def fetcher(self):
        return TwEcoFetcher()

    def test_fetch_calls_driver_methods(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.page_source = """
        <table>
          <tr><th>月份</th><th>扩散指数</th></tr>
          <tr><td>2024/01</td><td>50.1</td></tr>
        </table>
        """

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_interact_page", return_value=mock_driver.page_source):
                result = fetcher.fetch("扩散指数")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "扩散指数" in result.columns
        mock_driver.quit.assert_called_once()

    def test_fetch_with_date_range(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.page_source = """
        <table>
          <tr><th>月份</th><th>扩散指数</th></tr>
          <tr><td>2020/01</td><td>45.0</td></tr>
          <tr><td>2024/06</td><td>50.0</td></tr>
          <tr><td>2024/12</td><td>55.0</td></tr>
        </table>
        """

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_interact_page", return_value=mock_driver.page_source):
                result = fetcher.fetch("扩散指数", start="2024-01-01", end="2024-10-31")

        assert len(result) == 1
        assert result.index[0].month == 6

    def test_fetch_no_table_raises(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.page_source = "<html><body>No table here</body></html>"

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_interact_page", return_value=mock_driver.page_source):
                with pytest.raises(FetchError, match="找不到表格"):
                    fetcher.fetch("扩散指数")

    def test_fetch_closes_browser_on_error(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.get.side_effect = Exception("Connection failed")

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with pytest.raises(FetchError):
                fetcher.fetch("扩散指数")

        mock_driver.quit.assert_called_once()

    def test_fetch_missing_dependency_raises(self):
        with mock.patch("financial_data_query.sources.tw_ndc.uc", None):
            fetcher = TwEcoFetcher()
            with pytest.raises(FetchError, match="undetected-chromedriver"):
                fetcher.fetch("扩散指数")
```

- [ ] **Step 2: 执行测试确认通过**

Run: `pytest tests/test_tw_ndc.py -v`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add tests/test_tw_ndc.py
git commit -m "test: add mocked fetch flow tests for NDC fetchers"
```

---

### Task 4: 验证完整流程

**Files:**
- Test: all tests

- [ ] **Step 1: 执行所有测试**

Run: `pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 2: 提交**

```bash
git add -A
git commit -m "test: verify all tests pass with NDC fetchers integration"
```
