# BCI-BLE Encryption Security Research

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

**Doctoral Praxis Research** - George Washington University  
**Author:** Dr. Saheed Yusuf  
**Research Focus:** Securing Brain-Computer Interfaces via Bluetooth Low Energy

---

## 🎯 Research Overview

This repository contains the complete implementation of a doctoral praxis investigating **authenticated encryption protocols for Bluetooth Low Energy (BLE) communication in Brain-Computer Interface (BCI) systems**.

### Key Research Questions
1. **RQ1:** Can encryption protocols protect BCI data against eavesdropping?
2. **RQ2:** Which encryption protocol offers optimal security-performance balance?
3. **RQ3:** Is encryption latency practically negligible for real-time BCIs?

### Primary Contributions
1. **First comprehensive security evaluation** of authenticated encryption (AES-GCM, AES-CCM, ChaCha20-Poly1305) for BCI/BLE using real EEG data
2. **Novel multi-criteria risk assessment framework** integrating vulnerability testing, latency analysis, and implementation complexity via TOPSIS/AHP
3. **Empirical validation** against MITM, Replay, BLESA, and Backdoor attacks

---

## 📊 Key Findings

| Metric | NONE | AES-CCM | AES-GCM | ChaCha20-Poly1305 |
|--------|------|---------|---------|-------------------|
| MITM Protection | 0% | **95%** | **95%** | **95%** |
| Replay Protection | 0% | **95%** | **95%** | **95%** |
| Avg Latency (ms) | 8.5 | 12.5 | 11.2 | **10.8** |
| TOPSIS Score | 0.12 | 0.54 | 0.68 | **0.87** |

**Recommendation:** ChaCha20-Poly1305 for optimal security-performance tradeoff

---

## 📁 Repository Structure

```
BCI-BLE-Encryption/
├── phase1_data_preparation/          # EEG data loading (supports .mat, .edf)
│   └── universal_eeg_loader.py
├── phase3_vulnerability_testing/      # Encryption & attack simulation
│   ├── encryption_module.py            # AES-GCM, AES-CCM, ChaCha20
│   ├── eeg_to_ble_converter.py        # EEG → BLE packets
│   └── vulnerability_tester.py         # MITM, Replay tests
├── phase4_comparative_analysis/       # AHP/TOPSIS ranking
│   ├── ahp_analysis.py                 # Analytic Hierarchy Process
│   └── topsis_analysis.py              # TOPSIS ranking
├── phase5_latency_analysis/           # Statistical analysis
│   ├── measure_latency.py              # Latency measurement
│   ├── statistical_analysis.py         # T-tests, TOST, power analysis
│   └── create_statistical_plots.py    # Distribution plots
├── documentation/                      # Research methodology
├── setup.py                            # Package installation
├── requirements.txt                    # Dependencies
└── README.md                           # This file
```

---

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/dryusufsaheed/BCI-BLE-Encryption.git
cd BCI-BLE-Encryption

# Install dependencies
pip install -r requirements.txt

# Install as package (optional)
pip install -e .
```

### Basic Usage

#### 1. Load EEG Data
```python
from phase1_data_preparation.universal_eeg_loader import UniversalEEGLoader

# Supports both .mat and .edf formats
loader = UniversalEEGLoader('your_dataset.mat')
if loader.load():
    loader.print_summary()
    eeg_data = loader.data  # channels × samples
```

#### 2. Test Encryption
```python
from phase3_vulnerability_testing.encryption_module import BCIEncryption

# Test all protocols
for protocol in ['NONE', 'AES-GCM', 'AES-CCM', 'ChaCha20-Poly1305']:
    enc = BCIEncryption(protocol=protocol)
    ciphertext, nonce, tag, metadata = enc.encrypt_packet(test_data)
    plaintext, valid, error = enc.decrypt_packet(ciphertext, nonce, tag, metadata)
    print(f"{protocol}: {'✓ OK' if valid else '✗ FAILED'}")
```

#### 3. Run Complete Pipeline
```bash
# Phase 3: Vulnerability Testing
cd phase3_vulnerability_testing
./RUN_PHASE3.sh

# Phase 4: Comparative Analysis
cd ../phase4_comparative_analysis
./RUN_PHASE4.sh

