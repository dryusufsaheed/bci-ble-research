#!/usr/bin/env python3
"""
noninferiority.py  — RQ3b one-sided noninferiority test against a 10 ms margin.
Reads data/latency_raw.csv (protocol,trial,latency_ms). For each encrypted
protocol vs NONE, tests whether the latency increase is below 10 ms.

H0 (inferior):    mean_enc - mean_none >= 10 ms
H1 (noninferior): mean_enc - mean_none <  10 ms
Reject H0 (declare noninferior) if the upper 95% one-sided CI bound < 10 ms,
equivalently if the one-sided p < .05.

Usage:  python3 noninferiority.py --raw data/latency_raw.csv
"""
import argparse
import numpy as np, pandas as pd
from scipy import stats

MARGIN=10.0; ALPHA=0.05
ORDER=["NONE","AES-CCM","AES-GCM","ChaCha20-Poly1305"]

ap=argparse.ArgumentParser(); ap.add_argument("--raw",default="data/latency_raw.csv")
a=ap.parse_args()
df=pd.read_csv(a.raw)
g={p:df.loc[df.protocol==p,"latency_ms"].to_numpy() for p in ORDER}
base=g["NONE"]; nb=len(base); vb=base.var(ddof=1)

print(f"RQ3b noninferiority test  (margin = {MARGIN} ms, one-sided alpha = {ALPHA})")
print(f"{'comparison':30} {'diff':>8} {'upper95CI':>10} {'t_NI':>10} {'p':>10} {'decision'}")
for p in ORDER[1:]:
    x=g[p]; nx=len(x); md=x.mean()-base.mean()
    se=np.sqrt(x.var(ddof=1)/nx+vb/nb)
    dfree=(x.var(ddof=1)/nx+vb/nb)**2/((x.var(ddof=1)/nx)**2/(nx-1)+(vb/nb)**2/(nb-1))
    # one-sided noninferiority: H0 diff>=MARGIN ; test statistic
    t_ni=(md-MARGIN)/se
    p_ni=stats.t.cdf(t_ni,dfree)            # P(T < t) lower tail = evidence diff<MARGIN
    upper=md+stats.t.ppf(1-ALPHA,dfree)*se  # one-sided upper 95% bound
    dec="Noninferior" if p_ni<ALPHA else "Not shown"
    print(f"{'NONE vs '+p:30} {md:8.4f} {upper:10.4f} {t_ni:10.2f} {p_ni:10.2e} {dec}")
print(f"\nMargin {MARGIN} ms = 10% of the 100 ms real-time BCI budget and matches the")
print("±10 ms sensorimotor-BCI delay tolerance cited in the praxis.")
