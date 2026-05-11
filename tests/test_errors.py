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
