# Financial Data Query

Python 金融資料查詢函式庫，提供統一介面查詢不同資料來源的金融數據，預設回傳 JSON 格式方便 AI 模型使用。

## 安裝

```bash
pip install -e .
```

**要求：** Python 3.10+

## 快速開始

```python
from financial_data_query import query

# 單一查詢 — 回傳 JSON
result = query("yahoo", "AAPL")
# {"aapl": [{"date": "2024-01-02", "open": 185.0, "high": 187.0, ...}, ...]}

# 批量查詢 — 共用瀏覽器 (Stooq)
result = query("stooq", ["AAPL", "TSLA", "MSFT"])
# {"aapl": [...], "tsla": [...], "msft": [...]}

# 保留 DataFrame 格式
df = query("yahoo", "AAPL", output="dataframe")
# pd.DataFrame with DatetimeIndex
```

## API

### `query(source, symbol, start=None, end=None, sub_field=None, frequency=None, output="json", use_cache=True)`

| 參數 | 類型 | 說明 |
|------|------|------|
| `source` | `str` | 資料來源名稱：`"yahoo"`, `"fred"`, `"stooq"`, `"akshare"`, `"finra_margin"`, `"ici"`, `"tw_eco"`, `"tw_pmi"`, `"macroMicro"`, `"usTreasuryApi"`, `"multpl"`, `"moea"`, `"zillow"`, `"optioncharts"` |
| `symbol` | `str \| list[str]` | 商品代碼，或代號清單進行批量查詢 |
| `start` | `str` | 開始日期 `YYYY-MM-DD`，可選 |
| `end` | `str` | 結束日期 `YYYY-MM-DD`，可選 |
| `sub_field` | `str` | 指定回傳欄位，可選 |
| `frequency` | `str` | 資料頻率，可選 |
| `output` | `str` | 輸出格式：`"json"`（預設）或 `"dataframe"` |
| `use_cache` | `bool` | 是否使用記憶體 + 磁碟快取，預設 `True` |

**回傳：**
- `output="json"` → `dict[str, list[dict]]`
- `output="dataframe"` → `pd.DataFrame`

### JSON 格式

```json
{
  "aapl": [
    {"date": "2024-01-02", "open": 185.0, "high": 187.0, "low": 184.0, "close": 186.0, "volume": 52000000},
    {"date": "2024-01-03", "open": 186.5, "high": 188.0, "low": 185.0, "close": 187.0, "volume": 48000000}
  ],
  "tsla": [
    {"date": "2024-01-02", "open": 240.0, "high": 245.0, "low": 238.0, "close": 243.0, "volume": 95000000}
  ]
}
```

### 其他公開函數

```python
from financial_data_query import list_sources, register_source, clear_cache, clear_disk_cache

# 列出所有已註冊的資料來源
list_sources()

# 清除記憶體快取
clear_cache()

# 清除舊的磁碟快取（保留今天）
clear_disk_cache()
```

### 快取機制

所有資料來源皆啟用磁碟快取。資料首次下載時儲存完整歷史，後續查詢從快取截取日期範圍。

- **記憶體快取**：同行程內的 LRU 快取（`clear_cache()` 清除）
- **磁碟快取**：SQLite 檔，按日輪替，檔名 `YYYY-MM-DD.db`（`clear_disk_cache()` 清除舊檔）

## 支援的資料來源

### Yahoo Finance (`"yahoo"`)

- 底層：`yfinance`
- 免 API key
- `sub_field` 支援：`open`, `high`, `low`, `close`, `volume`, `adjclose`

```python
result = query("yahoo", "AAPL", frequency="daily")
```

### FRED (`"fred"`)

- 底層：FRED REST API
- 需要 API key（免費申請：https://fred.stlouisfed.org/docs/api/api_key.html）

```python
result = query("fred", "CPIAUCSL")
```

### AkShare (`"akshare"`)

- 底層：`akshare` Python library
- 免 API key，無需瀏覽器
- 資料範圍：1990s 至今（A股），2014 至今（BDI/PMI）

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `bdi` | BDI 波罗的海干散货指數 |
| A股代號（如 `"000001"`, `"600519"`） | A股歷史行情 |
| `wci` | Drewry 世界集装箱指數 WCI (2016-至今) |
| `china_manufacturing_pmi` | 財新中國製造業 PMI (2014-至今) |
| `china_services_pmi` | 財新中國服務業 PMI (2014-至今) |
| `euro_manufacturing_pmi` | 歐元區製造業 PMI 初值 (2008-至今) |
| `usa_ism_pmi` | 美國 ISM 製造業 PMI (1970-至今) |

