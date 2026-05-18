import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.tw_ndc import NdcFetcher, TwEcoFetcher, TwPmiFetcher
from financial_data_query.errors import FetchError


class TestTwEcoFetcher:
    @pytest.fixture
    def fetcher(self):
        return TwEcoFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "tw_eco"

    def test_base_url(self, fetcher):
        assert "eco" in fetcher.base_url


class TestTwPmiFetcher:
    @pytest.fixture
    def fetcher(self):
        return TwPmiFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "tw_pmi"

    def test_base_url(self, fetcher):
        assert "PMI" in fetcher.base_url


class TestNdcParseTable:
    @pytest.fixture
    def fetcher(self):
        return TwEcoFetcher()

    def test_parse_table_basic(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>擴散指數</th><th>景氣指標</th></tr>
          <tr><td>2024-01</td><td>50.1</td><td>102.3</td></tr>
          <tr><td>2024-02</td><td>51.2</td><td>103.4</td></tr>
        </table>
        """
        df = fetcher._parse_table(html)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert isinstance(df.index, pd.DatetimeIndex)
        assert "擴散指數" in df.columns
        assert "景氣指標" in df.columns

    def test_parse_table_filters_symbol(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>擴散指數</th><th>景氣指標</th></tr>
          <tr><td>2024-01</td><td>50.1</td><td>102.3</td></tr>
          <tr><td>2024-02</td><td>51.2</td><td>103.4</td></tr>
        </table>
        """
        df = fetcher._parse_table(html, symbol="擴散指數")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["擴散指數"]

    def test_parse_table_symbol_not_found_raises(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>擴散指數</th></tr>
          <tr><td>2024-01</td><td>50.1</td></tr>
        </table>
        """
        with pytest.raises(FetchError, match="找不到"):
            fetcher._parse_table(html, symbol="不存在的指標")

    def test_parse_table_empty_raises(self, fetcher):
        html = "<table><tr><th>月份</th></tr></table>"
        with pytest.raises(FetchError):
            fetcher._parse_table(html, symbol="任何指標")

    def test_parse_table_date_filtering(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>擴散指數</th></tr>
          <tr><td>2020-01</td><td>45.0</td></tr>
          <tr><td>2022-06</td><td>50.0</td></tr>
          <tr><td>2024-12</td><td>55.0</td></tr>
        </table>
        """
        df = fetcher._parse_table(html, symbol="擴散指數", start="2021-01-01", end="2023-12-31")
        assert len(df) == 1
        assert df.index[0].year == 2022

    def test_parse_table_with_empty_rows(self, fetcher):
        html = """
        <table>
          <tr><th>月份</th><th>擴散指數</th><th>景氣指標</th></tr>
          <tr><td>2020-01</td><td></td><td></td></tr>
          <tr><td>2020-02</td><td></td><td></td></tr>
          <tr><td>2024-01</td><td>50.1</td><td>102.3</td></tr>
          <tr><td>2024-02</td><td>51.2</td><td>103.4</td></tr>
        </table>
        """
        df = fetcher._parse_table(html, symbol="擴散指數")
        assert len(df) == 2
        assert df.index[0].year == 2024


class TestNdcRegistration:
    def test_tw_eco_is_registered(self):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("tw_eco")

    def test_tw_pmi_is_registered(self):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("tw_pmi")

    def test_tw_eco_fetcher_inherits_base(self):
        from financial_data_query.base import DataSourceFetcher
        fetcher = TwEcoFetcher()
        assert isinstance(fetcher, DataSourceFetcher)

    def test_tw_pmi_fetcher_inherits_base(self):
        from financial_data_query.base import DataSourceFetcher
        fetcher = TwPmiFetcher()
        assert isinstance(fetcher, DataSourceFetcher)


class TestNdcFetchFlow:
    @pytest.fixture
    def fetcher(self):
        return TwEcoFetcher()

    def test_fetch_calls_driver_methods(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.page_source = """
        <table>
          <tr><th>月份</th><th>擴散指數</th></tr>
          <tr><td>2024-01</td><td>50.1</td></tr>
        </table>
        """

        with mock.patch("financial_data_query.sources.tw_ndc.uc", mock.MagicMock()):
            with mock.patch("financial_data_query.sources.tw_ndc.WebDriverWait", mock.MagicMock()):
                with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
                    with mock.patch.object(fetcher, "_interact_page", return_value=mock_driver.page_source):
                        result = fetcher.fetch("擴散指數")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "擴散指數" in result.columns
        mock_driver.quit.assert_called_once()

    def test_fetch_with_date_range(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.page_source = """
        <table>
          <tr><th>月份</th><th>擴散指數</th></tr>
          <tr><td>2020-01</td><td>45.0</td></tr>
          <tr><td>2024-06</td><td>50.0</td></tr>
          <tr><td>2024-12</td><td>55.0</td></tr>
        </table>
        """

        with mock.patch("financial_data_query.sources.tw_ndc.uc", mock.MagicMock()):
            with mock.patch("financial_data_query.sources.tw_ndc.WebDriverWait", mock.MagicMock()):
                with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
                    with mock.patch.object(fetcher, "_interact_page", return_value=mock_driver.page_source):
                        result = fetcher.fetch("擴散指數", start="2024-01-01", end="2024-10-31")

        assert len(result) == 1
        assert result.index[0].month == 6

    def test_fetch_no_table_raises(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.page_source = "<html><body>No table here</body></html>"

        with mock.patch("financial_data_query.sources.tw_ndc.uc", mock.MagicMock()):
            with mock.patch("financial_data_query.sources.tw_ndc.WebDriverWait", mock.MagicMock()):
                with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
                    with mock.patch.object(fetcher, "_interact_page", return_value=mock_driver.page_source):
                        with pytest.raises(FetchError):
                            fetcher.fetch("擴散指數")

    def test_fetch_closes_browser_on_error(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.get.side_effect = Exception("Connection failed")

        with mock.patch("financial_data_query.sources.tw_ndc.uc", mock.MagicMock()):
            with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
                with pytest.raises(FetchError):
                    fetcher.fetch("擴散指數")

        mock_driver.quit.assert_called_once()

    def test_fetch_missing_dependency_raises(self):
        with mock.patch("financial_data_query.sources.tw_ndc.uc", None):
            fetcher = TwEcoFetcher()
            with pytest.raises(FetchError, match="undetected-chromedriver"):
                fetcher.fetch("擴散指數")