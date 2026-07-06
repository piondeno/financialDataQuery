"""
Test concurrent processes querying tw_pmi with different symbols.
"""
import subprocess
import sys
import tempfile
import shutil
import os
import multiprocessing
import time

tmpdir = tempfile.mkdtemp()

def make_script(symbol, label, result_file):
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
    print(f"  {label}: BROWSER OPEN #{{browser_opens}}!", flush=True)
    import pandas as pd
    # Simulate slow fetch (like real browser)
    import time
    time.sleep(3)
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
print(f"  {label}: Result rows: {{len(result)}}, Browser opens: {{browser_opens}}", flush=True)

# Write result to file
with open("{result_file}", "w") as f:
    f.write(f"{{label}}:opens={{browser_opens}}")

fdq._disk_cache.close()
'''

# Write scripts
for i, (symbol, label) in enumerate([("製造業PMI", "P1"), ("新增訂單數量", "P2")]):
    script = make_script(symbol, label, os.path.join(tmpdir, f"result_{label}.txt"))
    with open(os.path.join(tmpdir, f"proc_{i}.py"), "w", encoding="utf-8") as f:
        f.write(script)

try:
    print("=" * 70)
    print("Starting TWO processes SIMULTANEOUSLY...")
    print("=" * 70)

    # Start both processes at the same time
    procs = []
    for i in range(2):
        p = subprocess.Popen(
            [sys.executable, os.path.join(tmpdir, f"proc_{i}.py"), tmpdir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        procs.append(p)

    # Wait for both to finish
    for p in procs:
        stdout, stderr = p.communicate(timeout=30)
        print(stdout)
        if stderr:
            print("STDERR:", stderr)

    # Read results
    for label in ["P1", "P2"]:
        with open(os.path.join(tmpdir, f"result_{label}.txt"), "r") as f:
            print(f"  {label}: {f.read()}")

finally:
    shutil.rmtree(tmpdir)
