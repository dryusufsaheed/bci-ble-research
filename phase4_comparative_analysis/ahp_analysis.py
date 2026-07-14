#!/usr/bin/env python3
"""
AHP (Analytic Hierarchy Process) Implementation
Determines criterion importance weights for BCI security protocol evaluation

This module implements the complete AHP methodology with 7 criteria:
1. MITM_Protection (Security)
2. Replay_Protection (Security)
3. Avg_Latency (Performance)
4. CPU_Usage (Performance)
5. Memory_Usage (Performance)
6. Implementation_Complexity (Practicality)
7. Setup_Time (Practicality)
"""

import numpy as np
import pandas as pd


class AHP:
    """
    Analytic Hierarchy Process for Multi-Criteria Decision Making
    
    Implements Saaty's AHP method for pairwise comparison and weight calculation
    """
    
    def __init__(self, criteria_names):
        """
        Initialize AHP with list of criteria
        
        Args:
            criteria_names: List of criterion names
        """
        self.criteria_names = criteria_names
        self.n_criteria = len(criteria_names)
        self.comparison_matrix = np.ones((self.n_criteria, self.n_criteria))
        self.weights = None
        self.consistency_ratio = None
    
    def set_comparison(self, criterion1, criterion2, importance):
        """
        Set pairwise comparison between criteria
        
        Saaty's Scale:
        1 = Equal importance
        3 = Moderate importance (one criterion moderately preferred)
        5 = Strong importance (one criterion strongly preferred)
        7 = Very strong importance
        9 = Extreme importance (one criterion extremely preferred)
        
        Reciprocals (1/3, 1/5, 1/7, 1/9) for reverse comparisons
        
        Args:
            criterion1: Name of first criterion
            criterion2: Name of second criterion
            importance: Importance value (1-9 or reciprocal)
        """
        idx1 = self.criteria_names.index(criterion1)
        idx2 = self.criteria_names.index(criterion2)
        
        self.comparison_matrix[idx1, idx2] = importance
        self.comparison_matrix[idx2, idx1] = 1 / importance
    
    def calculate_weights(self):
        """
        Calculate criteria weights using eigenvector method
        
        Returns:
            weights: Normalized weights for each criterion
        """
        # Calculate eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eig(self.comparison_matrix)
        
        # Find principal eigenvector (corresponds to largest eigenvalue)
        max_eigenvalue_idx = np.argmax(eigenvalues.real)
        principal_eigenvector = eigenvectors[:, max_eigenvalue_idx].real
        
        # Normalize to get weights
        self.weights = principal_eigenvector / principal_eigenvector.sum()
        
        # Calculate consistency
        lambda_max = eigenvalues[max_eigenvalue_idx].real
        ci = (lambda_max - self.n_criteria) / (self.n_criteria - 1)
        
        # Random Index from Saaty's table
        # Values for n=1 to n=10
        ri_table = {
            1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }
        ri = ri_table.get(self.n_criteria, 1.49)
        
        # Consistency Ratio (CR) = CI / RI
        # CR < 0.1 indicates acceptable consistency
        self.consistency_ratio = ci / ri if ri != 0 else 0
        
        return self.weights
    
    def is_consistent(self, threshold=0.1):
        """
        Check if comparisons are consistent (CR < 0.1 is acceptable)
        
        Args:
            threshold: Maximum acceptable consistency ratio (default 0.1)
            
        Returns:
            bool: True if consistent, False otherwise
        """
        if self.consistency_ratio is None:
            self.calculate_weights()
        
        return self.consistency_ratio < threshold
    
    def display_results(self):
        """
        Display AHP analysis results with weights and consistency
        
        Returns:
            weights: Array of criterion weights
        """
        if self.weights is None:
            self.calculate_weights()
        
        print("\n" + "="*70)
        print("AHP ANALYSIS RESULTS")
        print("="*70)
        
        print("\nCriteria Weights:")
        print("-" * 70)
        for i, criterion in enumerate(self.criteria_names):
            print(f"  {criterion:30s}: {self.weights[i]:.4f} ({self.weights[i]*100:.2f}%)")
        
        print(f"\nConsistency Ratio (CR): {self.consistency_ratio:.4f}")
        print("-" * 70)
        
        if self.is_consistent():
            print("✓ Comparisons are CONSISTENT (CR < 0.1)")
            print("  → Weights are reliable for decision making")
        else:
            print("✗ WARNING: Comparisons are INCONSISTENT (CR >= 0.1)")
            print("  → Consider revising pairwise comparisons")
        
        print("="*70 + "\n")
        
        return self.weights


