import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.moeab import MoeaFetcher, REGION_NAMES
from financial_data_query.errors import FetchError


class TestMoeaFetcher:
    @pytest.fixture
    def fetcher(self):
        return MoeaFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "moea"

    def test_base_url(self, fetcher):
        assert "moea.gov.tw" in fetcher.base_url
        assert "InvestigateBA" in fetcher.base_url


class TestMoeaSymbolParsing:
    """Test commodity-only symbol parsing (not commodity_region)."""

    @pytest.fixture
    def fetcher(self):
        return MoeaFetcher()

    @pytest.mark.parametrize("commodity", [
        "化學品", "塑膠、橡膠及其製品", "紡織品", "基本金屬及其製品",
        "電子產品", "機械", "電機產品", "資訊與通信產品",
        "運輸工具及其設備", "光學器材", "礦產品", "其他",
    ])
    def test_parse_commodity_valid(self, fetcher, commodity):
        result = fetcher._parse_commodity(commodity)
        assert result == commodity

    def test_parse_commodity_invalid_raises(self, fetcher):
        with pytest.raises(FetchError, match="找不到商品代號"):
            fetcher._parse_commodity("不存在的商品")


class TestMoeaParseTableHtml:
    """Test _parse_table_html using real MOEA HTML from /tmp/moea_panel.html."""

    @pytest.fixture
    def fetcher(self):
        return MoeaFetcher()

    @pytest.fixture
    def real_html(self):
        try:
            with open("/tmp/moea_panel.html", "r") as f:
                return f.read()
        except FileNotFoundError:
            pytest.skip("Real MOEA HTML not available at /tmp/moea_panel.html")

    def test_parse_table_real_data(self, fetcher, real_html):
        df = fetcher._parse_table_html(real_html)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 500
        assert len(df.columns) == 72
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_parse_table_date_range(self, fetcher, real_html):
        df = fetcher._parse_table_html(real_html)
        assert df.index.min().year == 1984
        assert df.index.max().year == 2026
        assert df.index.min().month == 9

    def test_parse_table_has_all_symbols(self, fetcher, real_html):
        df = fetcher._parse_table_html(real_html)
        for comm in ["化學品", "電子產品", "機械"]:
            for region in REGION_NAMES:
                symbol = f"{comm}_{region}"
                assert symbol in df.columns

    def test_parse_table_numeric_values(self, fetcher, real_html):
        df = fetcher._parse_table_html(real_html)
        for col in df.columns:
            assert pd.api.types.is_float_dtype(df[col])

    def test_parse_table_sorted_by_date(self, fetcher, real_html):
        df = fetcher._parse_table_html(real_html)
        assert df.index.is_monotonic_increasing


class TestMoeaFetchFlow:
    """Test fetch() returns all regions as columns."""

    @pytest.fixture
    def mock_parsed_df(self):
        dates = pd.date_range("1984-09", periods=3, freq="ME")
        return pd.DataFrame({
            "化學品_美國": [17.0, 18.0, 20.0],
            "化學品_日本": [15.0, 16.0, 18.0],
            "化學品_中國大陸及香港": [10.0, 12.0, 14.0],
            "化學品_東協": [8.0, 9.0, 10.0],
            "化學品_歐洲": [5.0, 6.0, 7.0],
            "化學品_其他地區": [2.0, 3.0, 4.0],
        }, index=dates)

    def test_fetch_returns_all_regions_as_columns(self, mock_parsed_df):
        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_parsed_df):
            result = fetcher.fetch("化學品")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        # Columns should be region names only (without commodity prefix)
        for region in REGION_NAMES:
            assert region in result.columns
        # Should NOT have "value" column or "化學品_美國" column
        assert "value" not in result.columns
        assert "化學品_美國" not in result.columns

    def test_fetch_columns_are_region_names(self, mock_parsed_df):
        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_parsed_df):
            result = fetcher.fetch("化學品")

        # All columns should be region names
        assert set(result.columns) == set(REGION_NAMES)

    def test_fetch_values_correctly_mapped(self, mock_parsed_df):
        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_parsed_df):
            result = fetcher.fetch("化學品")

        # Check first row values
        assert result.iloc[0]["美國"] == 17.0
        assert result.iloc[0]["日本"] == 15.0
        assert result.iloc[0]["中國大陸及香港"] == 10.0

    def test_fetch_with_date_range(self, mock_parsed_df):
        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_parsed_df):
            result = fetcher.fetch("化學品", start="1984-10-01")

        assert len(result) == 2
        assert result.index[0].month == 10
        for region in REGION_NAMES:
            assert region in result.columns

    def test_fetch_invalid_commodity_raises(self, mock_parsed_df):
        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_parsed_df):
            with pytest.raises(FetchError, match="找不到商品代號"):
                fetcher.fetch("不存在的商品")

    def test_fetch_no_data_raises(self):
        empty_df = pd.DataFrame(index=pd.date_range("1984-09", periods=3, freq="ME"))
        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=empty_df):
            with pytest.raises(FetchError, match="無法取得"):
                fetcher.fetch("化學品")

    def test_fetch_missing_dependency_raises(self):
        import financial_data_query.sources.moeab as moeab_module

        original_has_deps = getattr(moeab_module, "_HAS_DEPS", True)
        try:
            moeab_module._HAS_DEPS = False
            fetcher = MoeaFetcher()
            with pytest.raises(FetchError, match="webdriver-manager"):
                fetcher.fetch("化學品")
        finally:
            moeab_module._HAS_DEPS = original_has_deps

    def test_fetch_closes_browser_on_error(self):
        mock_driver = mock.MagicMock()
        mock_driver.get.side_effect = Exception("Connection failed")
        mock_driver.quit = mock.MagicMock()

        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with pytest.raises(FetchError):
                fetcher.fetch("化學品")

        mock_driver.quit.assert_called_once()


