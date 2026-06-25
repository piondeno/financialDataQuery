from abc import ABC
import io
import re
import subprocess
import time
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


def _get_chrome_version_main() -> int | None:
    """Auto-detect Chrome browser major version from system."""
    candidates = ["google-chrome", "google-chrome-stable", "google-chrome-beta", "chromium", "chromium-browser"]
    for cmd in candidates:
        try:
            out = subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL, text=True)
            for part in out.split():
                if part[0].isdigit():
                    return int(part.split(".")[0])
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError, IndexError):
            continue
    return None


class NdcFetcher(DataSourceFetcher, ABC):
    base_url: str = ""
    _full_table_cache: dict = {}

    def _get_full_table_cached(self) -> pd.DataFrame:
        if self.source_name not in self._full_table_cache:
            self._full_table_cache[self.source_name] = self._get_full_table()
        return self._full_table_cache[self.source_name]

    def _parse_table(
        self,
        html: str,
        symbol: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        dfs = pd.read_html(io.StringIO(html))
        if not dfs:
            raise FetchError("無法解析表格: HTML 中找不到表格")

        df = dfs[0]
        if df.empty:
            raise FetchError("表格為空")

        first_col = df.columns[0]
        df[first_col] = df[first_col].astype(str).str.strip()
        df = df[df[first_col] != ""]
        df[first_col] = pd.to_datetime(df[first_col], format="%Y-%m", errors="coerce")
        df[first_col] = df[first_col] + pd.offsets.MonthEnd(0)
        df = df.dropna(subset=[first_col])
        df.set_index(first_col, inplace=True)

        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(how="all")
        df = df[~df.index.duplicated(keep="first")]
        if df.empty:
            raise FetchError("表格無有效資料")

        if symbol:
            if symbol not in df.columns:
                raise FetchError(
                    f"找不到指標 '{symbol}'。可用的指標: {list(df.columns)}"
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
        time.sleep(2)

        slider_handle = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".ui-slider-handle.ui-corner-all.ui-state-default")
            )
        )
        slider_handle.click()
        time.sleep(0.5)

        for _ in range(10):
            slider_handle.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)

        month_start = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@title, '月 起') and contains(text(), '1')]")
            )
        )
        month_start.click()
        time.sleep(0.5)

        month_end = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@title, '月 迄') and contains(text(), '12')]")
            )
        )
        month_end.click()
        time.sleep(0.5)

        table_view = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "table__view"))
        )
        table_view.click()
        time.sleep(3)

        tables = driver.find_elements(By.TAG_NAME, "table")
        for table in tables:
            table_html = table.get_attribute("outerHTML")
            if table_html and "<tbody>" in table_html:
                return table_html
        raise FetchError("找不到包含資料的表格")

    def _create_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        version_main = _get_chrome_version_main()
        if version_main:
            return uc.Chrome(options=options, version_main=version_main)
        return uc.Chrome(options=options)

    def _get_full_table(self) -> pd.DataFrame:
        driver = self._create_driver()
        try:
            driver.get(self.base_url)
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return window.angular") is not None
            )
            time.sleep(3)
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#select_all_1"))
            )
            table_html = self._interact_page(driver)
            return self._parse_table(table_html)
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"NDC fetch failed: {e}") from e
        finally:
            driver.quit()

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
        df_full = self._get_full_table_cached()
        if symbol not in df_full.columns:
            raise FetchError(
                f"找不到指標 '{symbol}'。可用的指標: {list(df_full.columns)}"
            )
        df = df_full[[symbol]].copy()
        df = df.rename(columns={symbol: "value"})
        if start:
            df = df[df.index >= pd.Timestamp(start)]
        if end:
            df = df[df.index <= pd.Timestamp(end)]
        return df

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
        df_full = self._get_full_table_cached()
        results = {}
        for symbol in symbols:
            if symbol not in df_full.columns:
                raise FetchError(
                    f"找不到指標 '{symbol}'。可用的指標: {list(df_full.columns)}"
                )
            df = df_full[[symbol]].copy()
            df = df.rename(columns={symbol: "value"})
            if start:
                df = df[df.index >= pd.Timestamp(start)]
            if end:
                df = df[df.index <= pd.Timestamp(end)]
            results[symbol] = df
        return results


class TwEcoFetcher(NdcFetcher):
    source_name = "tw_eco"
    base_url = "https://index.ndc.gov.tw/n/zh_tw/data/eco#/"


class TwPmiFetcher(NdcFetcher):
    source_name = "tw_pmi"
    base_url = "https://index.ndc.gov.tw/n/zh_tw/data/PMI#/"


