#!/usr/bin/env python3
"""
build_recording_means.py
Collapse the trial-level latencies to ONE mean per recording per protocol,
which makes the recording (session) the experimental unit. This removes the
pseudoreplication that arises from treating 1,000 timing calls within a
recording as independent observations.

Reads:  the 17 per-recording pickles in data/latency_raw_*.pkl
Writes: data/recording_means.csv  with columns
          recording, protocol, n_trials, mean_latency_ms
        (17 recordings x 4 protocols = 68 rows)

Run from:  ~/BCI_BLE_Research/phase5_latency
"""
import pickle, glob, csv, os
import numpy as np

FIELD = "raw_total_times"           # round-trip, matches Table 4.7
PROTS = ["NONE","AES-CCM","AES-GCM","ChaCha20-Poly1305"]

files = sorted(glob.glob("data/latency_raw_*.pkl"))
assert files, "no latency_raw_*.pkl found in data/"

rows=[]
for f in files:
    recs = pickle.load(open(f,"rb"))
    recs = recs if isinstance(recs,list) else [recs]
    for r in recs:
        vals = np.asarray(r[FIELD], dtype=float)
        rows.append((r.get("dataset", os.path.basename(f)), r["protocol"],
                     len(vals), vals.mean()))

os.makedirs("data", exist_ok=True)
with open("data/recording_means.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["recording","protocol","n_trials","mean_latency_ms"])
    w.writerows(rows)

# report: how many recordings, and the between-recording spread per protocol
import collections
byp=collections.defaultdict(list)
for rec,p,n,m in rows: byp[p].append(m)
print(f"recordings (experimental units): {len(set(r[0] for r in rows))}")
print(f"{'protocol':20} {'k_recordings':>12} {'grand_mean':>12} {'between_rec_SD':>15}")
for p in PROTS:
    a=np.array(byp[p]); print(f"{p:20} {len(a):12d} {a.mean():12.6f} {a.std(ddof=1):15.6f}")
print("\nwrote data/recording_means.csv")
