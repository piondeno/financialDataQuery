"""
Cross-process disk cache validation.
Tests that disk cache written in one process can be read in another.
"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import pytest


def _run_subprocess(test_code: str) -> subprocess.CompletedProcess:
    """Run test code in a separate Python process."""
    return subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )


def test_disk_cache_writer_then_reader(tmp_path):
    """Verify disk cache write + read across processes."""
    cache_dir = str(tmp_path / "cross_cache")

    writer_code = f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df = pd.DataFrame(
    [10, 20, 30],
    index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
    columns=["value"]
)
cache.set("test_src", "TEST", df, frequency="none")
cache.close()
print("WRITE_OK")
'''

    reader_code = f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df = cache.get("test_src", "TEST", frequency="none")
cache.close()

assert df is not None, "Reader should find data"
assert len(df) == 3
assert list(df["value"].astype(int)) == [10, 20, 30]
print("READ_OK")
'''

    r1 = _run_subprocess(writer_code)
    assert r1.returncode == 0, f"Writer failed: {r1.stderr}"
    assert "WRITE_OK" in r1.stdout

    r2 = _run_subprocess(reader_code)
    assert r2.returncode == 0, f"Reader failed: {r2.stderr}"
    assert "READ_OK" in r2.stdout


def test_disk_cache_update(tmp_path):
    """Verify disk cache update across processes."""
    cache_dir = str(tmp_path / "update_cache")

    writer1_code = f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df1 = pd.DataFrame([1, 2, 3], index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]), columns=["v"])
cache.set("s", "T", df1, frequency="daily")
cache.close()
'''

    writer2_code = f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df2 = pd.DataFrame([4, 5], index=pd.to_datetime(["2024-04-01", "2024-05-01"]), columns=["v"])
cache.set("s", "T", df2, frequency="daily")
cache.close()
'''

    reader_code = f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df = cache.get("s", "T", frequency="daily")
cache.close()

assert df is not None
# DiskCache INSERT OR REPLACE keeps old rows not in new data
assert len(df) >= 2
print("UPDATE_OK")
'''

    r1 = _run_subprocess(writer1_code)
    assert r1.returncode == 0, f"Writer1 failed: {r1.stderr}"

    r2 = _run_subprocess(writer2_code)
    assert r2.returncode == 0, f"Writer2 failed: {r2.stderr}"

    r3 = _run_subprocess(reader_code)
    assert r3.returncode == 0, f"Reader failed: {r3.stderr}"
    assert "UPDATE_OK" in r3.stdout


def test_disk_cache_file_persistence(tmp_path):
    """Verify cache file persists on disk between processes."""
    cache_dir = str(tmp_path / "persist_cache")

    # Write
    r1 = _run_subprocess(f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df = pd.DataFrame([[1.0]], columns=["val"])
df.index = pd.to_datetime(["2024-01-01"])
cache.set("src", "sym", df, frequency="daily")
cache.close()
print("W")
''')
    assert r1.returncode == 0
    assert "W" in r1.stdout

    # Check DB file exists (named with today's date)
    db_files = list(Path(cache_dir).glob("*.db"))
    assert len(db_files) == 1, f"Expected 1 DB file, found {len(db_files)}"

    # Read in new process
    r2 = _run_subprocess(f'''
import sys
sys.path.insert(0, "src")
from financial_data_query.disk_cache import DiskCache
cache = DiskCache("{cache_dir}")
df = cache.get("src", "sym", frequency="daily")
cache.close()
assert df is not None, "Cache file should persist"
assert len(df) == 1
print("PERSIST_OK")
''')
    assert r2.returncode == 0
    assert "PERSIST_OK" in r2.stdout


def test_cross_process_cache_isolation(tmp_path):
    """Verify different sources don't share cache."""
    cache_dir = str(tmp_path / "isolate_cache")

    _run_subprocess(f'''
import sys
sys.path.insert(0, "src")
import pandas as pd
from financial_data_query.disk_cache import DiskCache

cache = DiskCache("{cache_dir}")
df1 = pd.DataFrame([1], index=pd.to_datetime(["2024-01-01"]), columns=["v"])
df2 = pd.DataFrame([2], index=pd.to_datetime(["2024-01-01"]), columns=["v"])
cache.set("src_a", "sym", df1, frequency="daily")
cache.set("src_b", "sym", df2, frequency="daily")
cache.close()
''')

    r = _run_subprocess(f'''
import sys
sys.path.insert(0, "src")
from financial_data_query.disk_cache import DiskCache
cache = DiskCache("{cache_dir}")
a = cache.get("src_a", "sym", frequency="daily")
b = cache.get("src_b", "sym", frequency="daily")
cache.close()
assert a is not None and b is not None
assert int(a["v"].iloc[0]) == 1 and int(b["v"].iloc[0]) == 2, "Sources should be isolated"
print("ISO_OK")
''')
    assert r.returncode == 0
    assert "ISO_OK" in r.stdout
