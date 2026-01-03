"""
Step 2: Extract Net Income
===========================
Extract Net Income from SEC EDGAR data with proper annual period filtering.

Prompt: "Extract NetIncomeLoss from amd_data.json for annual reports (10-K, FY).
Handle duplicate entries per fiscal year by:
1. Filtering for periods spanning ~365 days (full year, not quarterly)
2. Matching the period dates to the fiscal year (avoid historical restatements)
3. Selecting entries where the end date year matches the fiscal year
Show fiscal year, value, and year-over-year growth."
"""

from step1 import fetch_company_facts
from datetime import datetime
from collections import defaultdict


def extract_metric(data, metric_name):
    """Extract annual values for any financial metric from SEC data.

    Handles duplicate entries by selecting the full-year period (~365 days)
    that matches the fiscal year.
    """
    try:
        filings = data['facts']['us-gaap'][metric_name]['units']['USD']
        annual = [f for f in filings if f.get('form') == '10-K' and f.get('fp') == 'FY']

        by_year = defaultdict(list)
        for filing in annual:
            by_year[filing['fy']].append(filing)

        results = []
        for year in sorted(by_year.keys()):
            # Balance sheet items (Assets, etc.) have only 'end' date, no 'start'
            # Income statement items (Revenue, NetIncome, etc.) have both 'start' and 'end'
            has_start_date = 'start' in by_year[year][0]

            if has_start_date:
                # For period metrics: find entries spanning ~365 days within the fiscal year
                candidates = []
                for filing in by_year[year]:
                    start = datetime.strptime(filing['start'], '%Y-%m-%d')
                    end = datetime.strptime(filing['end'], '%Y-%m-%d')
                    days = (end - start).days

                    # Must be full year and end date close to fiscal year
                    if days >= 350 and start.year >= year - 1 and end.year >= year - 1:
                        score = abs(end.year - year)
                        candidates.append((filing, score, -days))

                if candidates:
                    candidates.sort(key=lambda x: (x[1], x[2]))
                    results.append(candidates[0][0])
            else:
                # For point-in-time metrics: just take the most recent filing
                most_recent = max(by_year[year], key=lambda x: x['filed'])
                results.append(most_recent)

        return results

    except (KeyError, TypeError) as e:
        print(f"Error extracting {metric_name}: {e}")
        return []


def display_net_income(filings):
    """Display net income with growth rates."""
    print("\nAMD NET INCOME HISTORY")
    print("=" * 70)
    print(f"{'Year':<8} {'Net Income':>15} {'Status':>10} {'YoY Growth':>12}")
    print("-" * 70)

    prev_val = None
    for filing in filings:
        year = filing['fy']
        val = filing['val']
        val_b = val / 1e9

        status = "PROFIT" if val > 0 else "LOSS"

        if prev_val and prev_val != 0:
            growth = ((val - prev_val) / abs(prev_val)) * 100
            growth_str = f"{growth:+.1f}%"
        else:
            growth_str = "N/A"

        print(f"{year:<8} ${val_b:>13.2f}B {status:>10} {growth_str:>12}")
        prev_val = val


if __name__ == "__main__":
    import json
    import os

    print("Extracting Net Income from AMD data...")

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

    results = extract_metric(data, 'NetIncomeLoss')

    if results:
        print(f"✓ Found {len(results)} years")
        display_net_income(results)
    else:
        print("✗ No data found")
