#!/usr/bin/env python3
"""
Create Results Summary Table for Dissertation
"""

import pandas as pd
from tabulate import tabulate

def create_summary_table():
    """
    Create comprehensive results summary
    """
    print("\n" + "="*70)
    print("CREATING RESULTS SUMMARY TABLE")
    print("="*70)
    
    # Load data
    latency = pd.read_csv('../data/latency_final_summary.csv', index_col='Protocol')
    stats = pd.read_csv('../results/statistical_comparisons.csv')
    
    # Create summary
    summary = []
    
    for _, row in stats.iterrows():
        prot1 = row['Protocol_1']
        prot2 = row['Protocol_2']
        
        summary.append({
            'Comparison': f"{prot1} vs {prot2}",
            'Mean_Diff_ms': f"{row['Mean_Difference_ms']:.4f}",
            'P_Value': f"{row['P_Value']:.6f}",
            'Significant': 'Yes' if row['Is_Significant'] else 'No',
            'Cohens_d': f"{row['Cohens_d']:.4f}",
            'Effect_Size': row['Effect_Size'],
            'Conclusion': 'Different' if row['Is_Significant'] else 'Similar'
        })
    
    df = pd.DataFrame(summary)
    
    print("\n" + "="*70)
    print("STATISTICAL COMPARISON SUMMARY")
    print("="*70)
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    
    # Save
    df.to_csv('../results/results_summary.csv', index=False)
    print("\n✓ Saved: results/results_summary.csv")
    
    # Create LaTeX version
    with open('../results/results_summary_latex.tex', 'w') as f:
        f.write(df.to_latex(index=False))
    print("✓ Saved: results/results_summary_latex.tex")
    
    return df


if __name__ == "__main__":
    create_summary_table()
