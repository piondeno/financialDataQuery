import requests
import pandas as pd
from datetime import datetime
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError

_API_BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"

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

# 到期債務的 symbol
_DEBT_MATURITY_SYMBOL = "debtMaturity"

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

# 模組層快取：原始記錄，用於到期債務計算
_cached_raw_records: list | None = None

# 到期債務計算的快取
_debt_maturity_cache: dict[tuple[str, str], tuple[datetime, pd.DataFrame]] | None = None


class UsTreasuryFetcher(DataSourceFetcher):
    """美國財政部公債拍賣資料來源。"""

    source_name = "usTreasuryApi"
    _fetches_full_data = True

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        if symbol == _DEBT_MATURITY_SYMBOL:
            if not end:
                raise FetchError(
                    f"使用 '{_DEBT_MATURITY_SYMBOL}' 時，必須指定 end 參數（到期截止日期）"
                )
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d")
            except (ValueError, TypeError):
                raise FetchError(
                    f"end 參數格式錯誤，必須為 YYYY-MM-DD，收到: '{end}'"
                )
            today = datetime.now()
            if end_date <= today:
                raise FetchError(
                    f"end 必須晚於今日（{today.strftime('%Y-%m-%d')}），收到: {end}"
                )
            start_date = today if not start else datetime.strptime(start, "%Y-%m-%d")
            if end_date <= start_date:
                raise FetchError(
                    f"end 必須晚於 start（{start_date.strftime('%Y-%m-%d')}），收到: {end}"
                )
            return self._calculate_debt_maturity(start_date, end_date)

        if symbol == "allBond":
            security_term = None
        elif symbol in _SYMBOL_MAP:
            security_term = _SYMBOL_MAP[symbol]
        else:
            valid_symbols = list(_SYMBOL_MAP.keys()) + [_DEBT_MATURITY_SYMBOL] + ["allBond"]
            raise FetchError(
                f"無效的商品代號 '{symbol}'。"
                f"有效的代號為: {', '.join(valid_symbols)}"
            )

        df = self._get_full_dataframe()

        if security_term:
            df = df[df["security_term"] == security_term]

        if df.empty:
            term_desc = security_term if security_term else "所有期限"
            raise FetchError(
                f"找不到期限為「{term_desc}」的拍賣資料"
            )

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

    def _get_raw_records(self) -> list:
        """取得原始記錄（使用模組層快取）。"""
        global _cached_raw_records
        if _cached_raw_records is not None:
            return _cached_raw_records

        _cached_raw_records = self._fetch_all_pages()
        return _cached_raw_records

    def _calculate_debt_maturity(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """計算指定日期範圍內到期的債務規模，依債券類型分類。

        Args:
            start_date: 起始日期（預設今天）。
            end_date: 截止日期。

        Returns:
            DataFrame 包含各債券類型的到期債務總額。
        """
        global _debt_maturity_cache
        if _debt_maturity_cache is None:
            _debt_maturity_cache = {}

        cache_key = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if cache_key in _debt_maturity_cache:
            cache_date, cache_df = _debt_maturity_cache[cache_key]
            if (datetime.now() - cache_date).days < 1:
                return cache_df.copy()

        records = self._get_raw_records()

        maturing_records = []
        for r in records:
            mat_str = r.get("maturity_date", "")
            out_str = r.get("currently_outstanding")

            try:
                mat_date = datetime.strptime(mat_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                continue

            if not (start_date <= mat_date <= end_date):
                continue

            if not out_str or out_str == "null":
                offering_amt = r.get("offering_amt", "")
                if not offering_amt or offering_amt == "null":
                    continue
                out_str = offering_amt

            maturing_records.append(r)

        if not maturing_records:
            raise FetchError(
                f"在日期範圍「{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}」內找不到到期的債務資料"
            )

        from collections import defaultdict

        cusip_groups = defaultdict(list)
        for r in maturing_records:
            cusip_groups[r.get("cusip")].append(r)

        latest_per_cusip = []
        for cusip, rs in cusip_groups.items():
            rs.sort(key=lambda x: x.get("issue_date", ""), reverse=True)
            latest_per_cusip.append(rs[0])

        result = {
            "T_Bills": 0,
            "T_Notes": 0,
            "T_Bonds": 0,
            "TIPS": 0,
            "FRNs": 0,
        }

        for r in latest_per_cusip:
            out_str = r.get("currently_outstanding", "")
            if not out_str or out_str == "null":
                out_str = r.get("offering_amt", "0")
            out_val = float(out_str or 0)
            inflation = r.get("inflation_index_security", "No")
            floating = r.get("floating_rate", "No")
            sec_type = r.get("security_type", "")

            if inflation == "Yes":
                result["TIPS"] += out_val
            elif floating == "Yes":
                result["FRNs"] += out_val
            elif sec_type == "Bill":
                result["T_Bills"] += out_val
            elif sec_type == "Note":
                result["T_Notes"] += out_val
            elif sec_type == "Bond":
                result["T_Bonds"] += out_val

        df = pd.DataFrame([result], index=[pd.Timestamp(start_date)])
        df.attrs["start_date"] = start_date.strftime("%Y-%m-%d")
        df.attrs["end_date"] = end_date.strftime("%Y-%m-%d")

        _debt_maturity_cache[cache_key] = (datetime.now(), df)
        return df

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
