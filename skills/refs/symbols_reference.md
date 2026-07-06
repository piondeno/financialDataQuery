# 金融商品代號查詢表

---

## 資料源：`fred`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 利率 | `DGS10` | 10 年公債殖利率 |
| 利率 | `DGS2` | 2 年公債殖利率 |
| 利率 | `SOFR` | 擔保隔夜融資利率 |
| 利率 | `IORB` | 儲備金餘額利率 |
| 利率 | `T10Y2Y` | 10-2 年利差 (殖利率曲線) |
| 貨幣 | `M2SL` | M2 貨幣供給（名目） |
| 貨幣 | `M2REAL` | 實質 M2 貨幣供給 |
| 通膨 | `CPIAUCSL` | 名目 CPI |
| 通膨 | `CPILFESL` | 核心 CPI（不含食物與能源） |
| 通膨 | `PCEPI` | 名目 PCE |
| 通膨 | `PCEPILFE` | 核心 PCE |
| 通膨 | `STICKCPIM159SFRBATL` | 黏性價格 CPI |
| 通膨 | `CORESTICKM159SFRBATL` | 核心黏性價格 CPI |
| 通膨 | `FLEXCPIM159SFRBATL` | 彈性價格 CPI |
| 通膨 | `COREFLEXCPIM159SFRBATL` | 核心彈性價格 CPI |
| GDP | `GDP` | 名目 GDP |
| 消費 | `PCEC96` | 實質個人消費支出 |
| 消費 | `PCEDGC96` | 實際 PCE：耐用品 |
| 消費 | `PCESC96` | 實際 PCE：服務 |
| 消費 | `DGDSRX1` | 實際 PCE：商品 |
| 消費 | `PCENDC96` | 實際 PCE：非耐久財 |
| 消費 | `DFXARX1M020SBEA` | 實際 PCE：食品 |
| 消費 | `DNRGRX1M020SBEA` | 實際 PCE：能源商品和服務 |
| 零售 | `RSXFS` | 零售銷售初值 |
| 零售 | `RETAILIRSA` | 零售業庫存銷售比 |
| 就業 | `UNRATE` | 失業率 |
| 就業 | `ICSA` | 初領失業金人數 |
| 就業 | `IURSA` | 保險失業率 |
| 就業 | `SAHMCURRENT` | 薩姆規則衰退指標 |
| 就業 | `MANEMP` | 製造業就業人數 |
| 工業 | `INDPRO` | 工業生產指數 |
| 工業 | `TCU` | 產能利用率 |
| 工業 | `AWHAEMAN` | 製造業每週平均工時 |
| 生產力 | `PRS85006091` | 非農勞動生產力每小時 |
| 生產力 | `PRS30006092` | 製造業勞動生產力每小時 |
| 生產力 | `PRS85006111` | 非農單位勞動成本每小時 |
| 生產力 | `PRS30006112` | 製造業單位勞動成本每小時 |
| 投資 | `B985RC1Q027SBEA` | 軟體投資 |
| 投資 | `Y006RC1Q027SBEA` | 研發投資 |
| 投資 | `Y001RC1Q027SBEA` | 智慧財產權投資 |
| 人口 | `POPTHM` | 美國總人口 |

---

## 資料源：`yahoo`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 商品 | `GC=F` | 黃金期貨價格 |
| 商品 | `CL=F` | 西德州原油期貨價格 |
| 商品 | `BZ=F` | 布蘭特原油期貨價格 |
| 商品 | `^DJCI` | 道瓊工業平均指數 |
| 商品 | `^SPGSCI` | S&P GSCI 期貨指數 |
| 匯率 | `DX-Y.NYB` | 美元指數 |
| 匯率 | `CNY=X` | 在岸人民幣兌美元 |
| 匯率 | `CNH=X` | 離岸人民幣兌美元 |
| 匯率 | `EURUSD=X` | 歐元兌美元 |
| 指數 | `^VIX` | VIX 恐慌指數 |
| 指數 | `^GSPC` | S&P 500 指數 |
| 商品 | `ZW=F` | 芝加哥SRW小麥期貨 |
| 商品 | `NG=F` | 天然氣期貨 |

