# 美國財政部公債拍賣 (`"usTreasuryApi"`)

US Treasury Fiscal Data API 公債拍賣數據。免 API key，免瀏覽器。

資料來源: https://api.fiscaldata.treasury.gov
資料範圍: 1970 年至今，每週更新（拍賣日）


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
| `debtMaturity` | 到期債務分析 | 配合 `start`（預設今天）和 `end`（必填）指定到期日期範圍 |

## 到期分析回傳欄位

| 欄位 | 說明 |
|------|------|
| `T_Bills` | T-Bills（國庫券）到期金額 |
| `T_Notes` | T-Notes（中期國庫券）到期金額 |
| `T_Bonds` | T-Bonds（長期國庫債券）到期金額 |
| `TIPS` | TIPS（通膨指數化債券）到期金額 |
| `FRNs` | FRNs（浮動利率債券）到期金額 |

金額單位：美元。回傳為單行 DataFrame。

## 回傳欄位

| 欄位 | 說明 |
|------|------|
| `issue_date` | 拍賣日 |
| `security_term` | 債券期限（例：10-Year, 13-Week） |
| `maturity_date` | 到期日 |
| `int_rate` | 票面利率（%） |
| `avg_med_yield` | 平均/中位收益率（%） |
| `high_yield` | 最高收益率（%） |
| `low_yield` | 最低收益率（%） |
| `offering_amount` | 發行金額（美元） |
| `total_accepted` | 總中标金額（美元） |
| `total_tendered` | 總投標金額（美元） |
| `bid_to_cover_ratio` | 投標覆蓋率 |
| `auction_format` | 拍賣方式（Multi-Price / Price-Based） |

### 一級交易商

| 欄位 | 說明 |
|------|------|
| `primary_dealer_tendered` | 一級交易商投標金額（美元） |
| `primary_dealer_accepted` | 一級交易商中标金額（美元） |

### 競爭 / 非競爭投標

| 欄位 | 說明 |
|------|------|
| `comp_accepted` | 競爭投標中标金額（美元） |
| `comp_tendered` | 競爭投標金額（美元） |
| `noncomp_accepted` | 非競爭投標中标金額（美元） |

### 直接 / 間接投標人

| 欄位 | 說明 |
|------|------|
| `direct_bidder_tendered` | 直接投標人投標金額（美元） |
| `direct_bidder_accepted` | 直接投標人中标金額（美元） |
| `indirect_bidder_tendered` | 間接投標人投標金額（美元） |
| `indirect_bidder_accepted` | 間接投標人中标金額（美元） |

### SOMA（System Open Market Account）

| 欄位 | 說明 |
|------|------|
| `soma_tendered` | SOMA 投標金額（美元） |
| `soma_accepted` | SOMA 中标金額（美元） |

### FIMA（Foreign Official Sectors）

| 欄位 | 說明 |
|------|------|
| `fima_noncomp_tendered` | FIMA 非競爭投標金額（美元） |
| `fima_noncomp_accepted` | FIMA 非競爭中标金額（美元） |

### 國庫零售

| 欄位 | 說明 |
|------|------|
| `treas_retail_tenders_accepted` | 國庫零售投标中标金額（美元） |
| `treas_retail_accepted` | 國庫零售中标金額（美元） |

### 投標筆數

| 欄位 | 說明 |
|------|------|
| `comp_tenders_accepted` | 競爭投標中标筆數 |
| `noncomp_tenders_accepted` | 非競爭投標中标筆數 |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期 `YYYY-MM-DD`（按拍賣日篩選） |
| `sub_field` | 指定上述任一欄位名稱 |
| `end` | 僅 `debtMaturity` 使用，到期截止日期（必填） |

## 使用範例

```python
from financial_data_query import query

# 查詢 10 年期公債
result = query("usTreasuryApi", "note_10y")

# 指定日期範圍
result = query("usTreasuryApi", "note_10y", start="2024-01-01", end="2024-12-31")

# 查詢所有期限的拍賣資料
result = query("usTreasuryApi", "allBond", start="2024-01-01", end="2024-12-31")

# 查詢 24 個月內到期的債務
result = query("usTreasuryApi", "debtMaturity", end="2026-12-31")

# 批量查詢多個期限
result = query("usTreasuryApi", ["note_2y", "note_10y", "bond_30y"])

# 只回傳收益率欄位
result = query("usTreasuryApi", "note_10y", sub_field="avg_med_yield")
```

## 注意事項

- 首次查詢會下載全部歷史資料並儲存至磁碟快取
- 後續查詢從磁碟快取讀取，速度很快
- `allBond` 回傳所有期限的拍賣記錄
- 金額欄位單位為美元
