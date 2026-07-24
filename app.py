import re
from urllib.parse import urlparse


import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

BRAND_ICON_SLUGS = {
    "AAPL": "apple",
    "MSFT": "microsoft",
    "GOOG": "google",
    "GOOGL": "google",
    "AMZN": "amazon",
    "META": "meta",
    "NVDA": "nvidia",
    "TSLA": "tesla",
    "NFLX": "netflix",
    "ORCL": "oracle",
    "IBM": "ibm",
    "INTC": "intel",
    "AMD": "amd",
    "ADBE": "adobe",
    "CSCO": "cisco",
    "PYPL": "paypal",
    "SPOT": "spotify",
    "UBER": "uber",
    "ABNB": "airbnb",
}

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
    """Find a financial-statement row despite label-format differences."""
    if statement is None or statement.empty:
        return pd.Series(dtype="float64")

    normalized_index = {
        re.sub(r"[^a-z0-9]", "", str(label).lower()): label
        for label in statement.index
    }

    for name in possible_names:
        normalized_name = re.sub(
            r"[^a-z0-9]",
            "",
            name.lower(),
        )

        matching_label = normalized_index.get(normalized_name)

        if matching_label is not None:
            return statement.loc[matching_label]

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


def get_company_logo(info, ticker_symbol):
    """Return the best available logo and an appropriate display width."""

    icon_slug = BRAND_ICON_SLUGS.get(ticker_symbol.upper())

    if icon_slug:
        return f"https://cdn.simpleicons.org/{icon_slug}", 72

    logo_url = info.get("logo_url")

    if logo_url:
        return logo_url, 56

    website = info.get("website")

    if not website:
        return None, 48

    normalized_website = (
        website
        if website.startswith(("http://", "https://"))
        else f"https://{website}"
    )

    domain = urlparse(normalized_website).netloc
    domain = domain.removeprefix("www.")

    if not domain:
        return None, 48

    favicon_url = (
        "https://www.google.com/s2/favicons"
        f"?domain={domain}&sz=256"
    )

    return favicon_url, 48

def calculate_dcf(
    base_free_cash_flow,
    growth_rate,
    discount_rate,
    terminal_growth_rate,
    cash,
    debt,
    shares_outstanding,
    forecast_years=5,
):
    """Calculate a simple free-cash-flow DCF valuation."""

    required_values = [
        base_free_cash_flow,
        growth_rate,
        discount_rate,
        terminal_growth_rate,
        shares_outstanding,
    ]

    if any(
        value is None or pd.isna(value)
        for value in required_values
    ):
        return None

    if base_free_cash_flow <= 0:
        return None

    if shares_outstanding <= 0:
        return None

    if discount_rate <= terminal_growth_rate:
        return None

    cash = cash or 0
    debt = debt or 0

    projected_rows = []
    projected_fcf = base_free_cash_flow
    present_value_sum = 0

    for year in range(1, forecast_years + 1):
        projected_fcf *= 1 + growth_rate

        discount_factor = (1 + discount_rate) ** year
        present_value = projected_fcf / discount_factor

        present_value_sum += present_value

        projected_rows.append(
            {
                "Year": year,
                "Projected Free Cash Flow": projected_fcf,
                "Present Value": present_value,
            }
        )

    terminal_value = (
        projected_fcf
        * (1 + terminal_growth_rate)
        / (discount_rate - terminal_growth_rate)
    )

    present_value_terminal = (
        terminal_value
        / (1 + discount_rate) ** forecast_years
    )

    enterprise_value = (
        present_value_sum + present_value_terminal
    )

    equity_value = enterprise_value + cash - debt

    fair_value_per_share = (
        equity_value / shares_outstanding
    )

    forecast_table = pd.DataFrame(projected_rows)

    return {
        "forecast_table": forecast_table,
        "terminal_value": terminal_value,
        "present_value_terminal": present_value_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "fair_value_per_share": fair_value_per_share,
    }


@st.cache_data(ttl=3600)
def load_company_data(ticker_symbol):
    company = yf.Ticker(ticker_symbol)

    price_history = company.history(
        period="5d",
        interval="1d",
        auto_adjust=False,
        repair=True,
    )

    quarterly_cash_flow = company.quarterly_cashflow

    if (
        quarterly_cash_flow is None
        or quarterly_cash_flow.empty
    ):
        quarterly_cash_flow = company.get_cash_flow(
            freq="quarterly"
        )

    return {
        "info": company.info,
        "income_statement": company.financials,
        "cash_flow": company.cashflow,
        "balance_sheet": company.balance_sheet,
        "quarterly_cash_flow": quarterly_cash_flow,
        "price_history": price_history,
    }