---

## 資料源：`akshare`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 運費指數 | `bdi` | 波羅的海乾散貨指數 |
| 集運指數 | `wci` | Drewry 世界集装箱指數 (2016-至今) |
| A股 | `000001`, `600519` 等 | A股歷史行情（需輸入股票代碼） |
| PMI | `china_manufacturing_pmi` | 財新中國製造業 PMI (2014-至今) |
| PMI | `china_services_pmi` | 財新中國服務業 PMI (2014-至今) |
| PMI | `euro_manufacturing_pmi` | 歐元區製造業 PMI 初值（含今值/預測值/前值） |
| PMI | `usa_ism_pmi` | 美國 ISM 製造業 PMI（含今值/預測值/前值，1970-至今） |

呼叫格式：`{"source":"akshare","symbols":["bdi"]}`

---

## 資料源：`stooq`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 美股 | `aapl.us` | Apple |
| 美股 | `tsla.us` | Tesla |
| 美股 | `msft.us` | Microsoft |
| 指數 | `sp500.c` | S&P 500 |
| 指數 | `dx.c` | 美元指數 |
| 匯率 | `usdeurf.f` | 歐元兌美元 |
| 期貨 | `gold.cf` | 黃金期貨 |
| 加密貨幣 | `btcusd.cc` | 比特幣 |

呼叫格式：`{"source":"stooq","symbols":["aapl.us"]}`

**注意事項：**
- 商品代號後綴：`.us`（美股）、`.c`（指數）、`.f`（匯率）、`.cf`（期貨）、`.cc`（加密貨幣）
- 需要 Chrome 瀏覽器安裝在系統中
- 支援 `frequency`：`"1d"`（日）、`"1wk"`（周）、`"1mo"`（月）、`"3mo"`（季）、`"1y"`（年）
- 支援 `sub_field`：`"Open"`、`"High"`、`"Low"`、`"Close"`、`"Volume"`
- 批量查詢會共用同一個瀏覽器實例
- CAPTCHA 識別需要本地 LLM（預設 `localhost:12345`，model `qwen3.5-9b`）
- 爬蟲速度較慢，每次查詢約需數秒

---

## 資料源：`usTreasuryApi`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 短期國庫票據 (Bill) | `bill_4w` | 4 週公債 |
| 短期國庫票據 (Bill) | `bill_8w` | 8 週公債 |
| 短期國庫票據 (Bill) | `bill_13w` | 13 週公債 |
| 短期國庫票據 (Bill) | `bill_26w` | 26 週公債 |
| 短期國庫票據 (Bill) | `bill_52w` | 52 週公債（1 年） |
| 中期國庫券 (Note) | `note_2y` | 2 年期公債 |
| 中期國庫券 (Note) | `note_3y` | 3 年期公債 |
| 中期國庫券 (Note) | `note_5y` | 5 年期公債 |
| 中期國庫券 (Note) | `note_7y` | 7 年期公債 |
| 中期國庫券 (Note) | `note_10y` | 10 年期公債 |
| 長期國庫債券 (Bond) | `bond_30y` | 30 年期公債 |
| 全部品種 | `allBond` | 所有期限公債 |
| 到期分析 | `debtMaturity` | 到期債務分析（配合 `start`/`end` 指定日期範圍，`start` 預設今天，`end` 必填） |

呼叫格式：`{"source":"usTreasuryApi","symbols":["note_10y"]}`

**到期分析回傳欄位：** `T_Bills`, `T_Notes`, `T_Bonds`, `TIPS`, `FRNs`（單位：美元，單行 DataFrame）

---