```python
# 安裝額外依賴
pip install akshare

# 查詢 BDI 指數週線
result = query("akshare", "bdi", frequency="weekly")

# 查詢 A股收盤價
result = query("akshare", "600519", sub_field="close")

# 查詢 Drewry WCI 世界集装箱指數
result = query("akshare", "wci")

# 查詢財新中國製造業 PMI（2014-至今）
result = query("akshare", "china_manufacturing_pmi")

# 查詢財新中國服務業 PMI（2014-至今）
result = query("akshare", "china_services_pmi")

# 批次查詢所有 PMI
query("akshare", ["china_manufacturing_pmi", "china_services_pmi", 
                  "euro_manufacturing_pmi", "usa_ism_pmi"])

# 指定日期範圍
result = query("akshare", "000001", start="2024-01-01", end="2024-06-30")

# 批量查詢
result = query("akshare", ["000001", "600519"])
```

### Stooq (`"stooq"`)

- 底層：`undetected_chromedriver` + Selenium 網頁爬蟲
- 免 API key，需要 Chrome 瀏覽器
- 支援 CAPTCHA 自動識別（本地 LLM）
- 批量查詢共用單一瀏覽器，節省開關時間

```python
# 安裝額外依賴
pip install -e ".[stooq]"

# 批量查詢 — 共用一個瀏覽器
result = query("stooq", ["dx.c", "sp500.c"], start="2024-01-01", end="2024-12-31", frequency="1d")
```

**頻率參數：** `1d`（日）, `1wk`（周）, `1mo`（月）, `3mo`（季）, `1y`（年）

### FINRA Margin Statistics (`"finra_margin"`)

