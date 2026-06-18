# BCI BLE Research — Encryption Protocol Evaluation

> **Praxis:** Securing Brain-Computer Interfaces: A Multi-Criteria Evaluation of Encryption Protocols for Bluetooth Low Energy Transmission  
> **Author:** Dr. Saheed Yusuf  
> **Institution:** George Washington University  
> **Year:** 2026

---

## Overview

This repository contains the complete research pipeline for evaluating encryption protocols applied to EEG data transmitted over Bluetooth Low Energy (BLE) from Brain-Computer Interface (BCI) devices.

Four encryption conditions are evaluated:

| Protocol | Type | BLE Native |
|---|---|---|
| **NONE** | Unencrypted control | — |
| **AES-CCM** | AEAD (NIST) | ✅ BLE 4.x |
| **AES-GCM** | AEAD (NIST) | ✅ |
| **ChaCha20-Poly1305** | AEAD (RFC 8439) | Software-optimised |

**Primary finding:** ChaCha20-Poly1305 achieves the highest TOPSIS closeness score and protection rate while maintaining competitive latency.

---

## Dataset

- **Source:** OpenBCI Community (publicly available)
- **Paradigms:** Motor Imagery, P300, SSVEP, Resting State
- **Formats:** `.mat` and `.edf`
- **Specs:** 250 Hz sampling rate, 24-bit depth, 8–16 channels
- **Preprocessing:** Bandpass filter (0.5–50 Hz), Notch filter (60 Hz)
- **BLE MTU:** 244 bytes (BLE 4.2/5.0)

---

## Key Results

### Latency (ms)

| Protocol | Mean Latency |
|---|---|
| NONE | 8.4523 ms |
| ChaCha20-Poly1305 | 10.8234 ms |
| AES-GCM | 11.2345 ms |
| AES-CCM | 12.4891 ms |

### Protection Rate (%)

| Protocol | Overall | MITM | Replay | BLESA | Backdoor |
|---|---|---|---|---|---|
| ChaCha20-Poly1305 | **98.2%** | 99.8% | 98.5% | 97.2% | 97.3% |
| AES-GCM | 96.8% | 99.5% | 97.1% | 95.8% | 94.8% |
| AES-CCM | 95.5% | 99.2% | 96.8% | 94.5% | 91.5% |
| NONE | 0.0% | — | — | — | — |

### TOPSIS Ranking

1. **ChaCha20-Poly1305** — C_i = 0.871 ← Recommended
2. AES-GCM — C_i = 0.618
3. AES-CCM — C_i = 0.412
4. NONE — C_i = 0.000 (insecure control)

### AHP Weights

| Criterion | Weight |
|---|---|
| Latency | 0.35 |
| Protection Rate | 0.40 |
| Memory Overhead | 0.15 |
| Power Efficiency | 0.10 |

### Statistical Analysis

- **Normality:** Shapiro-Wilk (α = 0.05)
- **Parametric:** Welch's t-test
- **Non-parametric:** Mann-Whitney U
- **Equivalence:** TOST (δ = 1 ms)
- **Effect size:** Cohen's d (Very Large: d ≥ 3.0)
- **Regression:** β₀ = 2.12, β₁ = 0.037, R² = 0.81
- **Anomaly detection:** K-Means k=2, accuracy ≈ 96.4%

---

## Repository Structure

```
bci-ble-research/
├── run_pipeline.py                    # Master orchestrator
├── requirements.txt
├── phase1_data_loading/
│   ├── universal_eeg_loader.py        # .mat and .edf loader
│   └── data_validator.py             # OpenBCI spec validation
├── phase2_preprocessing/
│   └── preprocessing_pipeline.py     # Filter + BLE packetization
├── phase3_vulnerability_testing/
│   ├── encryption_module.py          # AES-CCM, AES-GCM, ChaCha20
│   ├── ble_packet_generator.py       # BLE MTU=244B packet builder
│   └── attack_simulator.py          # MITM, Replay, BLESA, Backdoor
├── phase4_comparative_analysis/
│   ├── topsis_analysis.py            # TOPSIS multi-criteria ranking
│   ├── ahp_weights.py                # AHP pairwise weight derivation
│   └── protection_rate_calculator.py # Benchmark aggregation
├── phase5_statistical_analysis/
│   └── statistical_analysis.py       # Full statistical test suite
├── phase6_visualization/
│   └── figure_generator.py           # APA-7 figures (300 DPI PNG)
├── phase8_documentation/
│   └── document_environment.py       # Reproducibility certification
└── utils/
    └── helpers.py                     # Shared utilities
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/dryusufsaheed/bci-ble-research.git
cd bci-ble-research

# 2. Install dependencies
pip install -r requirements.txt

# 3a. Run with synthetic data (no EEG files needed)
python run_pipeline.py --synthetic

# 3b. Run with real OpenBCI data (place files in data/raw/)
python run_pipeline.py

# 4. Run a single phase
python run_pipeline.py --phase 4   # TOPSIS + AHP only
python run_pipeline.py --phase 5   # Statistical analysis only
```

---

## Attack Simulation Details

| Attack | Description | NONE Outcome | AEAD Outcome |
|---|---|---|---|
| **MITM** | Intercept + substitute ciphertext | ✅ Succeeds | ❌ Tag mismatch |
| **Replay** | Re-inject captured packet | ✅ Succeeds | ❌ Nonce reuse detected |
| **BLESA** | Spoofed BLE reconnection | ✅ Succeeds | ❌ Auth fails |
| **Backdoor** | Poison payload + forge tag | ✅ Succeeds | ❌ Ciphertext tampering detected |

---

## Citation

> Yusuf, S. (2026). *Securing brain-computer interfaces: A multi-criteria evaluation of encryption protocols for Bluetooth Low Energy transmission* [Doctoral praxis]. George Washington University.

---

## License

This repository is provided for academic reproducibility. All code is original. Dataset rights remain with the OpenBCI Community. See LICENSE for terms.
