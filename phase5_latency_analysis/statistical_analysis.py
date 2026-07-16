#!/usr/bin/env python3
"""
Statistical Hypothesis Testing for Latency Analysis
Tests H0: μ_encrypted = μ_unencrypted
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from scipy import stats
from scipy.stats import shapiro, levene, ttest_ind, mannwhitneyu

class LatencyStatistics:
    """
    Statistical analysis for latency comparisons
    """
    
    def __init__(self, data_dir='../data'):
        self.data_dir = Path(data_dir)
        self.results = {}
        self.raw_data = {}
    
    def load_raw_data(self):
        """
        Load raw latency measurements
        """
        print(f"\n{'='*70}")
        print("LOADING RAW LATENCY DATA")
        print(f"{'='*70}")
        
        raw_files = list(self.data_dir.glob('latency_raw_*.pkl'))
        
        if not raw_files:
            print("✗ No raw data files found!")
            return False
        
        all_data = {}
        
        for raw_file in raw_files:
            with open(raw_file, 'rb') as f:
                data = pickle.load(f)
            
            for protocol_data in data:
                protocol = protocol_data['protocol']
                
                if protocol not in all_data:
                    all_data[protocol] = {
                        'encryption': [],
                        'decryption': [],
                        'total': []
                    }
                
                all_data[protocol]['encryption'].extend(protocol_data['raw_encryption_times'])
                all_data[protocol]['decryption'].extend(protocol_data['raw_decryption_times'])
                all_data[protocol]['total'].extend(protocol_data['raw_total_times'])
            
            print(f"  ✓ Loaded: {raw_file.name}")
        
        self.raw_data = all_data
        
        print(f"\n{'='*70}")
        print("DATA SUMMARY")
        print(f"{'='*70}")
        for protocol, data in all_data.items():
            print(f"{protocol}:")
            print(f"  Samples: {len(data['total']):,}")
            print(f"  Mean: {np.mean(data['total']):.4f} ms")
            print(f"  Std: {np.std(data['total'], ddof=1):.4f} ms")
        
        return True
    
    def test_normality(self):
        """
        Test if data follows normal distribution
        """
        print(f"\n{'='*70}")
        print("NORMALITY TESTS (Shapiro-Wilk)")
        print(f"{'='*70}")
        print("H0: Data is normally distributed")
        print("H1: Data is not normally distributed")
        print("Decision rule: Reject H0 if p < 0.05")
        
        normality_results = []
        
        for protocol, data in self.raw_data.items():
            # Use sample for large datasets (Shapiro-Wilk limit)
            sample_size = min(5000, len(data['total']))
            sample = np.random.choice(data['total'], sample_size, replace=False)
            
            statistic, p_value = shapiro(sample)
            is_normal = p_value >= 0.05
            
            result = {
                'Protocol': protocol,
                'Statistic': statistic,
                'P_Value': p_value,
                'Is_Normal': is_normal,
                'Decision': 'Fail to reject H0' if is_normal else 'Reject H0',
                'Sample_Size': sample_size
            }
            
            normality_results.append(result)
            
            print(f"\n{protocol}:")
            print(f"  W = {statistic:.6f}, p = {p_value:.6f}")
            print(f"  Decision: {result['Decision']}")
            print(f"  → Data is {'normally' if is_normal else 'NOT normally'} distributed")
        
        self.results['normality'] = pd.DataFrame(normality_results)
        
        return self.results['normality']
    
    def test_variance_equality(self, protocol1='NONE', protocol2='AES-GCM'):
        """
        Test equality of variances (Levene's test)
        """
        print(f"\n{'='*70}")
        print(f"LEVENE'S TEST FOR EQUALITY OF VARIANCES")
        print(f"{'='*70}")
        print(f"Comparing: {protocol1} vs {protocol2}")
        print("H0: Variances are equal")
        print("H1: Variances are not equal")
        
        data1 = self.raw_data[protocol1]['total']
        data2 = self.raw_data[protocol2]['total']
        
        statistic, p_value = levene(data1, data2)
        equal_var = p_value >= 0.05
        
        print(f"\nW = {statistic:.6f}, p = {p_value:.6f}")
        print(f"Decision: {'Fail to reject H0' if equal_var else 'Reject H0'}")
        print(f"→ Variances are {'equal' if equal_var else 'NOT equal'}")
        
        return equal_var
    
    def compare_protocols_parametric(self, protocol1='NONE', protocol2='AES-GCM'):
        """
        Independent samples t-test (parametric)
        """
        print(f"\n{'='*70}")
        print(f"INDEPENDENT SAMPLES T-TEST")
        print(f"{'='*70}")
        print(f"Comparing: {protocol1} vs {protocol2}")
        print(f"H0: μ_{protocol1} = μ_{protocol2}")
        print(f"H1: μ_{protocol1} ≠ μ_{protocol2}")
        
        data1 = self.raw_data[protocol1]['total']
        data2 = self.raw_data[protocol2]['total']
        
        # Check variance equality
        equal_var = self.test_variance_equality(protocol1, protocol2)
        
        # Perform t-test
        statistic, p_value = ttest_ind(data1, data2, equal_var=equal_var)
        
        # Calculate effect size (Cohen's d)
        mean1 = np.mean(data1)
        mean2 = np.mean(data2)
        std1 = np.std(data1, ddof=1)
        std2 = np.std(data2, ddof=1)
        
        # Pooled standard deviation
        n1, n2 = len(data1), len(data2)
        pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
        cohens_d = (mean1 - mean2) / pooled_std
        
        # Interpret effect size
        if abs(cohens_d) < 0.2:
            effect_interpretation = "Negligible"
        elif abs(cohens_d) < 0.5:
            effect_interpretation = "Small"
        elif abs(cohens_d) < 0.8:
            effect_interpretation = "Medium"
        else:
            effect_interpretation = "Large"
        
        is_significant = p_value < 0.05
        
        result = {
            'Protocol_1': protocol1,
            'Protocol_2': protocol2,
            'Mean_1_ms': mean1,
            'Mean_2_ms': mean2,
            'Std_1_ms': std1,
            'Std_2_ms': std2,
            'Mean_Difference_ms': mean1 - mean2,
            'T_Statistic': statistic,
            'P_Value': p_value,
            'Cohens_d': cohens_d,
            'Effect_Size': effect_interpretation,
            'Is_Significant': is_significant,
            'Equal_Variance': equal_var
        }
        
        print(f"\n{'='*70}")
        print("RESULTS")
        print(f"{'='*70}")
        print(f"{protocol1}: {mean1:.4f} ± {std1:.4f} ms (n={n1:,})")
        print(f"{protocol2}: {mean2:.4f} ± {std2:.4f} ms (n={n2:,})")
        print(f"Mean Difference: {mean1 - mean2:.4f} ms")
        print(f"\nt = {statistic:.4f}, p = {p_value:.6f}")
        print(f"Cohen's d = {cohens_d:.4f} ({effect_interpretation} effect)")
        print(f"\nDecision: {'Reject H0' if is_significant else 'Fail to reject H0'}")
        
        if is_significant:
            print(f"→ There IS a statistically significant difference (p < 0.05)")
        else:
            print(f"→ There is NO statistically significant difference (p ≥ 0.05)")
        
        return result
    
    def compare_protocols_nonparametric(self, protocol1='NONE', protocol2='AES-GCM'):
        """
        Mann-Whitney U test (non-parametric)
        """
        print(f"\n{'='*70}")
        print(f"MANN-WHITNEY U TEST (Non-parametric)")
        print(f"{'='*70}")
        print(f"Comparing: {protocol1} vs {protocol2}")
        print(f"H0: Distributions are equal")
        print(f"H1: Distributions are not equal")
        
        data1 = self.raw_data[protocol1]['total']
        data2 = self.raw_data[protocol2]['total']
        
        statistic, p_value = mannwhitneyu(data1, data2, alternative='two-sided')
        
        is_significant = p_value < 0.05
        
        print(f"\nU = {statistic:.2f}, p = {p_value:.6f}")
        print(f"Decision: {'Reject H0' if is_significant else 'Fail to reject H0'}")
        
        if is_significant:
            print(f"→ There IS a statistically significant difference")
        else:
            print(f"→ There is NO statistically significant difference")
        
        return {'U_Statistic': statistic, 'P_Value': p_value, 'Is_Significant': is_significant}
    
    def equivalence_test_tost(self, protocol1='NONE', protocol2='AES-GCM', delta=5.0):
        """
        Two One-Sided Tests (TOST) for equivalence
        """
        print(f"\n{'='*70}")
        print(f"EQUIVALENCE TESTING (TOST)")
        print(f"{'='*70}")
        print(f"Comparing: {protocol1} vs {protocol2}")
        print(f"Equivalence margin: ±{delta} ms")
        print(f"H0: |μ_1 - μ_2| ≥ {delta}")
        print(f"H1: |μ_1 - μ_2| < {delta} (protocols are equivalent)")
        
        data1 = self.raw_data[protocol1]['total']
        data2 = self.raw_data[protocol2]['total']
        
        mean1 = np.mean(data1)
        mean2 = np.mean(data2)
        diff = mean1 - mean2
        
        n1, n2 = len(data1), len(data2)
        std1 = np.std(data1, ddof=1)
        std2 = np.std(data2, ddof=1)
        
        # Pooled standard error
        se_pooled = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        
        # Test 1: Mean difference < upper bound (+delta)
        t_upper = (diff - delta) / se_pooled
        df = n1 + n2 - 2
        p_upper = stats.t.cdf(t_upper, df)
        
        # Test 2: Mean difference > lower bound (-delta)
        t_lower = (diff + delta) / se_pooled
        p_lower = 1 - stats.t.cdf(t_lower, df)
        
        # For equivalence, both tests must be significant
        is_equivalent = (p_upper < 0.05 and p_lower < 0.05)
        
        print(f"\n{'='*70}")
        print("RESULTS")
        print(f"{'='*70}")
        print(f"Mean difference: {diff:.4f} ms")
        print(f"Standard error: {se_pooled:.4f} ms")
        print(f"\nTest 1 (μ1 - μ2 < +{delta}):")
        print(f"  t = {t_upper:.4f}, p = {p_upper:.6f}")
        print(f"Test 2 (μ1 - μ2 > -{delta}):")
        print(f"  t = {t_lower:.4f}, p = {p_lower:.6f}")
        
        if is_equivalent:
            print(f"\n✓ Protocols are EQUIVALENT within ±{delta} ms")
            print(f"  (Difference is practically negligible)")
        else:
            print(f"\n✗ Cannot conclude equivalence within ±{delta} ms")
        
        return {
            'Protocol_1': protocol1,
            'Protocol_2': protocol2,
            'Mean_Difference_ms': diff,
            'Equivalence_Margin_ms': delta,
            'Is_Equivalent': is_equivalent,
            'P_Upper': p_upper,
            'P_Lower': p_lower
        }
    
    def power_analysis(self, protocol1='NONE', protocol2='AES-GCM', alpha=0.05, power_target=0.80):
        """
        Post-hoc power analysis
        """
        print(f"\n{'='*70}")
        print(f"POWER ANALYSIS")
        print(f"{'='*70}")
        
        data1 = self.raw_data[protocol1]['total']
        data2 = self.raw_data[protocol2]['total']
        
        mean1 = np.mean(data1)
        mean2 = np.mean(data2)
        std1 = np.std(data1, ddof=1)
        std2 = np.std(data2, ddof=1)
        n1, n2 = len(data1), len(data2)
        
        # Calculate pooled std
        pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
        cohens_d = abs(mean1 - mean2) / pooled_std
        
        # Calculate noncentrality parameter
        n = min(n1, n2)
        ncp = cohens_d * np.sqrt(n / 2)
        df = n1 + n2 - 2
        
        # Critical t-value for two-tailed test
        t_crit = stats.t.ppf(1 - alpha/2, df)
        
        # Calculate power
        power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
        
        print(f"Effect size (Cohen's d): {cohens_d:.4f}")
        print(f"Sample sizes: n1={n1:,}, n2={n2:,}")
        print(f"Significance level (α): {alpha}")
        print(f"Achieved power: {power:.4f} ({power*100:.1f}%)")
        print(f"Target power: {power_target} ({power_target*100:.0f}%)")
        
        if power >= power_target:
            print(f"\n✓ Achieved power meets target")
            print(f"  Sample size is adequate")
        else:
            print(f"\n⚠ Achieved power below target")
            print(f"  Consider larger sample size")
        
        return {
            'Effect_Size': cohens_d,
            'Sample_Size': min(n1, n2),
            'Alpha': alpha,
            'Achieved_Power': power,
            'Target_Power': power_target,
            'Adequate': power >= power_target
        }
    
    def comprehensive_analysis(self):
        """
        Run complete statistical analysis
        """
        print(f"\n{'#'*70}")
        print("# COMPREHENSIVE STATISTICAL ANALYSIS")
        print(f"{'#'*70}")
        
        # Load data
        if not self.load_raw_data():
            return None
        
        # Test normality
        normality = self.test_normality()
        
        # Compare encrypted vs unencrypted
        comparisons = []
        
        # NONE vs each encrypted protocol
        encrypted_protocols = ['AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']
        
        for enc_protocol in encrypted_protocols:
            print(f"\n{'='*70}")
            print(f"COMPARING: NONE vs {enc_protocol}")
            print(f"{'='*70}")
            
            # Parametric test
            t_result = self.compare_protocols_parametric('NONE', enc_protocol)
            comparisons.append(t_result)
            
            # Non-parametric test
            u_result = self.compare_protocols_nonparametric('NONE', enc_protocol)
            
            # Equivalence test (5ms margin)
            equiv_result = self.equivalence_test_tost('NONE', enc_protocol, delta=5.0)
            
            # Power analysis
            power_result = self.power_analysis('NONE', enc_protocol)
        
        # Save results
        comparisons_df = pd.DataFrame(comparisons)
        
        # Create results directory
        Path('../results').mkdir(parents=True, exist_ok=True)
        
        comparisons_df.to_csv('../results/statistical_comparisons.csv', index=False)
        print(f"\n✓ Results saved: results/statistical_comparisons.csv")
        
        return comparisons_df


def main():
    """
    Run statistical analysis
    """
    analyzer = LatencyStatistics()
    results = analyzer.comprehensive_analysis()
    
    if results is not None:
        print(f"\n{'='*70}")
        print("STATISTICAL ANALYSIS COMPLETE")
        print(f"{'='*70}")
    
    return results


if __name__ == "__main__":
    main()
