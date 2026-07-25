# Public Company Financial Analysis and Valuation

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

## Project Files

```text
Public-Company-Financial-Analysis/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── .devcontainer/
└── .gitignore
```

Run the app:

```bash
git clone https://github.com/Raby88/Public-Company-Financial-Analysis.git
cd Public-Company-Financial-Analysis
pip install -r requirements.txt
python -m streamlit run app.py
```

## Shareable ticker links

Append a ticker parameter to the live app URL:

```text
https://public-company-financial-analysis.streamlit.app/?ticker=GOOGL
```

## Live App

No download, installation, or GitHub account is required.

[Open the Live App](https://public-company-financial-analysis.streamlit.app/)

No download, installation, or GitHub account is required.

Users can:

- Enter a stock ticker and analyze a public company
- Review financial performance and company information
- Adjust DCF valuation assumptions
- Compare the company with peer companies
- Open recent SEC filing links
- Download a PDF analysis report

Example direct ticker link:

[Analyze NVIDIA](https://public-company-financial-analysis.streamlit.app/?ticker=NVDA)

Users can interact with the app, but they cannot edit the source code or modify the GitHub repository. Each visitor uses a separate Streamlit session.

## Data sources

Market and financial data are retrieved from Yahoo Finance through
`yfinance`. Regulatory filing links point to SEC EDGAR.

Data may be delayed, incomplete, restated, or reported differently
across providers. Important figures should be verified against the
company's latest regulatory filing.

## Author

Raby Pich

Developed as an independent financial-analysis and valuation project.

## Disclaimer

This application is for educational analysis only. It is not
investment advice or a recommendation to buy or sell securities.
