#!/usr/bin/env python3
"""
Latency Measurement Framework
Measures encryption/decryption latency with real EEG data
"""

import sys
import time
import numpy as np
import pandas as pd
import pickle
from pathlib import Path

# Import encryption module from Phase 3
sys.path.append('../../phase3_testing/scripts')
from encryption_module import BCIEncryption

class LatencyMeasurement:
    """
    Measures encryption/decryption latency for BLE BCI communications
    """
    
    def __init__(self, packet_stream_file):
        """
        Load packet stream from Phase 3
        """
        print(f"\n{'='*70}")
        print("LATENCY MEASUREMENT FRAMEWORK")
        print(f"{'='*70}")
        
        with open(packet_stream_file, 'rb') as f:
            data = pickle.load(f)
        
        self.packets = data['packets']
        self.metadata = data['metadata']
        self.dataset_id = data['dataset_id']
        
        print(f"Dataset: {self.dataset_id}")
        print(f"Packets available: {len(self.packets):,}")
        
        self.latency_results = []
    
    def measure_protocol_latency(self, protocol='AES-GCM', n_trials=1000, warmup=100):
        """
        Measure latency for a specific protocol
        
        Args:
            protocol: Encryption protocol to test
            n_trials: Number of measurement trials
            warmup: Number of warmup iterations (excluded from results)
        """
        print(f"\n{'#'*70}")
        print(f"# Measuring Latency: {protocol}")
        print(f"{'#'*70}")
        print(f"Trials: {n_trials}")
        print(f"Warmup: {warmup}")
        
        # Initialize encryption
        if protocol == 'NONE':
            enc = None
        else:
            enc = BCIEncryption(protocol=protocol, key_size=128)
        
        # Prepare test packets
        test_packets = self.packets[:n_trials + warmup]
        
        encryption_times = []
        decryption_times = []
        total_times = []
        
        print("\nRunning trials...")
        
        for i, packet in enumerate(test_packets):
            if protocol == 'NONE':
                # Measure baseline (no encryption)
                start = time.perf_counter()
                # Simulate minimal processing
                _ = packet
                enc_time = time.perf_counter() - start
                
                start = time.perf_counter()
                _ = packet
                dec_time = time.perf_counter() - start
                
            else:
                # Measure encryption
                start = time.perf_counter()
                ciphertext, nonce, tag, metadata = enc.encrypt_packet(packet, i)
                enc_time = time.perf_counter() - start
                
                # Measure decryption
                start = time.perf_counter()
                plaintext, valid, error = enc.decrypt_packet(ciphertext, nonce, tag, metadata)
                dec_time = time.perf_counter() - start
            
            total_time = enc_time + dec_time
            
            # Skip warmup iterations
            if i >= warmup:
                encryption_times.append(enc_time * 1000)  # Convert to ms
                decryption_times.append(dec_time * 1000)
                total_times.append(total_time * 1000)
            
            # Progress indicator
            if (i + 1) % 200 == 0:
                print(f"  Progress: {i+1}/{len(test_packets)}")
        
        # Calculate statistics
        results = {
            'protocol': protocol,
            'dataset': self.dataset_id,
            'n_trials': n_trials,
            'encryption_mean_ms': np.mean(encryption_times),
            'encryption_std_ms': np.std(encryption_times, ddof=1),
            'encryption_median_ms': np.median(encryption_times),
            'encryption_min_ms': np.min(encryption_times),
            'encryption_max_ms': np.max(encryption_times),
            'decryption_mean_ms': np.mean(decryption_times),
            'decryption_std_ms': np.std(decryption_times, ddof=1),
            'decryption_median_ms': np.median(decryption_times),
            'decryption_min_ms': np.min(decryption_times),
            'decryption_max_ms': np.max(decryption_times),
            'total_mean_ms': np.mean(total_times),
            'total_std_ms': np.std(total_times, ddof=1),
            'total_median_ms': np.median(total_times),
            'total_min_ms': np.min(total_times),
            'total_max_ms': np.max(total_times),
            'raw_encryption_times': encryption_times,
            'raw_decryption_times': decryption_times,
            'raw_total_times': total_times
        }
        
        print(f"\n{'='*70}")
        print("RESULTS")
        print(f"{'='*70}")
        print(f"Encryption:  {results['encryption_mean_ms']:.4f} ± {results['encryption_std_ms']:.4f} ms")
        print(f"Decryption:  {results['decryption_mean_ms']:.4f} ± {results['decryption_std_ms']:.4f} ms")
        print(f"Total:       {results['total_mean_ms']:.4f} ± {results['total_std_ms']:.4f} ms")
        print(f"{'='*70}")
        
        self.latency_results.append(results)
        
        return results
    
    def measure_all_protocols(self, n_trials=1000, warmup=100):
        """
        Measure latency for all protocols
        """
        protocols = ['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']
        
        print(f"\n{'='*70}")
        print("MEASURING ALL PROTOCOLS")
        print(f"{'='*70}")
        
        all_results = []
        
        for protocol in protocols:
            results = self.measure_protocol_latency(protocol, n_trials, warmup)
            all_results.append(results)
            time.sleep(2)  # Brief pause between protocols
        
        return all_results
    
    def save_results(self, output_dir='../data'):
        """
        Save latency measurement results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create summary DataFrame
        summary_data = []
        for result in self.latency_results:
            summary_data.append({
                'Protocol': result['protocol'],
                'Dataset': result['dataset'],
                'N_Trials': result['n_trials'],
                'Encryption_Mean_ms': result['encryption_mean_ms'],
                'Encryption_Std_ms': result['encryption_std_ms'],
                'Decryption_Mean_ms': result['decryption_mean_ms'],
                'Decryption_Std_ms': result['decryption_std_ms'],
                'Total_Mean_ms': result['total_mean_ms'],
                'Total_Std_ms': result['total_std_ms']
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Save summary
        summary_file = output_path / f'latency_summary_{self.dataset_id}.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"\n✓ Summary saved: {summary_file}")
        
        # Save raw data
        raw_file = output_path / f'latency_raw_{self.dataset_id}.pkl'
        with open(raw_file, 'wb') as f:
            pickle.dump(self.latency_results, f)
        print(f"✓ Raw data saved: {raw_file}")
        
        return summary_file, raw_file


def measure_all_datasets(packet_dir='../../phase3_testing/datasets/ble_packets',
                         n_trials=1000, warmup=100):
    """
    Measure latency across all datasets
    """
    packet_path = Path(packet_dir)
    packet_files = list(packet_path.glob('*_packets.pkl'))
    
    if not packet_files:
        print(f"\n✗ No packet files found in {packet_dir}")
        print("Please complete Phase 3 first!")
        return None
    
    print(f"\n{'='*70}")
    print("COMPREHENSIVE LATENCY MEASUREMENT")
    print(f"{'='*70}")
    print(f"Datasets: {len(packet_files)}")
    print(f"Trials per protocol: {n_trials}")
    print(f"Warmup iterations: {warmup}")
    
    all_summaries = []
    
    for packet_file in packet_files:
        print(f"\n{'#'*70}")
        print(f"# Processing: {packet_file.name}")
        print(f"{'#'*70}")
        
        measurer = LatencyMeasurement(packet_file)
        measurer.measure_all_protocols(n_trials, warmup)
        summary_file, raw_file = measurer.save_results()
        
        # Load summary
        df = pd.read_csv(summary_file)
        all_summaries.append(df)
    
    # Combine all summaries
    combined = pd.concat(all_summaries, ignore_index=True)
    
    # Aggregate across datasets
    final_summary = combined.groupby('Protocol').agg({
        'Encryption_Mean_ms': 'mean',
        'Encryption_Std_ms': 'mean',
        'Decryption_Mean_ms': 'mean',
        'Decryption_Std_ms': 'mean',
        'Total_Mean_ms': 'mean',
        'Total_Std_ms': 'mean',
        'N_Trials': 'sum'
    }).round(4)
    
    print(f"\n{'='*70}")
    print("FINAL AGGREGATED RESULTS")
    print(f"{'='*70}")
    print(final_summary)
    
    # Save final summary
    final_file = Path('../data/latency_final_summary.csv')
    final_summary.to_csv(final_file)
    print(f"\n✓ Final summary saved: {final_file}")
    
    return final_summary


if __name__ == "__main__":
    # Run comprehensive latency measurement
    measure_all_datasets(n_trials=1000, warmup=100)
