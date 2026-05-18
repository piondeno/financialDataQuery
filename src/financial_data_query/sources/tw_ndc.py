from abc import ABC
import io
import re
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

        slider_handle = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".ui-slider-handle.ui-corner-all.ui-state-default")
            )
        )
        slider_handle.click()

        for _ in range(10):
            slider_handle.send_keys(Keys.PAGE_DOWN)

        month_start = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, '月 起') and contains(text(), '1')]"))
        )
        month_start.click()

        month_end = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, '月 迄') and contains(text(), '12')]"))
        )
        month_end.click()

        table_view = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "table__view"))
        )
        table_view.click()

        import time
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

        driver = None
        try:
            driver = self._create_driver()
            driver.get(self.base_url)
            WebDriverWait(driver, 30).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "#select_all_1")
            )

            table_html = self._interact_page(driver)

            return self._parse_table(
                table_html, symbol=symbol, start=start, end=end
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
