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

            st.write(business_summary)

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
                f"{debt_to_equity:,.2f}"
                if debt_to_equity is not None
                else "N/A",
            )

        except Exception as error:
            st.error(
                f"Unable to retrieve data for {ticker}. "
                "Check the ticker and try again."
            )
            st.caption(f"Technical details: {error}")