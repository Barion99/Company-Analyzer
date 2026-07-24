import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Company Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("Company Analyzer")
st.write("Analyze public companies using market and financial data.")

ticker = st.text_input(
    "Enter a stock ticker",
    placeholder="AAPL",
).strip().upper()

if st.button("Analyze"):
    if not ticker:
        st.warning("Please enter a ticker.")
    else:
        try:
            with st.spinner(f"Loading data for {ticker}..."):
                company = yf.Ticker(ticker)
                info = company.info

            company_name = info.get("longName", ticker)
            sector = info.get("sector", "Not available")
            industry = info.get("industry", "Not available")
            current_price = info.get("currentPrice")
            market_cap = info.get("marketCap")
            trailing_pe = info.get("trailingPE")
            dividend_yield = info.get("dividendYield")

            st.subheader(f"{company_name} ({ticker})")
            st.write(f"**Sector:** {sector}")
            st.write(f"**Industry:** {industry}")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Current Price",
                f"${current_price:,.2f}" if current_price is not None else "N/A",
            )

            col2.metric(
                "Market Cap",
                f"${market_cap / 1_000_000_000:,.2f}B"
                if market_cap is not None
                else "N/A",
            )

            col3.metric(
                "P/E Ratio",
                f"{trailing_pe:,.2f}" if trailing_pe is not None else "N/A",
            )

            col4.metric(
                "Dividend Yield",
                f"{dividend_yield:,.2f}%"
                if dividend_yield is not None
                else "N/A",
            )

            business_summary = info.get(
                "longBusinessSummary",
                "No company description is available.",
            )

            st.subheader("Company Overview")
            st.write(business_summary)

        except Exception as error:
            st.error(
                f"Unable to retrieve data for {ticker}. "
                "Check the ticker symbol and try again."
            )
            st.caption(f"Technical details: {error}")