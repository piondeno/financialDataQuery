# FINRA Margin Statistics (`"finra_margin"`)

FINRA 客戶融資帳戶統計數據。直接下載 Excel 檔案解析，免 API key。

資料來源: https://www.finra.org/margin-statistics
資料範圍: 1997-01 至今，每月更新

## 安裝

```bash
pip install -e ".[finra_margin]"
```

## Symbols

| Symbol | 說明 |
|--------|------|
| `debit_balances` | 客戶信貸 (Debit Balances in Customers' Securities Margin Accounts) |
| `free_credit_cash` | 現金賬戶 (Free Credit Balances in Customers' Cash Accounts) |
| `free_credit_margin` | 融資賬戶 (Free Credit Balances in Customers' Securities Margin Accounts) |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期格式 `YYYY-MM` 或 `YYYY-MM-DD` |

`sub_field` 和 `frequency` 不適用。

## 使用範例

```python
from financial_data_query import query

# 查詢客戶信貸
result = query("finra_margin", "debit_balances")

# 指定日期範圍
result = query("finra_margin", "free_credit_cash", start="2024-01", end="2024-06")

# 批量查詢多個指標
result = query("finra_margin", ["debit_balances", "free_credit_margin"])

# 回傳 DataFrame
df = query("finra_margin", "debit_balances", output="dataframe")
```

## 回傳欄位

`date`（月終）, `value`
