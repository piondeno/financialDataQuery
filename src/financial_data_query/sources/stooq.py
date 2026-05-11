import pandas as pd
import io
import requests
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    uc = None
    By = None
    WebDriverWait = None
    Select = None
    EC = None


class StooqFetcher(DataSourceFetcher):
    source_name = "stooq"

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

    def _set_date_range(
        self,
        driver,
        start: str | None,
        end: str | None,
    ) -> None:
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

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
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
