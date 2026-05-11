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

_FREQUENCY_TO_VALUE = {
    "1d": "d",
    "1wk": "w",
    "1mo": "m",
    "3mo": "q",
    "1y": "y",
}


class StooqFetcher(DataSourceFetcher):
    source_name = "stooq"

    _FREQUENCY_MAP = _FREQUENCY_TO_VALUE

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
        if start:
            year, month, day = start.split("-")
            day_input = driver.find_element(By.NAME, "d7")
            year_input = driver.find_element(By.NAME, "d3")
            month_select = Select(driver.find_element(By.NAME, "d5"))
            day_input.clear()
            day_input.send_keys(day)
            year_input.clear()
            year_input.send_keys(year)
            month_select.select_by_visible_text(month.zfill(2))

        if end:
            year, month, day = end.split("-")
            day_input = driver.find_element(By.NAME, "d8")
            year_input = driver.find_element(By.NAME, "d4")
            month_select = Select(driver.find_element(By.NAME, "d6"))
            day_input.clear()
            day_input.send_keys(day)
            year_input.clear()
            year_input.send_keys(year)
            month_select.select_by_visible_text(month.zfill(2))

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        import time

        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = uc.Chrome(options=options)

            url = f"https://stooq.com/q/d/?s={symbol}"
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "i"))
            )
            time.sleep(2)

            # Remove any overlay that blocks clicks
            overlay = driver.find_elements(By.ID, "drk_scr")
            for o in overlay:
                driver.execute_script("arguments[0].remove();", o)

            if frequency:
                self._validate_frequency(frequency)
                freq_value = self._FREQUENCY_MAP[frequency]
                radio = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, f"input[type=radio][name=i][value={freq_value}]")
                    )
                )
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(1)

            if start or end:
                self._set_date_range(driver, start, end)

            show_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "input[type=submit][value=Show]")
                )
            )
            show_btn.click()
            time.sleep(5)

            dl_link = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href^='q/d/l/']")
                )
            )
            csv_url = dl_link.get_attribute("href")
            if not csv_url:
                raise FetchError("Could not retrieve CSV download URL")
            if not csv_url.startswith("http"):
                csv_url = f"https://stooq.com/{csv_url}"

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
