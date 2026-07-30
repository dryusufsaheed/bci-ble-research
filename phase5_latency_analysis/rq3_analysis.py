#!/usr/bin/env python3
"""
rq3_analysis.py
===============
Single source of truth for every RQ3 latency statistic, table, and figure.

The committee's finding on Item 4 is that the printed t-statistics, degrees of
freedom, and Cohen's d values in Tables 4.9-4.12 do not reconcile with the
printed means, standard deviations, and n = 1000 in Table 4.7. This script
removes the possibility of that class of error by computing EVERY reported
quantity from one raw input, in one run, with a fixed environment. Nothing is
transcribed by hand.

INPUT (the one thing this script does NOT invent)
-------------------------------------------------
  latency_raw.csv  with columns:  protocol,trial,latency_ms
  - protocol in {NONE, AES-CCM, AES-GCM, ChaCha20-Poly1305}
  - one row per retained trial per protocol
  - these are YOUR measured timings. This script cannot regenerate them,
    because they are empirical observations from your benchmark run. Recover
    the array your original run produced, or re-run the benchmark
    (measure_latency.py) to emit this file. See the memo for why this matters.

OUTPUTS
-------
  table_4_7_descriptives.csv
  table_4_8_shapiro.csv
  table_4_9_to_4_11_pairwise.csv     (NONE vs each encrypted protocol)
  table_4_12_effect_sizes.csv
  table_4_13_tost.csv
  table_4_14_power.csv
  rq3_manifest.json                  (environment, seed, checksums, exclusions)
  figures: fig_4_4_hist.png, fig_4_5_box.png, fig_4_6_ci.png, fig_4_7_qq.png

USAGE
-----
  python3 rq3_analysis.py --raw latency_raw.csv --out ./rq3_out

DESIGN NOTE (committee Required change 3)
-----------------------------------------
The four protocols were timed on the SAME set of input frames in sequence.
That makes the four latency columns REPEATED MEASURES on a shared trial index,
not four independent samples. This script therefore reports BOTH:
  (a) the independent/Welch pairwise tests that appear in the submitted draft,
      corrected so they reconcile with the descriptives, AND
  (b) the paired test that the repeated design actually calls for.
Choose (b) as primary if each trial index corresponds to the same input frame
across protocols; keep (a) only if the runs were independent. The memo explains
the decision. The equivalence (TOST) and effect sizes are reported for the
chosen model.
"""

import argparse, hashlib, json, os, platform, sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import scipy
from scipy import stats

PROTOCOLS = ["NONE", "AES-CCM", "AES-GCM", "ChaCha20-Poly1305"]
DELTA_MS = 5.0          # TOST equivalence margin (a priori; 5% of 100 ms budget)
ALPHA = 0.05
SEED = 20250722         # fixed so any resampling/bootstrap is reproducible


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cohen_d_pooled(x, y):
    nx, ny = len(x), len(y)
    sp = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    return (x.mean() - y.mean()) / sp


def cohen_dz(diff):
    """Effect size for paired design: mean(diff)/sd(diff)."""
    return diff.mean() / diff.std(ddof=1)


def magnitude(d):
    a = abs(d)
    # Cohen (1988) with the Sawilowsky (2009) upper extensions, both published.
    if a >= 2.0: return "huge (Sawilowsky, 2009)"
    if a >= 1.2: return "very large (Sawilowsky, 2009)"
    if a >= 0.8: return "large (Cohen, 1988)"
    if a >= 0.5: return "medium (Cohen, 1988)"
    if a >= 0.2: return "small (Cohen, 1988)"
    return "negligible"


