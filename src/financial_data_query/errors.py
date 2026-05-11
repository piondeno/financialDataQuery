class DataSourceError(Exception):
    """Base exception for all data source errors."""
    pass


class DataSourceNotFoundError(DataSourceError):
    """Raised when the requested source name is not registered."""

    def __init__(self, source: str):
        self.source = source
        super().__init__(f"Data source '{source}' is not registered.")


class ConfigError(DataSourceError):
    """Raised when required configuration (e.g., API key) is missing."""
    pass


class FetchError(DataSourceError):
    """Raised when a data fetch request fails."""
    pass
