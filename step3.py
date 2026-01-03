"""
Step 3: Multiple Metrics + CSV Export
======================================
Extract multiple financial metrics and combine into a CSV.

Prompt: "Extract NetIncomeLoss, Revenues, and Assets from amd_data.json.
Use the extract_metric function from step2 to handle duplicates properly.
Combine into a single table and save to CSV with company metadata."
"""

import json
import pandas as pd
from datetime import datetime
from step1 import fetch_company_facts
from step2 import extract_metric


METRICS = {
    'net_income': 'NetIncomeLoss',
    'revenue': 'RevenueFromContractWithCustomerExcludingAssessedTax',
    'assets': 'Assets'
}


def combine_metrics(data, metrics):
    """Extract multiple metrics and combine into one DataFrame."""
    dfs = []
    for name, concept in metrics.items():
        results = extract_metric(data, concept)
        if results:
            df = pd.DataFrame(results)[['fy', 'val']]
            df.columns = ['fiscal_year', name]
            dfs.append(df)
            print(f"  ✓ {name}: {len(df)} years")

    if not dfs:
        return None

    result = dfs[0]
    for df in dfs[1:]:
        result = result.merge(df, on='fiscal_year', how='outer')

    return result.sort_values('fiscal_year')


def save_csv(df, data, filename):
    """Save to CSV with metadata header."""
    with open(filename, 'w') as f:
        f.write(f"# Company: {data['entityName']}\n")
        f.write(f"# CIK: {data['cik']}\n")
        f.write(f"# Ticker: {', '.join(data.get('tickers', []))}\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("#\n")

    df.to_csv(filename, mode='a', index=False)
    print(f"\n✓ Saved to {filename}")


def display_summary(df):
    """Display recent data with profit margins."""
    print("\nRECENT FINANCIAL DATA (Last 5 Years)")
    print("=" * 80)

    recent = df.tail(5)
    for _, row in recent.iterrows():
        print(f"{int(row['fiscal_year'])}:", end="")
        if 'revenue' in df.columns:
            print(f"  Revenue: ${row['revenue']/1e9:.2f}B", end="")
        if 'net_income' in df.columns:
            print(f"  Net Income: ${row['net_income']/1e9:.2f}B", end="")
        if 'assets' in df.columns:
            print(f"  Assets: ${row['assets']/1e9:.2f}B", end="")
        print()

    if 'net_income' in df.columns and 'revenue' in df.columns:
        print("\nPROFIT MARGINS:")
        for _, row in recent.iterrows():
            margin = (row['net_income'] / row['revenue']) * 100
            print(f"  {int(row['fiscal_year'])}: {margin:.1f}%")


if __name__ == "__main__":
    import os

    print("Extracting multiple metrics from AMD data...\n")

    # Try to load from file first, otherwise fetch from API
    if os.path.exists('amd_data.json'):
        with open('amd_data.json', 'r') as f:
            data = json.load(f)
    else:
        print("Fetching from SEC EDGAR API...")
        data = fetch_company_facts("0000002488")
        if data:
            with open('amd_data.json', 'w') as f:
                json.dump(data, f, indent=2)
        else:
            print("✗ Failed to fetch data")
            exit(1)

    df = combine_metrics(data, METRICS)

    if df is not None:
        display_summary(df)
        save_csv(df, data, 'amd_financials.csv')
        print(f"\n✓ Extracted {len(METRICS)} metrics across {len(df)} years")
    else:
        print("✗ No metrics extracted")