class TestMoeaBatchFetch:
    """Test batch_fetch() for efficiency (single browser session)."""

    @pytest.fixture
    def mock_parsed_df(self, request):
        # Create a DataFrame with multiple commodities' data across all regions
        dates = pd.date_range("1984-09", periods=3, freq="ME")
        columns = {}
        
        for comm in ["化學品", "電子產品"]:
            for region in REGION_NAMES:
                col_name = f"{comm}_{region}"
                if comm == request.instance.commodity_list[0] and region == REGION_NAMES[0]:
                    columns[col_name] = [17.0, 18.0, 20.0]
                elif comm == request.instance.commodity_list[1] and region == REGION_NAMES[0]:
                    columns[col_name] = [29.0, 34.0, 30.0]
                else:
                    columns[col_name] = [i for i in range(5, 8)]
        
        return pd.DataFrame(columns, index=dates)

    def test_batch_fetch_returns_dict(self):
        import pandas as pd
        
        dates = pd.date_range("1984-09", periods=3, freq="ME")
        columns = {}
        for comm in ["化學品", "電子產品"]:
            for region in REGION_NAMES:
                columns[f"{comm}_{region}"] = [i for i in range(5, 8)]
        
        mock_df = pd.DataFrame(columns, index=dates)

        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_df):
            symbols = ["化學品", "電子產品"]
            results = fetcher.batch_fetch(symbols)

        assert isinstance(results, dict)
        assert len(results) == 2
        assert "化學品" in results
        assert "電子產品" in results

    def test_batch_each_commodity_has_region_columns(self):
        dates = pd.date_range("1984-09", periods=3, freq="ME")
        columns = {}
        for comm in ["化學品", "電子產品"]:
            for region in REGION_NAMES:
                columns[f"{comm}_{region}"] = [i for i in range(5, 8)]

        mock_df = pd.DataFrame(columns, index=dates)

        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_df):
            symbols = ["化學品", "電子產品"]
            results = fetcher.batch_fetch(symbols)

        for s, df in results.items():
            assert isinstance(df, pd.DataFrame)
            # Should have region columns, NOT 'value' column
            assert "value" not in df.columns
            assert set(df.columns) == set(REGION_NAMES)
            assert len(df) == 3

    def test_batch_one_browser_session(self):
        dates = pd.date_range("1984-09", periods=3, freq="ME")
        columns = {}
        for comm in ["化學品", "電子產品"]:
            for region in REGION_NAMES:
                columns[f"{comm}_{region}"] = [i for i in range(5, 8)]

        mock_df = pd.DataFrame(columns, index=dates)

        fetcher = MoeaFetcher()
        with mock.patch.object(fetcher, "_get_full_data", return_value=mock_df) as mock_get:
            symbols = ["化學品", "電子產品"]
            results = fetcher.batch_fetch(symbols)

        # _get_full_data should only be called ONCE for all commodities
        assert mock_get.call_count == 1


class TestMoeaRegistration:
    def test_moea_is_registered(self):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("moea")

    def test_moea_fetcher_inherits_base(self):
        from financial_data_query.base import DataSourceFetcher
        fetcher = MoeaFetcher()
        assert isinstance(fetcher, DataSourceFetcher)


class TestMoeaIntegration:
    """Integration tests using the real query() API with mocked browser."""

    @pytest.fixture
    def mock_df(self):
        dates = pd.date_range("1984-09", periods=3, freq="ME")
        columns = {}
        for comm in ["化學品", "電子產品"]:
            for region in REGION_NAMES:
                columns[f"{comm}_{region}"] = [i + j for i, j in zip([17.0, 18.0, 20.0], range(6))]
        return pd.DataFrame(columns, index=dates)

    def test_single_query_json_output(self, mock_df):
        with mock.patch.object(MoeaFetcher, "_get_full_data", return_value=mock_df):
            from financial_data_query import query
            result = query("moea", "化學品", output="json")

        assert isinstance(result, dict)
        assert "化學品" in result
        # Should have all region columns per record (not 'value')
        record = result["化學品"][0]
        assert "date" in record
        for region in REGION_NAMES:
            assert region in record

    def test_single_query_dataframe_output(self, mock_df):
        with mock.patch.object(MoeaFetcher, "_get_full_data", return_value=mock_df):
            from financial_data_query import query
            result = query("moea", "化學品", output="dataframe")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        for region in REGION_NAMES:
            assert region in result.columns
        # Should NOT have 'value' column or 'Symbol' column
        assert "value" not in result.columns
        assert "Symbol" not in result.columns

    def test_batch_query_json_output(self, mock_df):
        with mock.patch.object(MoeaFetcher, "_get_full_data", return_value=mock_df):
            from financial_data_query import query
            result = query("moea", ["化學品", "電子產品"], output="json")

        assert isinstance(result, dict)
        assert len(result) == 2
        for comm in ["化學品", "電子產品"]:
            assert comm in result
            record = result[comm][0]
            assert "date" in record
            for region in REGION_NAMES:
                assert region in record

    def test_batch_query_dataframe_output(self, mock_df):
        with mock.patch.object(MoeaFetcher, "_get_full_data", return_value=mock_df):
            from financial_data_query import query
            result = query("moea", ["化學品"], output="dataframe")

        # Single commodity batch should still be a DataFrame  
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        for region in REGION_NAMES:
            assert region in result.columns


class TestMoeaRegistrationInSourcesInit:
    def test_moea_in_list_sources(self):
        from financial_data_query import list_sources
        sources = list_sources()
        assert "moea" in sources
