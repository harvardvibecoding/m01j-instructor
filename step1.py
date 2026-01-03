"""
Step 1: Connect to SEC EDGAR API
=================================
Fetch company financial data from the SEC EDGAR API.

Prompt: "Fetch AMD's company data from SEC EDGAR API (CIK: 0000002488).
The endpoint is https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
Include User-Agent header and save the JSON file."
"""

import requests
import json


def fetch_company_facts(cik, email="student@university.edu"):
    """Fetch company data from SEC EDGAR API."""
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    headers = {'User-Agent': f'UniversityStudent {email}'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    print("Fetching AMD data from SEC EDGAR...\n")

    data = fetch_company_facts("0000002488")

    if data:
        print(f"Company: {data['entityName']}")
        print(f"CIK: {data['cik']}")
        print(f"Ticker: {', '.join(data.get('tickers', []))}")
        print(f"Financial concepts: {len(data['facts']['us-gaap'])}")

        with open('amd_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\n✓ Data saved to amd_data.json")
    else:
        print("✗ Failed to fetch data")
