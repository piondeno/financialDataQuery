import pandas as pd

# Date formats
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
ICI_DATE_FORMAT = "%m/%d/%Y"

# Default in-memory cache size
_DEFAULT_CACHE_SIZE = 128

# Auto-frequency thresholds: days span -> frequency
_DAILY_THRESHOLD_DAYS = 365
_WEEKLY_THRESHOLD_DAYS = 1825  # ~5 years

# ROC (Republic of China) year offset: AD = ROC + 1911
ROC_EPOCH_AD = 1911

# MOEA earliest date option
MOEA_EARLIEST_DATE = "73年9月"

# Epoch timestamp for Highcharts data conversion
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")

# HTTP request defaults
_HTTP_TIMEOUT = 30
_HTTP_TIMEOUT_LONG = 60

# Frequency interval mappings — shared between Yahoo and Stooq
FREQUENCY_YAHOO_INTERVALS = {
    "daily": "1d",
    "weekly": "1wk",
    "monthly": "1mo",
}

# AkShare default date boundaries
AKSHARE_DEFAULT_START = "19700101"
AKSHARE_DEFAULT_END = "20500101"
