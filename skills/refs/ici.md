# ICI Fund Flows (`"ici"`)

Investment Company Institute 基金資金流量數據。直接下載 XLS 檔案解析，免 API key。

資料範圍: 2024-01 至今，每週更新（MF/ETF/Combined）；2013-01 至今，每月更新（MMF）

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
| `mf_equity_domestic_other` | 國內其他 |
| `mf_equity_world_total` | 全球股票型基金合計 |
| `mf_equity_world_developed` | 已開發市場 |
| `mf_equity_world_emerging` | 新興市場 |
| `mf_hybrid` | 混合型基金 |
| `mf_bond_total` | 債券型基金合計 |
| `mf_bond_taxable_total` | 課稅債券合計 |
| `mf_bond_taxable_investment` | 投資等級 |
| `mf_bond_taxable_highyield` | 高收益 |
| `mf_bond_municipal` | 地方政府債券 |
| `mf_bond_taxable_government` | 政府債券 |
| `mf_bond_taxable_multisector` | 多部門 |
| `mf_bond_taxable_global` | 全球債券 |

### ETF

| Symbol | 說明 |
|--------|------|
| `etf_total` | ETF 總淨發行量 |
| `etf_equity_total` | 股票型 ETF 合計 |
| `etf_equity_domestic` | 國內股票型 ETF |
| `etf_equity_world` | 全球股票型 ETF |
| `etf_hybrid` | 混合型 ETF |
| `etf_bond_total` | 債券型 ETF 合計 |
| `etf_bond_taxable` | 課稅債券型 ETF |
| `etf_bond_municipal` | 地方政府債券型 ETF |
| `etf_commodity` | 商品型 ETF |

### 合併 (Combined MF + ETF)

| Symbol | 說明 |
|--------|------|
| `combined_total` | 總長期基金+ETF 資金流量 |
| `combined_equity_total` | 股票型基金+ETF 合計 |
| `combined_equity_domestic` | 國內股票型基金+ETF |
| `combined_equity_world` | 全球股票型基金+ETF |
| `combined_hybrid` | 混合型基金+ETF |
| `combined_bond_total` | 債券型基金+ETF 合計 |
| `combined_bond_taxable` | 課稅債券型基金+ETF |
| `combined_bond_municipal` | 地方政府債券型基金+ETF |
| `combined_commodity` | 商品型基金+ETF |

### 貨幣市場基金 (MMF - Government Funds)

| Symbol | 說明 |
|--------|------|
| `mmf_gov_total` | 總投資組合證券 |
| `mmf_gov_treasury` | 美國公債 |
| `mmf_gov_agency` | 政府機構債務 |
| `mmf_gov_repo_total` | 回購協議合計 |
| `mmf_gov_repo_agency` | 政府機構回購 |
| `mmf_gov_repo_treasury` | 公債回購 |
| `mmf_gov_repo_other` | 其他回購 |
| `mmf_gov_cdp` | 存單 |
| `mmf_gov_ntd` | 不可議轉定期存款（2016-04 起） |
| `mmf_gov_cp_total` | 商業本票合計 |
| `mmf_gov_cp_assetbacked` | 資產支持本票 |
| `mmf_gov_cp_financial` | 金融公司本票 |
| `mmf_gov_cp_nonfinancial` | 非金融公司本票 |
| `mmf_gov_otherabs` | 其他資產支持證券（2016-04 起） |
| `mmf_gov_muni_total` | 市政債務合計 |
| `mmf_gov_muni_vrdn` | 浮動利率需求票據 |
| `mmf_gov_muni_other` | 其他市政證券 |
| `mmf_gov_tob` | 認購選擇權債券（2016-04 起） |
| `mmf_gov_other_instrument` | 其他工具 |
| `mmf_gov_icfa` | 保險公司資金協議 |
| `mmf_gov_inv_company` | 投資公司 |
| `mmf_gov_nonus_sov` | 非美國主權債務（2016-04 起） |
| `mmf_gov_other_note` | 其他票據（僅至 2016-03） |
| `mmf_gov_wam` | 加權平均到期日 |
| `mmf_gov_wal` | 加權平均存續期 |

### 貨幣市場基金 (MMF - Prime Funds)

