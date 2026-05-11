from financial_data_query.registry import Registry
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.sources.fred import FredFetcher

Registry.register(YahooFetcher)
Registry.register(FredFetcher)
