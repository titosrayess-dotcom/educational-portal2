#!/usr/bin/env python3
"""
Simple loop - runs batch_downloader.py repeatedly until done.
"""
import sys, subprocess, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BATCH_SCRIPT = str(PROJECT_ROOT / "scraper" / "batch_downloader.py")
batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 80

for i in range(999999):
    print(f"\n--- Batch {i+1} ---")
    try:
        result = subprocess.run(
            [sys.executable, BATCH_SCRIPT, str(batch_size)],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=120,
        )
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    except subprocess.TimeoutExpired:
        print("  [Timeout]")
        continue
    
    if "All files already downloaded" in result.stdout or "Remaining: 0" in result.stdout:
        print("All done!")
        break
    
    time.sleep(0.3)
