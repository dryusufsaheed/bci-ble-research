#!/usr/bin/env python3
"""
paired_recording_analysis.py
Recording-level paired analysis (RQ3a) with the recording as the experimental unit.

Because every recording is measured under all four protocols, the recording-level
mean latencies are PAIRED across protocols. For each encrypted protocol vs NONE
this runs a paired-samples t-test on the 17 recording means (df = 16), with the
Wilcoxon signed-rank test as the nonparametric partner and Cohen's d_z as the
paired effect size. Packet-level descriptives are reported separately and are
NOT used for inference.

Reads:  data/recording_means.csv  (from build_recording_means.py)
Writes: recording_paired_results.json
Run:    python3 paired_recording_analysis.py --raw data/recording_means.csv
"""
import argparse, json
import numpy as np, pandas as pd
from scipy import stats

PROTS=["NONE","AES-CCM","AES-GCM","ChaCha20-Poly1305"]

ap=argparse.ArgumentParser(); ap.add_argument("--raw",default="data/recording_means.csv")
a=ap.parse_args()
df=pd.read_csv(a.raw)
piv=df.pivot(index="recording",columns="protocol",values="mean_latency_ms")[PROTS]
k=len(piv)
base=piv["NONE"].to_numpy()

print(f"Experimental unit: recording (session).  k = {k} recordings.")
print(f"Analysis unit: recording-level mean latency (round-trip).\n")
print(f"{'comparison':28} {'mean_diff':>10} {'t(df)':>14} {'p':>9} {'d_z':>7} {'Wilcoxon p':>11}")
out=[]
for p in PROTS[1:]:
    x=piv[p].to_numpy()
    diff=x-base
    tt,tp=stats.ttest_rel(x,base)
    dz=diff.mean()/diff.std(ddof=1)
    try: ww,wp=stats.wilcoxon(x,base)
    except Exception: ww,wp=np.nan,np.nan
    print(f"NONE vs {p:20} {diff.mean():10.4f} t({k-1})={tt:7.2f} {tp:9.2e} {dz:7.2f} {wp:11.2e}")
    out.append(dict(comparison=f"NONE vs {p}", mean_diff=float(diff.mean()),
                    t=float(tt), df=k-1, p_value=float(tp), cohen_dz=float(dz),
                    wilcoxon_p=float(wp)))

# recording-level descriptives (session-level uncertainty)
print(f"\nRecording-level means (n = {k} recordings):")
print(f"{'protocol':20} {'mean':>12} {'SD(between-rec)':>16} {'95% CI':>26}")
desc=[]
for p in PROTS:
    v=piv[p].to_numpy(); se=v.std(ddof=1)/np.sqrt(k)
    ci=(v.mean()-stats.t.ppf(.975,k-1)*se, v.mean()+stats.t.ppf(.975,k-1)*se)
    print(f"{p:20} {v.mean():12.6f} {v.std(ddof=1):16.6f}   [{ci[0]:.4f}, {ci[1]:.4f}]")
    desc.append(dict(protocol=p,mean=float(v.mean()),sd_between=float(v.std(ddof=1)),
                     ci_low=float(ci[0]),ci_high=float(ci[1])))

json.dump(dict(k_recordings=k,experimental_unit="recording",
               comparisons=out,recording_descriptives=desc),
          open("recording_paired_results.json","w"),indent=2)
print("\nwrote recording_paired_results.json")
