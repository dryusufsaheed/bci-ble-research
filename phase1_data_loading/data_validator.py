#!/usr/bin/env python3
"""
data_validator.py
Phase 1: Data Validation

Validates loaded EEG datasets against OpenBCI specification constraints
before preprocessing and BLE packet conversion.

Praxis: Securing Brain-Computer Interfaces | Dr. Saheed Yusuf | GWU 2026
"""

import numpy as np
from universal_eeg_loader import EEGDataset, SAMPLING_RATE, BIT_DEPTH, CHANNEL_RANGE


class DataValidator:
    """
    Validates EEGDataset objects against expected OpenBCI specifications.

    Checks performed
    ----------------
    1. Sampling rate matches 250 Hz
    2. Bit depth is 24-bit
    3. Channel count within [8, 16]
    4. No NaN or Inf values
    5. Signal amplitude within physiologically plausible range (±500 µV)
    6. Duration greater than zero
    """

    AMPLITUDE_LIMIT_UV = 500.0   # microvolts — physiological plausibility bound

    def validate(self, dataset: EEGDataset) -> dict:
        """
        Run full validation suite on a dataset.

        Returns
        -------
        dict with keys: passed (bool), checks (list of dicts)
        """
        checks = [
            self._check_sampling_rate(dataset),
            self._check_bit_depth(dataset),
            self._check_channels(dataset),
            self._check_nan_inf(dataset),
            self._check_amplitude(dataset),
            self._check_duration(dataset),
        ]
        passed = all(c["passed"] for c in checks)
        return {"dataset": dataset.paradigm, "passed": passed, "checks": checks}

    def validate_all(self, datasets: list[EEGDataset]) -> list[dict]:
        results = [self.validate(ds) for ds in datasets]
        n_pass = sum(r["passed"] for r in results)
        print(f"\n[Validator] {n_pass}/{len(results)} dataset(s) passed all checks.\n")
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"  {status}  {r['dataset']}")
            for chk in r["checks"]:
                if not chk["passed"]:
                    print(f"         ↳ FAILED: {chk['name']} — {chk['detail']}")
        return results

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_sampling_rate(self, ds: EEGDataset) -> dict:
        ok = ds.sampling_rate == SAMPLING_RATE
        return {
            "name": "Sampling rate",
            "passed": ok,
            "detail": f"{ds.sampling_rate} Hz (expected {SAMPLING_RATE} Hz)",
        }

    def _check_bit_depth(self, ds: EEGDataset) -> dict:
        ok = ds.bit_depth == BIT_DEPTH
        return {
            "name": "Bit depth",
            "passed": ok,
            "detail": f"{ds.bit_depth}-bit (expected {BIT_DEPTH}-bit)",
        }

    def _check_channels(self, ds: EEGDataset) -> dict:
        lo, hi = CHANNEL_RANGE
        ok = lo <= ds.num_channels <= hi
        return {
            "name": "Channel count",
            "passed": ok,
            "detail": f"{ds.num_channels} channels (expected {lo}–{hi})",
        }

    def _check_nan_inf(self, ds: EEGDataset) -> dict:
        has_nan = np.isnan(ds.data).any()
        has_inf = np.isinf(ds.data).any()
        ok = not has_nan and not has_inf
        detail = []
        if has_nan:
            detail.append(f"{np.isnan(ds.data).sum()} NaN value(s)")
        if has_inf:
            detail.append(f"{np.isinf(ds.data).sum()} Inf value(s)")
        return {
            "name": "NaN/Inf check",
            "passed": ok,
            "detail": ", ".join(detail) if detail else "Clean",
        }

    def _check_amplitude(self, ds: EEGDataset) -> dict:
        max_abs = float(np.max(np.abs(ds.data)))
        ok = max_abs <= self.AMPLITUDE_LIMIT_UV
        return {
            "name": "Amplitude plausibility",
            "passed": ok,
            "detail": f"Max |amplitude| = {max_abs:.2f} µV "
                      f"(limit {self.AMPLITUDE_LIMIT_UV} µV)",
        }

    def _check_duration(self, ds: EEGDataset) -> dict:
        ok = ds.duration_seconds > 0
        return {
            "name": "Duration",
            "passed": ok,
            "detail": f"{ds.duration_seconds:.2f} s",
        }


if __name__ == "__main__":
    from universal_eeg_loader import UniversalEEGLoader
    loader = UniversalEEGLoader(data_dir="data/raw")
    datasets = loader.load_all_paradigms()
    validator = DataValidator()
    validator.validate_all(datasets)
