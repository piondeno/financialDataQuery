# Financial Data Query Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python library that provides a unified `query()` interface to fetch financial data from Yahoo Finance and FRED, returning pandas DataFrames.

**Architecture:** Strategy pattern with a registry. Each data source implements `DataSourceFetcher` ABC. A global `Registry` routes `query()` calls to the correct fetcher. In-memory LRU cache reduces redundant API calls.

**Tech Stack:** Python 3.10+, pandas, yfinance, python-dotenv, requests, pytest, pytest-mock

---

## File Map

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Project metadata, dependencies, build config |
| `.gitignore` | Exclude `.env`, `__pycache__`, `.pytest_cache`, etc. |
| `.env.example` | Template for API keys |
| `src/financial_data_query/__init__.py` | Public API: `query`, `register_source`, error classes |
| `src/financial_data_query/errors.py` | Exception hierarchy |
| `src/financial_data_query/base.py` | `DataSourceFetcher` ABC |
| `src/financial_data_query/registry.py` | `Registry` singleton — register/lookup fetchers |
| `src/financial_data_query/config.py` | `get_config()` — load `.env`, read env vars |
| `src/financial_data_query/cache.py` | `QueryCache` — in-memory LRU cache |
| `src/financial_data_query/sources/__init__.py` | Auto-register built-in fetchers |
| `src/financial_data_query/sources/yahoo.py` | `YahooFetcher` using `yfinance` |
| `src/financial_data_query/sources/fred.py` | `FredFetcher` using FRED REST API |
| `tests/conftest.py` | Shared fixtures |
| `tests/test_errors.py` | Error class tests |
| `tests/test_config.py` | Config loading tests |
| `tests/test_cache.py` | LRU cache tests |
| `tests/test_registry.py` | Registry register/lookup tests |
| `tests/test_yahoo.py` | Yahoo fetcher tests (mocked) |
| `tests/test_fred.py` | FRED fetcher tests (mocked) |
| `tests/test_query.py` | End-to-end `query()` integration tests |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "financial-data-query"
version = "0.1.0"
description = "Unified financial data query library"
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.0",
    "yfinance>=0.2.30",
    "python-dotenv>=1.0",
    "requests>=2.31",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.10",
    "responses>=0.25",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.py[cod]
*.so
.env
.pytest_cache/
.mypy_cache/
dist/
build/
*.egg-info/
```

- [ ] **Step 3: Create .env.example**

```
FRED_API_KEY=your_key_here
```

- [ ] **Step 4: Create package directory structure**

```bash
mkdir -p src/financial_data_query/sources tests
```

- [ ] **Step 5: Install dependencies and verify**

```bash
pip install -e ".[dev]"
python -c "import pandas, yfinance, dotenv, requests; print('OK')"
```

Expected: prints `OK`

---

### Task 2: Error Classes

**Files:**
- Create: `src/financial_data_query/errors.py`
- Test: `tests/test_errors.py`

- [ ] **Step 1: Write test for error hierarchy**

```python
# tests/test_errors.py
import pytest
from financial_data_query.errors import (
    DataSourceError,
    DataSourceNotFoundError,
    ConfigError,
    FetchError,
)


def test_error_hierarchy():
    assert issubclass(DataSourceNotFoundError, DataSourceError)
    assert issubclass(ConfigError, DataSourceError)
    assert issubclass(FetchError, DataSourceError)
    assert issubclass(DataSourceError, Exception)


def test_data_source_not_found_error():
    err = DataSourceNotFoundError("blarg")
    assert "blarg" in str(err)
    assert isinstance(err, DataSourceError)


def test_config_error():
    err = ConfigError("missing key")
    assert "missing key" in str(err)


def test_fetch_error():
    err = FetchError("network timeout")
    assert "network timeout" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pip install -e ".[dev]" && python -m pytest tests/test_errors.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement error classes**

```python
# src/financial_data_query/errors.py
class DataSourceError(Exception):
    """Base exception for all data source errors."""
    pass


class DataSourceNotFoundError(DataSourceError):
    """Raised when the requested source name is not registered."""

    def __init__(self, source: str):
        self.source = source
        super().__init__(f"Data source '{source}' is not registered.")


class ConfigError(DataSourceError):
    """Raised when required configuration (e.g., API key) is missing."""
    pass


class FetchError(DataSourceError):
    """Raised when a data fetch request fails."""
    pass
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_errors.py -v
```

Expected: 4 tests PASS

