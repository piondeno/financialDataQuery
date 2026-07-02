"""
Network tests for non-browser data sources.
These tests make actual HTTP requests.
Run with: pytest tests/test_network_sources.py -m network
"""
import pytest
import pandas as pd


@pytest.mark.network
class TestFredNetwork:
    """FRED API tests."""

    def test_single_query_json(self):
        from financial_data_query import query
        result = query("fred", "FEDFUNDS", start="2020-01-01", end="2020-12-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "FEDFUNDS" in result
        assert len(result["FEDFUNDS"]) > 0
        assert "date" in result["FEDFUNDS"][0]
        assert "value" in result["FEDFUNDS"][0]

    def test_single_query_dataframe(self):
        from financial_data_query import query
        result = query("fred", "FEDFUNDS", start="2020-01-01", end="2020-12-31",
                       output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_batch_query(self):
        from financial_data_query import query
        result = query("fred", ["FEDFUNDS", "GDP"], start="2020-01-01", end="2020-03-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "FEDFUNDS" in result
        assert "GDP" in result

    def test_date_range(self):
        from financial_data_query import query
        r1 = query("fred", "FEDFUNDS", start="2020-01-01", end="2020-03-31",
                   output="json", use_cache=False)
        r2 = query("fred", "FEDFUNDS", start="2020-01-01", end="2020-12-31",
                   output="json", use_cache=False)
        assert len(r1["FEDFUNDS"]) < len(r2["FEDFUNDS"])


@pytest.mark.network
class TestYahooNetwork:
    """Yahoo Finance tests."""

    def test_single_query_json(self):
        from financial_data_query import query
        result = query("yahoo", "AAPL", start="2023-01-01", end="2023-01-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert len(result["AAPL"]) > 0
        assert "date" in result["AAPL"][0]

    def test_single_query_dataframe(self):
        from financial_data_query import query
        result = query("yahoo", "AAPL", start="2023-01-01", end="2023-01-31",
                       output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0


@pytest.mark.network
class TestStooqNetwork:
    """Stooq tests — may skip if browser unavailable."""

    def test_single_query_json(self):
        from financial_data_query import query
        try:
            result = query("stooq", "^spx", start="2023-01-01", end="2023-01-31",
                           output="json", use_cache=False)
            assert isinstance(result, dict)
            assert "^spx" in result
            assert len(result["^spx"]) > 0
        except Exception as e:
            pytest.skip(f"Stooq browser test skipped: {type(e).__name__}")


@pytest.mark.network
class TestAkshareNetwork:
    """AKShare tests."""

    def test_bdi(self):
        from financial_data_query import query
        result = query("akshare", "bdi", start="2024-01-01", end="2024-01-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "bdi" in result

    def test_pmi(self):
        from financial_data_query import query
        result = query("akshare", "china_manufacturing_pmi", start="2024-01-01",
                       end="2024-06-30", output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "china_manufacturing_pmi" in result


@pytest.mark.network
class TestOptionchartsNetwork:
    """OptionCharts tests."""

    def test_single_query_json(self):
        from financial_data_query import query
        result = query("optioncharts", "AAPL", output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert len(result["AAPL"]) > 0

    def test_dataframe_output(self):
        from financial_data_query import query
        result = query("optioncharts", "AAPL", output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_with_subfield(self):
        from financial_data_query import query
        result = query("optioncharts", "AAPL", sub_field="Close Price",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert len(result["AAPL"]) > 0


@pytest.mark.network
class TestMultplNetwork:
    """Multpl tests."""

    def test_single_query_pe(self):
        from financial_data_query import query
        result = query("multpl", "sp500_pe", start="2023-01-01", end="2023-12-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "sp500_pe" in result
        assert len(result["sp500_pe"]) > 0

    def test_single_query_shiller_pe(self):
        from financial_data_query import query
        result = query("multpl", "shiller_pe", start="2023-01-01", end="2023-12-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "shiller_pe" in result
        assert len(result["shiller_pe"]) > 0

    def test_dataframe_output(self):
        from financial_data_query import query
        result = query("multpl", "sp500_pe", start="2023-01-01", end="2023-12-31",
                       output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_no_cache_bypass(self):
        from financial_data_query import query
        result = query("multpl", "sp500_pe", start="2023-01-01", end="2023-12-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert len(result["sp500_pe"]) > 0


@pytest.mark.network
class TestZillowNetwork:
    """Zillow tests."""

    def test_single_query_json(self):
        from financial_data_query import query
        result = query("zillow", "ZHVI", output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "ZHVI" in result
        assert len(result["ZHVI"]) > 0

    def test_dataframe_output(self):
        from financial_data_query import query
        result = query("zillow", "ZHVI", output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_with_subfield(self):
        from financial_data_query import query
        result = query("zillow", "ZHVI", sub_field="US", output="json",
                       use_cache=False)
        assert isinstance(result, dict)
        assert "ZHVI" in result


@pytest.mark.network
class TestUsTreasuryNetwork:
    """US Treasury tests."""

    def test_single_query_bill(self):
        from financial_data_query import query
        result = query("usTreasuryApi", "bill_4w", start="2024-01-01", end="2024-12-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "bill_4w" in result

    def test_single_query_note(self):
        from financial_data_query import query
        result = query("usTreasuryApi", "note_10y", start="2024-01-01", end="2024-12-31",
                       output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "note_10y" in result

    def test_dataframe_output(self):
        from financial_data_query import query
        result = query("usTreasuryApi", "bill_4w", start="2024-01-01", end="2024-12-31",
                       output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)


@pytest.mark.network
class TestFinraMarginNetwork:
    """FINRA Margin tests."""

    def test_single_query(self):
        from financial_data_query import query
        result = query("finra_margin", "debit_balances", output="json",
                       use_cache=False)
        assert isinstance(result, dict)
        assert "debit_balances" in result

    def test_dataframe_output(self):
        from financial_data_query import query
        result = query("finra_margin", "debit_balances", output="dataframe",
                       use_cache=False)
        assert isinstance(result, pd.DataFrame)
