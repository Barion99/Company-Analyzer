import re
from urllib.parse import urlparse


import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf


st.set_page_config(
    page_title="Company Analyzer",
    page_icon="📊",
    layout="wide",
)


def format_money(value):
    """Format large currency values."""
    if value is None or pd.isna(value):
        return "N/A"

    if abs(value) >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:,.2f}T"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    return f"${value:,.2f}"


def get_statement_row(statement, possible_names):
    """Find a financial-statement row even when labels differ."""
    for name in possible_names:
        if name in statement.index:
            return statement.loc[name]

    return pd.Series(dtype="float64")



def safe_divide(numerator, denominator):
    """Divide safely when values are missing or zero."""
    if (
        numerator is None
        or denominator is None
        or pd.isna(numerator)
        or pd.isna(denominator)
        or denominator == 0
    ):
        return None

    return numerator / denominator


def latest_value(dataframe, column):
    """Return the latest available value from a dataframe."""
    if column not in dataframe.columns:
        return None

    values = dataframe[column].dropna()

    if values.empty:
        return None

    return float(values.iloc[-1])


def calculate_cagr(series):
    """Calculate compound annual growth rate."""
    values = series.dropna().sort_index()

    if len(values) < 2:
        return None

    starting_value = float(values.iloc[0])
    ending_value = float(values.iloc[-1])
    number_of_years = int(values.index[-1] - values.index[0])

    if (
        starting_value <= 0
        or ending_value <= 0
        or number_of_years <= 0
    ):
        return None

    return (
        ending_value / starting_value
    ) ** (1 / number_of_years) - 1


def format_percent(value):
    """Format a decimal value as a percentage."""
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value * 100:,.1f}%"

def shorten_overview(text, max_sentences=3, max_chars=650):
    """Create a concise company description."""
    if not text:
        return "No company description is available."

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    overview = " ".join(sentences[:max_sentences])

    if len(overview) > max_chars:
        overview = overview[:max_chars].rsplit(" ", 1)[0] + "..."

    return overview


def get_company_logo_url(info):
    """Return a company logo or website favicon URL."""
    logo_url = info.get("logo_url")

    if logo_url:
        return logo_url

    website = info.get("website")

    if not website:
        return None

    normalized_website = (
        website
        if website.startswith(("http://", "https://"))
        else f"https://{website}"
    )

    domain = urlparse(normalized_website).netloc
    domain = domain.removeprefix("www.")

    if not domain:
        return None

    return (
        "https://www.google.com/s2/favicons"
        f"?domain={domain}&sz=128"
    )

@st.cache_data(ttl=3600)
def load_company_data(ticker_symbol):
    company = yf.Ticker(ticker_symbol)

    return {
        "info": company.info,
        "income_statement": company.financials,
        "cash_flow": company.cashflow,
        "balance_sheet": company.balance_sheet,
    }


st.title("Company Analyzer")
st.write("Analyze public companies using market and financial data.")

ticker = st.text_input(
    "Enter a stock ticker",
    placeholder="AAPL",
).strip().upper()

analyze = st.button("Analyze", type="primary")

