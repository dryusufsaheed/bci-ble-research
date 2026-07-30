#!/usr/bin/env python3
"""
vuln_inference.py  --  RQ1 inferential analysis (chi-square / Fisher exact).

For each encrypted protocol versus the unencrypted baseline, builds the 2x2
protection table, runs Fisher's exact test (primary, because the tables show
complete separation with zero cells) and the chi-square test (secondary), and
reports the effect size, an exact Clopper-Pearson confidence interval for the
protection rate, and a Bonferroni-adjusted significance threshold.

Counts are taken from the vulnerability-test tables:
  MITM/confidentiality : n = 500 packets per protocol (Table 4.2)
  Replay               : n = 80 attempts per protocol (Table 4.3; 40 immediate + 40 delayed)

Usage: python3 vuln_inference.py
"""
import json
import numpy as np
from scipy import stats
from scipy.stats import beta

PROTOCOLS=["AES-CCM","AES-GCM","ChaCha20-Poly1305"]

def clopper_pearson(k,n,alpha=0.05):
    lo=beta.ppf(alpha/2,k,n-k+1) if k>0 else 0.0
    hi=beta.ppf(1-alpha/2,k+1,n-k) if k<n else 1.0
    return lo,hi

def analyze(none_vuln,none_prot,enc_vuln,enc_prot):
    tbl=np.array([[none_vuln,none_prot],[enc_vuln,enc_prot]])
    n=int(tbl.sum())
    chi2,pchi,dof,_=stats.chi2_contingency(tbl,correction=True)
    chi2n,_,_,_=stats.chi2_contingency(tbl,correction=False)
    _,pfish=stats.fisher_exact(tbl)
    phi=float(np.sqrt(chi2n/n))
    a,b,c,d=(x+0.5 for x in (none_vuln,none_prot,enc_vuln,enc_prot))
    OR=(a*d)/(b*c)
    prot_enc=enc_prot/(enc_vuln+enc_prot)
    prot_none=none_prot/(none_vuln+none_prot)
    lo,hi=clopper_pearson(enc_prot,enc_vuln+enc_prot)
    return dict(n=n,chi2=float(chi2n),chi2_yates=float(chi2),df=int(dof),
                fisher_p=float(pfish),chi2_p=float(pchi),phi=phi,odds_ratio_HA=float(OR),
                risk_difference=float(prot_enc-prot_none),
                enc_protection=float(prot_enc),ci=[float(lo),float(hi)])

def main():
    tests={
      "MITM_confidentiality":dict(none=(500,0),enc=(0,500)),   # (vuln, protected)
      "Replay":dict(none=(80,0),enc=(0,80)),
    }
    m=sum(len(PROTOCOLS) for _ in tests)          # total comparisons
    bonf=0.05/m
    out={"comparisons":[],"bonferroni_alpha":bonf,"n_comparisons":m}
    print(f"Bonferroni-adjusted alpha = .05/{m} = {bonf:.4f}\n")
    for attack,cfg in tests.items():
        nv,npr=cfg["none"]; ev,epr=cfg["enc"]
        for prot in PROTOCOLS:
            r=analyze(nv,npr,ev,epr); r["attack"]=attack; r["comparison"]=f"NONE vs {prot}"
            r["significant_bonferroni"]=r["fisher_p"]<bonf
            out["comparisons"].append(r)
            print(f"[{attack}] NONE vs {prot}: n={r['n']}  Fisher p={r['fisher_p']:.2e}  "
                  f"chi2({r['df']})={r['chi2']:.1f}  phi={r['phi']:.2f}  "
                  f"protection={r['enc_protection']*100:.1f}% CI[{r['ci'][0]*100:.2f},{r['ci'][1]*100:.2f}]  "
                  f"{'SIG' if r['significant_bonferroni'] else 'ns'}")
    json.dump(out,open("rq1_inference_results.json","w"),indent=2)
    print("\nAll comparisons significant after Bonferroni correction. Wrote rq1_inference_results.json")
    print("Note: tables show complete separation; Fisher's exact is the primary test and effect sizes are at maximum (phi = 1.0).")

if __name__=="__main__": main()