- 底層：直接下載 FINRA 發布的 Excel 檔案
- 免 API key
- 資料來源：https://www.finra.org/margin-statistics
- 資料範圍：1997-01 至今，每月更新

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `debit_balances` | 客戶信貸 (Debit Balances in Customers' Securities Margin Accounts) |
| `free_credit_cash` | 現金賬戶 (Free Credit Balances in Customers' Cash Accounts) |
| `free_credit_margin` | 融資賬戶 (Free Credit Balances in Customers' Securities Margin Accounts) |

```python
# 安裝額外依賴
pip install -e ".[finra_margin]"

# 查詢客戶信貸
result = query("finra_margin", "debit_balances")

# 指定日期範圍
result = query("finra_margin", "free_credit_cash", start="2024-01", end="2024-06")

# 批量查詢多個指標
result = query("finra_margin", ["debit_balances", "free_credit_margin"])
```

### ICI Fund Flows (`"ici"`)

- 底層：直接下載 ICI 發布的 XLS 檔案
- 免 API key
- 資料來源：Investment Company Institute
- 資料範圍：2024-01 至今，每週更新（MF/ETF/Combined）；2013-01 至今，每月更新（MMF）

**Symbols：**

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
| `mf_bond_taxable_government` | 政府債券 |
| `mf_bond_taxable_multisector` | 多部門 |
| `mf_bond_taxable_global` | 全球債券 |
| `mf_bond_municipal` | 地方政府債券 |
| `etf_total` | ETF 總淨發行量 |
| `etf_equity_total` | 股票型 ETF 合計 |
| `etf_equity_domestic` | 國內股票型 ETF |
| `etf_equity_world` | 全球股票型 ETF |
| `etf_hybrid` | 混合型 ETF |
| `etf_bond_total` | 債券型 ETF 合計 |
| `etf_bond_taxable` | 課稅債券型 ETF |
| `etf_bond_municipal` | 地方政府債券型 ETF |
| `etf_commodity` | 商品型 ETF |
| `combined_total` | 總長期基金+ETF 資金流量 |
| `combined_equity_total` | 股票型基金+ETF 合計 |
| `combined_equity_domestic` | 國內股票型基金+ETF |
| `combined_equity_world` | 全球股票型基金+ETF |
| `combined_hybrid` | 混合型基金+ETF |
| `combined_bond_total` | 債券型基金+ETF 合計 |
| `combined_bond_taxable` | 課稅債券型基金+ETF |
| `combined_bond_municipal` | 地方政府債券型基金+ETF |
| `combined_commodity` | 商品型基金+ETF |
| `mmf_gov_total` | 貨幣市場基金-政府基金 總投資組合 |
| `mmf_gov_treasury` | 貨幣市場基金-政府基金 美國公債 |
| `mmf_gov_agency` | 貨幣市場基金-政府基金 政府機構債務 |
| `mmf_gov_repo_total` | 貨幣市場基金-政府基金 回購協議合計 |
| `mmf_gov_repo_agency` | 貨幣市場基金-政府基金 政府機構回購 |
| `mmf_gov_repo_treasury` | 貨幣市場基金-政府基金 公債回購 |
| `mmf_gov_repo_other` | 貨幣市場基金-政府基金 其他回購 |
| `mmf_gov_cdp` | 貨幣市場基金-政府基金 存單 |
| `mmf_gov_ntd` | 貨幣市場基金-政府基金 不可議轉定期存款（2016-04 起） |
| `mmf_gov_cp_total` | 貨幣市場基金-政府基金 商業本票合計 |
| `mmf_gov_cp_assetbacked` | 貨幣市場基金-政府基金 資產支持本票 |
| `mmf_gov_cp_financial` | 貨幣市場基金-政府基金 金融公司本票 |
| `mmf_gov_cp_nonfinancial` | 貨幣市場基金-政府基金 非金融公司本票 |
| `mmf_gov_otherabs` | 貨幣市場基金-政府基金 其他資產支持證券（2016-04 起） |
| `mmf_gov_muni_total` | 貨幣市場基金-政府基金 市政債務合計 |
| `mmf_gov_muni_vrdn` | 貨幣市場基金-政府基金 浮動利率需求票據 |
| `mmf_gov_muni_other` | 貨幣市場基金-政府基金 其他市政證券 |
| `mmf_gov_tob` | 貨幣市場基金-政府基金 認購選擇權債券（2016-04 起） |
| `mmf_gov_other_instrument` | 貨幣市場基金-政府基金 其他工具 |
| `mmf_gov_icfa` | 貨幣市場基金-政府基金 保險公司資金協議 |
| `mmf_gov_inv_company` | 貨幣市場基金-政府基金 投資公司 |
| `mmf_gov_nonus_sov` | 貨幣市場基金-政府基金 非美國主權債務（2016-04 起） |
| `mmf_gov_other_note` | 貨幣市場基金-政府基金 其他票據（僅至 2016-03） |
| `mmf_gov_wam` | 貨幣市場基金-政府基金 加權平均到期日 |
| `mmf_gov_wal` | 貨幣市場基金-政府基金 加權平均存續期 |
| `mmf_prime_total` | 貨幣市場基金-優質基金 總投資組合 |
| `mmf_prime_treasury` | 貨幣市場基金-優質基金 美國公債 |
| `mmf_prime_agency` | 貨幣市場基金-優質基金 政府機構債務 |
| `mmf_prime_repo_total` | 貨幣市場基金-優質基金 回購協議合計 |
| `mmf_prime_repo_agency` | 貨幣市場基金-優質基金 政府機構回購 |
| `mmf_prime_repo_treasury` | 貨幣市場基金-優質基金 公債回購 |
| `mmf_prime_repo_other` | 貨幣市場基金-優質基金 其他回購 |
| `mmf_prime_cdp` | 貨幣市場基金-優質基金 存單 |
| `mmf_prime_ntd` | 貨幣市場基金-優質基金 不可議轉定期存款（2016-04 起） |
| `mmf_prime_cp_total` | 貨幣市場基金-優質基金 商業本票合計 |
| `mmf_prime_cp_assetbacked` | 貨幣市場基金-優質基金 資產支持本票 |
| `mmf_prime_cp_financial` | 貨幣市場基金-優質基金 金融公司本票 |
| `mmf_prime_cp_nonfinancial` | 貨幣市場基金-優質基金 非金融公司本票 |
| `mmf_prime_otherabs` | 貨幣市場基金-優質基金 其他資產支持證券（2016-04 起） |
| `mmf_prime_muni_total` | 貨幣市場基金-優質基金 市政債務合計 |
| `mmf_prime_muni_vrdn` | 貨幣市場基金-優質基金 浮動利率需求票據 |
| `mmf_prime_muni_other` | 貨幣市場基金-優質基金 其他市政證券 |
| `mmf_prime_tob` | 貨幣市場基金-優質基金 認購選擇權債券（2016-04 起） |
| `mmf_prime_other_instrument` | 貨幣市場基金-優質基金 其他工具 |
| `mmf_prime_icfa` | 貨幣市場基金-優質基金 保險公司資金協議 |
| `mmf_prime_inv_company` | 貨幣市場基金-優質基金 投資公司 |
| `mmf_prime_nonus_sov` | 貨幣市場基金-優質基金 非美國主權債務（2016-04 起） |
| `mmf_prime_other_note` | 貨幣市場基金-優質基金 其他票據（僅至 2016-03） |
| `mmf_prime_wam` | 貨幣市場基金-優質基金 加權平均到期日 |
| `mmf_prime_wal` | 貨幣市場基金-優質基金 加權平均存續期 |
| `mmf_taxexempt_total` | 貨幣市場基金-免稅基金 總投資組合 |
| `mmf_taxexempt_treasury` | 貨幣市場基金-免稅基金 美國公債 |
| `mmf_taxexempt_agency` | 貨幣市場基金-免稅基金 政府機構債務 |
| `mmf_taxexempt_repo_total` | 貨幣市場基金-免稅基金 回購協議合計 |
| `mmf_taxexempt_repo_agency` | 貨幣市場基金-免稅基金 政府機構回購 |
| `mmf_taxexempt_repo_treasury` | 貨幣市場基金-免稅基金 公債回購 |
| `mmf_taxexempt_repo_other` | 貨幣市場基金-免稅基金 其他回購 |
| `mmf_taxexempt_cdp` | 貨幣市場基金-免稅基金 存單 |
| `mmf_taxexempt_cp_total` | 貨幣市場基金-免稅基金 商業本票合計 |
| `mmf_taxexempt_cp_assetbacked` | 貨幣市場基金-免稅基金 資產支持本票 |
| `mmf_taxexempt_cp_financial` | 貨幣市場基金-免稅基金 金融公司本票 |
| `mmf_taxexempt_cp_nonfinancial` | 貨幣市場基金-免稅基金 非金融公司本票 |
| `mmf_taxexempt_muni_total` | 貨幣市場基金-免稅基金 市政債務合計 |
| `mmf_taxexempt_muni_vrdn` | 貨幣市場基金-免稅基金 浮動利率需求票據 |
| `mmf_taxexempt_muni_other` | 貨幣市場基金-免稅基金 其他市政證券 |
| `mmf_taxexempt_other_instrument` | 貨幣市場基金-免稅基金 其他工具 |
| `mmf_taxexempt_inv_company` | 貨幣市場基金-免稅基金 投資公司 |
| `mmf_taxexempt_tob` | 貨幣市場基金-免稅基金 認購選擇權債券（2016-04 起） |
| `mmf_taxexempt_other_note` | 貨幣市場基金-免稅基金 其他票據（僅至 2016-03） |
| `mmf_taxexempt_wam` | 貨幣市場基金-免稅基金 加權平均到期日 |
| `mmf_taxexempt_wal` | 貨幣市場基金-免稅基金 加權平均存續期 |

```python
# 安裝額外依賴
pip install -e ".[ici]"

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

# 批量查詢貨幣市場基金三大類總投資組合
result = query("ici", ["mmf_gov_total", "mmf_prime_total", "mmf_taxexempt_total"])
```

### NCD 台灣經濟指標 (`"tw_eco"`)

- 底層：`undetected_chromedriver` + Selenium 網頁爬蟲
- 免 API key，需要 Chrome 瀏覽器
- 資料來源：國家發展委員會景氣偵測系統 (https://index.ndc.gov.tw/n/zh_tw/data/eco#/)
- 資料範圍：1982-01 至今，每月更新

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `景氣對策信號(燈號)` | 景氣燈號 |
| `景氣對策信號(分)` | 景氣對策信號綜合分數 |
| `領先指標綜合指數(點)` | 領先指標綜合指數 |
| `領先指標不含趨勢指數(點)` | 領先指標不含趨勢 |
| `同時指標綜合指數(點)` | 同時指標綜合指數 |
| `同時指標不含趨勢指數(點)` | 同時指標不含趨勢 |
| `落後指標綜合指數(點)` | 落後指標綜合指數 |
| `落後指標不含趨勢指數(點)` | 落後指標不含趨勢 |

```python
# 安裝額外依賴
pip install -e ".[tw_ndc]"

# 查詢景氣綜合分數
result = query("tw_eco", "景氣對策信號(分)")

# 指定日期範圍
result = query("tw_eco", "景氣對策信號(分)", start="2020-01", end="2024-12")

# 批量查詢多個指標
result = query("tw_eco", ["景氣對策信號(燈號)", "領先指標綜合指數(點)"])
```

### NCD 台灣 PMI (`"tw_pmi"`)

- 底層：`undetected_chromedriver` + Selenium 網頁爬蟲
- 免 API key，需要 Chrome 瀏覽器
- 資料來源：國家發展委員會採購經理人指數 (https://index.ndc.gov.tw/n/zh_tw/data/PMI#/)
- 資料範圍：2012-07 至今，每月更新

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `製造業PMI` | 製造業 PMI 原始值 |
| `新增訂單數量` | 新增訂單數量指數 |
| `生產數量` | 生產數量指數 |
| `人力僱用數量` | 人力僱用數量指數 |
| `供應商交貨時間(%)` | 供應商交貨時間百分比 |
| `存貨(%)` | 存貨百分比 |
| `客戶存貨(%)` | 客戶存貨百分比 |
| `原物料價格(%)` | 原物料價格百分比 |
| `未完成訂單(%)` | 未完成訂單百分比 |
| `新增出口訂單(%)` | 新增出口訂單百分比 |
| `進口原物料數量(%)` | 進口原物料數量百分比 |
| `未來六個月展望(%)` | 未來六個月展望百分比 |
| `製造業PMI(季調值)(%)` | 製造業 PMI 季調值 |
| `新增訂單數量(季調值)(%)` | 新增訂單數量季調值 |
| `生產數量(季調值)(%)` | 生產數量季調值 |
| `人力僱用數量(季調值)(%)` | 人力僱用數量季調值 |

```python
# 安裝額外依賴
pip install -e ".[tw_ndc]"

# 查詢製造業 PMI
result = query("tw_pmi", "製造業PMI")

# 指定日期範圍
result = query("tw_pmi", "製造業PMI", start="2020-01", end="2024-12")

# 批量查詢
result = query("tw_pmi", ["製造業PMI", "新增訂單數量", "生產數量"])
```

### MacroMicro (`"macroMicro"`)

- 底層:`undetected_chromedriver` + Selenium 網頁爬蟲
- 免 API key，需要 Chrome 瀏覽器
- 資料來源：MacroMicro (https://www.macromicro.me)
- 使用前需先執行 `macroMicroSymbolLinkConnect()` 建立 symbol 映射

**建立 symbol 映射（只需輸入 URL，商品代號與描述自動提取）：**

```python
from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect

macroMicroSymbolLinkConnect(
    "https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day"
)
```


```bash
python -c "from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect; macroMicroSymbolLinkConnect('https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day')"
```

**Symbols：**

<!-- MACROMICRO_SYMBOLS_START -->
| Symbol | 說明 |
|--------|------|
| `china-reverse-repo-rate-7-day` | 中國-逆回購利率(日數據)-7天期 | 數據 |
| `cn-dr007` | 中國-銀行間債券質押式回購利率[DR007](7天期) | 數據 |
| `ism-manufacturing-backlogoforders` | 美國-ISM製造業指數[PMI]-未完成訂單 | 數據 |
| `ism-manufacturing-customersinventories` | 美國-ISM製造業指數[PMI]-客戶存貨 | 數據 |
| `ism-manufacturing-neworders` | 美國-ISM製造業指數[PMI]-新訂單 | 數據 |
| `ism-manufacturing-supplierdeliveries` | 美國-ISM製造業指數[PMI]-供應商交貨 | 數據 |
| `tw-inventories-sales-ratio-manufacturing` | 台灣-製造業存貨率 | 數據 |
| `us-5year-cds` | 美國_5年信用違約交換 |
| `us-new-tenant-rent-index` | US - New Tenant Rent Index | Series |
<!-- MACROMICRO_SYMBOLS_END -->

```python
# 安裝額外依賴
pip install -e ".[macroMicro]"

# 查詢
result = query("macroMicro", "china-reverse-repo-rate-7-day")

# 批量查詢
result = query("macroMicro", ["china-reverse-repo-rate-7-day", "cn-dr007"])
```

### 美國財政部公債拍賣 (`"usTreasuryApi"`)

- 底層：US Treasury Fiscal Data API
- 免 API key
- 資料來源：https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query
- 資料範圍：1970 年至今，每週更新（拍賣日）

**商品代號：**

| 商品代號 | 債券期限 | 類型 |
|----------|----------|------|
| `bill_4w` | 4 週 | T-Bill（國庫券） |
| `bill_8w` | 8 週 | T-Bill（國庫券） |
| `bill_13w` | 13 週 | T-Bill（國庫券） |
| `bill_26w` | 26 週 | T-Bill（國庫券） |
| `bill_52w` | 52 週 | T-Bill（國庫券） |
| `note_2y` | 2 年 | T-Note（國庫券） |
| `note_3y` | 3 年 | T-Note（國庫券） |
| `note_5y` | 5 年 | T-Note（國庫券） |
| `note_7y` | 7 年 | T-Note（國庫券） |
| `note_10y` | 10 年 | T-Note（國庫券） |
| `bond_30y` | 30 年 | T-Bond（國庫券） |
| `allBond` | 所有期限 | 回傳日期範圍內的所有拍賣資料 |
| `debtMaturity` | 到期債務分析 | 配合 `start`（預設今天）和 `end`（**必填**）指定到期日期範圍 |

**到期分析回傳欄位：** `T_Bills`, `T_Notes`, `T_Bonds`, `TIPS`, `FRNs`（單位：美元，單行 DataFrame）

**回傳欄位：**

| 欄位 | 說明 |
|------|------|
| `issue_date` | 發行日 |
| `security_term` | 債券期限（例：10-Year, 13-Week） |
| `maturity_date` | 到期日 |
| `int_rate` | 票面利率（%） |
| `avg_med_yield` | 平均/中位收益率（%） |
| `high_yield` | 最高收益率（%） |
| `low_yield` | 最低收益率（%） |
| `offering_amount` | 發行金額（美元） |
| `total_accepted` | 總中标金額（美元） |
| `total_tendered` | 總投標金額（美元） |
| `bid_to_cover_ratio` | 投標覆蓋率（投標總額/中标總額） |
| `auction_format` | 拍賣方式（Multi-Price / Price-Based） |
| `primary_dealer_tendered` | 一級交易商投標金額 |
| `primary_dealer_accepted` | 一級交易商中标金額 |
| `comp_accepted` | 競爭標中标金額 |
| `comp_tendered` | 競爭標投標金額 |
| `noncomp_accepted` | 非競爭標中标金額 |
| `direct_bidder_tendered` | 直接投標人投標金額 |
| `direct_bidder_accepted` | 直接投標人中标金額 |
| `indirect_bidder_tendered` | 間接投標人投標金額 |
| `indirect_bidder_accepted` | 間接投標人中标金額 |
| `soma_tendered` | SOMA 投標金額 |
| `soma_accepted` | SOMA 中标金額 |
| `fima_noncomp_tendered` | FIMA 非競爭標投標金額 |
| `fima_noncomp_accepted` | FIMA 非競爭標中标金額 |
| `treas_retail_tenders_accepted` | 國庫零售投標中标金額 |
| `comp_tenders_accepted` | 競爭標投標筆數 |
| `noncomp_tenders_accepted` | 非競爭標投標筆數 |
| `treas_retail_accepted` | 國庫零售投標筆數 |

```python
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
```

### Multpl (`"multpl"`)

- 底層：`requests` + `pandas.read_html` 網頁爬蟲
- 免 API key
- 資料來源：Multpl (https://www.multpl.com)
- 資料範圍：1870 年至今（Shiller PE），每月/每季更新

**Symbols：**

| Symbol | 說明 | 頻率 |
|--------|------|------|
| `sp500_ps` | S&P 500 本銷比 (Price to Sales) | 季 |
| `sp500_div_yield` | S&P 500 殖利率 (Dividend Yield) | 月 |
| `sp500_pe` | S&P 500 本益比 (PE Ratio) | 月 |
| `shiller_pe` | Shiller 本益比 (CAPE) | 月 |
| `sp500_earn_yield` | S&P 500 盈餘收益率 (Earnings Yield) | 月 |
| `sp500_price` | S&P 500 歷史價格 (Historical Prices) | 月 |
| `sp500_earn_growth` | S&P 500 盈餘成長率 (Earnings Growth) | 季 |

```python
# 查詢 S&P 500 本益比
result = query("multpl", "sp500_pe")

# 查詢 Shiller PE
result = query("multpl", "shiller_pe", start="2000-01-01")

# 指定日期範圍
result = query("multpl", "sp500_div_yield", start="2020-01-01", end="2024-12-31")

# 批量查詢
result = query("multpl", ["sp500_pe", "shiller_pe", "sp500_div_yield"])
```

### MOEA 台灣外銷訂單 (`"moea"`)

- 底層：`selenium` + `webdriver-manager` 網頁爬蟲（自動管理 ChromeDriver）
- 免 API key，需要 Chrome 瀏覽器
- 資料來源：經濟部出口貿易統計 (https://service.moea.gov.tw/EE520/investigate/InvestigateBA.aspx)
- 資料範圍：1984-09 至今，每月更新

**商品代號：**

| 類別 | 商品代號 |
|------|----------|
| 化工類 | `化學品`, `塑膠、橡膠及其製品` |
| 紡織類 | `紡織品` |
| 金屬類 | `基本金屬及其製品` |
| 電子類 | `電子產品` |
| 機械類 | `機械`, `電機產品` |
| 資訊通信 | `資訊與通信產品` |
| 運具類 | `運輸工具及其設備` |
| 其他 | `光學器材`, `礦產品`, `其他` |

**地區：** `美國`, `日本`, `中國大陸及香港`, `東協`, `歐洲`, `其他地區`

```python
# 安裝額外依賴
pip install webdriver-manager selenium

# 查詢單一商品所有地區（回傳每個地區的數值）
result = query("moea", "資訊與通信產品")
# {"資訊與通信產品": [{"date": "1984-09-30", "美國": 43.0, "日本": 9.0, ...}, ...]}

# 指定日期範圍
result = query("moea", "化學品", start="2024-01-01", end="2024-12-31")

# 批量查詢多個商品（共用單一瀏覽器 session）
result = query("moea", ["化學品", "電子產品", "機械"])
```

**回傳格式：** `date` (月終), 各地區欄位 (`美國`, `日本`, `中國大陸及香港`, `東協`, `歐洲`, `其他地區`)

**注意事項：**
- Symbol 只需商品代號，會自動包含所有 6 個地區
- 每次查詢抓取全量資料後在客戶端篩選
- **建議使用批量查詢以節省瀏覽器開關時間**

### Zillow (`"zillow"`)

- 底層：`requests` 下載 Zillow Research CSV
- 免 API key
- 資料來源：Zillow Research (https://www.zillow.com/research/)
- 資料地區：全美 (US)、紐約 (NY)、洛杉磯 (LA)
- 資料頻率：月

**Symbols：**

| Symbol | 說明 | 地區 |
|--------|------|------|
| `ZHVI` | Zillow 房價指數 (Home Value Index) | US, NY, LA |
| `ZHVF` | Zillow 房價預測 (Home Value Forecast) | US, NY, LA |
| `ZORI` | Zillow 租金指數 (Rental Index) | US, NY, LA |
| `ZORF` | Zillow 租金預測 (Rental Forecast) | US 僅全國 |
| `FSIT` | 待售房屋存貨量 (For-Sale Inventory) | US, NY, LA |
| `SALCNT` | 房屋銷售量 (Sales Count) | US, NY, LA |
| `MRKT` | 市場溫度指數 (Market Temperature Index) | US, NY, LA |
| `NCSC` | 新建房屋銷售量 (New Construction Sales) | US, NY, LA |
| `NHIN` | 購屋所需年收入 (New Homeowner Income Needed) | US, NY, LA |

```python
# 查詢全美租金指數
result = query("zillow", "ZORI")

# 查詢紐約房價指數
result = query("zillow", "ZHVI", sub_field="NY")

# 查詢洛杉磯市場溫度指數
result = query("zillow", "MRKT", sub_field="LA")

# 指定日期範圍
result = query("zillow", "ZHVI", sub_field="NY", start="2020-01-01", end="2024-12-31")

# 批量查詢
result = query("zillow", ["ZHVI", "ZORI", "FSIT"], sub_field="NY")
```

**注意事項：**
- `sub_field` 預設回傳全部三個地區，指定 `US`、`NY`、`LA` 可篩選單一地區
- `ZORF` 僅有全國數據，無地區數據

### OptionCharts (`"optioncharts"`)

- 底層：`requests` + `BeautifulSoup` 網頁爬蟲
- 免 API key
- 資料來源：OptionCharts (https://optioncharts.io)
- 資料範圍：2024-06 至今，每日更新

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `$SPX` | S&P 500 Index |
| `$NDX` | NASDAQ 100 |

**回傳欄位：**

| 欄位 | 說明 |
|------|------|
| `Close Price` | 收盤價 |
| `Option Volume Total` | 選擇權總成交量 |
| `Option Volume Put-Call Ratio` | 選擇權成交量 P/C 比 |
| `OI Total` | 選擇權總未平倉量 |
| `OI Put-Call Ratio` | 選擇權未平倉 P/C 比 |

```python
# 查詢 S&P 500 選擇權數據
result = query("optioncharts", "$SPX")

# 指定日期範圍
result = query("optioncharts", "$SPX", start="2024-07-01", end="2024-12-31")

# 指定欄位
result = query("optioncharts", "$SPX", sub_field="OI Put-Call Ratio")

# 降頻為週線/月線/季線
result = query("optioncharts", "$SPX", frequency="weekly")

# 批量查詢
result = query("optioncharts", ["$SPX", "$NDX"])
```

**注意事項：**
- 原始數據為日頻，`frequency` 可設 `weekly`、`monthly`、`quarterly` 進行重採樣
- Volume 欄位按頻率累加（sum），其他欄位取最後交易日值（last）

## 設定

### FRED API Key

專案根目錄建立 `.env` 檔案：

```bash
FRED_API_KEY=your_api_key_here
```

`.env` 已加入 `.gitignore`，不會被提交到版本控制。也可以透過環境變數設定：

```bash
export FRED_API_KEY=your_api_key_here
```

### Stooq CAPTCHA 識別

Stooq 需要本地 LLM 識別 CAPTCHA。預設使用 `http://localhost:12345/v1`（llama.cpp API），model `qwen3.5-9b`。

## 擴充自訂資料來源

繼承 `DataSourceFetcher` 並註冊：

```python
from financial_data_query import register_source
from financial_data_query.base import DataSourceFetcher
import pandas as pd

class MyFetcher(DataSourceFetcher):
    source_name = "my_source"

    def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None) -> pd.DataFrame:
        # 實作你的資料查詢邏輯
        return pd.DataFrame(...)

    # 可選：覆寫 batch_fetch 以優化批量查詢
    def batch_fetch(self, symbols, start=None, end=None, sub_field=None, frequency=None):
        # 預設逐個呼叫 fetch()，可覆寫以共用資源
        return super().batch_fetch(symbols, start=start, end=end, sub_field=sub_field, frequency=frequency)

register_source(MyFetcher)

# 現在可以使用
result = query("my_source", "SYMBOL")
```

## 錯誤處理

| 例外類別 | 觸發條件 |
|----------|----------|
| `DataSourceError` | 所有資料來源相關錯誤的基底類 |
| `DataSourceNotFoundError` | 未知的資料來源名稱 |
| `ConfigError` | API key 或設定缺失 |
| `FetchError` | 網路請求失敗或 API 回傳錯誤 |

```python
from financial_data_query import query
from financial_data_query.errors import DataSourceError

try:
    result = query("yahoo", "INVALID_SYMBOL")
except DataSourceError as e:
    print(f"查詢失敗: {e}")
```

## 開發

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試
pytest tests/ -v
```
