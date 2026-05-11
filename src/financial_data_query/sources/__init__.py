from financial_data_query.registry import Registry
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.sources.fred import FredFetcher

try:
    from financial_data_query.sources.stooq import StooqFetcher
    Registry.register(StooqFetcher)
except ImportError:
    pass

Registry.register(YahooFetcher)
Registry.register(FredFetcher)