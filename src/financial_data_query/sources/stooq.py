import pandas as pd
import io
import time
import os
import glob
import re
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError
from financial_data_query.browser_utils import _create_uc_driver, _make_chrome_options

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

# Yahoo interval -> Stooq value mapping (keys overlap with Yahoo intervals)
_FREQUENCY_TO_VALUE = {
    "1d": "d",
    "1wk": "w",
    "1mo": "m",
    "3mo": "q",
    "1y": "y",
}

_MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


class StooqFetcher(DataSourceFetcher):
    """Stooq market data via browser automation.

    Downloads CSV files by:
    1. Navigating to the symbol page
    2. Setting frequency, date range, clicking Show
    3. Clicking the CSV download link
    4. Reading the downloaded CSV file

    Includes CAPTCHA handling: detects CAPTCHA, uses GPT-Vision to solve it,
    and retries up to 5 times. batch_fetch reuses the same browser session
    for all symbols (one browser open, multiple downloads).
    """

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

    def _has_captcha(self, driver) -> bool:
        try:
            return driver.find_element(By.CSS_SELECTOR, "#cpt_cd img").is_displayed()
        except Exception:
            return False

    def _ocr_captcha(self, image_path: str) -> str:
        import base64
        from openai import OpenAI

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        client = OpenAI(
            base_url="http://localhost:12345/v1",
            api_key="not-needed",
        )

        response = client.chat.completions.create(
            model="qwen3.5-9b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a CAPTCHA recognition assistant. Only output the letters and numbers you see, nothing else."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "識別圖片中的驗證碼，只返回大寫字母和數字，不要返回任何其他內容。"
                        }
                    ]
                }
            ],
            max_tokens=512,
            temperature=0.1,
        )

        text = response.choices[0].message.content.strip()
        text = re.sub(r"[^A-Z0-9]", "", text)
        return text.upper()

    def _solve_captcha(self, driver, max_attempts: int = 5) -> bool:
        for attempt in range(max_attempts):
            try:
                captcha_img = driver.find_element(By.CSS_SELECTOR, "#cpt_cd img")
                captcha_img.screenshot(os.path.join(os.path.dirname(__file__), ".captcha_tmp.png"))

                text = self._ocr_captcha(os.path.join(os.path.dirname(__file__), ".captcha_tmp.png"))
                try:
                    os.remove(os.path.join(os.path.dirname(__file__), ".captcha_tmp.png"))
                except OSError:
                    pass

                if not text or len(text) < 3:
                    print(f"[Stooq] OCR attempt {attempt + 1}: '{text}' (too short, retrying)")
                    continue

                print(f"[Stooq] CAPTCHA solved: '{text}'")

                input_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr/td[1]/table/tbody/tr/td/table[5]/tbody/tr/td/table/tbody/tr/td[3]/div[1]/div[1]/table/tbody/tr/td/table/tbody/tr[5]/td/input"))
                )
                input_field.clear()
                input_field.send_keys(text)
                time.sleep(1)

                approve_btn = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=submit][value=Approve]"))
                )
                driver.execute_script("arguments[0].click();", approve_btn)
                time.sleep(3)

                # Click refresh link if it appears after Approve
                try:
                    refresh_link = driver.find_element(By.ID, "cpt_gh")
                    if refresh_link.is_displayed():
                        print(f"[Stooq] Clicking CAPTCHA refresh link")
                        driver.execute_script("arguments[0].click();", refresh_link)
                        time.sleep(3)
                except Exception:
                    pass

                if not self._has_captcha(driver):
                    return True
                print(f"[Stooq] CAPTCHA attempt {attempt + 1} failed, retrying...")
            except Exception as e:
                print(f"[Stooq] CAPTCHA error: {e}")
                time.sleep(1)

        raise FetchError("Failed to solve CAPTCHA after multiple attempts")

    def _set_input_value(self, driver, name, value):
        """Set input value using JavaScript to avoid residual characters."""
        driver.execute_script(
            f"document.querySelector('input[name=\"{name}\"]').value = '{value}';"
        )

    def _set_date_range(
        self,
        driver,
        start: str | None,
        end: str | None,
    ) -> None:
        if start:
            year, month, day = start.split("-")
            self._set_input_value(driver, "d7", day.zfill(2))
            self._set_input_value(driver, "d3", year)
            month_select = Select(driver.find_element(By.NAME, "d5"))
            month_select.select_by_visible_text(_MONTH_MAP[month.zfill(2)])

        if end:
            year, month, day = end.split("-")
            self._set_input_value(driver, "d8", day.zfill(2))
            self._set_input_value(driver, "d4", year)
            month_select = Select(driver.find_element(By.NAME, "d6"))
            month_select.select_by_visible_text(_MONTH_MAP[month.zfill(2)])

    def _remove_overlay(self, driver):
        overlays = driver.find_elements(By.ID, "drk_scr")
        for o in overlays:
            driver.execute_script("arguments[0].remove();", o)

    def _wait_no_captcha(self, driver, timeout=30):
        """Wait until CAPTCHA is no longer present."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self._has_captcha(driver):
                return True
            self._solve_captcha(driver)
        return False

    def _create_driver(self):
        """Create a new Chrome driver instance."""
        download_dir = os.path.join(os.path.dirname(__file__), ".downloads")
        os.makedirs(download_dir, exist_ok=True)

        options = _make_chrome_options()
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)
        return _create_uc_driver(options)

    def _fetch_with_driver(
        self,
        driver,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        """Fetch data for a single symbol using an existing browser driver."""
        download_dir = os.path.join(os.path.dirname(__file__), ".downloads")

        url = f"https://stooq.com/q/d/?s={symbol}"
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "i"))
        )
        time.sleep(2)

        if self._has_captcha(driver):
            self._solve_captcha(driver)

        self._remove_overlay(driver)

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

        csv_link_found = False
        for attempt in range(5):
            show_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[type=submit][value=Show]")
                )
            )
            driver.execute_script("arguments[0].click();", show_btn)
            time.sleep(3)

            if "Download data in csv" in driver.page_source:
                csv_link_found = True
                break

            time.sleep(3)

        if not csv_link_found:
            raise FetchError("CSV download link not found after multiple attempts")

        dl_link = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a[href^='q/d/l/']")
            )
        )
        driver.execute_script("arguments[0].click();", dl_link)

        time.sleep(5)
        csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
        if not csv_files:
            for _ in range(12):
                time.sleep(2)
                csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
                if csv_files:
                    break

        if not csv_files:
            raise FetchError("CSV file was not downloaded")

        csv_file = max(csv_files, key=os.path.getctime)

        with open(csv_file, "r", encoding="utf-8") as f:
            csv_content = f.read()

        df = self._parse_csv(csv_content)

        if sub_field and sub_field in df.columns:
            df = df[[sub_field]]

        return df

    def _cleanup(self):
        """Clean up temporary files."""
        download_dir = os.path.join(os.path.dirname(__file__), ".downloads")
        csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
        for f in csv_files:
            try:
                os.remove(f)
            except OSError:
                pass
        tmp = os.path.join(os.path.dirname(__file__), ".captcha_tmp.png")
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

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
            driver = self._create_driver()
            return self._fetch_with_driver(
                driver, symbol, start=start, end=end,
                sub_field=sub_field, frequency=frequency
            )
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"Stooq fetch failed: {e}") from e
        finally:
            if driver is not None:
                driver.quit()
            self._cleanup()

    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        driver = None
        try:
            driver = self._create_driver()
            results = {}
            for symbol in symbols:
                results[symbol] = self._fetch_with_driver(
                    driver, symbol, start=start, end=end,
                    sub_field=sub_field, frequency=frequency
                )
            return results
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"Stooq batch fetch failed: {e}") from e
        finally:
            if driver is not None:
                driver.quit()
            self._cleanup()
