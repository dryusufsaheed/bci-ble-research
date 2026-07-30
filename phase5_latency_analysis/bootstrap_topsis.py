#!/usr/bin/env python3
"""
bootstrap_topsis.py  —  RQ2 robustness evidence for the AHP-weighted TOPSIS ranking.

Two analyses, both requested by the committee:
  (1) Latency bootstrap: resample the measured latencies, recompute the decision
      matrix and TOPSIS each iteration, and report score confidence intervals,
      rank frequencies, and rank reversals. Only latency is resampled; the other
      six criteria are fixed measured/point values.
  (2) Weight sensitivity: perturb the seven AHP weights over plausible ranges and
      report how often each protocol ranks first and where rank reversals occur.

Input:  data/latency_raw.csv  (protocol,trial,latency_ms) from build_raw_csv.py
Output: printed tables + rq2_bootstrap_results.json

Usage:  python3 bootstrap_topsis.py --raw data/latency_raw.csv --iters 10000
"""
import argparse, json
import numpy as np, pandas as pd

PROTS=["NONE","AES-CCM","AES-GCM","ChaCha20-Poly1305"]
CRIT =["MITM","Replay","Latency","CPU","Memory","LoC","Setup"]
SENSE=np.array([+1,+1,-1,-1,-1,-1,-1])            # benefit(+)/cost(-)
WEIGHTS=np.array([0.3567,0.2694,0.1508,0.0691,0.0691,0.0424,0.0424])  # AHP (Table 4.5)

# Fixed criteria (all columns except Latency). Latency is filled from the data.
FIXED=np.array([
 [0.0,   0.0, np.nan, 5.0, 6.0, 50, 1.0],   # NONE
 [100.0,100.0,np.nan,15.0, 8.2,450, 8.0],   # AES-CCM
 [100.0,100.0,np.nan,14.0, 7.8,420, 7.0],   # AES-GCM
 [100.0,100.0,np.nan,12.0, 7.5,380, 6.0],   # ChaCha20-Poly1305
])
LAT_IDX=2
SEED=20250722
SUP_MARGIN=0.05                                   # pre-specified superiority rule

def topsis(X,w):
    r=X/np.sqrt((X**2).sum(0)); v=r*w
    ideal=np.where(SENSE>0,v.max(0),v.min(0)); anti=np.where(SENSE>0,v.min(0),v.max(0))
    Dp=np.sqrt(((v-ideal)**2).sum(1)); Dm=np.sqrt(((v-anti)**2).sum(1))
    return Dm/(Dp+Dm)

def matrix_with_latency(lat):
    X=FIXED.copy().astype(float); X[:,LAT_IDX]=lat; return X

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw",default="data/latency_raw.csv")
    ap.add_argument("--iters",type=int,default=10000)
    a=ap.parse_args(); rng=np.random.default_rng(SEED)

    df=pd.read_csv(a.raw)
    lat={p:df.loc[df.protocol==p,"latency_ms"].to_numpy() for p in PROTS}
    point_lat=np.array([lat[p].mean() for p in PROTS])

    # ---- point estimate ----
    C0=topsis(matrix_with_latency(point_lat),WEIGHTS)
    order0=np.argsort(-C0); rank0={PROTS[i]:int(r+1) for r,i in enumerate(order0)}
    lead0=sorted(C0)[-1]-sorted(C0)[-2]
    print("POINT ESTIMATE (corrected latency)")
    for i in order0: print(f"  {rank0[PROTS[i]]}. {PROTS[i]:20} {C0[i]:.4f}")
    print(f"  lead of #1 over #2 = {lead0:.4f}   ( >{SUP_MARGIN} rule: {lead0>SUP_MARGIN} )\n")

    # ---- (1) latency bootstrap ----
    B=a.iters; scores=np.zeros((B,4)); firsts=np.zeros(4); sup=0
    for b in range(B):
        rl=np.array([rng.choice(lat[p],size=len(lat[p]),replace=True).mean() for p in PROTS])
        C=topsis(matrix_with_latency(rl),WEIGHTS); scores[b]=C
        firsts[np.argmax(C)]+=1
        if sorted(C)[-1]-sorted(C)[-2]>SUP_MARGIN: sup+=1
    lo,hi=np.percentile(scores,[2.5,97.5],axis=0)
    print(f"(1) LATENCY BOOTSTRAP  (B={B}, resampling latency only)")
    print(f"    {'protocol':20} {'mean':>8} {'95% CI':>20} {'P(rank1)':>9}")
    for i in range(4):
        print(f"    {PROTS[i]:20} {scores[:,i].mean():8.4f}  [{lo[i]:.4f}, {hi[i]:.4f}]  {firsts[i]/B*100:8.1f}%")
    print(f"    ChaCha20 lead > {SUP_MARGIN} in {sup/B*100:.1f}% of resamples")
    print(f"    rank reversals vs point estimate: {(1-firsts[order0[0]]/B)*100:.2f}% of resamples had a different #1\n")

    # ---- (2) weight sensitivity ----
    # Dirichlet perturbation: concentration scaled so each weight's SD ~15% of its value.
    Wm=WEIGHTS.copy(); conc=Wm*(1/0.15**2)          # larger conc -> tighter around Wm
    firstsW=np.zeros(4); revW=0; ccm_gcm_reversal=0
    ranks_first={p:0 for p in PROTS}
    for b in range(B):
        w=rng.dirichlet(conc); C=topsis(matrix_with_latency(point_lat),w)
        winner=np.argmax(C); firstsW[winner]+=1
        ranks_first[PROTS[winner]]+=1
        o=np.argsort(-C)
        if PROTS[o[0]]!=PROTS[order0[0]]: revW+=1
        # rank reversal specifically between #2 and #3 (AES-CCM vs AES-GCM)
        r={PROTS[i]:list(o).index(i) for i in range(4)}
        if r["AES-GCM"]<r["AES-CCM"]: ccm_gcm_reversal+=1
    print(f"(2) WEIGHT SENSITIVITY  (Dirichlet, ~15% SD per weight, {B} draws)")
    for i in range(4):
        print(f"    {PROTS[i]:20} ranks #1 in {firstsW[i]/B*100:6.1f}% of weight configurations")
    print(f"    ChaCha20 remains #1 in {firstsW[order0[0]]/B*100:.1f}% of plausible weightings")
    print(f"    AES-GCM overtakes AES-CCM for #2 in {ccm_gcm_reversal/B*100:.1f}% of weightings")

    out=dict(point_scores={PROTS[i]:float(C0[i]) for i in range(4)},
             point_rank=rank0, lead=float(lead0), superiority_rule=SUP_MARGIN,
             boot_ci={PROTS[i]:[float(lo[i]),float(hi[i])] for i in range(4)},
             boot_rank1={PROTS[i]:float(firsts[i]/B) for i in range(4)},
             boot_superiority_rate=float(sup/B),
             weight_rank1={PROTS[i]:float(firstsW[i]/B) for i in range(4)},
             weight_ccm_gcm_reversal=float(ccm_gcm_reversal/B),
             iters=B, seed=SEED)
    json.dump(out,open("rq2_bootstrap_results.json","w"),indent=2)
    print("\nwrote rq2_bootstrap_results.json")

if __name__=="__main__": main()
