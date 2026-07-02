from abc import ABC
import re
import time
import pandas as pd
from financial_data_query.base import DataSourceFetcher, _filter_by_date
from financial_data_query.errors import FetchError
from financial_data_query.constants import ROC_EPOCH_AD, MOEA_EARLIEST_DATE

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select as SelSelect
    from webdriver_manager.chrome import ChromeDriverManager

    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

# Region names in the MOEA website tables ( Traditional Chinese)
REGION_NAMES = ["美國", "日本", "中國大陸及香港", "東協", "歐洲", "其他地區"]


class MoeaFetcher(DataSourceFetcher, ABC):
    """Fetch export order data from MOEA (經濟部) website.

    Data source: https://service.moea.gov.tw/EE520/investigate/InvestigateBA.aspx

    Symbol format: "商品代號_地區"
    Examples: "化學品_美國", "電子產品_日本", "機械_中國大陸及香港"

    Available commodity codes (商品代號):
        化學品, 塑膠、橡膠及其製品, 紡織品, 基本金屬及其製品,
        電子產品, 機械, 電機產品, 資訊與通信產品,
        運輸工具及其設備, 光學器材, 礦產品, 其他

    Available regions (地區):
        美國, 日本, 中國大陸及香港, 東協, 歐洲, 其他地區
    """

    source_name = "moea"
    base_url = "https://service.moea.gov.tw/EE520/investigate/InvestigateBA.aspx"
    _full_data_cache: dict = {}

    def _get_full_data_cached(self) -> pd.DataFrame:
        if self.source_name not in self._full_data_cache:
            self._full_data_cache[self.source_name] = self._get_full_data()
        return self._full_data_cache[self.source_name]

    # Valid commodity codes for validation/error messages
    VALID_COMMODITIES = [
        "化學品", "塑膠、橡膠及其製品", "紡織品", "基本金屬及其製品",
        "電子產品", "機械", "電機產品", "資訊與通信產品",
        "運輸工具及其設備", "光學器材", "礦產品", "其他",
    ]

    def _parse_table_html(self, html: str) -> pd.DataFrame:
        """Parse the MOEA cross-table format from HTML.

        Table structure (after query):
        - Row 0: Region headers (美國 colspan=12, 日本 colspan=12, etc.)
        - Row 1: Commodity names under each region (12 per region)
        - Rows 2+: Data rows with year in col[0], month in col[1], then values

        Column layout:
          Col[0]: Year label (e.g., "73年") — only on first month of year
          Col[1]: Month label (e.g., "9月", "10月") — always present
          Cols[2-13]: 美國 data for 12 commodities
          Cols[14-25]: 日本 data for 12 commodities
          ... and so on for each region

        Returns DataFrame with DatetimeIndex (month periods) and symbol columns.
        """
        if not BeautifulSoup:
            raise FetchError("BeautifulSoup 未安裝。請執行: uv pip install beautifulsoup4")

        soup = BeautifulSoup(html, "html.parser")

        # Find the main result table
        result_table = soup.find("table", id="ContentPlaceHolder1_tabResult")
        if not result_table:
            raise FetchError("無法解析表格: HTML 中找不到資料表")

        rows = result_table.find_all("tr")
        if len(rows) < 3:
            raise FetchError("表格資料不足")

        # Build column header mapping from row 1 (commodities under regions)
        commodities = self.VALID_COMMODITIES  # 12 items

        # Parse symbol names: commodity_region for each column
        col_symbols = {}  # col_index -> "commodity_region"
        for region_idx, region in enumerate(REGION_NAMES):
            for comm_idx, comm in enumerate(commodities):
                col_idx = 2 + region_idx * len(commodities) + comm_idx
                col_symbols[col_idx] = f"{comm}_{region}"

        # Parse data rows (skip first 2 header rows)
        current_year_roc = None
        data_records = []

        for row in rows[2:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            # Get year and month
            cell_0_text = cells[0].get_text().strip()
            cell_1_text = cells[1].get_text().strip()

            # Parse year (only present on first row of each year, e.g., "73年")
            if cell_0_text:
                year_match = re.match(r'(\d+)[\u5e74]', cell_0_text)
                if year_match:
                    current_year_roc = int(year_match.group(1))

            # Parse month (always present, e.g., "9月" or "10月")
            month_match = re.match(r'(\d+)[\u6708]', cell_1_text)
            if not month_match:
                continue  # Skip rows without valid month

            current_month = int(month_match.group(1))

            if current_year_roc is None:
                continue  # Need year to create date

            # Convert ROC year to AD year
            year_ad = current_year_roc + ROC_EPOCH_AD

            try:
                date_val = pd.Timestamp(f"{year_ad}-{current_month:02d}-01") + pd.offsets.MonthEnd(0)
            except Exception:
                continue

            # Parse numeric values for each commodity-region combination
            record = {"__date__": date_val}
            has_data = False

            for col_idx, symbol in col_symbols.items():
                if col_idx >= len(cells):
                    break
                cell_text = cells[col_idx].get_text().strip()
                # Remove commas from numbers (e.g., "1,040" -> "1040")
                cell_cleaned = cell_text.replace(",", "").replace("，", "")

                if cell_cleaned and cell_cleaned != "-":
                    try:
                        record[symbol] = float(cell_cleaned)
                        has_data = True
                    except ValueError:
                        record[symbol] = None
                else:
                    record[symbol] = None

            if has_data:
                data_records.append(record)

        if not data_records:
            raise FetchError("表格中找不到有效資料")

        # Build DataFrame
        result_df = pd.DataFrame(data_records)
        result_df.set_index("__date__", inplace=True)
        result_df.index.name = None  # Remove index name for consistency

        # Sort by date (ascending, oldest to newest like MOEA website)
        result_df.sort_index(inplace=True)

        if result_df.empty:
            raise FetchError("表格無有效資料")

        return result_df

    def _is_valid_symbol(self, col_name: str) -> bool:
        """Check if a column name looks like a valid MOEA symbol (commodity_region)."""
        # A valid symbol contains at least one commodity code AND one region name
        has_commodity = any(comm in col_name for comm in self.VALID_COMMODITIES)
        has_region = any(region in col_name for region in REGION_NAMES)

        # Also check if column name contains both a comma (from Chinese list items like "塑膠、橡膠") and region
        return has_commodity and has_region

    def _create_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _interact_page(self, driver) -> str:
        """Automate MOEA website interaction steps.

        Steps:
        1. Select date '73年9月' from dropdown
        2-4. Check tree-view checkboxes (Item1n0, Item2n1, Item3n1)
        5. Click query button and wait for results
        6. Return panVaule panel content as HTML string
        """
        wait = WebDriverWait(driver, 20)

        # Step 1: Select date '73年9月' from dropdown
        ddl = wait.until(EC.presence_of_element_located(
            (By.ID, "ContentPlaceHolder1_ddlDateBeg")
        ))
        select = SelSelect(ddl)

        found_date = False
        for opt in select.options:
            if MOEA_EARLIEST_DATE in opt.text:
                select.select_by_visible_text(MOEA_EARLIEST_DATE)
                found_date = True
                break

        if not found_date:
            # Fallback: try to find any option containing '73' and '9月'
            options_el = ddl.find_elements(By.TAG_NAME, "option")
            for opt in options_el:
                text = opt.text
                if "73" in text and "9月" in text:
                    driver.execute_script("arguments[0].selected = true;", opt)
                    found_date = True
                    break

        if not found_date:
            # Final fallback: select second option (index 1, first data entry after default)
            try:
                select.select_by_index(1)
            except Exception:
                pass  # If no options available, continue anyway

        time.sleep(1)

        # Steps 2-4: Check tree-view checkboxes
        checkbox_ids = [
            "ContentPlaceHolder1_tvItem1n0CheckBox",
            "ContentPlaceHolder1_tvItem2n1CheckBox",
            "ContentPlaceHolder1_tvItem3n1CheckBox",
        ]

        for cb_id in checkbox_ids:
            try:
                cb = wait.until(EC.presence_of_element_located((By.ID, cb_id)))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                time.sleep(0.5)
            except Exception as e:
                # Some checkboxes may not exist - continue anyway
                print(f"Warning: Checkbox {cb_id} not found: {e}")

        # Step 5: Click query button and wait for page to complete
        btn_query = wait.until(EC.element_to_be_clickable(
            (By.ID, "ContentPlaceHolder1_btnQuery")
        ))
        btn_query.click()

        # Wait for postback and data loading
        time.sleep(3)

        # Try to detect any loading states
        try:
            wait.until(lambda d: not any(
                loading_cls in d.execute_script("return document.body.className;")
                for loading_cls in ["loading", "wait", "busy"]
            ))
        except Exception:
            pass  # No loading detection available

        time.sleep(2)

        # Step 6: Get data from panVaule panel
        try:
            panel = wait.until(EC.presence_of_element_located(
                (By.ID, "ContentPlaceHolder1_panVaule")
            ))
            return panel.get_attribute("innerHTML")
        except Exception as e:
            raise FetchError(f"無法獲取 panVaule 資料面板: {e}")

    def _get_full_data(self) -> pd.DataFrame:
        """Fetch all export order data from MOEA website."""
        driver = self._create_driver()
        try:
            driver.get(self.base_url)
            time.sleep(2)

            # Wait for page to fully load
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            html = self._interact_page(driver)
            return self._parse_table_html(html)
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"MOEA fetch failed: {e}") from e
        finally:
            driver.quit()

    def _parse_commodity(self, symbol: str) -> str:
        """Parse commodity code from symbol.

        Symbol format: just commodity code (e.g., "化學品", "資訊與通信產品")
        """
        if symbol not in self.VALID_COMMODITIES:
            raise FetchError(
                f"找不到商品代號 '{symbol}'。可用的商品代號:\n{self.VALID_COMMODITIES}"
            )
        return symbol

    @staticmethod
    def _rename_region_columns(df: pd.DataFrame, commodity: str) -> None:
        """Rename columns from 'commodity_region' to just 'region'."""
        rename_map = {f"{commodity}_{region}": region for region in REGION_NAMES}
        df.rename(columns=rename_map, inplace=True)

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        """Fetch export order data for a specific commodity.

        Args:
            symbol: Commodity code (商品代號), e.g., "化學品", "資訊與通信產品"
            start: Start date (YYYY-MM-DD), optional
            end: End date (YYYY-MM-DD), optional
            sub_field: Not used for this source
            frequency: Not used for this source

        Returns:
            DataFrame with DatetimeIndex and columns = ['美國', '日本', '中國大陸及香港', '東協', '歐洲', '其他地區']
        """
        if not _HAS_DEPS:
            raise FetchError(
                "webdriver-manager 未安裝。"
                "請執行: uv pip install webdriver-manager selenium"
            )

        df_full = self._get_full_data_cached()
        if df_full.empty:
            raise FetchError("無法取得 MOEA 資料")

        # Parse and validate commodity code
        commodity = self._parse_commodity(symbol)

        # Build the list of region columns for this commodity
        region_cols = [f"{commodity}_{region}" for region in REGION_NAMES]

        # Check that all region columns exist
        missing_cols = [c for c in region_cols if c not in df_full.columns]
        if missing_cols:
            available_commodities = set()
            for col in df_full.columns:
                comm = "_".join(col.rsplit("_", 1)[0:-0] if "_" not in col else [col.rpartition("_")[0]])
                # Extract commodity from "commodity_region" format
                parts = col.rsplit("_", 1)
                if len(parts) == 2 and parts[0] in self.VALID_COMMODITIES:
                    available_commodities.add(parts[0])

            raise FetchError(
                f"找不到商品 '{symbol}' 的地區資料。"
                f"可用的商品代號:\n{sorted(available_commodities)}"
            )

        # Extract columns for all regions
        df = df_full[region_cols].copy()

        # Rename columns to region names only (without commodity prefix)
        self._rename_region_columns(df, commodity)

        # Filter by date range if specified
        df = _filter_by_date(df, start, end)

        # Drop rows with all NaN values
        df = df.dropna(how="all")

        if df.empty:
            raise FetchError(f"在指定日期範圍內找不到 '{symbol}' 的資料")

        return df

    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for multiple commodities in one browser session.

        Args:
            symbols: List of commodity codes, e.g., ["化學品", "電子產品"]
            start: Start date (YYYY-MM-DD), optional
            end: End date (YYYY-MM-DD), optional
            sub_field: Not used for this source
            frequency: Not used for this source

        Returns:
            Dict mapping commodity to DataFrame with DatetimeIndex and region columns.
        """
        if not _HAS_DEPS:
            raise FetchError(
                "webdriver-manager 未安裝。"
                "請執行: uv pip install webdriver-manager selenium"
            )

        df_full = self._get_full_data_cached()
        results = {}

        for symbol in symbols:
            commodity = self._parse_commodity(symbol)

            region_cols = [f"{commodity}_{region}" for region in REGION_NAMES]

            missing_cols = [c for c in region_cols if c not in df_full.columns]
            if missing_cols:
                raise FetchError(
                    f"找不到商品 '{symbol}' 的地區資料。"
                )

            df = df_full[region_cols].copy()
            self._rename_region_columns(df, commodity)

            df = _filter_by_date(df, start, end)

            df = df.dropna(how="all")

            if df.empty:
                raise FetchError(f"在指定日期範圍內找不到 '{symbol}' 的資料")

            results[symbol] = df

        return results