## 資料源：`macroMicro`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 貨幣政策 | `china-reverse-repo-rate-7-day` | 中國逆回購利率（日數據）- 7天期 |
| 貨幣政策 | `cn-dr007` | 中國銀行間債券質押式回購利率 - DR007（7天期） |
| PMI 子項目 | `ism-manufacturing-neworders` | ISM 製造業 PMI - 新訂單指數 (1948-至今) |
| PMI 子項目 | `ism-manufacturing-customersinventories` | ISM 製造業 PMI - 客戶存貨指數 (1997-至今) |
| PMI 子項目 | `ism-manufacturing-supplierdeliveries` | ISM 製造業 PMI - 供應商交貨指數 (1985-至今) |
| PMI 子項目 | `ism-manufacturing-backlogoforders` | ISM 製造業 PMI - 未完成訂單指數 (1993-至今) |
| 信用風險 | `us-5year-cds` | 美國 5年信用違約交換 (CDS) |
| 房地產 | `us-new-tenant-rent-index` | 美國新租客租金指數 (季頻，2005-至今) |
| 存貨 | `tw-inventories-sales-ratio-manufacturing` | 台灣製造業存貨率 (半年頻，1982-至今) |


---

## 資料源：`tw_pmi`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| PMI | `製造業PMI` | 製造業 PMI 原始值 |
| PMI | `製造業PMI(季調值)(%)` | 製造業 PMI 季調值 |
| 訂單 | `新增訂單數量` | 新增訂單數量指數 |
| 訂單 | `新增訂單數量(季調值)(%)` | 新增訂單數量季調值 |
| 訂單 | `新增出口訂單(%)` | 新增出口訂單百分比 |
| 生產 | `生產數量` | 生產數量指數 |
| 生產 | `生產數量(季調值)(%)` | 生產數量季調值 |
| 人力 | `人力僱用數量` | 人力僱用數量指數 |
| 人力 | `人力僱用數量(季調值)(%)` | 人力僱用數量季調值 |
| 交貨 | `供應商交貨時間(%)` | 供應商交貨時間 |
| 存貨 | `存貨(%)` | 存貨百分比 |
| 存貨 | `客戶存貨(%)` | 客戶存貨百分比 |
| 價格 | `原物料價格(%)` | 原物料價格指數 |
| 訂單 | `未完成訂單(%)` | 未完成訂單指數 |
| 進出口 | `進口原物料數量(%)` | 進口原物料數量指數 |
| 展望 | `未來六個月展望(%)` | 未來六個月展望指數 |

呼叫格式：`{"source":"tw_pmi","symbols":["製造業PMI"]}`

---

## 資料源：`tw_eco`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 燈號 | `景氣對策信號(燈號)` | 景氣對策信號（燈號） |
| 分數 | `景氣對策信號(分)` | 景氣對策信號（分數） |
| 領先 | `領先指標綜合指數(點)` | 領先指標綜合指數 |
| 領先 | `領先指標不含趨勢指數(點)` | 領先指標不含趨勢指數 |
| 同時 | `同時指標綜合指數(點)` | 同時指標綜合指數 |
| 同時 | `同時指標不含趨勢指數(點)` | 同時指標不含趨勢指數 |
| 落後 | `落後指標綜合指數(點)` | 落後指標綜合指數 |
| 落後 | `落後指標不含趨勢指數(點)` | 落後指標不含趨勢指數 |

呼叫格式：`{"source":"tw_eco","symbols":["領先指標綜合指數(點)"]}`

---

## 資料源：`finra_margin`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 融資餘額 | `debit_balances` | 客戶融資餘額 |
| 現金賬戶 | `free_credit_cash` | 現金賬戶餘額 |
| 融資賬戶 | `free_credit_margin` | 融資賬戶餘額 |

呼叫格式：`{"source":"finra_margin","symbols":["debit_balances"]}`

---

## 資料源：`ici`

美國投資公司協會 (ICI) 基金資金流量數據。MF/ETF/Combined 為每週數據（2024-01 至今），MMF 為每月數據（2013-01 至今）。