if analyze:
    if not ticker:
        st.warning("Please enter a ticker.")

    else:
        try:
            with st.spinner(f"Loading financial data for {ticker}..."):
                data = load_company_data(ticker)

            info = data["info"]
            income_statement = data["income_statement"]
            cash_flow = data["cash_flow"]
            balance_sheet = data["balance_sheet"]

            company_name = info.get("longName", ticker)
            sector = info.get("sector", "Not available")
            industry = info.get("industry", "Not available")
            current_price = info.get(
                "currentPrice",
                info.get("regularMarketPrice"),
            )
            market_cap = info.get("marketCap")
            trailing_pe = info.get("trailingPE")
            dividend_yield = info.get("dividendYield")

            logo_url = get_company_logo_url(info)
            
            logo_column, heading_column = st.columns([1, 9])
            
            with logo_column:
                if logo_url:
                    st.image(logo_url, width=85)
                else:
                    st.markdown("## 🏢")
                    
            with heading_column:
                st.header(f"{company_name} ({ticker})")
                st.write(f"**Sector:** {sector}")
                st.write(f"**Industry:** {industry}")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Current Price",
                f"${current_price:,.2f}"
                if current_price is not None
                else "N/A",
            )

            col2.metric(
                "Market Capitalization",
                format_money(market_cap),
            )

            col3.metric(
                "P/E Ratio",
                f"{trailing_pe:,.2f}"
                if trailing_pe is not None
                else "N/A",
            )

            col4.metric(
                "Dividend Yield",
                f"{dividend_yield:,.2f}%"
                if dividend_yield is not None
                else "N/A",
            )

            st.divider()

            st.subheader("Company Overview")

            business_summary = info.get(
                "longBusinessSummary",
                "No company description is available.",
            )

            short_overview = shorten_overview(business_summary)

            st.write(short_overview)

            headquarters_parts = [
                info.get("city"),
                info.get("state"),
                info.get("country"),
            ]
            
            headquarters = ", ".join(
                part for part in headquarters_parts if part
            )
            
            employees = info.get("fullTimeEmployees")
            website = info.get("website")
            
            overview1, overview2, overview3 = st.columns(3)
            
            with overview1:
                st.caption("HEADQUARTERS")
                st.write(headquarters or "N/A")
                
            with overview2:
                st.caption("EMPLOYEES")
                st.write(
                    f"{employees:,}"
                    if employees is not None
                    else "N/A"
                )
                
            with overview3:
                st.caption("WEBSITE")
                
                if website:
                    normalized_website = (
                        website
                        if website.startswith(("http://", "https://"))
                        else f"https://{website}"
                    )
                    
                    website_domain = urlparse(
                        normalized_website
                    ).netloc.removeprefix("www.")
                    
                    st.markdown(
                        f"[{website_domain}]({normalized_website})"
                    )
                else:
                    st.write("N/A")
                    
            st.divider()
            st.subheader("Historical Financial Performance")
            
            revenue = get_statement_row(
                income_statement,
                ["Total Revenue", "Operating Revenue"],
            )

            operating_income = get_statement_row(
                income_statement,
                ["Operating Income"],
            )

            net_income = get_statement_row(
                income_statement,
                [
                    "Net Income",
                    "Net Income Common Stockholders",
                ],
            )

            operating_cash_flow = get_statement_row(
                cash_flow,
                [
                    "Operating Cash Flow",
                    "Total Cash From Operating Activities",
                ],
            )

            capital_expenditure = get_statement_row(
                cash_flow,
                [
                    "Capital Expenditure",
                    "Capital Expenditures",
                ],
            )

            financial_data = pd.DataFrame(
                {
                    "Revenue": revenue,
                    "Operating Income": operating_income,
                    "Net Income": net_income,
                }
            )

            if not operating_cash_flow.empty:
                financial_data["Operating Cash Flow"] = operating_cash_flow

            if (
                not operating_cash_flow.empty
                and not capital_expenditure.empty
            ):
                financial_data["Free Cash Flow"] = (
                    operating_cash_flow + capital_expenditure
                )

            financial_data = financial_data.sort_index()
            financial_data.index = pd.to_datetime(
                financial_data.index
            ).year
            financial_data.index.name = "Year"

            financial_data = financial_data.dropna(
                axis=1,
                how="all",
            )

            if financial_data.empty:
                st.warning(
                    "Historical financial data is unavailable "
                    "for this company."
                )

            else:
                chart_data = (
                    financial_data.reset_index()
                    .melt(
                        id_vars="Year",
                        var_name="Metric",
                        value_name="Amount",
                    )
                    .dropna()
                )

                chart_data["Amount (Billions)"] = (
                    chart_data["Amount"] / 1_000_000_000
                )

                figure = px.bar(
                    chart_data,
                    x="Year",
                    y="Amount (Billions)",
                    color="Metric",
                    barmode="group",
                    title="Annual Financial Performance",
                    labels={
                        "Amount (Billions)": "USD Billions"
                    },
                    color_discrete_sequence=[
                        "#2563EB",  # Blue
                        "#0F766E",  # Teal
                        "#475569",  # Slate
                        "#7C3AED",  # Purple
                        "#0891B2",  # Cyan
                    ],
                )

                st.plotly_chart(
                    figure,
                    use_container_width=True,
                )

                display_table = financial_data.copy()

                for column in display_table.columns:
                    display_table[column] = display_table[
                        column
                    ].apply(format_money)

                st.dataframe(
                    display_table,
                    use_container_width=True,
                )

            st.divider()

            st.subheader("Balance-Sheet Snapshot")

            cash = info.get("totalCash")
            debt = info.get("totalDebt")
            current_ratio = info.get("currentRatio")
            debt_to_equity = info.get("debtToEquity")

            balance1, balance2, balance3, balance4 = st.columns(4)

            balance1.metric("Cash", format_money(cash))
            balance2.metric("Total Debt", format_money(debt))

            balance3.metric(
                "Current Ratio",
                f"{current_ratio:,.2f}"
                if current_ratio is not None
                else "N/A",
            )

            balance4.metric(
                "Debt-to-Equity",
                f"{debt_to_equity / 100:,.2f}x"
                if debt_to_equity is not None
                else "N/A",
            )

            st.divider()

            st.subheader("Financial Health and Profitability")

            latest_revenue = latest_value(
                financial_data,
                "Revenue",
            )

            latest_operating_income = latest_value(
                financial_data,
                "Operating Income",
            )

            latest_net_income = latest_value(
                financial_data,
                "Net Income",
            )

            latest_free_cash_flow = latest_value(
                financial_data,
                "Free Cash Flow",
            )

            revenue_cagr = (
                calculate_cagr(financial_data["Revenue"])
                if "Revenue" in financial_data.columns
                else None
            )

            operating_margin = safe_divide(
                latest_operating_income,
                latest_revenue,
            )

            net_margin = safe_divide(
                latest_net_income,
                latest_revenue,
            )

            free_cash_flow_margin = safe_divide(
                latest_free_cash_flow,
                latest_revenue,
            )

            return_on_assets = info.get("returnOnAssets")
            return_on_equity = info.get("returnOnEquity")

            ratio1, ratio2, ratio3 = st.columns(3)

            ratio1.metric(
                "Revenue CAGR",
                format_percent(revenue_cagr),
            )

            ratio2.metric(
                "Operating Margin",
                format_percent(operating_margin),
            )

            ratio3.metric(
                "Net Profit Margin",
                format_percent(net_margin),
            )

            ratio4, ratio5, ratio6 = st.columns(3)

            ratio4.metric(
                "Free-Cash-Flow Margin",
                format_percent(free_cash_flow_margin),
            )

            ratio5.metric(
                "Return on Assets",
                format_percent(return_on_assets),
            )

            ratio6.metric(
                "Return on Equity",
                format_percent(return_on_equity),
            )

        except Exception as error:
            st.error(
                f"Unable to retrieve data for {ticker}. "
                "Check the ticker and try again."
            )
            st.caption(f"Technical details: {error}")
            