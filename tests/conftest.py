import tempfile
import pytest
from financial_data_query import clear_cache


@pytest.fixture(autouse=True)
def isolate_disk_cache(tmp_path):
    """Replace global disk cache with a temp directory for test isolation."""
    from financial_data_query.disk_cache import DiskCache
    import financial_data_query as fdq

    old_disk_cache = fdq._disk_cache
    new_disk_cache = DiskCache(str(tmp_path / "cache"))
    fdq._disk_cache = new_disk_cache
    clear_cache()  # Also reset in-memory cache

    yield new_disk_cache

    fdq._disk_cache = old_disk_cache
    new_disk_cache.close()


@pytest.fixture(autouse=True)
def cleanup_registered_sources():
    """Cleanup dynamically registered test sources after each test."""
    from financial_data_query.registry import Registry
    before = set(Registry.list_sources())
    yield
    after = set(Registry.list_sources())
    for source in after - before:
        if source in Registry._fetchers:
            del Registry._fetchers[source]