st.title("Company Analyzer")
st.write("Analyze public companies using market and financial data.")

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None

ticker_input = st.text_input(
    "Enter a stock ticker",
    placeholder="AAPL",
).strip().upper()

if st.button("Analyze", type="primary"):
    if ticker_input:
        st.session_state.selected_ticker = ticker_input
    else:
        st.warning("Please enter a ticker.")

ticker = st.session_state.selected_ticker

if ticker:
    try:
        with st.spinner(f"Loading financial data for {ticker}..."):
            data = load_company_data(ticker)

        info = data["info"]
        income_statement = data["income_statement"]
        cash_flow = data["cash_flow"]
        balance_sheet = data["balance_sheet"]
        quarterly_cash_flow = data["quarterly_cash_flow"]
        price_history = data["price_history"]

        company_name = info.get("longName", ticker)
        sector = info.get("sector", "Not available")
        industry = info.get("industry", "Not available")
        reported_price = info.get(
            "currentPrice",
            info.get("regularMarketPrice"),
        )

        valid_closes = (
            price_history["Close"].dropna()
            if not price_history.empty and "Close" in price_history.columns
            else pd.Series(dtype="float64")
        )

        if not valid_closes.empty:
            current_price = float(valid_closes.iloc[-1])
            price_date = valid_closes.index[-1].date()
        else:
            current_price = reported_price
            price_date = None

        shares_outstanding = info.get("sharesOutstanding")

        if (
            current_price is not None
            and shares_outstanding is not None
        ):
            market_cap = current_price * shares_outstanding
        else:
            market_cap = info.get("marketCap")

        currency = info.get("currency", "USD")
        trailing_pe = info.get("trailingPE")
        dividend_yield = info.get("dividendYield")

        logo_url, logo_width = get_company_logo(info, ticker)

        logo_column, heading_column = st.columns([1, 9])

        with logo_column:
            if logo_url:
                st.image(logo_url, width=logo_width)
            else:
                st.markdown("## 🏢")

        with heading_column:
            st.header(f"{company_name} ({ticker})")
            st.write(f"**Sector:** {sector}")
            st.write(f"**Industry:** {industry}")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Latest Close",
            f"{current_price:,.2f} {currency}"
            if current_price is not None
            else "N/A",
        )

        if price_date is not None:
            col1.caption(f"As of {price_date}")

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

        if (
            reported_price is not None
            and current_price is not None
            and current_price != 0
        ):
            price_difference = abs(
                reported_price - current_price
            ) / current_price

            if price_difference > 0.10:
                st.warning(
                    "The live quote and historical closing price differ "
                    "significantly. The app is using the repaired latest "
                    "closing price."
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

        st.subheader("Quarterly Cash Flow Trend")
        st.caption(
            "Shows recent quarterly operating cash flow, capital "
            "expenditure, and free cash flow."
        )

        quarterly_operating_cash_flow = get_statement_row(
            quarterly_cash_flow,
            [
                "Operating Cash Flow",
                "OperatingCashFlow",
                "Total Cash From Operating Activities",
                "TotalCashFromOperatingActivities",
            ],
        )

        quarterly_capital_expenditure = get_statement_row(
            quarterly_cash_flow,
            [
                "Capital Expenditure",
                "CapitalExpenditure",
                "Capital Expenditures",
                "CapitalExpenditures",
            ],
        )

        quarterly_free_cash_flow = get_statement_row(
            quarterly_cash_flow,
            [
                "Free Cash Flow",
                "FreeCashFlow",
            ],
        )

        quarterly_data = pd.DataFrame()

        if not quarterly_operating_cash_flow.empty:
            quarterly_data["Operating Cash Flow"] = (
                quarterly_operating_cash_flow
            )

        if not quarterly_capital_expenditure.empty:
            quarterly_data["Capital Expenditure"] = (
                quarterly_capital_expenditure
            )

        if not quarterly_free_cash_flow.empty:
            quarterly_data["Free Cash Flow"] = (
                quarterly_free_cash_flow
            )
        elif (
            not quarterly_operating_cash_flow.empty
            and not quarterly_capital_expenditure.empty
        ):
            quarterly_data["Free Cash Flow"] = (
                quarterly_operating_cash_flow
                + quarterly_capital_expenditure
            )

        quarterly_data = quarterly_data.sort_index().tail(8)
        quarterly_data = quarterly_data.dropna(
            axis=1,
            how="all",
        )

        if (
            quarterly_data.empty
            or "Free Cash Flow" not in quarterly_data.columns
        ):
            st.info(
                "Quarterly free-cash-flow data was not returned "
                "for this company. Annual financials remain available."
            )

        else:
            quarterly_data.index = pd.to_datetime(
                quarterly_data.index
            )
            quarterly_data.index = [
                f"{date.year} Q{date.quarter}"
                for date in quarterly_data.index
            ]
            quarterly_data.index.name = "Quarter"

            latest_quarter = quarterly_data.index[-1]
            latest_quarter_fcf = quarterly_data[
                "Free Cash Flow"
            ].dropna()

            if not latest_quarter_fcf.empty:
                latest_fcf_value = float(
                    latest_quarter_fcf.iloc[-1]
                )

                q_metric1, q_metric2 = st.columns(2)

                q_metric1.metric(
                    "Latest Quarterly FCF",
                    format_money(latest_fcf_value),
                )
                q_metric2.metric(
                    "Latest Reported Quarter",
                    latest_quarter,
                )

                if latest_fcf_value < 0:
                    st.warning(
                        f"{latest_quarter} free cash flow was "
                        f"negative at {format_money(latest_fcf_value)}."
                    )

            quarterly_chart_data = (
                quarterly_data.reset_index()
                .dropna(subset=["Free Cash Flow"])
            )

            quarterly_chart_data["FCF (Billions)"] = (
                quarterly_chart_data["Free Cash Flow"]
                / 1_000_000_000
            )

            quarterly_chart_data["Status"] = (
                quarterly_chart_data["Free Cash Flow"]
                .apply(
                    lambda value: (
                        "Positive" if value >= 0 else "Negative"
                    )
                )
            )

            quarterly_figure = px.bar(
                quarterly_chart_data,
                x="Quarter",
                y="FCF (Billions)",
                color="Status",
                title="Quarterly Free Cash Flow",
                labels={
                    "FCF (Billions)": f"{currency} Billions",
                },
                color_discrete_map={
                    "Positive": "#0F766E",
                    "Negative": "#DC2626",
                },
            )

            quarterly_figure.update_layout(
                legend_title_text="",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                quarterly_figure,
                use_container_width=True,
            )

            quarterly_display = quarterly_data.copy()

            for column in quarterly_display.columns:
                quarterly_display[column] = quarterly_display[
                    column
                ].apply(format_money)

            st.dataframe(
                quarterly_display,
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

        ttm_free_cash_flow = info.get("freeCashflow")

        dcf_base_fcf = latest_free_cash_flow
        dcf_fcf_source = "Latest annual free cash flow"

        if (
            dcf_base_fcf is None
            or dcf_base_fcf <= 0
        ):
            if (
                ttm_free_cash_flow is not None
                and ttm_free_cash_flow > 0
            ):
                dcf_base_fcf = float(ttm_free_cash_flow)
                dcf_fcf_source = "Trailing 12-month free cash flow"

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

        st.divider()
        st.subheader("Discounted Cash Flow (DCF) Valuation")

        st.caption(
            "Adjust the assumptions to estimate the company's "
            "intrinsic value using a five-year free-cash-flow model."
        )
        st.caption(f"DCF base: {dcf_fcf_source}")

        if (
            dcf_base_fcf is None
            or dcf_base_fcf <= 0
        ):
            st.warning(
                "A DCF valuation cannot be calculated because "
                "both annual and trailing-12-month free cash flow "
                "are unavailable or negative."
            )

        elif (
            shares_outstanding is None
            or shares_outstanding <= 0
        ):
            st.warning(
                "A DCF valuation cannot be calculated because "
                "shares outstanding are unavailable."
            )

        else:
            if revenue_cagr is not None:
                default_growth_pct = min(
                    max(revenue_cagr * 100, -5.0),
                    15.0,
                )
            else:
                default_growth_pct = 5.0

            assumption1, assumption2, assumption3, assumption4 = (
                st.columns(4)
            )

            with assumption1:
                base_fcf_billions = st.number_input(
                    f"Base FCF ({currency} billions)",
                    min_value=0.01,
                    value=float(
                        round(
                            dcf_base_fcf / 1_000_000_000,
                            2,
                        )
                    ),
                    step=0.10,
                    key=f"base_fcf_{ticker}",
                )

            with assumption2:
                growth_rate_pct = st.number_input(
                    "Base annual FCF growth",
                    min_value=-20.0,
                    max_value=30.0,
                    value=float(round(default_growth_pct, 1)),
                    step=0.5,
                    format="%.1f",
                    key=f"growth_rate_{ticker}",
                )

            with assumption3:
                discount_rate_pct = st.number_input(
                    "Base discount rate",
                    min_value=4.0,
                    max_value=25.0,
                    value=9.0,
                    step=0.5,
                    format="%.1f",
                    key=f"discount_rate_{ticker}",
                )

            with assumption4:
                terminal_growth_pct = st.number_input(
                    "Base terminal growth",
                    min_value=0.0,
                    max_value=5.0,
                    value=2.5,
                    step=0.1,
                    format="%.1f",
                    key=f"terminal_growth_{ticker}",
                )

            base_growth = growth_rate_pct / 100
            base_discount = discount_rate_pct / 100
            base_terminal = terminal_growth_pct / 100
            base_fcf = base_fcf_billions * 1_000_000_000

            scenario_inputs = {
                "Bear": {
                    "growth_rate": max(base_growth - 0.03, -0.20),
                    "discount_rate": min(
                        base_discount + 0.015,
                        0.25,
                    ),
                    "terminal_growth_rate": max(
                        base_terminal - 0.005,
                        0.0,
                    ),
                },
                "Base": {
                    "growth_rate": base_growth,
                    "discount_rate": base_discount,
                    "terminal_growth_rate": base_terminal,
                },
                "Bull": {
                    "growth_rate": min(base_growth + 0.03, 0.30),
                    "discount_rate": max(
                        base_discount - 0.01,
                        0.04,
                    ),
                    "terminal_growth_rate": min(
                        base_terminal + 0.005,
                        0.05,
                    ),
                },
            }

            scenario_results = {}
            scenario_rows = []

            for scenario_name, assumptions in scenario_inputs.items():
                safe_terminal_growth = min(
                    assumptions["terminal_growth_rate"],
                    assumptions["discount_rate"] - 0.005,
                )
                safe_terminal_growth = max(
                    safe_terminal_growth,
                    0.0,
                )

                result = calculate_dcf(
                    base_free_cash_flow=base_fcf,
                    growth_rate=assumptions["growth_rate"],
                    discount_rate=assumptions["discount_rate"],
                    terminal_growth_rate=safe_terminal_growth,
                    cash=cash,
                    debt=debt,
                    shares_outstanding=shares_outstanding,
                )

                scenario_results[scenario_name] = result

                if result is not None:
                    fair_value = result["fair_value_per_share"]
                    upside_downside = (
                        fair_value / current_price - 1
                        if current_price is not None
                        and current_price > 0
                        else None
                    )

                    scenario_rows.append(
                        {
                            "Scenario": scenario_name,
                            "Fair Value": fair_value,
                            "Upside / Downside": upside_downside,
                            "FCF Growth": assumptions["growth_rate"],
                            "Discount Rate": assumptions["discount_rate"],
                            "Terminal Growth": safe_terminal_growth,
                        }
                    )

            if len(scenario_rows) != 3:
                st.error(
                    "The DCF scenarios could not be calculated. "
                    "Check that the discount rate remains above "
                    "the terminal growth rate."
                )

            else:
                scenario_data = pd.DataFrame(scenario_rows)

                st.markdown("#### Valuation Scenarios")

                bear_column, base_column, bull_column = st.columns(3)

                scenario_columns = {
                    "Bear": bear_column,
                    "Base": base_column,
                    "Bull": bull_column,
                }

                for _, scenario_row in scenario_data.iterrows():
                    scenario_name = scenario_row["Scenario"]
                    scenario_column = scenario_columns[scenario_name]

                    with scenario_column:
                        st.markdown(f"**{scenario_name} case**")
                        st.metric(
                            "Fair Value",
                            (
                                f"{scenario_row['Fair Value']:,.2f} "
                                f"{currency}"
                            ),
                            delta=format_percent(
                                scenario_row["Upside / Downside"]
                            ),
                            delta_color="normal",
                        )
                        st.caption(
                            "Growth "
                            f"{scenario_row['FCF Growth'] * 100:.1f}% · "
                            "Discount "
                            f"{scenario_row['Discount Rate'] * 100:.1f}% · "
                            "Terminal "
                            f"{scenario_row['Terminal Growth'] * 100:.1f}%"
                        )

                valuation_chart_data = scenario_data[
                    ["Scenario", "Fair Value"]
                ].copy()

                valuation_figure = px.bar(
                    valuation_chart_data,
                    x="Scenario",
                    y="Fair Value",
                    color="Scenario",
                    title="DCF Fair Value by Scenario",
                    labels={
                        "Fair Value": f"Fair Value per Share ({currency})",
                    },
                    category_orders={
                        "Scenario": ["Bear", "Base", "Bull"],
                    },
                    color_discrete_map={
                        "Bear": "#B91C1C",
                        "Base": "#2563EB",
                        "Bull": "#0F766E",
                    },
                )

                if current_price is not None:
                    valuation_figure.add_hline(
                        y=current_price,
                        line_dash="dash",
                        annotation_text="Current market price",
                        annotation_position="top left",
                    )

                valuation_figure.update_layout(
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(
                    valuation_figure,
                    use_container_width=True,
                )

                base_result = scenario_results["Base"]

                base_fair_value = base_result[
                    "fair_value_per_share"
                ]
                base_upside_downside = (
                    base_fair_value / current_price - 1
                    if current_price is not None
                    and current_price > 0
                    else None
                )

                result1, result2, result3, result4 = st.columns(4)

                result1.metric(
                    "Base Fair Value",
                    f"{base_fair_value:,.2f} {currency}",
                )

                result2.metric(
                    "Current Market Price",
                    f"{current_price:,.2f} {currency}"
                    if current_price is not None
                    else "N/A",
                )

                result3.metric(
                    "Base Upside / Downside",
                    format_percent(base_upside_downside),
                )

                result4.metric(
                    "Base Enterprise Value",
                    format_money(
                        base_result["enterprise_value"]
                    ),
                )

                st.caption(
                    "Bear and bull cases are automatically derived "
                    "from the base assumptions. This valuation is "
                    "highly sensitive to inputs and is for educational "
                    "analysis, not investment advice."
                )

                with st.expander(
                    "View scenario assumptions and base forecast"
                ):
                    scenario_display = scenario_data.copy()

                    scenario_display["Fair Value"] = (
                        scenario_display["Fair Value"]
                        .apply(
                            lambda value: (
                                f"{value:,.2f} {currency}"
                            )
                        )
                    )
                    scenario_display["Upside / Downside"] = (
                        scenario_display["Upside / Downside"]
                        .apply(format_percent)
                    )
                    scenario_display["FCF Growth"] = (
                        scenario_display["FCF Growth"]
                        .apply(format_percent)
                    )
                    scenario_display["Discount Rate"] = (
                        scenario_display["Discount Rate"]
                        .apply(format_percent)
                    )
                    scenario_display["Terminal Growth"] = (
                        scenario_display["Terminal Growth"]
                        .apply(format_percent)
                    )

                    st.dataframe(
                        scenario_display,
                        use_container_width=True,
                        hide_index=True,
                    )

                    forecast_display = base_result[
                        "forecast_table"
                    ].copy()

                    forecast_display[
                        "Projected Free Cash Flow"
                    ] = forecast_display[
                        "Projected Free Cash Flow"
                    ].apply(format_money)

                    forecast_display[
                        "Present Value"
                    ] = forecast_display[
                        "Present Value"
                    ].apply(format_money)

                    st.markdown("**Base-case forecast**")

                    st.dataframe(
                        forecast_display,
                        use_container_width=True,
                        hide_index=True,
                    )

                    detail1, detail2, detail3 = st.columns(3)

                    detail1.metric(
                        "Terminal Value",
                        format_money(
                            base_result["terminal_value"]
                        ),
                    )

                    detail2.metric(
                        "PV of Terminal Value",
                        format_money(
                            base_result[
                                "present_value_terminal"
                            ]
                        ),
                    )

                    detail3.metric(
                        "Equity Value",
                        format_money(
                            base_result["equity_value"]
                        ),
                    )
    except Exception as error:
        st.error(
            f"Unable to retrieve data for {ticker}. "
            "Check the ticker and try again."
        )
        st.caption(f"Technical details: {error}")