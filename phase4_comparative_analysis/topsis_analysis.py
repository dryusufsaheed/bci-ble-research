#!/usr/bin/env python3
"""
topsis_analysis.py
Phase 4: Multi-Criteria Decision Analysis — TOPSIS

Implements the Technique for Order of Preference by Similarity to
Ideal Solution (TOPSIS) to rank the four encryption protocols.

Criteria (with AHP-derived weights):
  C1 — Latency          (cost criterion — lower is better)
  C2 — Protection Rate  (benefit — higher is better)
  C3 — Memory Overhead  (cost — lower is better)
  C4 — Power Efficiency (benefit — higher is better)

Confirmed empirical latency values (Dr. Yusuf praxis, 2026):
  NONE              :  8.4523 ms
  AES-GCM           : 11.2345 ms
  ChaCha20-Poly1305 : 10.8234 ms
  AES-CCM           : 12.4891 ms

TOPSIS ranking (higher score = closer to ideal):
  1st — ChaCha20-Poly1305
  2nd — AES-GCM
  3rd — AES-CCM
  4th — NONE (insecure control)

Praxis: Securing Brain-Computer Interfaces | Dr. Saheed Yusuf | GWU 2026
"""

import numpy as np
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Decision matrix — empirical values from Phase 3 & 4 experiments
# ---------------------------------------------------------------------------

PROTOCOLS = ["NONE", "AES-CCM", "AES-GCM", "ChaCha20-Poly1305"]

# Columns: [Latency(ms), ProtectionRate(%), MemoryOverhead(KB), PowerEfficiency(score)]
DECISION_MATRIX = np.array([
    [ 8.4523,  0.0,  0.0, 40.0],   # NONE
    [12.4891, 95.5, 12.0, 72.0],   # AES-CCM
    [11.2345, 96.8, 10.5, 78.0],   # AES-GCM
    [10.8234, 98.2,  9.2, 85.0],   # ChaCha20-Poly1305
], dtype=float)

# Criterion types: True = benefit (maximise), False = cost (minimise)
BENEFIT_CRITERIA = [False, True, False, True]   # [Latency, ProtRate, Mem, Power]

# AHP-derived weights (see ahp_weights.py) — must sum to 1.0
AHP_WEIGHTS = np.array([0.35, 0.40, 0.15, 0.10])


@dataclass
class TOPSISResult:
    protocol:          str
    closeness_score:   float    # C_i: proximity to ideal (0–1)
    rank:              int
    d_positive:        float    # distance to positive ideal
    d_negative:        float    # distance to negative ideal


class TOPSISAnalyzer:
    """
    Standard TOPSIS implementation following Hwang & Yoon (1981).

    Steps
    -----
    1. Normalise decision matrix (vector normalisation)
    2. Apply criteria weights
    3. Determine positive ideal (A+) and negative ideal (A-)
    4. Calculate separation measures d+ and d-
    5. Calculate relative closeness C_i = d- / (d+ + d-)
    6. Rank alternatives by C_i descending
    """

    def __init__(
        self,
        decision_matrix: np.ndarray = DECISION_MATRIX,
        weights:         np.ndarray = AHP_WEIGHTS,
        benefit_criteria: list[bool] = BENEFIT_CRITERIA,
        alternatives:    list[str]   = PROTOCOLS,
    ):
        self.X       = decision_matrix.copy()
        self.w       = weights
        self.benefit = benefit_criteria
        self.alts    = alternatives

        assert self.X.shape[0] == len(self.alts), "Row count must match alternatives"
        assert self.X.shape[1] == len(self.w),    "Column count must match weights"
        assert abs(self.w.sum() - 1.0) < 1e-6,   "Weights must sum to 1.0"

    # ------------------------------------------------------------------
    # TOPSIS pipeline
    # ------------------------------------------------------------------

    def run(self) -> list[TOPSISResult]:
        R = self._normalise()
        V = self._weight(R)
        A_pos, A_neg = self._ideal_solutions(V)
        D_pos, D_neg = self._separation(V, A_pos, A_neg)
        C = self._closeness(D_pos, D_neg)
        return self._rank(C, D_pos, D_neg)

    def _normalise(self) -> np.ndarray:
        """Vector normalisation: r_ij = x_ij / sqrt(sum(x_kj^2))."""
        norms = np.sqrt((self.X ** 2).sum(axis=0))
        norms[norms == 0] = 1e-10   # avoid division by zero for NONE row
        return self.X / norms

    def _weight(self, R: np.ndarray) -> np.ndarray:
        """Weighted normalised matrix: v_ij = w_j * r_ij."""
        return R * self.w

    def _ideal_solutions(self, V: np.ndarray):
        """Compute A+ (positive ideal) and A- (negative ideal)."""
        A_pos = np.zeros(V.shape[1])
        A_neg = np.zeros(V.shape[1])
        for j in range(V.shape[1]):
            if self.benefit[j]:
                A_pos[j] = V[:, j].max()
                A_neg[j] = V[:, j].min()
            else:
                A_pos[j] = V[:, j].min()
                A_neg[j] = V[:, j].max()
        return A_pos, A_neg

    def _separation(self, V, A_pos, A_neg):
        """Euclidean distance to positive and negative ideals."""
        D_pos = np.sqrt(((V - A_pos) ** 2).sum(axis=1))
        D_neg = np.sqrt(((V - A_neg) ** 2).sum(axis=1))
        return D_pos, D_neg

    def _closeness(self, D_pos, D_neg) -> np.ndarray:
        """Relative closeness: C_i = D_neg / (D_pos + D_neg)."""
        denom = D_pos + D_neg
        denom[denom == 0] = 1e-10
        return D_neg / denom

    def _rank(self, C, D_pos, D_neg) -> list[TOPSISResult]:
        order = np.argsort(C)[::-1]   # descending
        results = []
        for rank, idx in enumerate(order, start=1):
            results.append(TOPSISResult(
                protocol=self.alts[idx],
                closeness_score=round(float(C[idx]), 6),
                rank=rank,
                d_positive=round(float(D_pos[idx]), 6),
                d_negative=round(float(D_neg[idx]), 6),
            ))
        return results

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def print_results(self, results: list[TOPSISResult]):
        print("\n" + "=" * 65)
        print("TOPSIS Multi-Criteria Ranking — BLE Encryption Protocols")
        print("=" * 65)
        print(f"{'Rank':<6} {'Protocol':<24} {'C_i Score':<12} "
              f"{'D+':<10} {'D-':<10}")
        print("-" * 65)
        for r in results:
            marker = " ← RECOMMENDED" if r.rank == 1 else ""
            print(f"{r.rank:<6} {r.protocol:<24} {r.closeness_score:<12.6f} "
                  f"{r.d_positive:<10.6f} {r.d_negative:<10.6f}{marker}")
        print("=" * 65)
        print(f"\nWeights (AHP-derived): Latency={self.w[0]}, "
              f"ProtectionRate={self.w[1]}, Memory={self.w[2]}, Power={self.w[3]}")
        print("Benefit criteria: ProtectionRate, PowerEfficiency")
        print("Cost criteria:    Latency, MemoryOverhead\n")


if __name__ == "__main__":
    analyzer = TOPSISAnalyzer()
    results  = analyzer.run()
    analyzer.print_results(results)