---

### Task 3: Config Module

**Files:**
- Create: `src/financial_data_query/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write tests for config module**

```python
# tests/test_config.py
import os
from unittest import mock
from financial_data_query.config import get_config, load_env


def test_load_env_creates_no_error_without_file(tmp_path):
    result = load_env(str(tmp_path / ".env"))
    assert result is None


def test_load_env_with_existing_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("MY_KEY=abc123\n")
    load_env(str(env_file))


def test_get_config_from_env():
    with mock.patch.dict(os.environ, {"FRED_API_KEY": "test123"}):
        val = get_config("FRED_API_KEY")
        assert val == "test123"


def test_get_config_missing_returns_none():
    with mock.patch.dict(os.environ, {}, clear=True):
        val = get_config("NONEXISTENT_KEY")
        assert val is None


def test_get_config_with_default():
    with mock.patch.dict(os.environ, {}, clear=True):
        val = get_config("NONEXISTENT_KEY", default="fallback")
        assert val == "fallback"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_config.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement config module**

```python
# src/financial_data_query/config.py
import os
from pathlib import Path
from dotenv import load_dotenv as _load_dotenv


def load_env(env_path: str | Path | None = None) -> None:
    """Load .env file. If path is None, searches standard locations."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    _load_dotenv(dotenv_path=str(env_path), override=False)


def get_config(key: str, default: str | None = None) -> str | None:
    """Read a configuration value from environment variables."""
    return os.environ.get(key, default)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_config.py -v
```

Expected: 5 tests PASS

---

### Task 4: Base Abstract Class

**Files:**
- Create: `src/financial_data_query/base.py`

- [ ] **Step 1: Implement DataSourceFetcher ABC**

```python
# src/financial_data_query/base.py
from abc import ABC, abstractmethod
import pandas as pd


class DataSourceFetcher(ABC):
    """Abstract base class for all data source fetchers."""

    source_name: str = ""

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> pd.DataFrame:
        """Fetch data and return as a DataFrame with DatetimeIndex."""
        ...

    def validate_config(self) -> bool:
        """Return True if required configuration is available."""
        return True
```

- [ ] **Step 2: Verify the module imports correctly**

```bash
python -c "from financial_data_query.base import DataSourceFetcher; print('OK')"
```

Expected: prints `OK`

---

### Task 5: Registry

**Files:**
- Create: `src/financial_data_query/registry.py`
- Test: `tests/test_registry.py`

- [ ] **Step 1: Write tests for registry**

```python
# tests/test_registry.py
import pytest
import pandas as pd
from financial_data_query.registry import Registry
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class MockFetcher(DataSourceFetcher):
    source_name = "mock"

    def fetch(self, symbol, start=None, end=None, sub_field=None):
        return pd.DataFrame({"value": [1]}, index=pd.to_datetime(["2024-01-01"]))


def test_register_and_get():
    Registry.register(MockFetcher)
    fetcher = Registry.get("mock")
    assert isinstance(fetcher, MockFetcher)


def test_get_unregistered_raises():
    try:
        Registry.get("nonexistent_source_xyz")
        assert False, "Should have raised"
    except DataSourceNotFoundError as e:
        assert "nonexistent_source_xyz" in str(e)


def test_register_returns_singleton_instance():
    Registry.register(MockFetcher)
    f1 = Registry.get("mock")
    f2 = Registry.get("mock")
    assert f1 is f2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_registry.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement registry**

```python
# src/financial_data_query/registry.py
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class Registry:
    _fetchers: dict[str, DataSourceFetcher] = {}

    @classmethod
    def register(cls, fetcher_cls: type[DataSourceFetcher]) -> None:
        """Register a fetcher class. An instance is created and cached."""
        instance = fetcher_cls()
        cls._fetchers[instance.source_name] = instance

    @classmethod
    def get(cls, source: str) -> DataSourceFetcher:
        """Get a fetcher instance by source name."""
        if source not in cls._fetchers:
            raise DataSourceNotFoundError(source)
        return cls._fetchers[source]

    @classmethod
    def is_registered(cls, source: str) -> bool:
        return source in cls._fetchers

    @classmethod
    def list_sources(cls) -> list[str]:
        return list(cls._fetchers.keys())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_registry.py -v
```

Expected: 3 tests PASS

---

### Task 6: In-Memory Cache

**Files:**
- Create: `src/financial_data_query/cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: Write tests for cache**

