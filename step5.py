"""
Step 5: Web Dashboard
======================
Interactive Flask web app for financial analysis.

Prompt: "Create a Flask app with a form to input company CIK.
Fetch data using step1, extract metrics using step2, combine with step3,
and display charts on a results page."
"""

from flask import Flask, render_template_string, request
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Import from previous steps
from step1 import fetch_company_facts
from step2 import extract_metric

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SEC EDGAR Analyzer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { text-align: center; color: #333; }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover { background: #0056b3; }
        .examples {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SEC EDGAR Financial Analyzer</h1>
        <form method="POST" action="/analyze">
            <input type="text" name="cik" placeholder="Enter CIK (e.g., 0000002488)" required>
            <button type="submit">Analyze Company</button>
        </form>
        <div class="examples">
            <strong>Try these:</strong><br>
            AMD: 0000002488 | NVIDIA: 0001045810 | Tesla: 0001318605
        </div>
    </div>
</body>
</html>
"""

RESULTS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Results - SEC EDGAR Analyzer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        .back {
            display: inline-block;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .error {
            background: #fee;
            border: 2px solid #fcc;
            padding: 15px;
            border-radius: 5px;
            color: #c33;
        }
        .chart { margin: 30px 0; text-align: center; }
        .chart img {
            max-width: 100%;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #007bff; color: white; padding: 10px; }
        td { padding: 8px; border-bottom: 1px solid #ddd; }
    </style>
</head>
<body>
    <a href="/" class="back">← Back</a>
    <div class="container">
        {% if error %}
        <div class="error">Error: {{ error }}</div>
        {% else %}
        <h1>{{ company_name }}</h1>
        <p><strong>CIK:</strong> {{ cik }} | <strong>Ticker:</strong> {{ ticker }}</p>
        <h2>Financial Data</h2>
        {{ table | safe }}
        <h2>Charts</h2>
        {% for title, img in charts.items() %}
        <div class="chart">
            <h3>{{ title }}</h3>
            <img src="data:image/png;base64,{{ img }}">
        </div>
        {% endfor %}
        {% endif %}
    </div>
</body>
</html>
"""


def fetch_company(cik):
    """Fetch company data from SEC EDGAR API using step1's function."""
    return fetch_company_facts(cik)


def combine_metrics(data, metrics_dict):
    """Extract multiple metrics and combine into one DataFrame."""
    dfs = []
    for name, concept in metrics_dict.items():
        results = extract_metric(data, concept)
        if results:
            df = pd.DataFrame(results)[['fy', 'val']]
            df.columns = ['fiscal_year', name]
            dfs.append(df)

    if not dfs:
        return None

    result = dfs[0]
    for df in dfs[1:]:
        result = result.merge(df, on='fiscal_year', how='outer')

    return result.sort_values('fiscal_year')


def create_chart_base64(df, metric, company_name):
    """Create chart and return as base64 string."""
    if metric not in df.columns:
        return None

    data = df[['fiscal_year', metric]].dropna()
    if data.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data['fiscal_year'], data[metric],
            marker='o', linewidth=2, markersize=6, color='#2E86AB')
    ax.set_xlabel('Fiscal Year', fontweight='bold')
    ax.set_ylabel(metric.replace('_', ' ').title(), fontweight='bold')
    ax.set_title(f"{company_name} - {metric.replace('_', ' ').title()}", fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x/1e9:.1f}B'))

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    return img_base64


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/analyze', methods=['POST'])
def analyze():
    cik = request.form.get('cik', '').strip()

    if not cik:
        return render_template_string(RESULTS_HTML, error="Please enter a CIK")

    data = fetch_company(cik)
    if not data:
        return render_template_string(RESULTS_HTML,
                                     error=f"Could not fetch data for CIK {cik}")

    company_name = data.get('entityName', 'Unknown')
    ticker = ', '.join(data.get('tickers', [])) or 'N/A'

    # Extract metrics using step2's extract_metric function
    metrics_dict = {
        'net_income': 'NetIncomeLoss',
        'revenue': 'RevenueFromContractWithCustomerExcludingAssessedTax',
        'assets': 'Assets'
    }

    result = combine_metrics(data, metrics_dict)

    if result is None or result.empty:
        return render_template_string(RESULTS_HTML,
                                     error="No financial data available")

    # Show last 10 years
    result = result.tail(10)

    # Create table
    table_html = result.to_html(index=False, float_format='${:,.0f}'.format)

    # Create charts
    charts = {}
    for metric in ['revenue', 'net_income', 'assets']:
        if metric in result.columns:
            img = create_chart_base64(result, metric, company_name)
            if img:
                charts[metric.replace('_', ' ').title()] = img

    return render_template_string(RESULTS_HTML,
                                 company_name=company_name,
                                 cik=cik,
                                 ticker=ticker,
                                 table=table_html,
                                 charts=charts)


if __name__ == "__main__":
    print("\nSEC EDGAR Financial Analyzer")
    print("=" * 50)
    print("Visit: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
