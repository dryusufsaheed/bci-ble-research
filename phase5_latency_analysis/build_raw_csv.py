#!/usr/bin/env python3
"""
build_raw_csv.py
Combine the 17 per-dataset latency pickles into one trial-level CSV, then
report per-protocol descriptives so they can be checked before analysis.

Run from:  ~/BCI_BLE_Research/phase5_latency
Output:    data/latency_raw.csv   with columns protocol,trial,latency_ms
"""
import pickle, glob, csv, os, sys
import numpy as np

FIELD = sys.argv[1] if len(sys.argv) > 1 else "raw_total_times"  # or raw_encryption_times
PROTO_ORDER = ["NONE", "AES-CCM", "AES-GCM", "ChaCha20-Poly1305"]

files = sorted(glob.glob("data/latency_raw_*.pkl"))
assert files, "no latency_raw_*.pkl found in data/"

rows = []
per_proto = {p: [] for p in PROTO_ORDER}
global_idx = {p: 0 for p in PROTO_ORDER}

for f in files:
    recs = pickle.load(open(f, "rb"))
    recs = recs if isinstance(recs, list) else [recs]
    for r in recs:
        p = r["protocol"]
        vals = np.asarray(r[FIELD], dtype=float)
        for v in vals:
            rows.append((p, global_idx[p], v))
            global_idx[p] += 1
        per_proto[p].extend(vals.tolist())

os.makedirs("data", exist_ok=True)
with open("data/latency_raw.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["protocol", "trial", "latency_ms"])
    w.writerows(rows)

print(f"field used         : {FIELD}")
print(f"files combined     : {len(files)}")
print(f"total rows written : {len(rows):,}")
print(f"\n{'protocol':20} {'n':>7} {'mean_ms':>12} {'sd_ms':>12} {'median_ms':>12}")
for p in PROTO_ORDER:
    a = np.asarray(per_proto[p], float)
    print(f"{p:20} {len(a):7d} {a.mean():12.6f} {a.std(ddof=1):12.6f} {np.median(a):12.6f}")
print("\nwrote data/latency_raw.csv")