def load(raw_path):
    df = pd.read_csv(raw_path)
    need = {"protocol", "trial", "latency_ms"}
    if not need.issubset(df.columns):
        sys.exit(f"raw file must have columns {need}; found {set(df.columns)}")
    df = df[df["protocol"].isin(PROTOCOLS)].copy()
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", default="./rq3_out")
    ap.add_argument("--paired", action="store_true",
                    help="treat protocols as repeated measures on a shared trial index (recommended)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    np.random.seed(SEED)

    raw = load(args.raw)
    groups = {p: raw.loc[raw.protocol == p, "latency_ms"].to_numpy() for p in PROTOCOLS}
    ns = {p: len(v) for p, v in groups.items()}

    # ---- Table 4.7 descriptives ------------------------------------------
    rows = []
    for p in PROTOCOLS:
        x = groups[p]
        se = x.std(ddof=1) / np.sqrt(len(x))
        rows.append(dict(Protocol=p, n=len(x), Mean=x.mean(), SD=x.std(ddof=1),
                         Median=np.median(x), Min=x.min(), Max=x.max(),
                         CI95_low=x.mean() - 1.96 * se, CI95_high=x.mean() + 1.96 * se))
    t47 = pd.DataFrame(rows)
    t47.to_csv(os.path.join(args.out, "table_4_7_descriptives.csv"), index=False)

    # ---- Table 4.8 Shapiro-Wilk ------------------------------------------
    rows = []
    for p in PROTOCOLS:
        x = groups[p]
        xs = x if len(x) <= 5000 else np.random.choice(x, 5000, replace=False)
        W, pw = stats.shapiro(xs)
        rows.append(dict(Protocol=p, W=W, p_value=pw,
                         Distribution="Normal" if pw >= ALPHA else "Non-normal",
                         Decision="Fail to reject H0" if pw >= ALPHA else "Reject H0"))
    t48 = pd.DataFrame(rows)
    t48.to_csv(os.path.join(args.out, "table_4_8_shapiro.csv"), index=False)
    all_normal = bool((t48.p_value >= ALPHA).all())

    # ---- Tables 4.9-4.11 pairwise NONE vs each encrypted -----------------
    base = groups["NONE"]
    pairwise = []
    for p in PROTOCOLS[1:]:
        x = groups[p]
        lev_F, lev_p = stats.levene(base, x, center="median")
        equal_var = lev_p >= ALPHA

        if args.paired and len(x) == len(base):
            diff = x - base
            t_stat, t_p = stats.ttest_rel(x, base)
            df_used = len(diff) - 1
            d_val = cohen_dz(diff)
            test_name = "Paired t-test"
            w_stat, w_p = stats.wilcoxon(x, base)
            np_name, np_stat, np_p = "Wilcoxon signed-rank", w_stat, w_p
        else:
            t_stat, t_p = stats.ttest_ind(x, base, equal_var=equal_var)
            if equal_var:
                df_used = len(x) + len(base) - 2
            else:
                s1, s2, n1, n2 = x.var(ddof=1), base.var(ddof=1), len(x), len(base)
                df_used = (s1 / n1 + s2 / n2) ** 2 / ((s1 / n1) ** 2 / (n1 - 1) + (s2 / n2) ** 2 / (n2 - 1))
            d_val = cohen_d_pooled(x, base)
            test_name = "Welch t-test" if not equal_var else "Independent t-test"
            u_stat, u_p = stats.mannwhitneyu(x, base, alternative="two-sided")
            np_name, np_stat, np_p = "Mann-Whitney U", u_stat, u_p

        pairwise.append(dict(
            Comparison=f"NONE vs {p}", Test=test_name,
            mean_diff=x.mean() - base.mean(), t=t_stat, df=df_used, t_p=t_p,
            Levene_F=lev_F, Levene_p=lev_p, equal_variances=equal_var,
            nonparam_test=np_name, nonparam_stat=np_stat, nonparam_p=np_p,
            cohen_d=d_val, magnitude=magnitude(d_val)))
    t49 = pd.DataFrame(pairwise)
    t49.to_csv(os.path.join(args.out, "table_4_9_to_4_11_pairwise.csv"), index=False)

    # ---- Table 4.12 effect-size summary ----------------------------------
    t412 = t49[["Comparison", "mean_diff", "cohen_d", "magnitude"]].copy()
    t412.to_csv(os.path.join(args.out, "table_4_12_effect_sizes.csv"), index=False)

    # ---- Table 4.13 TOST for all six pairs -------------------------------
    def tost(a, b, paired):
        # two one-sided tests at +/- DELTA on (mean_a - mean_b)
        if paired and len(a) == len(b):
            diff = a - b
            se = diff.std(ddof=1) / np.sqrt(len(diff)); dfree = len(diff) - 1
            md = diff.mean()
        else:
            na, nb = len(a), len(b)
            se = np.sqrt(a.var(ddof=1) / na + b.var(ddof=1) / nb)
            dfree = (a.var(ddof=1)/na + b.var(ddof=1)/nb) ** 2 / (
                (a.var(ddof=1)/na) ** 2 / (na - 1) + (b.var(ddof=1)/nb) ** 2 / (nb - 1))
            md = a.mean() - b.mean()
        t_low = (md - (-DELTA_MS)) / se          # H0: diff <= -Delta
        t_up = (md - DELTA_MS) / se               # H0: diff >= +Delta
        p_low = stats.t.sf(t_low, dfree)          # upper-tail
        p_up = stats.t.cdf(t_up, dfree)           # lower-tail
        return p_low, p_up, md
    rows = []
    names = PROTOCOLS
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = groups[names[i]], groups[names[j]]
            p_low, p_up, md = tost(a, b, args.paired)
            equiv = (p_low < ALPHA) and (p_up < ALPHA)
            rows.append(dict(Comparison=f"{names[i]} vs {names[j]}",
                             mean_diff=md, lower_test_p=p_low, upper_test_p=p_up,
                             equivalent="Yes" if equiv else "No"))
    t413 = pd.DataFrame(rows)
    t413.to_csv(os.path.join(args.out, "table_4_13_tost.csv"), index=False)

    # ---- Table 4.14 post-hoc power ---------------------------------------
    try:
        from statsmodels.stats.power import TTestIndPower, TTestPower
        rows = []
        for r in pairwise:
            d = abs(r["cohen_d"])
            if r["Test"] == "Paired t-test":
                power = TTestPower().power(effect_size=d, nobs=ns["NONE"], alpha=ALPHA, alternative="two-sided")
            else:
                power = TTestIndPower().power(effect_size=d, nobs1=ns["NONE"], alpha=ALPHA, ratio=1.0)
            rows.append(dict(Comparison=r["Comparison"], effect_size_d=d,
                             n_per_group=ns["NONE"], achieved_power=min(power, 0.999999),
                             adequate="Yes" if power >= 0.80 else "No"))
        pd.DataFrame(rows).to_csv(os.path.join(args.out, "table_4_14_power.csv"), index=False)
    except Exception as e:
        with open(os.path.join(args.out, "table_4_14_power.csv"), "w") as fh:
            fh.write(f"# statsmodels required for power; {e}\n")

    # ---- Figures ---------------------------------------------------------
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "DejaVu Serif"]})

    fig, ax = plt.subplots(figsize=(8, 5))
    for p in PROTOCOLS:
        ax.hist(groups[p], bins=40, alpha=0.5, label=p, density=True)
    ax.set_xlabel("Latency (ms)"); ax.set_ylabel("Density"); ax.legend()
    ax.set_title("Figure 4.4  Latency distribution by protocol")
    fig.savefig(os.path.join(args.out, "fig_4_4_hist.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot([groups[p] for p in PROTOCOLS], labels=PROTOCOLS, showmeans=True)
    ax.set_ylabel("Latency (ms)"); ax.set_title("Figure 4.5  Latency box plots")
    fig.savefig(os.path.join(args.out, "fig_4_5_box.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    means = [groups[p].mean() for p in PROTOCOLS]
    err = [1.96 * groups[p].std(ddof=1) / np.sqrt(len(groups[p])) for p in PROTOCOLS]
    ax.errorbar(PROTOCOLS, means, yerr=err, fmt="o", capsize=5)
    ax.set_ylabel("Mean latency (ms)"); ax.set_title("Figure 4.6  Mean latency with 95% CI")
    fig.savefig(os.path.join(args.out, "fig_4_6_ci.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    for ax, p in zip(axes.ravel(), PROTOCOLS):
        stats.probplot(groups[p], dist="norm", plot=ax); ax.set_title(p)
    fig.suptitle("Figure 4.7  Q-Q plots"); fig.tight_layout()
    fig.savefig(os.path.join(args.out, "fig_4_7_qq.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    # ---- Manifest --------------------------------------------------------
    manifest = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=sys.version.split()[0], numpy=np.__version__,
                         scipy=scipy.__version__, pandas=pd.__version__,
                         platform=platform.platform()),
        seed=SEED, alpha=ALPHA, tost_delta_ms=DELTA_MS,
        model="paired/repeated-measures" if args.paired else "independent-samples",
        raw_file=os.path.abspath(args.raw), raw_sha256=sha256(args.raw),
        n_per_protocol=ns, all_normal=all_normal)
    with open(os.path.join(args.out, "rq3_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)

    print("RQ3 regenerated. Model:",
          "paired" if args.paired else "independent")
    print(t47.to_string(index=False))
    print()
    print(t49[["Comparison", "Test", "mean_diff", "t", "df", "cohen_d", "magnitude"]].to_string(index=False))
    print("\nAll tables and figures written to", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
