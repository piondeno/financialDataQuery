import requests
import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


_API_BASE_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
    "accounting/od/auctions_query"
)

# 商品代號對應至 security_term 的值
_SYMBOL_MAP = {
    "bill_4w": "4-Week",
    "bill_8w": "8-Week",
    "bill_13w": "13-Week",
    "bill_26w": "26-Week",
    "bill_52w": "52-Week",
    "note_2y": "2-Year",
    "note_3y": "3-Year",
    "note_5y": "5-Year",
    "note_7y": "7-Year",
    "note_10y": "10-Year",
    "bond_30y": "30-Year",
}

# API 欄位名稱 → 輸出欄位名稱的映射
_COLUMN_RENAME_MAP = {
    "offering_amt": "offering_amount",
}

# 回傳的欄位清單（使用 API 的原始欄位名稱）
_API_COLUMNS = [
    "issue_date",
    "security_term",
    "maturity_date",
    "int_rate",
    "avg_med_yield",
    "high_yield",
    "low_yield",
    "offering_amt",
    "total_accepted",
    "bid_to_cover_ratio",
    "auction_format",
]

# 每頁最大筆數
_PAGE_SIZE = 10000

# 模組層快取：解析後的 DataFrame，避免每次都重新下載
_cached_df: pd.DataFrame | None = None


class UsTreasuryFetcher(DataSourceFetcher):
    """美國財政部公債拍賣資料來源。"""

    source_name = "usTreasuryApi"

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        # 特殊處理：allBond 回傳所有債券
        if symbol == "allBond":
            security_term = None
        elif symbol in _SYMBOL_MAP:
            security_term = _SYMBOL_MAP[symbol]
        else:
            valid_symbols = list(_SYMBOL_MAP.keys()) + ["allBond"]
            raise FetchError(
                f"無效的商品代號 '{symbol}'。"
                f"有效的代號為: {', '.join(valid_symbols)}"
            )

        df = self._get_full_dataframe()

        # 客戶端過濾：依債券期限篩選
        if security_term:
            df = df[df["security_term"] == security_term]

        # 客戶端過濾：依日期範圍篩選
        if start:
            df = df[df.index >= pd.Timestamp(start)]
        if end:
            df = df[df.index <= pd.Timestamp(end)]

        if df.empty:
            term_desc = security_term if security_term else "所有期限"
            date_desc = f"{start} ~ {end}" if start and end else "全部"
            raise FetchError(
                f"在日期範圍「{date_desc}」內找不到期限為「{term_desc}」的拍賣資料"
            )

        if sub_field and sub_field in df.columns:
            df = df[[sub_field]]

        return df

    def _get_full_dataframe(self) -> pd.DataFrame:
        """取得完整的 DataFrame（使用模組層快取）。"""
        global _cached_df
        if _cached_df is not None:
            return _cached_df

        all_records = self._fetch_all_pages()
        _cached_df = self._parse_records(all_records)
        return _cached_df

    def _fetch_all_pages(self):
        """從 API 撷取所有頁面的資料。"""
        all_records = []
        page_number = 1

        while True:
            params = {"page[number]": page_number, "page[size]": _PAGE_SIZE}

            resp = requests.get(_API_BASE_URL, params=params, timeout=60)

            if resp.status_code != 200:
                raise FetchError(
                    f"財政部 API 錯誤 ({resp.status_code}): {resp.text[:200]}"
                )

            data = resp.json()
            records = data.get("data", [])

            if not records:
                break

            all_records.extend(records)

            # 如果回傳筆數少於 page[size]，表示已讀取完畢
            if len(records) < _PAGE_SIZE:
                break

            page_number += 1

        return all_records

    @staticmethod
    def _parse_records(records):
        """將 API 回傳的記錄解析為 DataFrame。"""
        df = pd.DataFrame(records)

        # API 會忽略 $select，回傳所有欄位；手動過濾為需要的欄位
        existing_cols = [c for c in _API_COLUMNS if c in df.columns]
        df = df[existing_cols]

        # 重新命名欄位（例如 offering_amt → offering_amount）
        df.rename(columns=_COLUMN_RENAME_MAP, inplace=True)

        # API 使用 "null" 字串表示空值，轉換為 NaN
        df.replace("null", pd.NA, inplace=True)

        # 轉換日期欄位
        df["issue_date"] = pd.to_datetime(df["issue_date"])
        df["maturity_date"] = pd.to_datetime(df["maturity_date"])
        df.set_index("issue_date", inplace=True)

        # 轉換數值欄位
        numeric_cols = [
            "int_rate",
            "avg_med_yield",
            "high_yield",
            "low_yield",
            "offering_amount",
            "total_accepted",
            "bid_to_cover_ratio",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df
