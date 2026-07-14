#!/usr/bin/env python3
"""
AHP Weights Calculator for BCI Security Research
Calculates importance weights for ALL 7 criteria using Analytic Hierarchy Process

CRITERIA (7 Total):
===================
SECURITY CRITERIA (40-50% of total weight):
1. MITM_Protection - Protection against man-in-the-middle attacks
2. Replay_Protection - Protection against replay attacks

PERFORMANCE CRITERIA (30-40% of total weight):
3. Avg_Latency - Average encryption/decryption latency (milliseconds)
4. CPU_Usage - CPU resource consumption (percentage)
5. Memory_Usage - Memory footprint (bytes/MB)

PRACTICALITY CRITERIA (10-20% of total weight):
6. Implementation_Complexity - Code complexity and development effort
7. Setup_Time - Time required for initial setup/configuration
"""

import numpy as np
import pandas as pd
from scipy.linalg import eig


class AHPWeightsCalculator:
    """
    Complete AHP implementation for 7 criteria decision making
    """
    
    def __init__(self):
        """Initialize with all 7 criteria"""
        self.criteria = [
            'MITM_Protection',           # Criterion 1
            'Replay_Protection',         # Criterion 2
            'Avg_Latency',               # Criterion 3
            'CPU_Usage',                 # Criterion 4
            'Memory_Usage',              # Criterion 5
            'Implementation_Complexity', # Criterion 6
            'Setup_Time'                 # Criterion 7
        ]
        
        self.n = len(self.criteria)
        print(f"\n{'='*80}")
        print(f"AHP WEIGHTS CALCULATOR - {self.n} CRITERIA")
        print(f"{'='*80}")
        print("\nCriteria loaded:")
        for i, criterion in enumerate(self.criteria, 1):
            print(f"  {i}. {criterion}")
        print(f"{'='*80}\n")
        
        # Initialize 7x7 pairwise comparison matrix
        self.comparison_matrix = np.ones((self.n, self.n))
    
    def set_comparison(self, i, j, value):
        """
        Set pairwise comparison: criterion i is 'value' times more important than j
        
        Saaty's 1-9 Scale:
        1 = Equal importance
        3 = Weakly more important
        5 = Strongly more important
        7 = Very strongly more important
        9 = Absolutely more important
        Reciprocals for reverse comparisons
        """
        self.comparison_matrix[i, j] = value
        self.comparison_matrix[j, i] = 1 / value
    
    def calculate_weights(self):
        """
        Calculate criterion weights using eigenvalue method
        Returns: weights array (normalized)
        """
        # Calculate eigenvalues and eigenvectors
        eigenvalues, eigenvectors = eig(self.comparison_matrix)
        eigenvalues = eigenvalues.real
        eigenvectors = eigenvectors.real
        
        # Find principal eigenvector
        max_idx = np.argmax(eigenvalues)
        principal_eigenvector = eigenvectors[:, max_idx]
        
        # Normalize to get weights
        weights = principal_eigenvector / principal_eigenvector.sum()
        weights = np.abs(weights)  # Ensure positive
        weights = weights / weights.sum()  # Renormalize
        
        # Calculate consistency ratio
        lambda_max = eigenvalues[max_idx]
        ci = (lambda_max - self.n) / (self.n - 1)
        
        # Random Index table (Saaty)
        ri_table = {
            1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }
        ri = ri_table.get(self.n, 1.49)
        cr = ci / ri if ri != 0 else 0
        
        return weights, cr, lambda_max
    
    def build_comparison_matrix(self):
        """
        Build the complete 7x7 pairwise comparison matrix
        Based on research priorities for BCI security
        """
        print("Building pairwise comparison matrix...")
        print(f"{'='*80}")
        
        # ====================================================================
        # SECURITY CRITERIA (Highest Priority)
        # BCIs handle critical neural data - security is paramount
        # ====================================================================
        print("\n[SECURITY TIER] Setting comparisons...")
        
        # Row 0: MITM_Protection vs all others
        # MITM protection is critical - eavesdropping would expose neural data
        self.set_comparison(0, 1, 1.5)   # MITM slightly > Replay
        self.set_comparison(0, 2, 4.0)   # MITM very strongly > Latency
        self.set_comparison(0, 3, 5.0)   # MITM extremely > CPU_Usage
        self.set_comparison(0, 4, 5.0)   # MITM extremely > Memory_Usage
        self.set_comparison(0, 5, 6.0)   # MITM extremely > Implementation
        self.set_comparison(0, 6, 6.0)   # MITM extremely > Setup_Time
        print("  ✓ MITM_Protection (criterion 1) comparisons set")
        
        # Row 1: Replay_Protection vs others
        # Replay protection prevents unauthorized neural signal replay
        self.set_comparison(1, 2, 3.0)   # Replay strongly > Latency
        self.set_comparison(1, 3, 4.0)   # Replay very strongly > CPU
        self.set_comparison(1, 4, 4.0)   # Replay very strongly > Memory
        self.set_comparison(1, 5, 5.0)   # Replay extremely > Implementation
        self.set_comparison(1, 6, 5.0)   # Replay extremely > Setup_Time
        print("  ✓ Replay_Protection (criterion 2) comparisons set")
        
        # ====================================================================
        # PERFORMANCE CRITERIA (Medium Priority)
        # BCIs require real-time response (~100-500ms total latency tolerance)
        # ====================================================================
        print("\n[PERFORMANCE TIER] Setting comparisons...")
        
        # Row 2: Avg_Latency vs others
        # Latency critical for real-time neural feedback
        self.set_comparison(2, 3, 3.0)   # Latency strongly > CPU
        self.set_comparison(2, 4, 3.0)   # Latency strongly > Memory
        self.set_comparison(2, 5, 4.0)   # Latency very strongly > Implementation
        self.set_comparison(2, 6, 4.0)   # Latency very strongly > Setup_Time
        print("  ✓ Avg_Latency (criterion 3) comparisons set")
        
        # Row 3: CPU_Usage vs others
        # Embedded devices need efficient computation
        self.set_comparison(3, 4, 1.0)   # CPU equal to Memory (balanced resources)
        self.set_comparison(3, 5, 2.0)   # CPU moderately > Implementation
        self.set_comparison(3, 6, 2.0)   # CPU moderately > Setup_Time
        print("  ✓ CPU_Usage (criterion 4) comparisons set")
        
        # Row 4: Memory_Usage vs others
        # Devices have constrained memory (e.g., wearables, implants)
        self.set_comparison(4, 5, 2.0)   # Memory moderately > Implementation
        self.set_comparison(4, 6, 2.0)   # Memory moderately > Setup_Time
        print("  ✓ Memory_Usage (criterion 5) comparisons set")
        
        # ====================================================================
        # PRACTICALITY CRITERIA (Lower Priority)
        # Implementation effort is least critical compared to security/performance
        # ====================================================================
        print("\n[PRACTICALITY TIER] Setting comparisons...")
        
        # Row 5 & 6: Implementation_Complexity vs Setup_Time
        # These are roughly equal in importance
        self.set_comparison(5, 6, 1.0)   # Implementation equal to Setup_Time
        print("  ✓ Implementation_Complexity (criterion 6) vs Setup_Time (criterion 7)")
        
        print(f"\n{'='*80}")
        print("Pairwise comparison matrix complete!")
        print(f"{'='*80}\n")
    
    def get_weights_dataframe(self):
        """Calculate and return weights as pandas DataFrame"""
        weights, cr, lambda_max = self.calculate_weights()
        
        df = pd.DataFrame({
            'Criterion': self.criteria,
            'Weight': weights,
            'Percentage': weights * 100,
            'Rank': np.arange(1, self.n + 1)
        })
        
        # Sort by weight descending
        df = df.sort_values('Weight', ascending=False).reset_index(drop=True)
        df['Rank'] = np.arange(1, self.n + 1)
        
        return df, cr, lambda_max
    
    def print_results(self):
        """Print comprehensive AHP results"""
        df, cr, lambda_max = self.get_weights_dataframe()
        
        print("\n" + "="*80)
        print("FINAL WEIGHTS - RANKED BY IMPORTANCE")
        print("="*80)
        
        for idx, row in df.iterrows():
            criterion = row['Criterion']
            weight = row['Weight']
            percentage = row['Percentage']
            rank = row['Rank']
            
            # Visual bar
            bar_length = int(percentage / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            print(f"\n{rank}. {criterion:30s}")
            print(f"   Weight: {weight:.6f}")
            print(f"   [{bar}] {percentage:5.2f}%")
        
        print("\n" + "="*80)
        print("CATEGORY BREAKDOWN")
        print("="*80)
        
        security_weight = df[df['Criterion'].isin([
            'MITM_Protection', 'Replay_Protection'
        ])]['Weight'].sum() * 100
        
        performance_weight = df[df['Criterion'].isin([
            'Avg_Latency', 'CPU_Usage', 'Memory_Usage'
        ])]['Weight'].sum() * 100
        
        practicality_weight = df[df['Criterion'].isin([
            'Implementation_Complexity', 'Setup_Time'
        ])]['Weight'].sum() * 100
        
        print(f"\nSecurity:      {security_weight:6.2f}% (MITM + Replay Protection)")
        print(f"Performance:   {performance_weight:6.2f}% (Latency + CPU + Memory)")
        print(f"Practicality:  {practicality_weight:6.2f}% (Implementation + Setup)")
        print(f"{'-'*80}")
        print(f"Total:         {security_weight + performance_weight + practicality_weight:6.2f}%")
        
        print("\n" + "="*80)
        print("CONSISTENCY ANALYSIS")
        print("="*80)
        print(f"Lambda Max (λmax):      {lambda_max:.6f}")
        print(f"Consistency Index (CI): {(lambda_max - self.n) / (self.n - 1):.6f}")
        print(f"Consistency Ratio (CR): {cr:.6f}")
        
        if cr < 0.1:
            print(f"✓ ACCEPTABLE CONSISTENCY (CR < 0.1)")
            print(f"  → Pairwise comparisons are reliable")
        else:
            print(f"✗ WARNING: INCONSISTENT (CR >= 0.1)")
            print(f"  → Consider revising pairwise comparisons")
        
        print("="*80 + "\n")
        
        return df
    
    def save_weights(self, filename='ahp_weights_7criteria.csv'):
        """Save weights to CSV file"""
        df, cr, lambda_max = self.get_weights_dataframe()
        
        # Add metadata
        df['Consistency_Ratio'] = cr
        df['Lambda_Max'] = lambda_max
        
        df.to_csv(filename, index=False)
        print(f"✓ Weights saved to: {filename}")
        
        return df


def main():
    """
    Main execution: Calculate AHP weights for 7 criteria
    """
    calculator = AHPWeightsCalculator()
    
    # Build the pairwise comparison matrix with all 7 criteria
    calculator.build_comparison_matrix()
    
    # Calculate and display weights
    df = calculator.print_results()
    
    # Save to file
    calculator.save_weights('ahp_weights_7criteria.csv')
    
    print("\n" + "="*80)
    print("WEIGHT TABLE - READY FOR TOPSIS INPUT")
    print("="*80)
    print(df[['Criterion', 'Weight', 'Percentage']].to_string(index=False))
    print("="*80 + "\n")
    
    return calculator, df


if __name__ == "__main__":
    calculator, weights_df = main()
