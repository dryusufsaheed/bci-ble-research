#!/usr/bin/env python3
"""
universal_eeg_loader.py
Phase 1: Data Loading and Validation

Loads EEG datasets from OpenBCI Community in .mat and .edf formats.
Supports four paradigms: Motor Imagery, P300, SSVEP, Resting State.

Praxis: Securing Brain-Computer Interfaces: A Multi-Criteria Evaluation
        of Encryption Protocols for Bluetooth Low Energy Transmission
Author: Dr. Saheed Yusuf | George Washington University | 2026
"""

import os
import numpy as np
import scipy.io as sio
import mne
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EEGDataset:
    """Container for loaded EEG data and associated metadata."""
    paradigm: str
    sampling_rate: int
    bit_depth: int
    num_channels: int
    duration_seconds: float
    data: np.ndarray
    channel_names: list
    file_format: str
    file_path: str
    labels: Optional[np.ndarray] = None


# Paradigm identifiers matching OpenBCI Community dataset structure
PARADIGMS = {
    "motor_imagery": "Motor Imagery",
    "p300":          "P300",
    "ssvep":         "SSVEP",
    "resting_state": "Resting State",
}

SAMPLING_RATE  = 250    # Hz — OpenBCI Cyton spec
BIT_DEPTH      = 24     # bits
CHANNEL_RANGE  = (8, 16)


class UniversalEEGLoader:
    """
    Unified loader for OpenBCI EEG files in .mat and .edf formats.

    Supports automatic format detection and consistent output regardless
    of source format, enabling reproducible cross-paradigm analysis.
    """

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.loaded_datasets: list[EEGDataset] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load_all_paradigms(self) -> list[EEGDataset]:
        """Load all four paradigm datasets found in data_dir."""
        datasets = []
        for paradigm_key in PARADIGMS:
            files = self._find_files(paradigm_key)
            for fp in files:
                dataset = self.load_file(fp, paradigm_key)
                if dataset:
                    datasets.append(dataset)
        self.loaded_datasets = datasets
        print(f"[Loader] Loaded {len(datasets)} dataset(s) across "
              f"{len(PARADIGMS)} paradigm(s).")
        return datasets

    def load_file(self, filepath: str | Path, paradigm: str) -> Optional[EEGDataset]:
        """Load a single .mat or .edf file."""
        filepath = Path(filepath)
        ext = filepath.suffix.lower()
        try:
            if ext == ".mat":
                return self._load_mat(filepath, paradigm)
            elif ext == ".edf":
                return self._load_edf(filepath, paradigm)
            else:
                print(f"[Loader] Unsupported format: {ext}")
                return None
        except Exception as exc:
            print(f"[Loader] ERROR loading {filepath.name}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Format-specific loaders
    # ------------------------------------------------------------------

    def _load_mat(self, filepath: Path, paradigm: str) -> EEGDataset:
        mat = sio.loadmat(str(filepath), squeeze_me=True)

        # Common key patterns in OpenBCI-derived .mat exports
        data_key = next(
            (k for k in mat if k in ("EEG", "data", "signal", "eeg")), None
        )
        if data_key is None:
            raise KeyError(f"No recognised data key in {filepath.name}. "
                           f"Keys: {list(mat.keys())}")

        raw = np.array(mat[data_key], dtype=np.float64)
        if raw.ndim == 1:
            raw = raw.reshape(1, -1)

        n_channels, n_samples = raw.shape
        duration = n_samples / SAMPLING_RATE

        labels = mat.get("labels", mat.get("y", None))
        channel_names = [f"CH{i+1}" for i in range(n_channels)]

        return EEGDataset(
            paradigm=PARADIGMS.get(paradigm, paradigm),
            sampling_rate=SAMPLING_RATE,
            bit_depth=BIT_DEPTH,
            num_channels=n_channels,
            duration_seconds=duration,
            data=raw,
            channel_names=channel_names,
            file_format="mat",
            file_path=str(filepath),
            labels=np.array(labels) if labels is not None else None,
        )

    def _load_edf(self, filepath: Path, paradigm: str) -> EEGDataset:
        raw_edf = mne.io.read_raw_edf(str(filepath), preload=True, verbose=False)
        data, _ = raw_edf[:, :]          # shape: (n_channels, n_times)
        data = data.astype(np.float64)

        n_channels, n_samples = data.shape
        fs = int(raw_edf.info["sfreq"])
        duration = n_samples / fs
        ch_names = raw_edf.ch_names

        return EEGDataset(
            paradigm=PARADIGMS.get(paradigm, paradigm),
            sampling_rate=fs,
            bit_depth=BIT_DEPTH,
            num_channels=n_channels,
            duration_seconds=duration,
            data=data,
            channel_names=ch_names,
            file_format="edf",
            file_path=str(filepath),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_files(self, paradigm_key: str) -> list[Path]:
        pattern_map = {
            "motor_imagery": ["*motor*", "*MI*"],
            "p300":          ["*p300*", "*P300*"],
            "ssvep":         ["*ssvep*", "*SSVEP*"],
            "resting_state": ["*rest*", "*RS*"],
        }
        found = []
        for pattern in pattern_map.get(paradigm_key, [f"*{paradigm_key}*"]):
            found.extend(self.data_dir.rglob(pattern + ".mat"))
            found.extend(self.data_dir.rglob(pattern + ".edf"))
        return list(set(found))

    def summary(self):
        """Print dataset summary table."""
        if not self.loaded_datasets:
            print("[Loader] No datasets loaded yet.")
            return
        print("\n" + "=" * 60)
        print(f"{'Paradigm':<20} {'Format':<6} {'Channels':<10} "
              f"{'Duration(s)':<14} {'Samples':<10}")
        print("-" * 60)
        for ds in self.loaded_datasets:
            n_samples = int(ds.duration_seconds * ds.sampling_rate)
            print(f"{ds.paradigm:<20} {ds.file_format:<6} {ds.num_channels:<10} "
                  f"{ds.duration_seconds:<14.2f} {n_samples:<10}")
        print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = UniversalEEGLoader(data_dir="data/raw")
    datasets = loader.load_all_paradigms()
    loader.summary()