# Phase 5: Latency Analysis
cd ../phase5_latency_analysis
./RUN_PHASE5.sh
```

---

## 📋 Dataset Specifications

**OpenBCI Community EEG Dataset**

- **Sampling Rate:** 250 Hz
- **Channels:** 8-16 EEG channels
- **Resolution:** 24-bit
- **File Formats:** .mat (MATLAB), .edf (European Data Format)

### Paradigms
- Motor Imagery
- P300
- SSVEP
- Resting State

### Preprocessing
- Bandpass filter: 0.5-50 Hz
- Notch filter: 60 Hz
- BLE packet MTU: 244 bytes

---

## 🔐 Encryption Protocols Tested

### 1. **AES-GCM** (Advanced Encryption Standard - Galois/Counter Mode)
- 128/256-bit key options
- Hardware-accelerated
- Industry standard for IoT
- Good latency profile

### 2. **AES-CCM** (AES - Counter with CBC-MAC)
- 128/256-bit key options
- Suitable for constrained devices
- Moderate latency impact

### 3. **ChaCha20-Poly1305** (Chacha20 + Poly1305)
- Modern stream cipher
- Optimal latency performance
- Cryptographically superior
- **Recommended choice**

---

## 📈 Methodology

### Phase 1: Data Preparation
Load and preprocess OpenBCI EEG datasets

### Phase 3: Vulnerability Testing
- Convert EEG data to BLE packet streams (244-byte MTU)
- Implement AES-GCM, AES-CCM, ChaCha20-Poly1305 encryption
- Simulate attacks: MITM, Replay, BLESA, Backdoor

### Phase 4: Comparative Analysis
- Apply **AHP** to determine criterion importance weights
- Use **TOPSIS** to rank protocols across 7 criteria
- Generate publication-ready figures and tables

### Phase 5: Latency Analysis
- Measure encryption/decryption latency (1000+ trials per protocol)
- Conduct statistical hypothesis testing (t-tests, TOST)
- Calculate effect sizes and power analysis

---

## 📊 Key Results

### Hypothesis Testing Results

**H₀₁: Protection ≤10%**
- Result: REJECTED
- Finding: 95-100% protection achieved across encrypted protocols
- p-value: < 0.001

**H₀₂: TOPSIS Δ ≤0.05**
- Result: REJECTED
- Finding: ChaCha20-Poly1305 superior (0.87 vs 0.68 for AES-GCM)
- p-value: < 0.001

**H₀₃: Latency Δ ≤0.5ms**
- Result: REJECTED
- Finding: 2.3-4.0ms increase, practically negligible for BCIs
- p-value: < 0.001, Cohen's d > 6.0

---

## 🛠️ Dependencies

```
numpy >= 1.21.0
pandas >= 1.3.0
scipy >= 1.7.0
matplotlib >= 3.4.0
seaborn >= 0.11.0
mne >= 0.23.0
h5py >= 3.0.0
pyedflib >= 0.1.0
pycryptodome >= 3.13.0
```

---

## 📝 Citation

If you use this code in your research, please cite:

```bibtex
@thesis{yusuf2026bci,
  title={Securing Brain-Computer Interfaces: A Multi-Criteria Evaluation 
         of Encryption Protocols for Bluetooth Low Energy Transmission},
  author={Yusuf, Saheed},
  school={George Washington University},
  year={2026}
}
```

---

## 📚 Documentation

- [METHODOLOGY.md](documentation/METHODOLOGY.md) - Detailed research methodology
- [RESULTS_INTERPRETATION.md](documentation/RESULTS_INTERPRETATION.md) - How to interpret results
- Individual phase README files

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- [ ] Additional encryption protocols (e.g., Crypto-GCM)
- [ ] Support for other EEG devices (NeuroSky, Emotiv, etc.)
- [ ] Real-world attack simulations with SDR
- [ ] Performance benchmarking on embedded systems
- [ ] Docker containerization

---

## ⚖️ License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Dr. Saheed Yusuf**
- 🎓 Doctoral Candidate, George Washington University
- 🏢 Information Security Manager, 32BJ Benefit Funds
- 🔐 Certifications: CISSP, CEH
- 🌍 GitHub: [@dryusufsaheed](https://github.com/dryusufsaheed)

---

## ⭐ Acknowledgments

- George Washington University - Doctoral Praxis Supervision
- OpenBCI Community - EEG Dataset
- Research Advisors & Committee Members

---

**Last Updated:** June 2026  
**Status:** Active Research

---

## 📞 Contact & Support

For questions about:
- **Research methodology:** See [METHODOLOGY.md](documentation/METHODOLOGY.md)
- **Code usage:** See phase-specific README files
- **Bug reports:** Open a GitHub Issue
- **General inquiries:** saheed@32bjbenefits.org

---

*"Security through cryptography, validation through real-world EEG data"*
