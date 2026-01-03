"""
Step 4: Data Visualization
===========================
Create professional charts from financial data.

Prompt: "Read amd_financials.csv and create line charts for revenue, 
net_income, and assets. Format y-axis in billions with proper styling."
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def load_csv(filename):
    """Load CSV skipping comment lines."""
    return pd.read_csv(filename, comment='#')


def plot_metric(df, metric, output_file):
    """Create a line chart for a single metric."""
    if metric not in df.columns:
        return
    
    data = df[['fiscal_year', metric]].dropna()
    if data.empty:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data['fiscal_year'], data[metric], 
            marker='o', linewidth=2, markersize=6, color='#2E86AB')
    
    ax.set_xlabel('Fiscal Year', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'{metric.replace("_", " ").title()} (USD)', 
                  fontsize=12, fontweight='bold')
    ax.set_title(f'AMD - {metric.replace("_", " ").title()}', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, p: f'${x/1e9:.1f}B')
    )
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {metric} chart saved")


def create_dashboard(df, metrics, output_file):
    """Create dashboard with multiple metrics."""
    valid = [m for m in metrics if m in df.columns]
    if not valid:
        return
    
    fig, axes = plt.subplots(len(valid), 1, figsize=(10, 4*len(valid)))
    if len(valid) == 1:
        axes = [axes]
    
    for ax, metric in zip(axes, valid):
        data = df[['fiscal_year', metric]].dropna()
        if not data.empty:
            ax.plot(data['fiscal_year'], data[metric],
                   marker='o', linewidth=2, markersize=6, color='#2E86AB')
            ax.set_xlabel('Fiscal Year', fontweight='bold')
            ax.set_ylabel(f'{metric.replace("_", " ").title()}', fontweight='bold')
            ax.set_title(f'{metric.replace("_", " ").title()}', fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda x, p: f'${x/1e9:.1f}B')
            )
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Dashboard saved")


if __name__ == "__main__":
    print("Creating financial visualizations...\n")
    
    df = load_csv('amd_financials.csv')
    print(f"Loaded {len(df)} years of data\n")
    
    # Individual charts
    plot_metric(df, 'revenue', 'revenue.png')
    plot_metric(df, 'net_income', 'net_income.png')
    plot_metric(df, 'assets', 'assets.png')
    
    # Dashboard
    create_dashboard(df, ['revenue', 'net_income', 'assets'], 'dashboard.png')
    
    print("\n✓ All visualizations created")
