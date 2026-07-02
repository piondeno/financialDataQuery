# AkShare (`"akshare"`)

AkShare A股歷史行情、BDI（波罗的海干散货指数）等數據。免 API key，無需瀏覽器。

## 安裝

```bash
pip install akshare
```

## 支援商品

| Symbol | 說明 | frequency | sub_field |
|--------|------|-----------|-----------|
| `bdi` | BDI 波罗的海干散货指數 | `"daily"`, `"weekly"`, `"monthly"` | `"value"`, `"涨跌幅"`, `"近3月漲跌幅"`, ... |
| `wci` | Drewry 世界集装箱指數 (WCI) | — | `"value"` |
| A股代號（如 `"000001"`, `"600519"`） | A股歷史行情 | `"daily"`, `"weekly"`, `"monthly"` | 參見下方欄位說明 |
| `china_manufacturing_pmi` | 財新中國製造業 PMI | — | 所有回傳欄位 |
| `china_services_pmi` | 財新中國服務業 PMI | — | 所有回傳欄位 |
| `euro_manufacturing_pmi` | 歐元區製造業 PMI 初值 | — | 所有回傳欄位 |
| `usa_ism_pmi` | 美國 ISM 製造業 PMI | — | 所有回傳欄位 |

## 使用範例

```python
from financial_data_query import query

# BDI 指數週線
result = query("akshare", "bdi", frequency="weekly")

# Drewry WCI 世界集装箱指數
result = query("akshare", "wci")

# A股收盤價
result = query("akshare", "600519", sub_field="close")

# 查詢財新中國製造業 PMI（2014-至今）
result = query("akshare", "china_manufacturing_pmi")

# 查詢財新中國服務業 PMI（2014-至今）
result = query("akshare", "china_services_pmi")

# 查詢歐元區製造業 PMI（2008-至今，含今值/預測值/前值）
result = query("akshare", "euro_manufacturing_pmi")

# 批次查詢所有 PMI
query("akshare", ["china_manufacturing_pmi", "china_services_pmi", 
                  "euro_manufacturing_pmi", "usa_ism_pmi"])
```

## A股回傳欄位

`date`, `open`, `high`, `low`, `close`, `volume`, `amount`, `amplitude`, `pct_change`, `change`, `turnover_rate`

| 欄位 | 說明 |
|------|------|
| `open` | 開盤價 |
| `high` | 最高價 |
| `low` | 最低價 |
| `close` | 收盤價 |
| `volume` | 成交量 |
| `amount` | 成交金額 |
| `amplitude` | 振幅 |
| `pct_change` | 漲跌幅 (%) |
| `change` | 涨跌額 |
| `turnover_rate` | 換手率 (%) |

## WCI 回傳欄位

資料範圍：2016-03 ~ 至今，每週更新。Drewry World Container Index (WCI) 衡量跨洋航線集裝箱運費變化。

| 欄位 | 說明 |
|------|------|
| `date` | 週末日期 |
| `value` | WCI 指數值 |

```python
# 查詢 Drewry WCI
result = query("akshare", "wci")
# {'date': '2016-03-10', 'value': 700.57}

# 指定日期範圍（2024 年全年）
result = query("akshare", "wci", start="2024-01-01", end="2024-12-31")
```

## BDI 回傳欄位

`date`, `value`, `涨跌幅`, `近3月涨跌幅`, `近6月涨跌幅`, `近1年漲跌幅`, `近2年漲跌幅`, `近3年漲跌幅`

| 欄位 | 說明 |
|------|------|
| `value` | BDI 指數最新值 |
| `涨跌幅` | 當日漲跌幅 (%) |
| `近3月涨跌幅` | 近3個月漲跌幅 (%) |
| `近6月涨跌幅` | 近6個月漲跌幅 (%) |
| `近1年涨跌幅` | 近1年漲跌幅 (%) |
| `近2年涨跌幅` | 近2年漲跌幅 (%) |
| `近3年涨跌幅` | 近3年漲跌幅 (%) |

## PMI 回傳欄位

### china_manufacturing_pmi（財新中國製造業 PMI）

資料範圍：2014-04 ~ 至今，每月更新。僅涵蓋**製造業**。

| 欄位 | 說明 |
|------|------|
| `date` | 月份月末 |
| `制造业pmi` | 製造業 PMI 數值（50 為榮枯線） |
| `change_pct` | 較上月變化值 |

```python
# 查詢財新中國製造業 PMI
result = query("akshare", "china_manufacturing_pmi")
# {'date': '2014-04-30', '制造业pmi': 48.1, 'change_pct': 0.0}
```

### china_services_pmi（財新中國服務業 PMI）

資料範圍：2014-04 ~ 至今，每月更新。僅涵蓋**服務業**。

| 欄位 | 說明 |
|------|------|
| `date` | 月份月末 |
| `服务业pmi` | 服務業 PMI 數值（50 為榮枯線） |
| `change_pct` | 較上月變化值 |

```python
# 查詢財新中國服務業 PMI  
result = query("akshare", "china_services_pmi")
# {'date': '2014-04-30', '服务业pmi': 51.4, 'change_pct': 0.0}
```

### euro_manufacturing_pmi（歐元區製造業 PMI）

資料範圍：2008-02 ~ 至今，每月更新。歐元區製造業採購經理人指數初值。

| 欄位 | 說明 |
|------|------|
| `date` | 發布日期 |
| `商品` | 指標名稱（固定為"欧元区制造业 PMI 初值"） |
| `今值` | 實際公布數值 |
| `预测值` | 市場預測值 |
| `前值` | 上月修正後數值 |

```python
# 查詢歐元區製造業 PMI
result = query("akshare", "euro_manufacturing_pmi")
# {'date': '2008-02-22', '商品': '欧元区制造业PMI初值', '今值': 52.3, ...}
```

### usa_ism_pmi（美國 ISM 製造業 PMI）

資料範圍：1970-01 ~ 至今，每月更新。美國供應管理協會 (ISM) 製造業指數。

| 欄位 | 說明 |
|------|------|
| `date` | 發布日期 |
| `商品` | 指標名稱（固定為"美国ISM制造业PMI报告"） |
| `今值` | 實際公布數值 |
| `预测值` | 市場預測值 |
| `前值` | 上月修正後數值 |

```python
# 查詢美國 ISM 製造業 PMI（歷史最長，1970-至今）
result = query("akshare", "usa_ism_pmi")
# {'date': '1970-01-01', '商品': '美国ISM制造业PMI报告', '今值': 52.0, ...}
```

## 注意事項

- A股查詢支援前复权（`adjust=""`）
- BDI 週線/月線自動降頻：`weekly` → 周均價，`monthly` → 月均價
- 內建自動重試機制（3次），每次間隔 2~10 秒
