# Company Analyzer

A Streamlit application for public-company financial analysis,
valuation, comparable-company benchmarking, and SEC filing review.

## Features

- Company overview and market snapshot
- Annual financial performance
- Quarterly free-cash-flow analysis
- Balance-sheet and profitability metrics
- Bear, base, and bull DCF valuation
- Comparable-company analysis
- Peer-implied share values
- SEC filing links
- Downloadable PDF report
- Shareable ticker URLs such as `?ticker=GOOGL`
- Reset button for clearing the current analysis

## Project files

```text
company_analyzer_final_release/
├── app.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```
Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
Open a terminal and run:

```bash
git clone https://github.com/Barion99/Company-Analyzer.git
cd Company-Analyzer
pip install -r requirements.txt
python -m streamlit run app.py
```

## Shareable ticker links

After deployment, append a ticker parameter to the URL:

```text
https://your-app-url.streamlit.app/?ticker=GOOGL
```

## Data sources

Market and financial data are retrieved from Yahoo Finance through
`yfinance`. Regulatory filing links point to SEC EDGAR.

Data may be delayed, incomplete, restated, or reported differently
across providers. Important figures should be verified against the
company's latest regulatory filing.

## Disclaimer

This application is for educational analysis only. It is not
investment advice or a recommendation to buy or sell securities.