def create_bci_security_ahp():
    """
    Create AHP model for BCI security research with 7 criteria
    
    Criteria organized in two categories:
    
    SECURITY (40-50% weight):
    - MITM Protection (attack resistance)
    - Replay Protection (freshness verification)
    
    PERFORMANCE (30-40% weight):
    - Avg Latency (real-time requirements)
    - CPU Usage (resource utilization)
    - Memory Usage (device constraints)
    
    PRACTICALITY (10-20% weight):
    - Implementation Complexity (developer effort)
    - Setup Time (deployment time)
    
    Returns:
        AHP: Configured AHP model with all comparisons set
    """
    criteria = [
        "MITM_Protection",
        "Replay_Protection",
        "Avg_Latency",
        "CPU_Usage",
        "Memory_Usage",
        "Implementation_Complexity",
        "Setup_Time"
    ]
    
    ahp = AHP(criteria)
    
    print("\n" + "="*70)
    print("SETTING UP AHP FOR BCI SECURITY ANALYSIS")
    print("="*70)
    print(f"Number of criteria: {len(criteria)}")
    print("Criteria categories:")
    print("  Security: MITM_Protection, Replay_Protection")
    print("  Performance: Avg_Latency, CPU_Usage, Memory_Usage")
    print("  Practicality: Implementation_Complexity, Setup_Time")
    print("="*70 + "\n")
    
    # ===========================================================================
    # SECURITY CRITERIA (Highest Priority - BCIs handle critical neural data)
    # ===========================================================================
    
    print("Setting security criterion comparisons...")
    
    # MITM Protection vs others
    # Security is paramount in BCI - protection against eavesdropping is critical
    ahp.set_comparison("MITM_Protection", "Replay_Protection", 1.5)
    # MITM slightly more critical than Replay (eavesdropping > replay)
    
    ahp.set_comparison("MITM_Protection", "Avg_Latency", 2.0)
    # Security is moderately more important than latency
    
    ahp.set_comparison("MITM_Protection", "CPU_Usage", 3.0)
    # Security is strongly more important than resource usage
    
    ahp.set_comparison("MITM_Protection", "Memory_Usage", 3.0)
    # Security strongly dominates memory concerns
    
    ahp.set_comparison("MITM_Protection", "Implementation_Complexity", 4.0)
    # Security very strongly preferred over implementation ease
    
    ahp.set_comparison("MITM_Protection", "Setup_Time", 4.0)
    # Security very strongly preferred over setup convenience
    
    # Replay Protection vs others
    print("  ✓ MITM Protection comparisons set")
    
    ahp.set_comparison("Replay_Protection", "Avg_Latency", 1.5)
    # Replay protection slightly more critical than latency
    
    ahp.set_comparison("Replay_Protection", "CPU_Usage", 2.5)
    # Replay protection is strongly preferred over CPU usage
    
    ahp.set_comparison("Replay_Protection", "Memory_Usage", 2.5)
    # Replay protection strongly preferred over memory
    
    ahp.set_comparison("Replay_Protection", "Implementation_Complexity", 3.0)
    # Replay protection very strongly preferred over complexity
    
    ahp.set_comparison("Replay_Protection", "Setup_Time", 3.0)
    # Replay protection very strongly preferred over setup time
    
    print("  ✓ Replay Protection comparisons set")
    
    # ===========================================================================
    # PERFORMANCE CRITERIA (Medium Priority - BCIs need real-time response)
    # ===========================================================================
    
    print("Setting performance criterion comparisons...")
    
    # Latency vs resource usage
    # Real-time BCIs are latency-sensitive (typically require <100ms)
    ahp.set_comparison("Avg_Latency", "CPU_Usage", 2.0)
    # Latency is moderately more important than CPU usage
    
    ahp.set_comparison("Avg_Latency", "Memory_Usage", 2.0)
    # Latency is moderately more important than memory
    
    ahp.set_comparison("Avg_Latency", "Implementation_Complexity", 3.0)
    # Latency is strongly preferred over implementation complexity
    
    ahp.set_comparison("Avg_Latency", "Setup_Time", 3.0)
    # Latency is strongly preferred over setup time
    
    # CPU usage vs others
    ahp.set_comparison("CPU_Usage", "Memory_Usage", 1.0)
    # CPU and memory usage are equally important (resource balance)
    
    ahp.set_comparison("CPU_Usage", "Implementation_Complexity", 1.5)
    # CPU usage slightly more important than complexity
    
    ahp.set_comparison("CPU_Usage", "Setup_Time", 1.5)
    # CPU usage slightly more important than setup time
    
    # Memory usage vs others
    ahp.set_comparison("Memory_Usage", "Implementation_Complexity", 1.5)
    # Memory usage slightly more important than complexity
    
    ahp.set_comparison("Memory_Usage", "Setup_Time", 1.5)
    # Memory usage slightly more important than setup time
    
    print("  ✓ Performance criteria comparisons set")
    
    # ===========================================================================
    # PRACTICALITY CRITERIA (Lower Priority - less critical than security/perf)
    # ===========================================================================
    
    print("Setting practicality criterion comparisons...")
    
    # Implementation Complexity vs Setup Time
    ahp.set_comparison("Implementation_Complexity", "Setup_Time", 1.0)
    # Equal importance (both relate to deployment effort)
    
    print("  ✓ Practicality criteria comparisons set")
    
    print("\n" + "="*70)
    print("AHP Setup Complete - Calculating weights...")
    print("="*70 + "\n")
    
    return ahp


