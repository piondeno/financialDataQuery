import json
import os
import time
from pathlib import Path

import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError
from financial_data_query.browser_utils import (
    _create_uc_driver,
    _make_chrome_options,
    _check_uc_installed,
)
from financial_data_query.constants import EPOCH

LINKS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".macroMicro_links.json")
README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "README.md")
MACROMICRO_START_MARKER = "<!-- MACROMICRO_SYMBOLS_START -->"
MACROMICRO_END_MARKER = "<!-- MACROMICRO_SYMBOLS_END -->"


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


def _symbol_from_url(url: str) -> str:
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else ""


def _parse_title(title: str) -> str:
    for sep in [" - MacroMicro", " | MacroMicro"]:
        idx = title.find(sep)
        if idx >= 0:
            return title[:idx].strip()
    return title.strip()


def macroMicroSymbolLinkConnect(url: str) -> None:
    _check_uc_installed("macroMicro")

    symbol = _symbol_from_url(url)
    if not symbol:
        raise FetchError(f"無法從 URL 提取商品代號: {url}")

    driver = None
    try:
        driver = _create_uc_driver(_make_chrome_options())
        driver.get(url)
        time.sleep(3)
        page_title = driver.title
        description = _parse_title(page_title) if page_title else ""
    except FetchError:
        raise
    except Exception as e:
        raise FetchError(f"無法存取 MacroMicro 頁面: {url}: {e}") from e
    finally:
        if driver:
            driver.quit()

    links = _load_links()
    links[symbol] = {"url": url, "description": description}
    _save_links(links)
    _update_readme_symbols(links)


class MacroMicroFetcher(DataSourceFetcher):
    """MacroMicro economic data via browser automation.

    Before querying, symbols must be registered with macroMicroSymbolLinkConnect()
    to establish a URL mapping. Data is extracted from Highcharts charts on each
    page by reading the JavaScript chart data directly (no DOM parsing needed).

    The links file (.macroMicro_links.json) stores symbol -> URL mappings and
    is automatically synced to README.md via marker-based section replacement.
    """

    source_name = "macroMicro"
    # Full data caching: Highcharts charts contain ALL historical data; no date filtering on fetch.
    # _fetches_full_data = True: disk cache stores the complete data per symbol;
    # query layer filters by start/end on each read.
    _fetches_full_data = True

    def _extract_highcharts_data(self, driver):
        """Extract data points from Highcharts chart on the page."""
        return driver.execute_script(
            "return Highcharts.charts[0].series[0].data.map(function(point) {"
            "  return {x: point.x, y: point.y};"
            "});"
        )

    def _create_driver(self):
        return _create_uc_driver(_make_chrome_options())

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        _check_uc_installed("macroMicro")

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
            data_points = self._extract_highcharts_data(driver)
            if not data_points:
                raise FetchError("頁面中找不到 Highcharts 圖表資料")

            rows = []
            for point in data_points:
                dt = EPOCH + pd.Timedelta(milliseconds=point["x"])
                dt_twt = dt.tz_convert("Asia/Taipei").tz_localize(None)
                rows.append((dt_twt, point["y"]))

            df = pd.DataFrame(rows, columns=["date", "value"])
            df.set_index("date", inplace=True)

            return df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"無法存取 MacroMicro 頁面: {url}: {e}") from e
        finally:
            driver.quit()

    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        _check_uc_installed("macroMicro")

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
                data_points = self._extract_highcharts_data(driver)
                if not data_points:
                    raise FetchError(f"頁面中找不到 Highcharts 圖表資料: {url}")

                rows = []
                for point in data_points:
                    dt = EPOCH + pd.Timedelta(milliseconds=point["x"])
                    dt_twt = dt.tz_convert("Asia/Taipei").tz_localize(None)
                    rows.append((dt_twt, point["y"]))

                df = pd.DataFrame(rows, columns=["date", "value"])
                df.set_index("date", inplace=True)

                results[symbol] = df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"MacroMicro batch fetch failed: {e}") from e
        finally:
            driver.quit()
        return results
