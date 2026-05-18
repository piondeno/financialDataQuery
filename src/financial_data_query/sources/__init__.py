from financial_data_query.registry import Registry
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.sources.fred import FredFetcher

try:
    from financial_data_query.sources.stooq import StooqFetcher
    Registry.register(StooqFetcher)
except ImportError:
    pass

try:
    from financial_data_query.sources.tw_ndc import TwEcoFetcher, TwPmiFetcher
    Registry.register(TwEcoFetcher)
    Registry.register(TwPmiFetcher)
except ImportError:
    pass

try:
    from financial_data_query.sources.finra_margin import FinraMarginFetcher
    Registry.register(FinraMarginFetcher)
except ImportError:
    pass

try:
    from financial_data_query.sources.ici import IciFetcher
    Registry.register(IciFetcher)
except ImportError:
    pass

try:
    from financial_data_query.sources.macroMicro import MacroMicroFetcher
    Registry.register(MacroMicroFetcher)
except ImportError:
    pass

Registry.register(YahooFetcher)
Registry.register(FredFetcher)