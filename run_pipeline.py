#!/usr/bin/env python3
"""
run_pipeline.py
Master Pipeline Orchestrator

Executes all 8 phases of the BCI BLE encryption research pipeline in sequence.

Usage:  python run_pipeline.py [--phase N] [--synthetic]

Flags:
  --phase N      Run only phase N (1–8)
  --synthetic    Skip real EEG data loading; use synthetic packets

Praxis: Securing Brain-Computer Interfaces: A Multi-Criteria Evaluation
        of Encryption Protocols for Bluetooth Low Energy Transmission
Author: Dr. Saheed Yusuf | George Washington University | 2026
"""

import sys
import argparse
import time
from pathlib import Path


def run_phase1(synthetic: bool = False):
    print("\n▶ PHASE 1 — Data Loading")
    if synthetic:
        print("  [Synthetic mode] Skipping EEG file loading.")
        return None
    try:
        from phase1_data_loading.universal_eeg_loader import UniversalEEGLoader
        loader = UniversalEEGLoader(data_dir="data/raw")
        datasets = loader.load_all_paradigms()
        loader.summary()
        return datasets
    except Exception as e:
        print(f"  [Phase 1] WARNING: {e}. Falling back to synthetic mode.")
        return None


def run_phase2(datasets):
    print("\n▶ PHASE 2 — Preprocessing")
    from phase2_preprocessing.preprocessing_pipeline import PreprocessingPipeline
    pipeline = PreprocessingPipeline(sampling_rate=250)
    all_packets = []
    if datasets:
        for ds in datasets:
            pkts = pipeline.process(ds)
            all_packets.extend(pkts)
    else:
        from phase3_vulnerability_testing.ble_packet_generator import BLEPacketGenerator
        gen = BLEPacketGenerator()
        all_packets = gen.generate_synthetic(n_packets=200, paradigm="Motor Imagery")
        print(f"  [Synthetic] Generated {len(all_packets)} BLE packets.")
    return all_packets


def run_phase3(packets):
    print("\n▶ PHASE 3 — Vulnerability Testing")
    from phase3_vulnerability_testing.encryption_module import (
        EncryptionEngine, EncryptionProtocol
    )
    from phase3_vulnerability_testing.attack_simulator import AttackSimulator

    sim = AttackSimulator()
    all_results = {}
    sample_pkts = packets[:50]   # limit for speed

    for proto in EncryptionProtocol:
        engine   = EncryptionEngine(proto)
        enc_pkts = [engine.encrypt(p) for p in sample_pkts]
        results  = sim.run_all(enc_pkts, engine)
        rates    = sim.protection_rate(results)
        all_results[proto.value] = rates
        overall = sum(rates.values()) / len(rates) if rates else 0
        print(f"  {proto.value:<22} Overall protection: {overall:.1f}%")

    return all_results


def run_phase4():
    print("\n▶ PHASE 4 — Comparative Analysis (AHP + TOPSIS)")
    from phase4_comparative_analysis.ahp_weights import AHPCalculator
    from phase4_comparative_analysis.topsis_analysis import TOPSISAnalyzer
    from phase4_comparative_analysis.protection_rate_calculator import ProtectionRateCalculator

    ahp      = AHPCalculator()
    ahp.run()

    topsis   = TOPSISAnalyzer()
    rankings = topsis.run()
    topsis.print_results(rankings)

    calc      = ProtectionRateCalculator()
    benchmarks = calc.from_empirical()
    calc.print_table(benchmarks)

    return rankings


def run_phase5():
    print("\n▶ PHASE 5 — Statistical Analysis")
    from phase5_statistical_analysis.statistical_analysis import StatisticalAnalyzer
    analyzer = StatisticalAnalyzer(n_samples=120)
    analyzer.run_all()


def run_phase6():
    print("\n▶ PHASE 6 — Figure Generation (APA-7, 300 DPI)")
    from phase6_visualization.figure_generator import FigureGenerator
    gen = FigureGenerator()
    gen.generate_all()


def run_phase8():
    print("\n▶ PHASE 8 — Documentation & Reproducibility")
    from phase8_documentation.document_environment import EnvironmentDocumenter
    doc = EnvironmentDocumenter()
    doc.run()


def main():
    parser = argparse.ArgumentParser(description="BCI BLE Research Pipeline")
    parser.add_argument("--phase", type=int, default=0, help="Run single phase (1-8)")
    parser.add_argument("--synthetic", action="store_true",
                        help="Use synthetic data (no EEG files required)")
    args = parser.parse_args()

    t_start = time.perf_counter()
    print("\n" + "=" * 60)
    print("BCI BLE RESEARCH PIPELINE")
    print("Dr. Saheed Yusuf | GWU | 2026")
    print("=" * 60)

    if args.phase == 0:
        # Run all phases
        datasets = run_phase1(synthetic=args.synthetic)
        packets  = run_phase2(datasets)
        run_phase3(packets)
        run_phase4()
        run_phase5()
        run_phase6()
        run_phase8()
    elif args.phase == 1:
        run_phase1(synthetic=args.synthetic)
    elif args.phase == 2:
        packets = run_phase2(None if args.synthetic else [])
    elif args.phase == 3:
        from phase3_vulnerability_testing.ble_packet_generator import BLEPacketGenerator
        pkts = BLEPacketGenerator().generate_synthetic(100)
        run_phase3(pkts)
    elif args.phase == 4:
        run_phase4()
    elif args.phase == 5:
        run_phase5()
    elif args.phase == 6:
        run_phase6()
    elif args.phase == 8:
        run_phase8()
    else:
        print(f"Unknown phase: {args.phase}. Valid: 1-6, 8.")

    elapsed = time.perf_counter() - t_start
    print(f"\n✅ Pipeline complete in {elapsed:.2f}s\n")


if __name__ == "__main__":
    main()
