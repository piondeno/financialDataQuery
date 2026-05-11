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
