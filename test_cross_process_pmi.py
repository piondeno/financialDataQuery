"""
Test cross-process caching for tw_pmi.
"""
import subprocess
import sys
import tempfile
import shutil
import os

tmpdir = tempfile.mkdtemp()

writer_script = """
import sys
import os

cache_dir = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
from financial_data_query.sources.tw_ndc import TwPmiFetcher
from financial_data_query.registry import Registry
from financial_data_query import _cache, _has_batch_cache, _get_batch_cache, _BATCH_CACHE_ATTRS, _set_batch_cache
from financial_data_query.disk_cache import DiskCache

import financial_data_query as fdq
fdq._disk_cache = DiskCache(cache_dir)
_disk_cache = fdq._disk_cache

print("=== Process 1: Querying symbol A ===", flush=True)

dates = pd.date_range("2020-01-31", "2024-12-31", freq="ME")
full_table = pd.DataFrame({
    "製造業PMI": [50.5 + i*0.1 for i in range(len(dates))],
    "新增訂單數量": [48.2 + i*0.05 for i in range(len(dates))],
}, index=dates)

fetcher = TwPmiFetcher()

cached = _cache.get("tw_pmi", "A", None, None, None, None)
print(f"  Memory cache: {'HIT' if cached is not None else 'MISS'}", flush=True)

has_batch = _has_batch_cache(fetcher, "tw_pmi")
print(f"  _has_batch_cache: {has_batch}", flush=True)

batch_df = _get_batch_cache(fetcher, "tw_pmi")
print(f"  _get_batch_cache: {type(batch_df).__name__ if batch_df is not None else None}", flush=True)

disk_df = _disk_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
print(f"  Disk cache full table: {'HIT' if disk_df is not None else 'MISS'}", flush=True)

print(f"  ** BROWSER OPENS TO FETCH DATA **", flush=True)
fetcher._full_table_cache["tw_pmi"] = full_table

for attr in _BATCH_CACHE_ATTRS:
    ft = getattr(fetcher, attr, None)
    if ft is not None and hasattr(ft, 'get'):
        cached_df = ft.get("tw_pmi")
        if cached_df is not None and len(cached_df):
            _disk_cache.set("tw_pmi", "_tw_pmi_full_table", cached_df, frequency=None)
            break

disk_verify = _disk_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
print(f"  Disk after write: {'HIT' if disk_verify is not None else 'MISS'}", flush=True)
if disk_verify is not None:
    print(f"  Disk cols: {list(disk_verify.columns)}", flush=True)
    print(f"  Disk rows: {len(disk_verify)}", flush=True)

_disk_cache.close()
print(f"  Process 1 DONE", flush=True)
"""

reader_script = """
import sys
import os

cache_dir = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
from financial_data_query.sources.tw_ndc import TwPmiFetcher
from financial_data_query.registry import Registry
from financial_data_query import _cache, _has_batch_cache, _get_batch_cache, _BATCH_CACHE_ATTRS, _set_batch_cache
from financial_data_query.disk_cache import DiskCache

import financial_data_query as fdq
fdq._disk_cache = DiskCache(cache_dir)
_disk_cache = fdq._disk_cache

print("=== Process 2: Querying symbol B ===", flush=True)

fetcher = TwPmiFetcher()

cached = _cache.get("tw_pmi", "B", None, None, None, None)
print(f"  Memory cache: {'HIT' if cached is not None else 'MISS'}", flush=True)

has_batch = _has_batch_cache(fetcher, "tw_pmi")
print(f"  _has_batch_cache: {has_batch}", flush=True)

batch_df = _get_batch_cache(fetcher, "tw_pmi")
print(f"  _get_batch_cache: {type(batch_df).__name__ if batch_df is not None else None}", flush=True)

disk_df = _disk_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
print(f"  Disk cache full table: {'HIT' if disk_df is not None else 'MISS'}", flush=True)

if disk_df is not None and len(disk_df):
    print(f"  Disk cols: {list(disk_df.columns)}", flush=True)
    print(f"  Disk rows: {len(disk_df)}", flush=True)
    
    symbol = "新增訂單數量"
    match_cols = [c for c in disk_df.columns if c == symbol or c.startswith(symbol + "_")]
    print(f"  Symbol in disk: {len(match_cols) > 0}, match_cols={match_cols}", flush=True)
    print(f"  ** NO BROWSER NEEDED **", flush=True)
else:
    print(f"  ** BUG: Disk cache empty! Browser opens unnecessarily! **", flush=True)

_disk_cache.close()
print(f"  Process 2 DONE", flush=True)
"""

writer_path = os.path.join(tmpdir, "writer.py")
reader_path = os.path.join(tmpdir, "reader.py")

with open(writer_path, "w", encoding="utf-8") as f:
    f.write(writer_script)
with open(reader_path, "w", encoding="utf-8") as f:
    f.write(reader_script)

try:
    print("=" * 70)
    print("Process 1 - queries symbol A")
    print("=" * 70)
    result1 = subprocess.run(
        [sys.executable, writer_path, tmpdir],
        capture_output=True, text=True,
    )
    print(result1.stdout)
    if result1.stderr:
        print("STDERR:", result1.stderr)

    print("=" * 70)
    print("Process 2 - queries symbol B")
    print("=" * 70)
    result2 = subprocess.run(
        [sys.executable, reader_path, tmpdir],
        capture_output=True, text=True,
    )
    print(result2.stdout)
    if result2.stderr:
        print("STDERR:", result2.stderr)

    if "BUG" in result2.stdout:
        print("\\nBUG CONFIRMED: Cross-process disk cache not working!")
    else:
        print("\\nOK: Cross-process disk cache working.")

finally:
    shutil.rmtree(tmpdir)