| Symbol | 說明 |
|--------|------|
| `mmf_prime_total` | 總投資組合證券 |
| `mmf_prime_treasury` | 美國公債 |
| `mmf_prime_agency` | 政府機構債務 |
| `mmf_prime_repo_total` | 回購協議合計 |
| `mmf_prime_repo_agency` | 政府機構回購 |
| `mmf_prime_repo_treasury` | 公債回購 |
| `mmf_prime_repo_other` | 其他回購 |
| `mmf_prime_cdp` | 存單 |
| `mmf_prime_ntd` | 不可議轉定期存款（2016-04 起） |
| `mmf_prime_cp_total` | 商業本票合計 |
| `mmf_prime_cp_assetbacked` | 資產支持本票 |
| `mmf_prime_cp_financial` | 金融公司本票 |
| `mmf_prime_cp_nonfinancial` | 非金融公司本票 |
| `mmf_prime_otherabs` | 其他資產支持證券（2016-04 起） |
| `mmf_prime_muni_total` | 市政債務合計 |
| `mmf_prime_muni_vrdn` | 浮動利率需求票據 |
| `mmf_prime_muni_other` | 其他市政證券 |
| `mmf_prime_tob` | 認購選擇權債券（2016-04 起） |
| `mmf_prime_other_instrument` | 其他工具 |
| `mmf_prime_icfa` | 保險公司資金協議 |
| `mmf_prime_inv_company` | 投資公司 |
| `mmf_prime_nonus_sov` | 非美國主權債務（2016-04 起） |
| `mmf_prime_other_note` | 其他票據（僅至 2016-03） |
| `mmf_prime_wam` | 加權平均到期日 |
| `mmf_prime_wal` | 加權平均存續期 |

### 貨幣市場基金 (MMF - Tax Exempt Funds)

| Symbol | 說明 |
|--------|------|
| `mmf_taxexempt_total` | 總投資組合證券 |
| `mmf_taxexempt_treasury` | 美國公債 |
| `mmf_taxexempt_agency` | 政府機構債務 |
| `mmf_taxexempt_repo_total` | 回購協議合計 |
| `mmf_taxexempt_repo_agency` | 政府機構回購 |
| `mmf_taxexempt_repo_treasury` | 公債回購 |
| `mmf_taxexempt_repo_other` | 其他回購 |
| `mmf_taxexempt_cdp` | 存單 |
| `mmf_taxexempt_cp_total` | 商業本票合計 |
| `mmf_taxexempt_cp_assetbacked` | 資產支持本票 |
| `mmf_taxexempt_cp_financial` | 金融公司本票 |
| `mmf_taxexempt_cp_nonfinancial` | 非金融公司本票 |
| `mmf_taxexempt_muni_total` | 市政債務合計 |
| `mmf_taxexempt_muni_vrdn` | 浮動利率需求票據 |
| `mmf_taxexempt_muni_other` | 其他市政證券 |
| `mmf_taxexempt_other_instrument` | 其他工具 |
| `mmf_taxexempt_inv_company` | 投資公司 |
| `mmf_taxexempt_tob` | 認購選擇權債券（2016-04 起） |
| `mmf_taxexempt_other_note` | 其他票據（僅至 2016-03） |
| `mmf_taxexempt_wam` | 加權平均到期日 |
| `mmf_taxexempt_wal` | 加權平均存續期 |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期 `YYYY-MM-DD`（MF/ETF/Combined 為每週數據，MMF 為每月數據） |

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

# 查詢貨幣市場基金 - 政府基金總投資組合
result = query("ici", "mmf_gov_total")

# 查詢貨幣市場基金 - 優質基金商業本票
result = query("ici", "mmf_prime_cp_total")

# 查詢貨幣市場基金 - 免稅基金市政債務
result = query("ici", "mmf_taxexempt_muni_total")

# 查詢貨幣市場基金 - 加權平均到期日
result = query("ici", "mmf_gov_wam")

# 批量查詢貨幣市場基金
result = query("ici", ["mmf_gov_total", "mmf_prime_total", "mmf_taxexempt_total"])
```

## 回傳欄位

`date`（MF/ETF/Combined 為週，MMF 為月）, `value`（單位：百萬美元）
