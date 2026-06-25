import io
import time

import pandas as pd
import requests
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


_ZILLow_BASE = "https://files.zillowstatic.com/research/public_csvs"

_SYMBOL_URL = {
    "ZHVI": f"{_ZILLow_BASE}/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "ZHVF": f"{_ZILLow_BASE}/zhvf_growth/Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "ZORI": f"{_ZILLow_BASE}/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
    "ZORF": f"{_ZILLow_BASE}/zorf_growth/National_zorf_growth_uc_sfr_sm_month.csv",
    "FSIT": f"{_ZILLow_BASE}/invt_fs/Metro_invt_fs_uc_sfrcondo_sm_month.csv",
    "SALCNT": f"{_ZILLow_BASE}/sales_count_now/Metro_sales_count_now_uc_sfrcondo_month.csv",
    "MRKT": f"{_ZILLow_BASE}/market_temp_index/Metro_market_temp_index_uc_sfrcondo_month.csv",
    "NCSC": f"{_ZILLow_BASE}/new_con_sales_count_raw/Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv",
    "NHIN": f"{_ZILLow_BASE}/new_homeowner_income_needed/Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
}

_REGION_FILTER = {
    "US": "United States",
    "NY": "New York, NY",
    "LA": "Los Angeles, CA",
}

_METADATA_COLS = ["RegionID", "SizeRank", "RegionName", "RegionType", "StateName", "BaseDate"]


class ZillowFetcher(DataSourceFetcher):
    source_name = "zillow"

    def _download_csv(self, url: str) -> pd.DataFrame:
        ts = int(time.time())
        resp = requests.get(url, params={"t": ts}, timeout=60)
        resp.raise_for_status()
        return pd.read_csv(io.StringIO(resp.text))

    def _region_to_col(self, name: str) -> str:
        return name.replace('"', "").replace(", ", "_").replace(" ", "")

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        sym = symbol.upper()
        if sym not in _SYMBOL_URL:
            raise FetchError(
                f"Invalid symbol '{symbol}'. "
                f"Must be one of: {', '.join(sorted(_SYMBOL_URL.keys()))}"
            )

        raw = self._download_csv(_SYMBOL_URL[sym])

        meta_cols = [c for c in _METADATA_COLS if c in raw.columns]
        date_cols = [c for c in raw.columns if c not in meta_cols]

        for col in date_cols:
            raw[col] = pd.to_numeric(raw[col], errors="coerce")

        if sub_field:
            sub_upper = sub_field.upper()
            if sub_upper in _REGION_FILTER:
                region_names = [_REGION_FILTER[sub_upper]]
            else:
                region_names = [sub_field]
        else:
            region_names = list(_REGION_FILTER.values())

        filtered = raw[raw["RegionName"].isin(region_names)].copy()

        if filtered.empty:
            raise FetchError(
                f"No data for symbol '{sym}' with region filter '{sub_field}'"
            )

        records = []
        col_names = []
        for _, row in filtered.iterrows():
            rname = row["RegionName"]
            col_label = self._region_to_col(rname)
            col_names.append(col_label)
            values = row[date_cols].values
            records.append(values)

        index = pd.to_datetime(date_cols)
        result = pd.DataFrame(dict(zip(col_names, records)), index=index)

        if start:
            result = result[result.index >= pd.Timestamp(start)]
        if end:
            result = result[result.index <= pd.Timestamp(end)]

        if result.empty:
            raise FetchError(
                f"No data for '{sym}' in the given date range ({start} to {end})"
            )

        return result
