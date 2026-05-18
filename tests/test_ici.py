import os
import shutil
import tempfile
from unittest.mock import patch
import pandas as pd
import pytest
from financial_data_query.sources.ici import IciFetcher
from financial_data_query.errors import FetchError


def _create_sample_mf_xls(path: str):
    """Create a minimal XLS file matching ICI mutual fund structure."""
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Weekly MF Flow Estimates")
    # Row 4: top-level headers
    ws.write(4, 0, "Date")
    ws.write(4, 1, "Total     long-term")
    ws.write(4, 3, "Equity")
    # Row 5: sub-headers
    ws.write(5, 3, "Total equity")
    ws.write(5, 4, "Domestic")
    # Row 6: leaf headers
    ws.write(6, 4, "Total domestic")
    # Data rows (monthly then weekly)
    ws.write(8, 0, "01/31/2024")
    ws.write(8, 1, -20567)
    ws.write(8, 3, -44924)
    ws.write(8, 4, -39251)
    ws.write(9, 0, "02/29/2024")
    ws.write(9, 1, -2979)
    ws.write(9, 3, -31769)
    ws.write(9, 4, -29152)
    wb.save(path)


class TestIciFetcher:
    def setup_method(self):
        self.fetcher = IciFetcher()

    def test_source_name(self):
        assert self.fetcher.source_name == "ici"

    @patch("financial_data_query.sources.ici.urllib.request.urlretrieve")
    def test_fetch_mf_total_returns_dataframe(self, mock_retrieve):
        xls_path = tempfile.mktemp(suffix=".xls")
        try:
            _create_sample_mf_xls(xls_path)
            mock_retrieve.side_effect = lambda url, path: os.rename(xls_path, path)

            df = self.fetcher.fetch("mf_total")

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "value" in df.columns
            assert df.iloc[0]["value"] == -20567
            assert df.iloc[1]["value"] == -2979
        finally:
            if os.path.exists(xls_path):
                os.unlink(xls_path)

    def test_invalid_symbol_raises_error(self):
        with pytest.raises(FetchError, match="Invalid symbol"):
            self.fetcher.fetch("invalid_symbol")

    @patch("financial_data_query.sources.ici.urllib.request.urlretrieve")
    def test_fetch_with_date_filter(self, mock_retrieve):
        xls_path = tempfile.mktemp(suffix=".xls")
        try:
            _create_sample_mf_xls(xls_path)
            mock_retrieve.side_effect = lambda url, path: os.rename(xls_path, path)

            df = self.fetcher.fetch("mf_total", start="2024-02-01")

            assert len(df) == 1
            assert df.iloc[0]["value"] == -2979
        finally:
            if os.path.exists(xls_path):
                os.unlink(xls_path)

    @patch("financial_data_query.sources.ici.urllib.request.urlretrieve")
    def test_temp_file_is_cleaned_up(self, mock_retrieve):
        xls_path = tempfile.mktemp(suffix=".xls")
        cleaned_paths = []

        def track_cleanup(url, path):
            _create_sample_mf_xls(xls_path)
            os.rename(xls_path, path)
            cleaned_paths.append(path)

        mock_retrieve.side_effect = track_cleanup

        self.fetcher.fetch("mf_total")

        assert not os.path.exists(cleaned_paths[0])

    def test_batch_fetch_multiple_symbols(self):
        with patch("financial_data_query.sources.ici.urllib.request.urlretrieve") as mock_retrieve:
            xls_path = tempfile.mktemp(suffix=".xls")
            try:
                _create_sample_mf_xls(xls_path)
                mock_retrieve.side_effect = lambda url, path: shutil.copy2(
                    xls_path, path
                )

                results = self.fetcher.batch_fetch(["mf_total", "mf_equity_total"])

                assert "mf_total" in results
                assert "mf_equity_total" in results
                assert isinstance(results["mf_total"], pd.DataFrame)
                assert isinstance(results["mf_equity_total"], pd.DataFrame)
            finally:
                if os.path.exists(xls_path):
                    os.unlink(xls_path)
