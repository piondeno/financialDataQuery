# 美國財政部公債拍賣 (`"usTreasuryApi"`)

US Treasury Fiscal Data API 公債拍賣數據。免 API key，免瀏覽器。

資料來源: https://api.fiscaldata.treasury.gov
資料範圍: 1970 年至今，每週更新（拍賣日）

## 安裝

基本安裝已包含，無需額外依賴。

## Symbols

| Symbol | 債券期限 | 類型 |
|--------|----------|------|
| `bill_4w` | 4 週 | T-Bill |
| `bill_8w` | 8 週 | T-Bill |
| `bill_13w` | 13 週 | T-Bill |
| `bill_26w` | 26 週 | T-Bill |
| `bill_52w` | 52 週 | T-Bill |
| `note_2y` | 2 年 | T-Note |
| `note_3y` | 3 年 | T-Note |
| `note_5y` | 5 年 | T-Note |
| `note_7y` | 7 年 | T-Note |
| `note_10y` | 10 年 | T-Note |
| `bond_30y` | 30 年 | T-Bond |
| `allBond` | 所有期限 | 回傳日期範圍內的所有拍賣資料 |

## 回傳欄位

| 欄位 | 說明 |
|------|------|
| `security_term` | 債券期限（例：10-Year, 13-Week） |
| `maturity_date` | 到期日 |
| `int_rate` | 票面利率（%） |
| `avg_med_yield` | 平均/中位收益率（%） |
| `high_yield` | 最高收益率（%） |
| `low_yield` | 最低收益率（%） |
| `offering_amount` | 發行金額（美元） |
| `total_accepted` | 總中标金額（美元） |
| `bid_to_cover_ratio` | 投標覆蓋率 |
| `auction_format` | 拍賣方式（Multi-Price / Price-Based） |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期 `YYYY-MM-DD`（按拍賣日篩選） |
| `sub_field` | 指定上述任一欄位名稱 |

`frequency` 不適用。

## 使用範例

```python
from financial_data_query import query

# 查詢 10 年期公債
result = query("usTreasuryApi", "note_10y")

# 指定日期範圍
result = query("usTreasuryApi", "note_10y", start="2024-01-01", end="2024-12-31")

# 查詢所有期限的拍賣資料
result = query("usTreasuryApi", "allBond", start="2024-01-01", end="2024-12-31")

# 批量查詢多個期限
result = query("usTreasuryApi", ["note_2y", "note_10y", "bond_30y"])

# 只回傳收益率欄位
result = query("usTreasuryApi", "note_10y", sub_field="avg_med_yield")
```

## 注意事項

- 首次查詢會下載全部歷史資料並快取在記憶體中
- 後續查詢使用快取，速度很快
- `allBond` 回傳所有期限的拍賣記錄