### 共同基金 (Mutual Fund)

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 總計 | `mf_total` | 長期共同基金總計 |
| 股票型 - 總計 | `mf_equity_total` | 股票型基金總計 |
| 股票型 - 國內 | `mf_equity_domestic_total` | 國內股票型總計 |
| 股票型 - 大盤股 | `mf_equity_domestic_large` | 大型股 |
| 股票型 - 中盤股 | `mf_equity_domestic_mid` | 中型股 |
| 股票型 - 小盤股 | `mf_equity_domestic_small` | 小型股 |
| 股票型 - 多檔股 | `mf_equity_domestic_multi` | 多檔股 |
| 股票型 - 其他 | `mf_equity_domestic_other` | 其他國內 |
| 股票型 - 全球 | `mf_equity_world_total` | 全球股票型總計 |
| 股票型 - 已開發市場 | `mf_equity_world_developed` | 已開發市場 |
| 股票型 - 新興市場 | `mf_equity_world_emerging` | 新興市場 |
| 混合型 | `mf_hybrid` | 混合型基金 |
| 債券型 - 總計 | `mf_bond_total` | 債券型基金總計 |
| 債券型 - 應稅 | `mf_bond_taxable_total` | 應稅債券型總計 |
| 債券型 - 投資等級 | `mf_bond_taxable_investment` | 投資等級 |
| 債券型 - 高收益債 | `mf_bond_taxable_highyield` | 垃圾債/高收益債 |
| 債券型 - 公債 | `mf_bond_taxable_government` | 公債 |
| 債券型 - 多部門 | `mf_bond_taxable_multisector` | 多部門債券 |
| 債券型 - 全球債 | `mf_bond_taxable_global` | 全球債券 |
| 債券型 - 市政債 | `mf_bond_municipal` | 市政工程債 |

### ETF

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 總計 | `etf_total` | ETF 總計 |
| 股票型 - 總計 | `etf_equity_total` | 股票型 ETF 總計 |
| 股票型 - 國內 | `etf_equity_domestic` | 國內股票型 |
| 股票型 - 全球 | `etf_equity_world` | 全球股票型 |
| 混合型 | `etf_hybrid` | 混合型基金 |
| 債券型 - 總計 | `etf_bond_total` | 債券型 ETF 總計 |
| 債券型 - 應稅 | `etf_bond_taxable` | 應稅債券型 |
| 債券型 - 市政債 | `etf_bond_municipal` | 市政工程債 |
| 大宗商品 | `etf_commodity` | 商品 ETF |

### 合併 (MF + ETF)

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 總計 | `combined_total` | 共同基金+ETF 總計 |
| 股票型 - 總計 | `combined_equity_total` | 股票型基金總計 |
| 股票型 - 國內 | `combined_equity_domestic` | 國內股票型 |
| 股票型 - 全球 | `combined_equity_world` | 全球股票型 |
| 混合型 | `combined_hybrid` | 混合型基金 |
| 債券型 - 總計 | `combined_bond_total` | 債券型基金總計 |
| 債券型 - 應稅 | `combined_bond_taxable` | 應稅債券型 |
| 債券型 - 市政債 | `combined_bond_municipal` | 市政工程債 |
| 大宗商品 | `combined_commodity` | 商品基金 |

