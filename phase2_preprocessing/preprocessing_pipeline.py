#!/usr/bin/env python3
"""
preprocessing_pipeline.py
Phase 2: EEG Signal Preprocessing

Applies bandpass (0.5–50 Hz) and notch (60 Hz) filters to raw EEG data,
then converts filtered signals to BLE-compliant 244-byte MTU packets.

Praxis: Securing Brain-Computer Interfaces | Dr. Saheed Yusuf | GWU 2026
"""

import numpy as np
import struct
from dataclasses import dataclass
from scipy.signal import butter, filtfilt, iirnotch
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1_data_loading'))
from universal_eeg_loader import EEGDataset


# BLE 4.2 / 5.0 maximum ATT payload
BLE_MTU_BYTES   = 244
BANDPASS_LOW_HZ  = 0.5
BANDPASS_HIGH_HZ = 50.0
NOTCH_FREQ_HZ    = 60.0
FILTER_ORDER     = 4


@dataclass
class BLEPacket:
    """Represents a single BLE data packet carrying EEG samples."""
    packet_id:    int
    channel_id:   int
    paradigm:     str
    payload:      bytes           # raw bytes, len ≤ BLE_MTU_BYTES
    sample_count: int             # number of float32 samples in payload
    timestamp_ms: float


class PreprocessingPipeline:
    """
    Two-stage pipeline:
        Stage 1 — Filter   : bandpass (0.5–50 Hz) + notch (60 Hz)
        Stage 2 — Packetize: convert filtered signal to BLE packets
    """

    def __init__(self, sampling_rate: int = 250):
        self.fs = sampling_rate

    # ------------------------------------------------------------------
    # Stage 1: Filtering
    # ------------------------------------------------------------------

    def filter_dataset(self, dataset: EEGDataset) -> np.ndarray:
        """
        Apply bandpass then notch filter to every channel.

        Returns
        -------
        filtered: ndarray of shape (n_channels, n_samples), float64
        """
        filtered = np.zeros_like(dataset.data)
        for ch_idx in range(dataset.num_channels):
            signal = dataset.data[ch_idx, :]
            bp = self._bandpass(signal)
            filtered[ch_idx, :] = self._notch(bp)
        print(f"[Preprocess] Filtered {dataset.paradigm}: "
              f"{dataset.num_channels} ch × "
              f"{dataset.data.shape[1]} samples")
        return filtered

    def _bandpass(self, signal: np.ndarray) -> np.ndarray:
        """4th-order Butterworth bandpass 0.5–50 Hz."""
        nyq = self.fs / 2.0
        b, a = butter(
            FILTER_ORDER,
            [BANDPASS_LOW_HZ / nyq, BANDPASS_HIGH_HZ / nyq],
            btype="band",
        )
        return filtfilt(b, a, signal)

    def _notch(self, signal: np.ndarray) -> np.ndarray:
        """IIR notch at 60 Hz (US power-line interference)."""
        q = 30.0   # quality factor
        b, a = iirnotch(NOTCH_FREQ_HZ / (self.fs / 2.0), q)
        return filtfilt(b, a, signal)

    # ------------------------------------------------------------------
    # Stage 2: BLE Packetization
    # ------------------------------------------------------------------

    def packetize(
        self,
        filtered_data: np.ndarray,
        paradigm: str,
        start_time_ms: float = 0.0,
    ) -> list[BLEPacket]:
        """
        Convert a filtered multi-channel signal into BLE packets.

        Each packet carries as many float32 samples as fit within
        BLE_MTU_BYTES (244 bytes). float32 = 4 bytes → 61 samples/packet.

        Parameters
        ----------
        filtered_data : ndarray (n_channels, n_samples)
        paradigm      : paradigm label string
        start_time_ms : timestamp offset for the first packet

        Returns
        -------
        list of BLEPacket
        """
        n_channels, n_samples = filtered_data.shape
        # float32 samples per packet
        samples_per_packet = BLE_MTU_BYTES // 4   # = 61

        packets: list[BLEPacket] = []
        packet_id = 0
        sample_interval_ms = 1000.0 / self.fs   # ms per sample

        for ch in range(n_channels):
            ch_signal = filtered_data[ch, :].astype(np.float32)
            for start in range(0, n_samples, samples_per_packet):
                chunk = ch_signal[start:start + samples_per_packet]
                payload = struct.pack(f"{len(chunk)}f", *chunk)

                # Pad to MTU if last chunk is short
                payload = payload.ljust(BLE_MTU_BYTES, b'\x00')

                ts = start_time_ms + start * sample_interval_ms
                packets.append(BLEPacket(
                    packet_id=packet_id,
                    channel_id=ch,
                    paradigm=paradigm,
                    payload=payload,
                    sample_count=len(chunk),
                    timestamp_ms=ts,
                ))
                packet_id += 1

        print(f"[Preprocess] Generated {len(packets)} BLE packets "
              f"({n_channels} ch × {n_samples} samples, MTU={BLE_MTU_BYTES}B)")
        return packets

    # ------------------------------------------------------------------
    # Convenience end-to-end
    # ------------------------------------------------------------------

    def process(self, dataset: EEGDataset) -> list[BLEPacket]:
        """Filter then packetize a dataset in one call."""
        filtered = self.filter_dataset(dataset)
        return self.packetize(filtered, dataset.paradigm)


if __name__ == "__main__":
    from universal_eeg_loader import UniversalEEGLoader
    loader = UniversalEEGLoader(data_dir="../data/raw")
    datasets = loader.load_all_paradigms()
    pipeline = PreprocessingPipeline(sampling_rate=250)
    for ds in datasets:
        packets = pipeline.process(ds)
        print(f"  → {ds.paradigm}: {len(packets)} packets ready for encryption\n")
