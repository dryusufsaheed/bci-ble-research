#!/usr/bin/env python3
"""
Create Statistical Visualization Plots
Publication-ready figures for latency analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from pathlib import Path
from scipy import stats

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11

class LatencyVisualizations:
    """
    Create statistical visualizations for latency analysis
    """
    
    def __init__(self, data_dir='../data'):
        self.data_dir = Path(data_dir)
        self.raw_data = self.load_raw_data()
        
        # Create figures directory
        Path('../figures').mkdir(parents=True, exist_ok=True)
    
    def load_raw_data(self):
        """Load all raw latency data"""
        raw_files = list(self.data_dir.glob('latency_raw_*.pkl'))
        
        all_data = {}
        
        for raw_file in raw_files:
            with open(raw_file, 'rb') as f:
                data = pickle.load(f)
            
            for protocol_data in data:
                protocol = protocol_data['protocol']
                
                if protocol not in all_data:
                    all_data[protocol] = []
                
                all_data[protocol].extend(protocol_data['raw_total_times'])
        
        return all_data
    
    def plot_distributions(self):
        """
        Plot latency distributions
        """
        print("\nCreating distribution plots...")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        protocols = ['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']
        colors = ['gray', 'skyblue', 'lightcoral', 'lightgreen']
        
        for ax, protocol, color in zip(axes, protocols, colors):
            data = self.raw_data[protocol]
            
            # Histogram with KDE
            ax.hist(data, bins=50, density=True, alpha=0.6, color=color, edgecolor='black')
            
            # Overlay normal distribution
            mu = np.mean(data)
            sigma = np.std(data, ddof=1)
            x = np.linspace(min(data), max(data), 100)
            ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2, label='Normal fit')
            
            ax.set_title(f'{protocol}\nμ={mu:.4f} ms, σ={sigma:.4f} ms', fontweight='bold')
            ax.set_xlabel('Latency (ms)')
            ax.set_ylabel('Density')
            ax.legend()
            ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../figures/latency_distributions.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: figures/latency_distributions.png")
        plt.close()
    
    def plot_box_plots(self):
        """
        Create box plots for comparison
        """
        print("\nCreating box plots...")
        
        # Prepare data
        plot_data = []
        for protocol, data in self.raw_data.items():
            for value in data:
                plot_data.append({'Protocol': protocol, 'Latency_ms': value})
        
        df = pd.DataFrame(plot_data)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create box plot
        bp = ax.boxplot([self.raw_data[p] for p in ['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']],
                        labels=['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305'],
                        patch_artist=True,
                        showmeans=True,
                        meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        
        # Color boxes
        colors = ['gray', 'skyblue', 'lightcoral', 'lightgreen']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Encryption Protocol', fontsize=12, fontweight='bold')
        ax.set_title('Latency Distribution Comparison\n(Diamond = Mean, Line = Median)', 
                    fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../figures/latency_boxplots.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: figures/latency_boxplots.png")
        plt.close()
    
    def plot_violin_plots(self):
        """
        Create violin plots
        """
        print("\nCreating violin plots...")
        
        # Prepare data
        plot_data = []
        for protocol, data in self.raw_data.items():
            # Sample for visualization (too many points slow down violin)
            sample = np.random.choice(data, min(5000, len(data)), replace=False)
            for value in sample:
                plot_data.append({'Protocol': protocol, 'Latency_ms': value})
        
        df = pd.DataFrame(plot_data)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create violin plot
        parts = ax.violinplot([self.raw_data[p] for p in ['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']],
                              positions=[0, 1, 2, 3],
                              showmeans=True,
                              showmedians=True)
        
        # Customize
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xticklabels(['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305'])
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Encryption Protocol', fontsize=12, fontweight='bold')
        ax.set_title('Latency Distribution Violin Plots', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../figures/latency_violin.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: figures/latency_violin.png")
        plt.close()
    
    def plot_qq_plots(self):
        """
        Create Q-Q plots for normality assessment
        """
        print("\nCreating Q-Q plots...")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        protocols = ['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']
        
        for ax, protocol in zip(axes, protocols):
            data = self.raw_data[protocol]
            
            # Sample for Q-Q plot
            sample = np.random.choice(data, min(5000, len(data)), replace=False)
            
            stats.probplot(sample, dist="norm", plot=ax)
            ax.set_title(f'Q-Q Plot: {protocol}', fontweight='bold')
            ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../figures/latency_qq_plots.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: figures/latency_qq_plots.png")
        plt.close()
    
    def plot_mean_comparison(self):
        """
        Create mean comparison bar plot with error bars
        """
        print("\nCreating mean comparison plot...")
        
        protocols = ['NONE', 'AES-CCM', 'AES-GCM', 'ChaCha20-Poly1305']
        means = [np.mean(self.raw_data[p]) for p in protocols]
        stds = [np.std(self.raw_data[p], ddof=1) for p in protocols]
        
        # Calculate 95% confidence intervals
        n = len(self.raw_data[protocols[0]])
        ci = [1.96 * std / np.sqrt(n) for std in stds]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['gray', 'skyblue', 'lightcoral', 'lightgreen']
        bars = ax.bar(protocols, means, yerr=ci, capsize=10, 
                     color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
        
        # Add value labels
        for bar, mean, std in zip(bars, means, stds):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(ci)*0.1,
                   f'{mean:.4f} ms\n±{std:.4f}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_ylabel('Mean Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Encryption Protocol', fontsize=12, fontweight='bold')
        ax.set_title('Mean Latency Comparison with 95% Confidence Intervals', 
                    fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../figures/latency_mean_comparison.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: figures/latency_mean_comparison.png")
        plt.close()
    
    def create_all_plots(self):
        """
        Create all visualization plots
        """
        print(f"\n{'='*70}")
        print("CREATING STATISTICAL VISUALIZATIONS")
        print(f"{'='*70}")
        
        self.plot_distributions()
        self.plot_box_plots()
        self.plot_violin_plots()
        self.plot_qq_plots()
        self.plot_mean_comparison()
        
        print(f"\n{'='*70}")
        print("ALL VISUALIZATIONS COMPLETE")
        print(f"{'='*70}")


def main():
    """
    Create all visualizations
    """
    viz = LatencyVisualizations()
    viz.create_all_plots()


if __name__ == "__main__":
    main()