### 貨幣市場基金 - 政府基金 (MMF Government Funds)

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 總計 | `mmf_gov_total` | 總投資組合證券 |
| 公債 | `mmf_gov_treasury` | 美國公債 |
| 公債 | `mmf_gov_agency` | 政府機構債務 |
| 回購 | `mmf_gov_repo_total` | 回購協議合計 |
| 回購 | `mmf_gov_repo_agency` | 政府機構回購 |
| 回購 | `mmf_gov_repo_treasury` | 公債回購 |
| 回購 | `mmf_gov_repo_other` | 其他回購 |
| 定存 | `mmf_gov_cdp` | 存單 |
| 定存 | `mmf_gov_ntd` | 不可議轉定期存款（2016-04 起） |
| 本票 | `mmf_gov_cp_total` | 商業本票合計 |
| 本票 | `mmf_gov_cp_assetbacked` | 資產支持本票 |
| 本票 | `mmf_gov_cp_financial` | 金融公司本票 |
| 本票 | `mmf_gov_cp_nonfinancial` | 非金融公司本票 |
| 其他 | `mmf_gov_otherabs` | 其他資產支持證券（2016-04 起） |
| 市政債 | `mmf_gov_muni_total` | 市政債務合計 |
| 市政債 | `mmf_gov_muni_vrdn` | 浮動利率需求票據 |
| 市政債 | `mmf_gov_muni_other` | 其他市政證券 |
| 其他 | `mmf_gov_tob` | 認購選擇權債券（2016-04 起） |
| 其他 | `mmf_gov_other_instrument` | 其他工具 |
| 其他 | `mmf_gov_icfa` | 保險公司資金協議 |
| 其他 | `mmf_gov_inv_company` | 投資公司 |
| 其他 | `mmf_gov_nonus_sov` | 非美國主權債務（2016-04 起） |
| 其他 | `mmf_gov_other_note` | 其他票據（僅至 2016-03） |
| 指標 | `mmf_gov_wam` | 加權平均到期日 |
| 指標 | `mmf_gov_wal` | 加權平均存續期 |

### 貨幣市場基金 - 優質基金 (MMF Prime Funds)

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 總計 | `mmf_prime_total` | 總投資組合證券 |
| 公債 | `mmf_prime_treasury` | 美國公債 |
| 公債 | `mmf_prime_agency` | 政府機構債務 |
| 回購 | `mmf_prime_repo_total` | 回購協議合計 |
| 回購 | `mmf_prime_repo_agency` | 政府機構回購 |
| 回購 | `mmf_prime_repo_treasury` | 公債回購 |
| 回購 | `mmf_prime_repo_other` | 其他回購 |
| 定存 | `mmf_prime_cdp` | 存單 |
| 定存 | `mmf_prime_ntd` | 不可議轉定期存款（2016-04 起） |
| 本票 | `mmf_prime_cp_total` | 商業本票合計 |
| 本票 | `mmf_prime_cp_assetbacked` | 資產支持本票 |
| 本票 | `mmf_prime_cp_financial` | 金融公司本票 |
| 本票 | `mmf_prime_cp_nonfinancial` | 非金融公司本票 |
| 其他 | `mmf_prime_otherabs` | 其他資產支持證券（2016-04 起） |
| 市政債 | `mmf_prime_muni_total` | 市政債務合計 |
| 市政債 | `mmf_prime_muni_vrdn` | 浮動利率需求票據 |
| 市政債 | `mmf_prime_muni_other` | 其他市政證券 |
| 其他 | `mmf_prime_tob` | 認購選擇權債券（2016-04 起） |
| 其他 | `mmf_prime_other_instrument` | 其他工具 |
| 其他 | `mmf_prime_icfa` | 保險公司資金協議 |
| 其他 | `mmf_prime_inv_company` | 投資公司 |
| 其他 | `mmf_prime_nonus_sov` | 非美國主權債務（2016-04 起） |
| 其他 | `mmf_prime_other_note` | 其他票據（僅至 2016-03） |
| 指標 | `mmf_prime_wam` | 加權平均到期日 |
| 指標 | `mmf_prime_wal` | 加權平均存續期 |

