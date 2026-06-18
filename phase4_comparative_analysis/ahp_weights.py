#!/usr/bin/env python3
"""
ahp_weights.py
Phase 4: Analytic Hierarchy Process — Criteria Weight Calculation

Derives priority weights for TOPSIS criteria using pairwise comparison
matrices (Saaty, 1980). Consistency Ratio (CR) must be < 0.10.

Criteria:
  C1 — Latency (ms)          weight: 0.35
  C2 — Protection Rate (%)   weight: 0.40
  C3 — Memory Overhead (KB)  weight: 0.15
  C4 — Power Efficiency      weight: 0.10

Praxis: Securing Brain-Computer Interfaces | Dr. Saheed Yusuf | GWU 2026
"""

import numpy as np


CRITERIA = ["Latency", "Protection Rate", "Memory Overhead", "Power Efficiency"]

# Saaty pairwise comparison matrix (expert-elicited)
# Interpretation: row_i is N times more important than col_j
PAIRWISE_MATRIX = np.array([
    # Lat   Prot  Mem   Pow
    [1.000, 0.750, 2.500, 3.500],   # Latency
    [1.333, 1.000, 3.000, 4.000],   # Protection Rate
    [0.400, 0.333, 1.000, 1.500],   # Memory Overhead
    [0.286, 0.250, 0.667, 1.000],   # Power Efficiency
], dtype=float)

# Random Index (RI) table for Saaty CR calculation
RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


class AHPCalculator:
    """
    Analytic Hierarchy Process weight derivation.

    Steps
    -----
    1. Column normalise the pairwise matrix
    2. Compute priority vector (row means of normalised matrix)
    3. Compute lambda_max (principal eigenvalue)
    4. Compute Consistency Index (CI) = (lambda_max - n) / (n - 1)
    5. Compute Consistency Ratio (CR) = CI / RI
    6. CR < 0.10 → acceptable; else revise pairwise judgements
    """

    def __init__(
        self,
        matrix: np.ndarray = PAIRWISE_MATRIX,
        criteria: list[str] = CRITERIA,
    ):
        self.A = matrix.copy()
        self.criteria = criteria
        self.n = len(criteria)

    def run(self) -> dict:
        """Run full AHP and return weights + consistency metrics."""
        norm = self._normalise()
        weights = norm.mean(axis=0)
        lambda_max = self._lambda_max(weights)
        CI = (lambda_max - self.n) / (self.n - 1)
        RI = RI_TABLE.get(self.n, 1.49)
        CR = CI / RI if RI > 0 else 0.0

        result = {
            "weights":     dict(zip(self.criteria, np.round(weights, 4))),
            "lambda_max":  round(lambda_max, 6),
            "CI":          round(CI, 6),
            "CR":          round(CR, 6),
            "consistent":  CR < 0.10,
        }
        self._print(result)
        return result

    def _normalise(self) -> np.ndarray:
        col_sums = self.A.sum(axis=0)
        return self.A / col_sums

    def _lambda_max(self, weights: np.ndarray) -> float:
        weighted_sum = self.A @ weights
        ratios = weighted_sum / weights
        return float(ratios.mean())

    def weights_array(self) -> np.ndarray:
        """Return weights as a numpy array (for TOPSIS)."""
        result = self.run()
        return np.array(list(result["weights"].values()))

    def _print(self, result: dict):
        print("\n" + "=" * 50)
        print("AHP Criteria Weights")
        print("=" * 50)
        for crit, w in result["weights"].items():
            bar = "█" * int(w * 40)
            print(f"  {crit:<22} {w:.4f}  {bar}")
        print(f"\n  λ_max = {result['lambda_max']}")
        print(f"  CI    = {result['CI']}")
        print(f"  CR    = {result['CR']}  "
              f"({'✅ Consistent' if result['consistent'] else '❌ Revise matrix'})")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    ahp = AHPCalculator()
    result = ahp.run()
