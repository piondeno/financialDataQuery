# ICI Fund Flows (`"ici"`)

Investment Company Institute 基金資金流量數據。直接下載 XLS 檔案解析，免 API key。

資料範圍: 2024-01 至今，每週更新

## 安裝

```bash
pip install -e ".[ici]"
```

## Symbols

### 共同基金 (Mutual Fund)

| Symbol | 說明 |
|--------|------|
| `mf_total` | 共同基金總淨現金流 |
| `mf_equity_total` | 股票型基金合計 |
| `mf_equity_domestic_total` | 國內股票型基金合計 |
| `mf_equity_domestic_large` | 國內大型股 |
| `mf_equity_domestic_mid` | 國內中型股 |
| `mf_equity_domestic_small` | 國內小型股 |
| `mf_equity_domestic_multi` | 國內多類股 |
| `mf_equity_world_total` | 全球股票型基金合計 |
| `mf_equity_world_developed` | 已開發市場 |
| `mf_equity_world_emerging` | 新興市場 |
| `mf_hybrid` | 混合型基金 |
| `mf_bond_total` | 債券型基金合計 |
| `mf_bond_taxable_total` | 課稅債券合計 |
| `mf_bond_taxable_investment` | 投資等級 |
| `mf_bond_taxable_highyield` | 高收益 |
| `mf_bond_municipal` | 地方政府債券 |

### ETF

| Symbol | 說明 |
|--------|------|
| `etf_total` | ETF 總淨發行量 |
| `etf_equity_total` | 股票型 ETF 合計 |
| `etf_equity_domestic` | 國內股票型 ETF |
| `etf_equity_world` | 全球股票型 ETF |
| `etf_hybrid` | 混合型 ETF |
| `etf_bond_total` | 債券型 ETF 合計 |
| `etf_commodity` | 商品型 ETF |

### 合併 (Combined MF + ETF)

| Symbol | 說明 |
|--------|------|
| `combined_total` | 總長期基金+ETF 資金流量 |
| `combined_equity_total` | 股票型基金+ETF 合計 |
| `combined_equity_domestic` | 國內股票型基金+ETF |
| `combined_equity_world` | 全球股票型基金+ETF |
| `combined_bond_total` | 債券型基金+ETF 合計 |
| `combined_commodity` | 商品型基金+ETF |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期 `YYYY-MM-DD`（每週數據） |

`sub_field` 和 `frequency` 不適用。

## 使用範例

```python
from financial_data_query import query

# 查詢共同基金總淨現金流
result = query("ici", "mf_total")

# 查詢 ETF 總淨發行量
result = query("ici", "etf_total")

# 指定日期範圍
result = query("ici", "mf_equity_total", start="2024-01-01", end="2024-06-30")

# 批量查詢
result = query("ici", ["mf_total", "etf_total", "combined_total"])
```

## 回傳欄位

`date`（週）, `value`（單位：百萬美元）