### 貨幣市場基金 - 免稅基金 (MMF Tax Exempt Funds)

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 總計 | `mmf_taxexempt_total` | 總投資組合證券 |
| 公債 | `mmf_taxexempt_treasury` | 美國公債 |
| 公債 | `mmf_taxexempt_agency` | 政府機構債務 |
| 回購 | `mmf_taxexempt_repo_total` | 回購協議合計 |
| 回購 | `mmf_taxexempt_repo_agency` | 政府機構回購 |
| 回購 | `mmf_taxexempt_repo_treasury` | 公債回購 |
| 回購 | `mmf_taxexempt_repo_other` | 其他回購 |
| 定存 | `mmf_taxexempt_cdp` | 存單 |
| 本票 | `mmf_taxexempt_cp_total` | 商業本票合計 |
| 本票 | `mmf_taxexempt_cp_assetbacked` | 資產支持本票 |
| 本票 | `mmf_taxexempt_cp_financial` | 金融公司本票 |
| 本票 | `mmf_taxexempt_cp_nonfinancial` | 非金融公司本票 |
| 市政債 | `mmf_taxexempt_muni_total` | 市政債務合計 |
| 市政債 | `mmf_taxexempt_muni_vrdn` | 浮動利率需求票據 |
| 市政債 | `mmf_taxexempt_muni_other` | 其他市政證券 |
| 其他 | `mmf_taxexempt_other_instrument` | 其他工具 |
| 其他 | `mmf_taxexempt_inv_company` | 投資公司 |
| 其他 | `mmf_taxexempt_tob` | 認購選擇權債券（2016-04 起） |
| 其他 | `mmf_taxexempt_other_note` | 其他票據（僅至 2016-03） |
| 指標 | `mmf_taxexempt_wam` | 加權平均到期日 |
| 指標 | `mmf_taxexempt_wal` | 加權平均存續期 |

呼叫格式：`{"source":"ici","symbols":["mf_total"]}`

---

## 資料源：`multpl`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 估值 | `sp500_pe` | S&P 500 P/E ratio（本益比） |
| 估值 | `shiller_pe` | Shiller P/E（循環調整本益比 CAPE） |
| 收益 | `sp500_earn_yield` | S&P 500 earnings yield（盈餘收益率） |
| 股息 | `sp500_div_yield` | S&P 500 dividend yield（股息收益率/殖利率） |
| 估值 | `sp500_ps` | S&P 500 price-to-sales（股價/營收比 P/S） |
| 成長 | `sp500_earn_growth` | S&P 500 earnings growth（盈餘成長率） |
| 價格 | `sp500_price` | S&P 500 historical prices（歷史價格） |

呼叫格式：`{"source":"multpl","symbols":["sp500_pe"]}`

---

## 資料源：`moea`

經濟部出口貿易統計（外銷訂單 ） (百萬美元)。Symbol 只需商品代號，回傳自動包含所有 6 個地區。

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 化工類 | `化學品` | 化學品及關聯產品 |
| 化工類 | `塑膠、橡膠及其製品` | 塑膠與橡膠製品 |
| 紡織類 | `紡織品` | 紡織品及其製品 |
| 金屬類 | `基本金屬及其製品` | 基本金屬及加工製品 |
| 電子類 | `電子產品` | 電子零組件及設備 |
| 機械類 | `機械` | 機械設備及其零件 |
| 機械類 | `電機產品` | 電機產品及其線纜 |
| 資訊通信 | `資訊與通信產品` | 資訊與通信硬體設備 |
| 運具類 | `運輸工具及其設備` | 車輛、船舶、飛機等運具 |
| 其他 | `光學器材` | 醫療及光學器材 |
| 其他 | `礦產品` | 礦產燃料及相關製品 |
| 其他 | `其他` | 未分類其他商品 |

所有查詢回傳的 DataFrame 都會包含以下 6 個地區欄位：`美國`, `日本`, `中國大陸及香港`, `東協`, `歐洲`, `其他地區`

呼叫格式：`{"source":"moea","symbols":["化學品"]}`

---

## 資料源：`zillow`

Zillow 房地產市場數據，涵蓋全美 (US)、紐約 (NY)、洛杉磯 (LA) 三個地區。

