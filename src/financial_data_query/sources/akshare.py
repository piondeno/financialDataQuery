import pandas as pd
import akshare as ak
from financial_data_query.base import DataSourceFetcher, _filter_by_date, _retry_fetch
from financial_data_query.constants import AKSHARE_DEFAULT_START, AKSHARE_DEFAULT_END
from financial_data_query.errors import FetchError


_ASHARE_COLUMN_MAP = {
    "open": "开盘",
    "high": "最高",
    "low": "最低",
    "close": "收盘",
    "volume": "成交量",
    "amount": "成交额",
    "amplitude": "振幅",
    "pct_change": "涨跌幅",
    "change": "涨跌额",
    "turnover_rate": "换手率",
}


_SPECIAL_SYMBOLS = {
    "bdi": "macro_shipping_bdi",
    "wci": "drewry_wci_index",
}

_PMI_SYMBOLS = {
    "china_manufacturing_pmi": "index_pmi_man_cx",
    "china_services_pmi": "index_pmi_ser_cx",
    "euro_manufacturing_pmi": "macro_euro_manufacturing_pmi",
    "usa_ism_pmi": "macro_usa_ism_pmi",
}


class AkShareFetcher(DataSourceFetcher):
    source_name = "akshare"

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        if symbol.lower() in _SPECIAL_SYMBOLS:
            return self._fetch_special(
                ak_func_name=_SPECIAL_SYMBOLS[symbol.lower()],
                start=start, end=end, sub_field=sub_field, frequency=frequency,
            )

        if symbol.lower() in _PMI_SYMBOLS:
            func_name = _PMI_SYMBOLS[symbol.lower()]
            ak_func = getattr(ak, func_name)
            df = _retry_fetch(lambda: ak_func(), max_retries=3)
            return self._process_pmi_df(df, symbol, sub_field=sub_field, start=start, end=end, frequency=frequency)

        start_date = self._normalize_date(start) if start else AKSHARE_DEFAULT_START
        end_date = self._normalize_date(end) if end else AKSHARE_DEFAULT_END
        period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
        period = period_map.get(frequency, "daily") if frequency else "daily"

        df = _retry_fetch(
            lambda: ak.stock_zh_a_hist(
                symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust=""
            ),
            max_retries=3,
        )

        if df is None or df.empty:
            raise FetchError(f"No data returned for AKShare symbol '{symbol}'")

        df["日期"] = pd.to_datetime(df["日期"])
        df.set_index("日期", inplace=True)
        df.sort_index(inplace=True)

        if sub_field:
            cn_col = _ASHARE_COLUMN_MAP.get(sub_field.lower(), sub_field.title())
            if cn_col not in df.columns:
                raise FetchError(
                    f"Invalid sub_field '{sub_field}' for akshare. "
                    f"Available fields: {', '.join(sorted(_ASHARE_COLUMN_MAP.keys()))}"
                )
            df = df[[cn_col]]

        return df

    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.fetch(
                    symbol, start=start, end=end, sub_field=sub_field, frequency=frequency
                )
            except FetchError:
                pass
        return results

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        try:
            ts = pd.Timestamp(date_str)
            return ts.strftime("%Y%m%d")
        except Exception:
            return date_str

    def _fetch_special(
        self,
        ak_func_name: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        """Fetch special symbols (BDI, WCI) from akshare."""
        ak_func = getattr(ak, ak_func_name)
        df = _retry_fetch(lambda: ak_func(), max_retries=3)

        if df is None or df.empty:
            raise FetchError(f"No data returned for {ak_func_name}")

        # Normalize date column
        date_col = [c for c in df.columns if '日期' in str(c) or 'date' in str(c).lower()]
        if not date_col:
            raise FetchError(f"No date column found for {ak_func_name}. Columns: {list(df.columns)}")

        df[date_col[0]] = pd.to_datetime(df[date_col[0]], errors="coerce")
        df.dropna(subset=[date_col[0]], inplace=True)
        df.set_index(date_col[0], inplace=True)
        df.sort_index(inplace=True)

        # Rename value column to 'value' if single data column exists
        value_cols = [c for c in df.columns if c != date_col[0] and not str(c).lower().startswith('date')]
        if len(value_cols) == 1:
            rename_map = {value_cols[0]: "value"}
            df.rename(columns=rename_map, inplace=True)

        # Apply date filtering
        if start or end:
            df = _filter_by_date(df, start, end)

        # Handle weekly/monthly frequency for BDI (WCI is already weekly)
        if frequency and frequency.lower() in ("monthly",) and ak_func_name == "macro_shipping_bdi":
            value_col = "value"
            pct_cols = [c for c in df.columns if "涨跌幅" in str(c)]
            agg_dict = {value_col: "mean"}
            for col in pct_cols:
                agg_dict[col] = lambda x: x.iloc[-1] if len(x) else None
            df = df.resample("ME").agg(agg_dict).dropna()
            df.index.name = date_col[0]

        return df

    def _process_pmi_df(self, df: pd.DataFrame, symbol_key: str,
                        sub_field: str | None = None, start: str | None = None,
                        end: str | None = None, frequency: str | None = None) -> pd.DataFrame:
        """Process and normalize PMI DataFrame from akshare."""
        if df is None or df.empty:
            raise FetchError(f"No PMI data returned for '{symbol_key}'")

        # Apply date filtering
        if start or end:
            df = _filter_by_date(df, start, end)

        # Normalize column names to English equivalents
        col_rename = {}
        for col in df.columns:
            col_str = str(col).strip().lower()
            if "日期" in col_str:
                col_rename[col] = "date"
            elif any(kw in col_str for kw in ["pct", "change", "变化值", "涨跌幅"]):
                col_rename[col] = "change_pct"
            else:
                # Keep original column name but lowercase
                normalized = col.strip().lower()
                if normalized not in ["date", "change_pct"]:
                    col_rename[col] = normalized

        df.rename(columns=col_rename, inplace=True)

        # Set date index
        if "date" not in df.columns:
            available_cols = list(df.columns)
            raise FetchError(f"No date column found for PMI data ({symbol_key}). Available columns: {available_cols}")

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

        # Filter by sub_field if specified
        available_cols = [c for c in df.columns]
        if sub_field and sub_field not in available_cols:
            raise FetchError(
                f"Invalid sub_field '{sub_field}' for {symbol_key}. "
                f"Available fields: {', '.join(sorted(available_cols))}"
            )

        return df
