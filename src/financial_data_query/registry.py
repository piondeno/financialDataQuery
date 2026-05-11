from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class Registry:
    _fetchers: dict[str, DataSourceFetcher] = {}

    @classmethod
    def register(cls, fetcher_cls: type[DataSourceFetcher]) -> None:
        """Register a fetcher class. An instance is created and cached."""
        instance = fetcher_cls()
        cls._fetchers[instance.source_name] = instance

    @classmethod
    def get(cls, source: str) -> DataSourceFetcher:
        """Get a fetcher instance by source name."""
        if source not in cls._fetchers:
            raise DataSourceNotFoundError(source)
        return cls._fetchers[source]

    @classmethod
    def is_registered(cls, source: str) -> bool:
        return source in cls._fetchers

    @classmethod
    def list_sources(cls) -> list[str]:
        return list(cls._fetchers.keys())