def main():
    """
    Run AHP analysis for BCI security research
    """
    # Create AHP model with all 7 criteria
    ahp = create_bci_security_ahp()
    
    # Calculate and display weights
    weights = ahp.display_results()
    
    # Create results dataframe
    weights_df = pd.DataFrame({
        'Criterion': ahp.criteria_names,
        'Weight': weights,
        'Percentage': weights * 100,
        'Category': [
            'Security', 'Security',
            'Performance', 'Performance', 'Performance',
            'Practicality', 'Practicality'
        ]
    })
    
    # Sort by weight (highest first)
    weights_df = weights_df.sort_values('Weight', ascending=False)
    
    print("\nWEIGHTS RANKED BY IMPORTANCE")
    print("="*70)
    print(weights_df.to_string(index=False))
    print("="*70)
    
    # Summary statistics
    print("\nWEIGHT DISTRIBUTION BY CATEGORY")
    print("="*70)
    category_sums = weights_df.groupby('Category')['Percentage'].sum()
    for category, pct in category_sums.items():
        print(f"  {category:20s}: {pct:5.1f}%")
    print("="*70)
    
    # Save weights
    weights_df.to_csv('ahp_weights.csv', index=False)
    print("\n✓ Weights saved to: ahp_weights.csv")
    
    # Display consistency
    print(f"\n✓ Consistency Ratio: {ahp.consistency_ratio:.4f}")
    if ahp.is_consistent():
        print("  → Acceptable consistency (< 0.1)")
    else:
        print("  → WARNING: Consider revising comparisons")
    
    return weights_df, ahp


if __name__ == "__main__":
    weights_df, ahp = main()
