"""
Test: Multiple processes querying DIFFERENT symbols.
"""
import subprocess
import sys
import tempfile
import shutil
import os

tmpdir = tempfile.mkdtemp()

def make_script(symbol, label):
    return f'''
import sys, os
cache_dir = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from financial_data_query.disk_cache import DiskCache
import financial_data_query as fdq
fdq._disk_cache = DiskCache(cache_dir)

from financial_data_query.sources.tw_ndc import NdcFetcher
browser_opens = 0

def tracked_get_full_table(self):
    global browser_opens
    browser_opens += 1
    print(f"  BROWSER OPEN #{{browser_opens}}!", flush=True)
    import pandas as pd
    dates = pd.date_range("2020-01-31", "2024-12-31", freq="ME")
    return pd.DataFrame(
        {{"製造業PMI": [50.5 + i*0.1 for i in range(len(dates))],
          "新增訂單數量": [48.2 + i*0.05 for i in range(len(dates))],
          "生產數量": [51.3 + i*0.08 for i in range(len(dates))]}},
        index=dates)

NdcFetcher._get_full_table = tracked_get_full_table

print("=== {label}: query('tw_pmi', '{symbol}') ===", flush=True)
fdq.clear_cache()
result = fdq.query("tw_pmi", "{symbol}", output="dataframe")
print(f"  Result rows: {{len(result)}}", flush=True)
print(f"  Browser opens: {{browser_opens}} (expected: 0 after first)", flush=True)

fdq._disk_cache.close()
'''

scripts = {
    "p1a.py": make_script("製造業PMI", "P1-A"),
    "p2.py": make_script("新增訂單數量", "P2"),
    "p1c.py": make_script("生產數量", "P1-C"),
}

try:
    for name, content in scripts.items():
        with open(os.path.join(tmpdir, name), "w", encoding="utf-8") as f:
            f.write(content)

    for name in ["p1a.py", "p2.py", "p1c.py"]:
        print("=" * 70)
        result = subprocess.run(
            [sys.executable, os.path.join(tmpdir, name), tmpdir],
            capture_output=True, text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

finally:
    shutil.rmtree(tmpdir)
