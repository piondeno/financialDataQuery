# NDC 台湾经济指标资料来源设计

**日期:** 2026-05-15
**状态:** 已批准

## 总览

新增 `TwEcoFetcher` 和 `TwPmiFetcher` 两个资料来源，透过 undetected_chromedriver 操作 NDC 台湾景气指标网站，抓取 HTML 表格资料并回传 pandas DataFrame。

## 架构

### 类设计

```
NdcFetcher (abstract, DataSourceFetcher)
├── base_url: str              # 子类覆写
├── source_name: str           # 子类覆写
├── _create_driver()
├── _interact_page(driver)
├── _parse_table(driver) -> pd.DataFrame
└── fetch() -> pd.DataFrame

TwEcoFetcher (NdcFetcher)
├── base_url = "https://index.ndc.gov.tw/n/zh_tw/data/eco#/"
└── source_name = "tw_eco"

TwPmiFetcher (NdcFetcher)
├── base_url = "https://index.ndc.gov.tw/n/zh_tw/data/PMI#/"
└── source_name = "tw_pmi"
```

### 新增/修改档案

| 档案 | 类型 | 说明 |
|------|------|------|
| `src/financial_data_query/sources/tw_ndc.py` | 新增 | NdcFetcher 基类 + 两个子类 |
| `src/financial_data_query/sources/__init__.py` | 修改 | 注册 TwEcoFetcher, TwPmiFetcher |
| `tests/test_tw_ndc.py` | 新增 | 单元测试 |

### 使用方式

```python
import financial_data_query as fdq

# 基本查询 - 获取该指标全部历史数据
df = fdq.query("tw_eco", "扩散指数-未经季节调整")

# 指定日期范围过滤
df = fdq.query("tw_eco", "扩散指数-未经季节调整", start="2020-01-01", end="2024-12-31")

# PMI 数据
df = fdq.query("tw_pmi", "制造业PMI")
```

## 核心流程

1. 建立 headless Chrome 浏览器实例（undetected_chromedriver）
2. 导航至对应 `base_url`
3. 等待页面加载完成
4. 点击 `#select_all_1` 全选所有指标
5. 点击滑桿左句柄，发送 `PageDown` ×10 扩大年度范围
6. 依序点击 `1月`(起始) → `12月`(终止) → `表格` 视图
7. 读取页面 `<table>` 元素，解析为 DataFrame
8. 按 `symbol` 过滤列，回传单列 DataFrame
9. 若有 `start`/`end`，按日期索引过滤
10. 关闭浏览器，回传 DataFrame

## 参数对应

### symbol 参数

- `symbol` 直接对应表格列的中文标题文字
- 匹配后回传该列的 Series（包装在 DataFrame 中）
- 若找不到对应列，抛出 `FetchError` 并列出可用的列名

### start / end 参数

- 网页操作固定获取全部可用数据
- `start`/`end` 在 DataFrame 解析后作为日期过滤条件
- 未指定时回传全部数据

### frequency / sub_field 参数

- 目前不支持，传入时忽略

## 表格解析

NDC 表格结构：
- 第一列：年月（如 `2024/01`）
- 其余列：各指标的数值，列标题为中文名称

解析步骤：
1. 读取 `<table>` 的 HTML 内容
2. 用 `pd.read_html()` 解析为 DataFrame
3. 第一列转为 `DatetimeIndex`（格式 `%Y/%m`）
4. 数值列转为 numeric 类型
5. 按 `symbol` 匹配列名，回传对应列

## 错误处理

| 场景 | 行为 |
|------|------|
| Chrome 浏览器未安装 | `FetchError` |
| Selenium 未安装 | 注册时跳过（ImportError） |
| 页面加载超时 | `FetchError` |
| 找不到表格元素 | `FetchError` |
| 表格为空 | `FetchError` |
| symbol 不在表格列中 | `FetchError`（列出可用列名） |

## 依赖管理

复用 `stooq` optional dependency 组中的 `undetected-chromedriver` + `selenium`。

## 测试策略

- 单元测试：mock Selenium WebDriver，测试表格 HTML 解析、symbol 过滤、日期过滤
- 不写整合测试（需要真实浏览器环境）