| 類別 | 代號 | 中文說明 | sub_field |
|------|------|---------|-----------|
| 房價指數 | `ZHVI` | Zillow 房價指數 (Home Value Index) | `US`, `NY`, `LA` |
| 房價預測 | `ZHVF` | Zillow 房價預測 (Home Value Forecast) | `US`, `NY`, `LA` |
| 租金指數 | `ZORI` | Zillow 租金指數 (Rental Index) | `US`, `NY`, `LA` |
| 租金預測 | `ZORF` | Zillow 租金預測 (Rental Forecast) | `US` 僅全國 |
| 存貨量 | `FSIT` | 待售房屋存貨量 (For-Sale Inventory) | `US`, `NY`, `LA` |
| 成交量 | `SALCNT` | 房屋銷售量 (Sales Count) | `US`, `NY`, `LA` |
| 市場溫度 | `MRKT` | 市場溫度指數 (Market Temperature Index) | `US`, `NY`, `LA` |
| 新屋銷售 | `NCSC` | 新建房屋銷售量 (New Construction Sales Count) | `US`, `NY`, `LA` |
| 購屋收入 | `NHIN` | 購屋所需年收入 (New Homeowner Income Needed) | `US`, `NY`, `LA` |

呼叫格式：`{"source":"zillow","symbols":["ZORI"],"sub_field":"NY"}`

**注意事項：**
- `sub_field` 預設回傳全部三個地區，指定 `US`、`NY`、`LA` 可篩選單一地區
- `ZORF` 僅有全國數據，無地區數據
- 所有數據為月頻

---

## 資料源：`optioncharts`

OptionCharts 選擇權歷史數據（日頻），支援 `frequency` 參數做週線/月線/季線重採樣。

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| 指數 | `$SPX` | S&P 500 Index |
| 指數 | `$NDX` | NASDAQ 100 |

可選 `sub_field`：`Close Price`, `Option Volume Total`, `Option Volume Put-Call Ratio`, `OI Total`, `OI Put-Call Ratio`

呼叫格式：`{"source":"optioncharts","symbols":["$SPX"]}`
**注意事項：**
- 原始數據為日頻，`frequency` 可設 `weekly`、`monthly`、`quarterly` 進行重採樣
- Volume 欄位按頻率累加（sum），其他欄位取最後交易日值（last）
- 資料範圍：2024-06-28 至今

---

## 資料源：`mql5`

| 類別 | 代號 | 中文說明 |
|------|------|---------|
| PMI | `eu_markit_composite_pmi` | 歐元區 Markit 綜合 PMI（今值/預測值/前值） |
| PMI | `eu_markit_manufacturing_pmi` | 歐元區 Markit 製造業 PMI（今值/預測值/前值） |
| PMI | `china_caixin_composite_pmi` | 中國財新綜合 PMI（今值/預測值/前值） |
| PMI | `china_manufacturing_pmi` | 中國製造業 PMI（今值/預測值/前值） |
| PMI | `china_caixin_manufacturing_pmi` | 中國財新製造業 PMI（今值/預測值/前值） |
| PMI | `japan_markit_composite_pmi` | 日本 Markit 綜合 PMI（今值/預測值/前值） |
| PMI | `brazil_markit_composite_pmi` | 巴西 Markit 綜合 PMI（今值/預測值/前值） |
| PMI | `aus_cba_composite_pmi` | 澳洲 CBA 綜合 PMI（今值/預測值/前值） |
| PMI | `us_markit_composite_pmi` | 美國 Markit 綜合 PMI（今值/預測值/前值） 看清全美經濟全貌的終極指標|
| PMI | `us_markit_manufacturing_pmi` | 美國 Markit 製造業 PMI（今值/預測值/前值）涵蓋面更廣的中小企業視角 |
| PMI | `us_ism_manufacturing_pmi` | 美國 ISM 製造業 PMI（今值/預測值/前值） 市場敏感度最高、歷史最悠久|

呼叫格式：`{"source":"mql5","symbols":["eu_markit_composite_pmi"]}`

回傳欄位：`actual`（今值）、`forecast`（預測值）、`previous`（前值），部分日期可能為 NaN