```python
# tests/test_cache.py
import pandas as pd
from financial_data_query.cache import QueryCache


def test_cache_get_miss():
    cache = QueryCache()
    result = cache.get("yahoo", "AAPL")
    assert result is None


def test_cache_set_and_get():
    cache = QueryCache()
    df = pd.DataFrame({"close": [100]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("yahoo", "AAPL", df)
    result = cache.get("yahoo", "AAPL")
    pd.testing.assert_frame_equal(result, df)


def test_cache_clear():
    cache = QueryCache()
    df = pd.DataFrame({"close": [100]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("yahoo", "AAPL", df)
    cache.clear()
    assert cache.get("yahoo", "AAPL") is None


def test_cache_max_size_evicts_oldest():
    cache = QueryCache(max_size=3)
    df = pd.DataFrame({"v": [1]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("s", "a", df.copy())
    cache.set("s", "b", df.copy())
    cache.set("s", "c", df.copy())
    cache.set("s", "d", df.copy())
    assert cache.get("s", "a") is None
    assert cache.get("s", "d") is not None


def test_cache_with_sub_field():
    cache = QueryCache()
    df1 = pd.DataFrame({"close": [1]}, index=pd.to_datetime(["2024-01-01"]))
    df2 = pd.DataFrame({"open": [2]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("yahoo", "AAPL", df1, sub_field="close")
    cache.set("yahoo", "AAPL", df2, sub_field="open")
    result_close = cache.get("yahoo", "AAPL", sub_field="close")
    result_open = cache.get("yahoo", "AAPL", sub_field="open")
    pd.testing.assert_frame_equal(result_close, df1)
    pd.testing.assert_frame_equal(result_open, df2)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_cache.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement cache**

```python
# src/financial_data_query/cache.py
from collections import OrderedDict
import pandas as pd


