import json
import os
from pathlib import Path

import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError

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


def macroMicroSymbolLinkConnect(symbol: str, url: str, description: str) -> None:
    links = _load_links()
    links[symbol] = {"url": url, "description": description}
    _save_links(links)
    _update_readme_symbols(links)


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