class QueryCache:
    """In-memory LRU cache for query results."""

    def __init__(self, max_size: int = 128):
        self._cache: OrderedDict[tuple[str, str, str | None, str | None, str | None], pd.DataFrame] = OrderedDict()
        self._max_size = max_size

    def _key(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> tuple[str, str, str | None, str | None, str | None]:
        return (source, symbol, start, end, sub_field)

    def get(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> pd.DataFrame | None:
        key = self._key(source, symbol, start, end, sub_field)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(
        self,
        source: str,
        symbol: str,
        df: pd.DataFrame,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> None:
        key = self._key(source, symbol, start, end, sub_field)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = df
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_cache.py -v
```

Expected: 5 tests PASS

---

### Task 7: Yahoo Finance Fetcher

**Files:**
- Create: `src/financial_data_query/sources/__init__.py` (placeholder)
- Create: `src/financial_data_query/sources/yahoo.py`
- Test: `tests/test_yahoo.py`

- [ ] **Step 1: Write tests for YahooFetcher (mocked)**

```python
# tests/test_yahoo.py
import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.yahoo import YahooFetcher


class TestYahooFetcher:
    @pytest.fixture
    def fetcher(self):
        return YahooFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "yahoo"

    def test_validate_config_always_true(self, fetcher):
        assert fetcher.validate_config() is True

    def test_fetch_returns_dataframe(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0, 151.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            result = fetcher.fetch("AAPL")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_fetch_with_date_range(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0]},
            index=pd.to_datetime(["2024-06-01"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            fetcher.fetch("AAPL", start="2024-06-01", end="2024-06-30")
            MockTicker.return_value.history.assert_called_once_with(
                start="2024-06-01", end="2024-06-30"
            )

    def test_fetch_with_sub_field(self, fetcher):
        mock_df = pd.DataFrame(
            {"Open": [149.0], "Close": [150.0], "Volume": [1000]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            result = fetcher.fetch("AAPL", sub_field="open")
        assert list(result.columns) == ["Open"]

    def test_fetch_empty_result_raises(self, fetcher):
        empty_df = pd.DataFrame()
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = empty_df
            with pytest.raises(Exception):
                fetcher.fetch("INVALID_SYMBOL")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_yahoo.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement YahooFetcher**

```python
# src/financial_data_query/sources/yahoo.py
import pandas as pd
import yfinance as yf
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


_YAHOO_COLUMN_MAP = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
    "adjclose": "Adj Close",
}


class YahooFetcher(DataSourceFetcher):
    source_name = "yahoo"

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        kwargs = {}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end

        df = ticker.history(**kwargs)

        if df.empty:
            raise FetchError(f"No data returned for Yahoo symbol '{symbol}'")

        if sub_field:
            col = _YAHOO_COLUMN_MAP.get(sub_field.lower())
            if col and col in df.columns:
                df = df[[col]]
            elif sub_field.lower() in [c.lower() for c in df.columns]:
                match_col = [c for c in df.columns if c.lower() == sub_field.lower()][0]
                df = df[[match_col]]

        return df
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_yahoo.py -v
```

Expected: 6 tests PASS

---

### Task 8: FRED Fetcher

**Files:**
- Create: `src/financial_data_query/sources/fred.py`
- Test: `tests/test_fred.py`

- [ ] **Step 1: Write tests for FredFetcher (mocked)**

```python
# tests/test_fred.py
import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.fred import FredFetcher
from financial_data_query.errors import ConfigError, FetchError


class TestFredFetcher:
    @pytest.fixture
    def fetcher(self):
        return FredFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "fred"

    def test_validate_config_missing_key(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value=None):
            assert fetcher.validate_config() is False

    def test_validate_config_with_key(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="abc123"):
            assert fetcher.validate_config() is True

    def test_fetch_without_api_key_raises(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value=None):
            with pytest.raises(ConfigError):
                fetcher.fetch("GDP")

    def test_fetch_returns_dataframe(self, fetcher):
        mock_response = {
            "observations": [
                ["2024-01-01", "27000.0"],
                ["2024-04-01", "27500.0"],
            ]
        }
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="test_key"):
            with mock.patch("financial_data_query.sources.fred.requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_response
                result = fetcher.fetch("GDP")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_fetch_with_date_range(self, fetcher):
        mock_response = {"observations": [["2024-06-01", "100.0"]]}
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="test_key"):
            with mock.patch("financial_data_query.sources.fred.requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_response
                fetcher.fetch("GDP", start="2024-06-01", end="2024-12-31")
                call_url = mock_get.call_args[0][0]
                assert "sortOrder=asc" in call_url

    def test_fetch_api_error_raises(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="test_key"):
            with mock.patch("financial_data_query.sources.fred.requests.get") as mock_get:
                mock_get.return_value.status_code = 403
                with pytest.raises(FetchError):
                    fetcher.fetch("GDP")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_fred.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement FredFetcher**

```python
# src/financial_data_query/sources/fred.py
import requests
import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.config import get_config
from financial_data_query.errors import ConfigError, FetchError


_FRED_BASE_URL = "https://api.stlouisfed.org/fred/v1/series/observations"


class FredFetcher(DataSourceFetcher):
    source_name = "fred"

    def validate_config(self) -> bool:
        return get_config("FRED_API_KEY") is not None

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> pd.DataFrame:
        api_key = get_config("FRED_API_KEY")
        if not api_key:
            raise ConfigError("FRED_API_KEY is not set. Set it in your environment or .env file.")

        params = {
            "series_id": symbol,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "asc",
        }
        if start:
            params["sort_order"] = "asc"
            params["start_date"] = start
        if end:
            params["end_date"] = end

        resp = requests.get(_FRED_BASE_URL, params=params, timeout=30)

        if resp.status_code != 200:
            raise FetchError(f"FRED API error ({resp.status_code}): {resp.text[:200]}")

        data = resp.json()
        observations = data.get("observations", [])

        if not observations:
            raise FetchError(f"No data returned for FRED series '{symbol}'")

        df = pd.DataFrame(observations, columns=["date", "value"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        return df
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_fred.py -v
```

Expected: 7 tests PASS

---

### Task 9: Sources Auto-Registration & Public API

**Files:**
- Modify: `src/financial_data_query/sources/__init__.py`
- Create: `src/financial_data_query/__init__.py`
- Test: `tests/test_query.py`

- [ ] **Step 1: Write integration tests for query()**

```python
# tests/test_query.py
import pytest
import pandas as pd
from unittest import mock
from financial_data_query import query, register_source, list_sources
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class DummyFetcher(DataSourceFetcher):
    source_name = "dummy"

    def fetch(self, symbol, start=None, end=None, sub_field=None):
        return pd.DataFrame(
            {"value": [42.0]},
            index=pd.to_datetime(["2024-01-01"]),
        )


def test_list_sources_includes_builtins():
    sources = list_sources()
    assert "yahoo" in sources
    assert "fred" in sources


def test_query_with_dummy_source():
    register_source(DummyFetcher)
    df = query("dummy", "TEST")
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["value"] == 42.0


def test_query_unregistered_source_raises():
    with pytest.raises(DataSourceNotFoundError):
        query("nonexistent_xyz", "TEST")


def test_query_uses_cache():
    call_count = 0

    class CountingFetcher(DataSourceFetcher):
        source_name = "counting"

        def fetch(self, symbol, start=None, end=None, sub_field=None):
            nonlocal call_count
            call_count += 1
            return pd.DataFrame(
                {"value": [1.0]},
                index=pd.to_datetime(["2024-01-01"]),
            )

    register_source(CountingFetcher)
    query("counting", "A")
    query("counting", "A")
    assert call_count == 1, "Second call should hit cache"

    query("counting", "A", use_cache=False)
    assert call_count == 2, "use_cache=False should bypass cache"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_query.py -v
```

Expected: FAIL — functions not available

- [ ] **Step 3: Implement sources __init__.py with auto-registration**

```python
# src/financial_data_query/sources/__init__.py
from financial_data_query.registry import Registry
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.sources.fred import FredFetcher

Registry.register(YahooFetcher)
Registry.register(FredFetcher)
```

- [ ] **Step 4: Implement public API __init__.py**

```python
# src/financial_data_query/__init__.py
import pandas as pd
from financial_data_query.config import load_env
from financial_data_query.registry import Registry
from financial_data_query.cache import QueryCache
from financial_data_query.errors import DataSourceError, DataSourceNotFoundError
from financial_data_query.base import DataSourceFetcher

load_env()

_cache = QueryCache(max_size=128)


def query(
    source: str,
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    sub_field: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Query financial data from a registered source.

    Args:
        source: Data source name (e.g., 'yahoo', 'fred')
        symbol: Ticker or series identifier
        start: Start date (YYYY-MM-DD), optional
        end: End date (YYYY-MM-DD), optional
        sub_field: Specific column to return, optional
        use_cache: Use in-memory cache, default True

    Returns:
        pandas DataFrame with DatetimeIndex
    """
    _import_sources()

    if use_cache:
        cached = _cache.get(source, symbol, start, end, sub_field)
        if cached is not None:
            return cached

    fetcher = Registry.get(source)
    df = fetcher.fetch(symbol, start=start, end=end, sub_field=sub_field)

    if use_cache:
        _cache.set(source, symbol, df, start=start, end=end, sub_field=sub_field)

    return df


def register_source(fetcher_cls: type[DataSourceFetcher]) -> None:
    """Register a custom data source fetcher class."""
    Registry.register(fetcher_cls)


def list_sources() -> list[str]:
    """List all registered data source names."""
    _import_sources()
    return Registry.list_sources()


def clear_cache() -> None:
    """Clear the in-memory query cache."""
    _cache.clear()


def _import_sources() -> None:
    from financial_data_query import sources  # noqa: F401
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_query.py -v
```

Expected: 4 tests PASS

---

### Task 10: Full Test Suite Verification

**Files:**
- Run: all tests

- [ ] **Step 1: Run the complete test suite**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS (approximately 24+ tests across all files)

- [ ] **Step 2: Verify the library works with a smoke test**

```bash
python -c "
from financial_data_query import list_sources, clear_cache
print('Sources:', list_sources())
clear_cache()
print('Cache cleared: OK')
"
```

Expected: prints `Sources: ['yahoo', 'fred']` and `Cache cleared: OK`

---

## Self-Review Notes

**Spec coverage:**
- [x] Unified `query()` function with all parameters
- [x] `DataSourceFetcher` ABC in `base.py`
- [x] `Registry` in `registry.py`
- [x] Yahoo Finance fetcher with yfinance
- [x] FRED fetcher with REST API
- [x] Error hierarchy: `DataSourceError`, `DataSourceNotFoundError`, `ConfigError`, `FetchError`
- [x] In-memory LRU cache with max_size=128, `clear()`, `use_cache=False`
- [x] Config from env vars + `.env` file via python-dotenv
- [x] `.env.example` template
- [x] Tests: mocked unit tests, cache tests, integration tests

**Placeholder scan:** No TBDs, no TODOs, no vague instructions. All code blocks are complete.

**Type consistency:** `fetch()` signature matches across ABC, YahooFetcher, FredFetcher, and all mocks. Cache key tuple is consistent. Error classes follow the hierarchy.

**Scope check:** Single focused library — no decomposition needed.
