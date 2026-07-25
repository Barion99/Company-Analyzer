import re
from datetime import datetime
from html import escape
from io import BytesIO
from urllib.parse import urlparse


import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = [
    "#203A59",
    "#4F6B82",
    "#788793",
    "#3E665B",
    "#8A6E5A",
]

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
    page_title="Public Company Financial Analysis and Valuation",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
        :root {
            color-scheme: light;
            --ink: #111827;
            --navy: #203A59;
            --muted: #5B6570;
            --line: #C8CDD2;
            --soft-line: #E2E5E8;
            --paper: #FFFFFF;
            --soft-paper: #F5F6F7;
        }

        html, body, [class*="css"] {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 17px;
        }

        .stMarkdown p,
        .stMarkdown li,
        .stCaption,
        [data-testid="stCaptionContainer"],
        label {
            font-size: 0.96rem !important;
            line-height: 1.55 !important;
        }

        [data-testid="stTextInputRootElement"] input,
        [data-testid="stNumberInput"] input,
        textarea {
            font-size: 1rem !important;
            min-height: 3rem;
        }

        [data-testid="stTextInputRootElement"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stSelectbox"] label {
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }

        .stApp,
        [data-testid="stAppViewContainer"] {
            background: #EEF1F4;
            color: var(--ink);
        }

        .block-container {
            max-width: 1280px;
            padding: 2rem 2.5rem 4.5rem;
            margin-top: 1.25rem;
            margin-bottom: 2rem;
            background: #FFFFFF;
            border: 1px solid #D7DCE1;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.96);
            border-bottom: 1px solid var(--soft-line);
        }

        h1, h2, h3, h4 {
            color: var(--ink) !important;
            font-family: Arial, Helvetica, sans-serif;
            letter-spacing: 0;
        }

        h2 {
            font-size: 1.55rem !important;
            line-height: 1.3 !important;
            font-weight: 650 !important;
            border-bottom: 1px solid #9DA5AD;
            padding-bottom: 0.5rem;
            margin-top: 0.4rem !important;
        }

        h3 {
            font-size: 1.2rem !important;
            line-height: 1.35 !important;
            font-weight: 650 !important;
        }

        p, label, .stCaption, [data-testid="stCaptionContainer"],
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        div[data-testid="stText"], small {
            color: #24303D !important;
        }

        a {
            color: #174A7E !important;
            text-decoration: underline;
        }

        [data-testid="stTextInputRootElement"] input,
        [data-testid="stNumberInput"] input,
        textarea,
        input {
            background: #FFFFFF !important;
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
            border: 1px solid #AEB5BC !important;
            opacity: 1 !important;
        }

        [data-testid="stTextInputRootElement"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stSelectbox"] label {
            color: #374151 !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-testid="stNumberInput"] input {
            background: #FFFFFF !important;
            color: #111827 !important;
            border-color: #AEB5BC !important;
            border-radius: 2px !important;
        }

        div[data-baseweb="input"] input {
            background: #FFFFFF !important;
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 2px;
            border: 1px solid #172E49;
            background: #203A59;
            color: #FFFFFF !important;
            font-weight: 650;
            min-height: 3rem;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
            font-size: 0.95rem;
            box-shadow: none;
        }

        .stButton > button p,
        .stDownloadButton > button p,
        .stButton > button span,
        .stDownloadButton > button span {
            color: #FFFFFF !important;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {
            background: #6B7280 !important;
            color: #FFFFFF !important;
            border-color: #6B7280 !important;
            opacity: 1 !important;
        }

        div[data-testid="stDataFrame"] * {
            color: #111827 !important;
        }

        div[data-testid="stDataFrame"] {
            background: #FFFFFF !important;
        }

        div[data-testid="stExpander"] * {
            color: #111827 !important;
        }

        .hero-shell {
            padding: 1.2rem 0 1.3rem;
            border-top: 3px solid var(--navy);
            border-bottom: 1px solid #8F979F;
            background: transparent;
            box-shadow: none;
            margin-bottom: 1.25rem;
        }

        .hero-kicker {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            color: var(--ink);
            font-size: 2.55rem;
            line-height: 1.15;
            font-weight: 650;
            margin: 0;
        }

        .hero-subtitle {
            color: var(--muted);
            margin-top: 0.55rem;
            margin-bottom: 0;
            font-size: 1.08rem;
            line-height: 1.5;
        }

        .company-card {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.8rem 0;
            border-top: 1px solid var(--line);
            border-bottom: 1px solid var(--line);
            border-left: 0;
            border-right: 0;
            border-radius: 0;
            background: transparent;
            box-shadow: none;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .company-logo {
            width: 46px;
            height: 46px;
            flex: 0 0 46px;
            border-radius: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #FFFFFF;
            border: 1px solid var(--line);
            overflow: hidden;
        }

        .company-logo img {
            max-width: 34px;
            max-height: 34px;
            object-fit: contain;
            display: block;
        }

        .company-logo-fallback {
            width: 46px;
            height: 46px;
            flex: 0 0 46px;
            border-radius: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--navy);
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
            letter-spacing: 0.03em;
        }

        .company-name {
            color: var(--ink);
            font-size: 1.8rem;
            font-weight: 650;
            margin: 0;
            line-height: 1.2;
        }

        .company-meta {
            color: var(--muted);
            font-size: 1rem;
            margin-top: 0.25rem;
        }

        [data-testid="stMetric"] {
            background: transparent;
            border: 0;
            border-top: 1px solid var(--line);
            padding: 0.7rem 0 0.55rem;
            border-radius: 0;
            min-height: 94px;
            box-shadow: none;
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.045em;
            text-transform: uppercase;
        }

        [data-testid="stMetricValue"] {
            color: var(--ink) !important;
            font-size: 1.72rem !important;
            font-weight: 600;
        }

        [data-testid="stMetricDelta"] {
            font-weight: 600;
        }


        div[data-testid="stExpander"] {
            background: #FFFFFF;
            border: 1px solid var(--line);
            border-radius: 0;
            box-shadow: none;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 0;
            overflow: hidden;
        }

        [data-testid="stAlert"] {
            border-radius: 0;
            border-width: 1px;
        }

        hr {
            border: 0 !important;
            border-top: 1px solid var(--line) !important;
            margin-top: 1.55rem !important;
            margin-bottom: 1.55rem !important;
        }

        .section-tag {
            display: none;
        }

        @media (max-width: 800px) {
            .block-container {
                margin-top: 0;
                padding: 1.2rem 1rem 3rem;
                border-left: 0;
                border-right: 0;
            }

            .hero-title {
                font-size: 1.65rem;
            }

            .company-name {
                font-size: 1.25rem;
            }
        }

        /* Final high-contrast button overrides */
        div.stButton > button,
        div.stDownloadButton > button,
        [data-testid="stBaseButton-primary"],
        [data-testid="stBaseButton-secondary"] {
            background: #203A59 !important;
            background-color: #203A59 !important;
            border: 1px solid #172E49 !important;
            color: #FFFFFF !important;
            opacity: 1 !important;
            min-height: 3rem !important;
            font-size: 1rem !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }

        div.stButton > button {
            min-width: 130px !important;
        }

        div.stDownloadButton > button {
            min-width: 220px !important;
        }

        div.stButton > button *,
        div.stDownloadButton > button *,
        [data-testid="stBaseButton-primary"] *,
        [data-testid="stBaseButton-secondary"] * {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1 !important;
        }

        div.stButton > button:hover,
        div.stDownloadButton > button:hover,
        [data-testid="stBaseButton-primary"]:hover,
        [data-testid="stBaseButton-secondary"]:hover {
            background: #172E49 !important;
            background-color: #172E49 !important;
            border-color: #0D2238 !important;
            color: #FFFFFF !important;
        }

        div.stButton > button:focus,
        div.stDownloadButton > button:focus {
            outline: 2px solid #6B8DB0 !important;
            outline-offset: 2px !important;
        }

        .report-table-wrap {
            width: 100%;
            overflow-x: auto;
            margin-top: 0.65rem;
            margin-bottom: 0.4rem;
            border: 1px solid #BFC6CD;
            background: #FFFFFF;
        }

        .report-table {
            width: 100%;
            border-collapse: collapse;
            background: #FFFFFF;
            color: #111827;
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .report-table thead th {
            background: #E9EDF1;
            color: #172E49;
            border-bottom: 1px solid #9FA8B2;
            padding: 0.7rem 0.75rem;
            text-align: right;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.025em;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .report-table thead th:first-child,
        .report-table tbody td:first-child {
            text-align: left;
        }

        .report-table tbody td {
            background: #FFFFFF;
            color: #111827;
            border-bottom: 1px solid #D9DEE3;
            padding: 0.68rem 0.75rem;
            text-align: right;
            white-space: nowrap;
        }

        .report-table tbody tr:nth-child(even) td {
            background: #F7F8FA;
        }

        .report-table tbody tr.latest-row td {
            background: #EEF3F7;
            color: #0F2740;
            font-weight: 700;
            border-top: 1px solid #9FA8B2;
        }

        .report-table tbody tr:last-child td {
            border-bottom: 0;
        }

        .report-table .negative-value {
            color: #A61B1B;
            font-weight: 650;
        }

        .report-table .na-value {
            color: #7A838C;
            font-style: italic;
        }

        .table-note {
            color: #5B6570;
            font-size: 0.78rem;
            margin-top: 0.35rem;
        }

        [data-testid="stPlotlyChart"] {
            background: #FFFFFF !important;
            border: 1px solid #D7DCE1;
            padding: 0.35rem;
        }

        .data-source-strip {
            margin-top: 0.45rem;
            margin-bottom: 0.6rem;
            padding: 0.58rem 0.72rem;
            background: #F5F7F9;
            border-left: 3px solid #203A59;
            color: #374151;
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .data-source-strip strong {
            color: #172E49;
        }
    </style>
    """,
    unsafe_allow_html=True,
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

def apply_report_chart_style(figure):
    """Apply a clean, high-contrast report style to Plotly charts."""
    figure.update_layout(
        template="plotly_white",
        font=dict(
            family="Arial, Helvetica, sans-serif",
            color="#111827",
            size=14,
        ),
        title=dict(
            font=dict(size=17, color="#111827"),
            x=0.0,
            xanchor="left",
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        legend=dict(
            title_text="",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="#FFFFFF",
            bordercolor="#9CA3AF",
            borderwidth=1,
            font=dict(
                family="Arial, Helvetica, sans-serif",
                color="#111827",
                size=13,
            ),
        ),
        margin=dict(l=55, r=25, t=95, b=55),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#6B7280",
            font=dict(color="#111827", size=13),
        ),
    )

    figure.update_xaxes(
        showgrid=False,
        linecolor="#6B7280",
        linewidth=1,
        tickfont=dict(color="#111827", size=12),
        title_font=dict(color="#111827", size=13),
        zeroline=False,
    )

    figure.update_yaxes(
        showgrid=True,
        gridcolor="#D1D5DB",
        gridwidth=1,
        linecolor="#6B7280",
        linewidth=1,
        tickfont=dict(color="#111827", size=12),
        title_font=dict(color="#111827", size=13),
        zerolinecolor="#9CA3AF",
    )

    figure.update_traces(
        marker_line_color="#FFFFFF",
        marker_line_width=0.5,
    )

    return figure


def render_report_table(
    dataframe,
    index_label,
    highlight_index=None,
):
    """Render a clean white financial table with institutional styling."""
    if dataframe is None or dataframe.empty:
        return

    display_data = dataframe.copy()
    display_data = display_data.dropna(how="all")

    if display_data.empty:
        return

    columns = [index_label] + list(display_data.columns)

    header_cells = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in columns
    )

    body_rows = []
    row_count = len(display_data)

    for position, (index_value, row) in enumerate(
        display_data.iterrows()
    ):
        should_highlight = (
            str(index_value) == str(highlight_index)
            if highlight_index is not None
            else position == row_count - 1
        )

        row_class = (
            ' class="latest-row"'
            if should_highlight
            else ""
        )

        cells = [
            f"<td>{escape(str(index_value))}</td>"
        ]

        for value in row:
            value_text = str(value)
            cell_class = ""

            if value_text == "N/A":
                cell_class = ' class="na-value"'
            elif (
                value_text.startswith("$-")
                or value_text.startswith("-")
            ):
                cell_class = ' class="negative-value"'

            cells.append(
                f"<td{cell_class}>{escape(value_text)}</td>"
            )

        body_rows.append(
            f"<tr{row_class}>{''.join(cells)}</tr>"
        )

    table_html = (
        '<div class="report-table-wrap">'
        '<table class="report-table">'
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
        '<div class="table-note">'
        + (
            "The selected company is highlighted."
            if highlight_index is not None
            else "Most recent reported period is highlighted."
        )
        + "</div>"
    )

    st.markdown(
        table_html,
        unsafe_allow_html=True,
    )



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
    """Return a stable company-logo URL when available."""
    website = info.get("website")

    if website:
        normalized_website = (
            website
            if website.startswith(("http://", "https://"))
            else f"https://{website}"
        )

        domain = urlparse(normalized_website).netloc
        domain = domain.removeprefix("www.")

        if domain:
            return (
                "https://www.google.com/s2/favicons"
                f"?domain={domain}&sz=256"
            )

    icon_slug = BRAND_ICON_SLUGS.get(ticker_symbol.upper())

    if icon_slug:
        return f"https://cdn.simpleicons.org/{icon_slug}"

    return None


def company_initials(company_name, ticker_symbol):
    """Create a fallback mark when a logo cannot be shown."""
    words = [
        word
        for word in re.findall(r"[A-Za-z0-9]+", company_name)
        if word.lower() not in {
            "inc",
            "incorporated",
            "corp",
            "corporation",
            "company",
            "co",
            "plc",
            "limited",
            "ltd",
        }
    ]

    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()

    if words:
        return words[0][:2].upper()

    return ticker_symbol[:2].upper()

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



def build_pdf_report(report):
    """Create a downloadable company-analysis PDF."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        ParagraphStyle,
        getSampleStyleSheet,
    )
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=(
            f"{report['company_name']} "
            f"({report['ticker']}) Analysis"
        ),
        author="Public Company Financial Analysis and Valuation",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=7,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DisclaimerText",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#475569"),
        )
    )

    def paragraph(value, style="SmallText"):
        if value is None:
            value = "N/A"

        return Paragraph(
            escape(str(value)),
            styles[style],
        )

    def clean_number(value, formatter=None):
        if value is None or pd.isna(value):
            return "N/A"

        if formatter is not None:
            return formatter(value)

        return f"{value:,.2f}"

    def percent_value(value):
        return clean_number(value, format_percent)

    def multiple_value(value):
        if value is None or pd.isna(value):
            return "N/A"

        return f"{value:,.2f}x"

    def currency_value(value):
        if value is None or pd.isna(value):
            return "N/A"

        return (
            f"{value:,.2f} "
            f"{report.get('currency', 'USD')}"
        )

    def add_table(
        elements,
        headers,
        rows,
        widths=None,
        font_size=7.5,
    ):
        table_data = [
            [
                Paragraph(
                    f"<b>{escape(str(header))}</b>",
                    styles["SmallText"],
                )
                for header in headers
            ]
        ]

        for row in rows:
            table_data.append(
                [paragraph(value) for value in row]
            )

        table = Table(
            table_data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#E2E8F0"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#0F172A"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        font_size,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#F8FAFC"),
                        ],
                    ),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 8))

    def page_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(
            14 * mm,
            8 * mm,
            "Public Company Financial Analysis and Valuation - Educational analysis only",
        )
        canvas.drawRightString(
            A4[0] - 14 * mm,
            8 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    elements = []

    elements.append(
        Paragraph(
            (
                f"{escape(report['company_name'])} "
                f"({escape(report['ticker'])})"
            ),
            styles["ReportTitle"],
        )
    )

    elements.append(
        Paragraph(
            (
                "Company Analysis Report | Generated "
                f"{escape(report['generated_at'])}"
            ),
            styles["ReportSubtitle"],
        )
    )

    elements.append(
        Paragraph(
            "Company Overview",
            styles["SectionHeading"],
        )
    )

    overview_rows = [
        ["Sector", report.get("sector", "N/A")],
        ["Industry", report.get("industry", "N/A")],
        ["Headquarters", report.get("headquarters", "N/A")],
        ["Employees", report.get("employees", "N/A")],
        ["Website", report.get("website", "N/A")],
    ]

    add_table(
        elements,
        ["Company Detail", "Value"],
        overview_rows,
        widths=[42 * mm, 136 * mm],
    )

    elements.append(
        Paragraph(
            escape(report.get("overview", "N/A")),
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            "Market and Financial Snapshot",
            styles["SectionHeading"],
        )
    )

    snapshot_rows = [
        [
            "Latest Close",
            currency_value(report.get("current_price")),
            "Market Capitalization",
            format_money(report.get("market_cap")),
        ],
        [
            "P/E Ratio",
            multiple_value(report.get("trailing_pe")),
            "Dividend Yield",
            (
                f"{report['dividend_yield']:,.2f}%"
                if report.get("dividend_yield") is not None
                and not pd.isna(report.get("dividend_yield"))
                else "N/A"
            ),
        ],
        [
            "Cash",
            format_money(report.get("cash")),
            "Total Debt",
            format_money(report.get("debt")),
        ],
        [
            "Current Ratio",
            clean_number(report.get("current_ratio")),
            "Debt-to-Equity",
            multiple_value(report.get("debt_to_equity_ratio")),
        ],
    ]

    add_table(
        elements,
        ["Metric", "Value", "Metric", "Value"],
        snapshot_rows,
        widths=[36 * mm, 50 * mm, 36 * mm, 56 * mm],
    )

    health_rows = [
        ["Revenue CAGR", percent_value(report.get("revenue_cagr"))],
        [
            "Operating Margin",
            percent_value(report.get("operating_margin")),
        ],
        ["Net Profit Margin", percent_value(report.get("net_margin"))],
        [
            "Free-Cash-Flow Margin",
            percent_value(report.get("free_cash_flow_margin")),
        ],
        [
            "Return on Assets",
            percent_value(report.get("return_on_assets")),
        ],
        [
            "Return on Equity",
            percent_value(report.get("return_on_equity")),
        ],
    ]

    add_table(
        elements,
        ["Financial Health Metric", "Value"],
        health_rows,
        widths=[90 * mm, 88 * mm],
    )

    annual_data = report.get("annual_financials")

    if (
        isinstance(annual_data, pd.DataFrame)
        and not annual_data.empty
    ):
        elements.append(
            Paragraph(
                "Historical Financial Performance",
                styles["SectionHeading"],
            )
        )

        annual_columns = [
            column
            for column in [
                "Revenue",
                "Operating Income",
                "Net Income",
                "Operating Cash Flow",
                "Free Cash Flow",
            ]
            if column in annual_data.columns
        ]

        annual_rows = []

        for index, row in annual_data.tail(5).iterrows():
            annual_rows.append(
                [index]
                + [
                    format_money(row.get(column))
                    for column in annual_columns
                ]
            )

        add_table(
            elements,
            ["Year"] + annual_columns,
            annual_rows,
            font_size=6.8,
        )

    quarterly_data = report.get("quarterly_cash_flow")

    if (
        isinstance(quarterly_data, pd.DataFrame)
        and not quarterly_data.empty
    ):
        elements.append(
            Paragraph(
                "Quarterly Cash Flow",
                styles["SectionHeading"],
            )
        )

        quarterly_columns = [
            column
            for column in [
                "Operating Cash Flow",
                "Capital Expenditure",
                "Free Cash Flow",
            ]
            if column in quarterly_data.columns
        ]

        quarterly_rows = []

        for index, row in quarterly_data.tail(8).iterrows():
            quarterly_rows.append(
                [index]
                + [
                    format_money(row.get(column))
                    for column in quarterly_columns
                ]
            )

        add_table(
            elements,
            ["Quarter"] + quarterly_columns,
            quarterly_rows,
            font_size=7,
        )

    dcf_scenarios = report.get("dcf_scenarios")

    if (
        isinstance(dcf_scenarios, pd.DataFrame)
        and not dcf_scenarios.empty
    ):
        elements.append(PageBreak())
        elements.append(
            Paragraph(
                "Discounted Cash Flow Scenarios",
                styles["SectionHeading"],
            )
        )

        dcf_rows = []

        for _, row in dcf_scenarios.iterrows():
            dcf_rows.append(
                [
                    row.get("Scenario", "N/A"),
                    currency_value(row.get("Fair Value")),
                    percent_value(row.get("Upside / Downside")),
                    percent_value(row.get("FCF Growth")),
                    percent_value(row.get("Discount Rate")),
                    percent_value(row.get("Terminal Growth")),
                ]
            )

        add_table(
            elements,
            [
                "Scenario",
                "Fair Value",
                "Upside/Downside",
                "FCF Growth",
                "Discount Rate",
                "Terminal Growth",
            ],
            dcf_rows,
            font_size=6.8,
        )

        elements.append(
            Paragraph(
                (
                    "DCF base source: "
                    f"{escape(report.get('dcf_fcf_source', 'N/A'))}"
                ),
                styles["SmallText"],
            )
        )

    peer_data = report.get("peer_comparison")

    if (
        isinstance(peer_data, pd.DataFrame)
        and not peer_data.empty
    ):
        elements.append(
            Paragraph(
                "Comparable Company Analysis",
                styles["SectionHeading"],
            )
        )

        peer_rows = []

        for _, row in peer_data.head(5).iterrows():
            peer_rows.append(
                [
                    row.get("Ticker", "N/A"),
                    format_money(row.get("Market Cap")),
                    percent_value(row.get("Revenue Growth")),
                    percent_value(row.get("Operating Margin")),
                    multiple_value(row.get("P/E")),
                    multiple_value(row.get("EV/EBITDA")),
                ]
            )

        add_table(
            elements,
            [
                "Ticker",
                "Market Cap",
                "Revenue Growth",
                "Operating Margin",
                "P/E",
                "EV/EBITDA",
            ],
            peer_rows,
            font_size=6.8,
        )

        peer_valuation_rows = [
            [
                "P/E-Implied Share Value",
                currency_value(report.get("implied_pe_value")),
            ],
            [
                "EV/EBITDA-Implied Share Value",
                currency_value(
                    report.get("implied_ev_ebitda_value")
                ),
            ],
        ]

        add_table(
            elements,
            ["Peer Valuation Estimate", "Value"],
            peer_valuation_rows,
            widths=[95 * mm, 83 * mm],
        )

    filing_records = report.get("filings", [])

    if filing_records:
        elements.append(
            Paragraph(
                "Recent SEC Filings",
                styles["SectionHeading"],
            )
        )

        filing_rows = []

        for filing in filing_records[:8]:
            filing_rows.append(
                [
                    filing.get("type", "N/A"),
                    filing.get("date", "N/A"),
                    filing.get("title", "N/A"),
                    filing.get("edgarUrl", "N/A"),
                ]
            )

        add_table(
            elements,
            ["Form", "Filed", "Document", "SEC URL"],
            filing_rows,
            widths=[18 * mm, 25 * mm, 60 * mm, 75 * mm],
            font_size=6.2,
        )

    elements.append(
        Paragraph(
            "Data Sources and Limitations",
            styles["SectionHeading"],
        )
    )

    elements.append(
        Paragraph(
            (
                "Market information and financial statements are "
                "retrieved from Yahoo Finance through yfinance. "
                "Regulatory filing links point to SEC EDGAR. DCF and "
                "peer-implied values are calculated by this app from "
                "the displayed assumptions and available data. Data "
                "may be delayed, incomplete, restated, or reported "
                "differently across providers. Verify important "
                "figures against the latest company filing."
            ),
            styles["DisclaimerText"],
        )
    )

    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(
            (
                "This report is provided for educational analysis "
                "only and is not investment advice or a recommendation "
                "to buy or sell any security."
            ),
            styles["DisclaimerText"],
        )
    )

    document.build(
        elements,
        onFirstPage=page_footer,
        onLaterPages=page_footer,
    )

    buffer.seek(0)
    return buffer.getvalue()


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

    try:
        sec_filings = company.sec_filings
    except Exception:
        sec_filings = []

    return {
        "info": company.info,
        "income_statement": company.financials,
        "cash_flow": company.cashflow,
        "balance_sheet": company.balance_sheet,
        "quarterly_cash_flow": quarterly_cash_flow,
        "sec_filings": sec_filings,
        "price_history": price_history,
    }


@st.cache_data(ttl=3600)
def load_peer_metrics(ticker_symbols):
    """Load comparable-company metrics for a group of tickers."""
    rows = []

    for symbol in ticker_symbols:
        try:
            company = yf.Ticker(symbol)
            peer_info = company.info

            price = peer_info.get(
                "currentPrice",
                peer_info.get("regularMarketPrice"),
            )
            total_revenue = peer_info.get("totalRevenue")
            free_cash_flow = peer_info.get("freeCashflow")

            free_cash_flow_margin = safe_divide(
                free_cash_flow,
                total_revenue,
            )

            rows.append(
                {
                    "Ticker": symbol,
                    "Company": peer_info.get(
                        "shortName",
                        peer_info.get("longName", symbol),
                    ),
                    "Price": price,
                    "Market Cap": peer_info.get("marketCap"),
                    "Revenue Growth": peer_info.get(
                        "revenueGrowth"
                    ),
                    "Operating Margin": peer_info.get(
                        "operatingMargins"
                    ),
                    "Net Margin": peer_info.get(
                        "profitMargins"
                    ),
                    "FCF Margin": free_cash_flow_margin,
                    "P/E": peer_info.get("trailingPE"),
                    "EV/EBITDA": peer_info.get(
                        "enterpriseToEbitda"
                    ),
                    "Return on Equity": peer_info.get(
                        "returnOnEquity"
                    ),
                    "Debt/Equity": (
                        peer_info.get("debtToEquity") / 100
                        if peer_info.get("debtToEquity")
                        is not None
                        else None
                    ),
                    "EPS": peer_info.get("trailingEps"),
                    "EBITDA": peer_info.get("ebitda"),
                    "Cash": peer_info.get("totalCash"),
                    "Debt": peer_info.get("totalDebt"),
                    "Shares": peer_info.get(
                        "sharesOutstanding"
                    ),
                }
            )

        except Exception:
            rows.append(
                {
                    "Ticker": symbol,
                    "Company": symbol,
                    "Price": None,
                    "Market Cap": None,
                    "Revenue Growth": None,
                    "Operating Margin": None,
                    "Net Margin": None,
                    "FCF Margin": None,
                    "P/E": None,
                    "EV/EBITDA": None,
                    "Return on Equity": None,
                    "Debt/Equity": None,
                    "EPS": None,
                    "EBITDA": None,
                    "Cash": None,
                    "Debt": None,
                    "Shares": None,
                }
            )

    return pd.DataFrame(rows)


st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Financial Research and Valuation</div>
        <div class="hero-title">Public Company Financial Analysis</div>
        <div class="hero-subtitle">
            Financial statements, valuation, comparable companies,
            and regulatory filings.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

def reset_analysis():
    """Clear the current ticker and all ticker-specific inputs."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.query_params.clear()


query_ticker = str(
    st.query_params.get("ticker", "")
).strip().upper()

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = query_ticker or None

if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = (
        st.session_state.selected_ticker or ""
    )

ticker_input = st.text_input(
    "Enter a stock ticker",
    placeholder="AAPL",
    key="ticker_input",
).strip().upper()

button1, button2, button_space = st.columns(
    [1, 1, 5],
    gap="small",
)

with button1:
    analyze_clicked = st.button(
        "Analyze",
        type="primary",
        use_container_width=True,
    )

with button2:
    st.button(
        "Reset",
        use_container_width=True,
        on_click=reset_analysis,
    )

if analyze_clicked:
    if ticker_input:
        st.session_state.selected_ticker = ticker_input
        st.query_params["ticker"] = ticker_input
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
        sec_filings = data["sec_filings"]
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

        logo_url = get_company_logo(info, ticker)
        initials = company_initials(company_name, ticker)

        if logo_url:
            logo_markup = (
                '<div class="company-logo">'
                f'<img src="{logo_url}" alt="{company_name} logo" '
                'onerror="this.style.display=\'none\';'
                'this.parentElement.className='
                '\'company-logo-fallback\';'
                f'this.parentElement.innerText=\'{initials}\';">'
                "</div>"
            )
        else:
            logo_markup = (
                '<div class="company-logo-fallback">'
                f"{initials}"
                "</div>"
            )

        st.markdown(
            f"""
            <div class="company-card">
                {logo_markup}
                <div>
                    <div class="company-name">
                        {company_name} ({ticker})
                    </div>
                    <div class="company-meta">
                        {sector} &nbsp;•&nbsp; {industry}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

        market_data_date = (
            str(price_date)
            if price_date is not None
            else "latest available"
        )

        st.markdown(
            f"""
            <div class="data-source-strip">
                <strong>Market data:</strong> {market_data_date}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <strong>Sources:</strong> Yahoo Finance and SEC EDGAR
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Copy the current URL to share this ticker.
            </div>
            """,
            unsafe_allow_html=True,
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
                    "#12355B",  # Revenue - deep navy
                    "#2F6690",  # Operating Income - blue
                    "#7A8793",  # Net Income - slate
                    "#2A7F72",  # Operating Cash Flow - teal
                    "#C07A3D",  # Free Cash Flow - copper
                ],
            )

            apply_report_chart_style(figure)

            figure.update_traces(
                marker_line_color="#FFFFFF",
                marker_line_width=0.8,
            )

            figure.update_layout(
                height=500,
                bargap=0.18,
                bargroupgap=0.06,
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
                theme=None,
            )

            display_table = (
                financial_data.dropna(how="all").copy()
            )

            for column in display_table.columns:
                display_table[column] = display_table[
                    column
                ].apply(format_money)

            render_report_table(
                display_table,
                "Year",
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

            apply_report_chart_style(quarterly_figure)
            quarterly_figure.update_layout(
                legend_title_text="FCF Status",
                showlegend=True,
                height=470,
                bargap=0.28,
            )
            quarterly_figure.update_traces(
                texttemplate="%{y:,.2f}",
                textposition="outside",
                cliponaxis=False,
            )

            st.plotly_chart(
                quarterly_figure,
                use_container_width=True,
                theme=None,
            )

            quarterly_display = (
                quarterly_data.dropna(how="all").copy()
            )

            for column in quarterly_display.columns:
                quarterly_display[column] = quarterly_display[
                    column
                ].apply(format_money)

            render_report_table(
                quarterly_display,
                "Quarter",
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

        scenario_data = pd.DataFrame()

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
                    text="Fair Value",
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

                apply_report_chart_style(valuation_figure)
                valuation_figure.update_layout(showlegend=True)
                valuation_figure.update_traces(
                    texttemplate="%{text:,.2f}",
                    textposition="outside",
                    cliponaxis=False,
                )

                st.plotly_chart(
                    valuation_figure,
                    use_container_width=True,
                    theme=None,
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
        st.divider()

        st.subheader("SEC Filings and Data Sources")
        st.caption(
            "Review recent regulatory filings and verify important "
            "information using official SEC EDGAR documents."
        )

        if isinstance(sec_filings, dict):
            filing_records = sec_filings.get("filings", [])
        elif isinstance(sec_filings, list):
            filing_records = sec_filings
        else:
            filing_records = []

        preferred_forms = {
            "10-K",
            "10-K/A",
            "10-Q",
            "10-Q/A",
            "8-K",
            "8-K/A",
        }

        selected_filings = [
            filing
            for filing in filing_records
            if filing.get("type") in preferred_forms
        ]

        selected_filings = sorted(
            selected_filings,
            key=lambda filing: str(filing.get("date", "")),
            reverse=True,
        )[:8]

        sec_company_url = (
            "https://www.sec.gov/edgar/browse/"
            f"?CIK={ticker}&owner=exclude"
        )

        if not selected_filings:
            st.info(
                "Recent 10-K, 10-Q, or 8-K filing details were not "
                "returned for this ticker."
            )
            st.markdown(
                f"[Browse {ticker} on SEC EDGAR]"
                f"({sec_company_url})"
            )

        else:
            filing1, filing2, filing3 = st.columns(
                [1.2, 1.4, 5]
            )
            filing1.caption("FORM")
            filing2.caption("FILED")
            filing3.caption("DOCUMENT")

            for filing in selected_filings:
                form_type = filing.get("type", "Filing")
                filing_date = filing.get("date", "N/A")
                filing_title = filing.get(
                    "title",
                    f"{form_type} filing",
                )
                filing_url = filing.get("edgarUrl")

                row1, row2, row3 = st.columns(
                    [1.2, 1.4, 5]
                )

                row1.write(f"**{form_type}**")
                row2.write(str(filing_date))

                if filing_url:
                    row3.markdown(
                        f"[{filing_title}]({filing_url})"
                    )
                else:
                    row3.write(filing_title)

            st.markdown(
                f"[Browse all {ticker} filings on SEC EDGAR]"
                f"({sec_company_url})"
            )

        with st.expander("About the app's data sources"):
            st.markdown(
                """
**Market price and company information:** Yahoo Finance,
accessed through `yfinance`.

**Financial statements and quarterly cash flow:** Yahoo Finance,
accessed through `yfinance`.

**Regulatory filing documents:** Official SEC EDGAR links.

**DCF and peer-implied values:** Calculated by this app from the
displayed assumptions and available financial data.

Data can be delayed, incomplete, restated, or reported differently
across providers. Important figures should be checked against the
company's latest SEC filing before making a decision.
                """
            )

        st.divider()

        st.subheader("Comparable Company Analysis")
        st.caption(
            "Enter up to four peer tickers separated by commas. "
            "The current company is included automatically."
        )

        peer_input = st.text_input(
            "Peer tickers",
            placeholder="MSFT, AMZN, META",
            key=f"peer_input_{ticker}",
        )

        peer_symbols = []
        available_rows = pd.DataFrame()
        implied_pe_value = None
        implied_ev_ebitda_value = None

        for raw_symbol in peer_input.split(","):
            symbol = raw_symbol.strip().upper()

            if (
                symbol
                and symbol != ticker
                and symbol not in peer_symbols
            ):
                peer_symbols.append(symbol)

        if len(peer_symbols) > 4:
            st.warning(
                "Only the first four peer tickers will be used."
            )
            peer_symbols = peer_symbols[:4]

        if not peer_symbols:
            st.info(
                "Enter at least one peer ticker to generate "
                "the comparison."
            )

        else:
            comparison_symbols = [ticker] + peer_symbols

            with st.spinner(
                "Loading comparable-company data..."
            ):
                peer_data = load_peer_metrics(
                    tuple(comparison_symbols)
                )

            available_rows = peer_data[
                peer_data[
                    [
                        "Market Cap",
                        "Revenue Growth",
                        "Operating Margin",
                        "Net Margin",
                        "P/E",
                        "EV/EBITDA",
                    ]
                ].notna().any(axis=1)
            ].copy()

            missing_symbols = [
                symbol
                for symbol in comparison_symbols
                if symbol not in available_rows["Ticker"].tolist()
            ]

            if missing_symbols:
                st.warning(
                    "Limited or unavailable data for: "
                    + ", ".join(missing_symbols)
                )

            if available_rows.empty:
                st.warning(
                    "Comparable-company data could not be loaded."
                )

            else:
                comparison_display = available_rows[
                    [
                        "Ticker",
                        "Company",
                        "Price",
                        "Market Cap",
                        "Revenue Growth",
                        "Operating Margin",
                        "Net Margin",
                        "FCF Margin",
                        "P/E",
                        "EV/EBITDA",
                        "Return on Equity",
                        "Debt/Equity",
                    ]
                ].copy()

                comparison_display["Price"] = (
                    comparison_display["Price"].apply(
                        lambda value: (
                            f"{value:,.2f} {currency}"
                            if value is not None
                            and not pd.isna(value)
                            else "N/A"
                        )
                    )
                )

                comparison_display["Market Cap"] = (
                    comparison_display["Market Cap"].apply(
                        format_money
                    )
                )

                percentage_columns = [
                    "Revenue Growth",
                    "Operating Margin",
                    "Net Margin",
                    "FCF Margin",
                    "Return on Equity",
                ]

                for column in percentage_columns:
                    comparison_display[column] = (
                        comparison_display[column].apply(
                            format_percent
                        )
                    )

                for column in [
                    "P/E",
                    "EV/EBITDA",
                    "Debt/Equity",
                ]:
                    comparison_display[column] = (
                        comparison_display[column].apply(
                            lambda value: (
                                f"{value:,.2f}x"
                                if value is not None
                                and not pd.isna(value)
                                else "N/A"
                            )
                        )
                    )

                peer_table = comparison_display.set_index(
                    "Ticker"
                )

                render_report_table(
                    peer_table,
                    "Ticker",
                    highlight_index=ticker,
                )

                st.markdown("#### Valuation Multiples")

                valuation_metrics = available_rows[
                    ["Ticker", "P/E", "EV/EBITDA"]
                ].melt(
                    id_vars="Ticker",
                    var_name="Multiple",
                    value_name="Value",
                ).dropna()

                if valuation_metrics.empty:
                    st.info(
                        "Valuation multiples are unavailable "
                        "for this peer group."
                    )
                else:
                    valuation_peer_figure = px.bar(
                        valuation_metrics,
                        x="Ticker",
                        y="Value",
                        color="Multiple",
                        text="Value",
                        barmode="group",
                        title="Peer Valuation Multiples",
                        labels={"Value": "Multiple (x)"},
                        color_discrete_map={
                            "P/E": "#12355B",
                            "EV/EBITDA": "#C07A3D",
                        },
                    )

                    apply_report_chart_style(
                        valuation_peer_figure
                    )

                    valuation_peer_figure.update_traces(
                        texttemplate="%{text:,.1f}x",
                        textposition="outside",
                        cliponaxis=False,
                        marker_line_color="#FFFFFF",
                        marker_line_width=0.8,
                    )

                    valuation_peer_figure.update_layout(
                        height=450,
                        bargap=0.28,
                        bargroupgap=0.08,
                    )

                    st.plotly_chart(
                        valuation_peer_figure,
                        use_container_width=True,
                        theme=None,
                    )

                st.markdown("#### Profitability Comparison")

                profitability_metrics = available_rows[
                    [
                        "Ticker",
                        "Operating Margin",
                        "Net Margin",
                        "FCF Margin",
                    ]
                ].melt(
                    id_vars="Ticker",
                    var_name="Metric",
                    value_name="Value",
                ).dropna()

                if profitability_metrics.empty:
                    st.info(
                        "Profitability data is unavailable "
                        "for this peer group."
                    )
                else:
                    profitability_metrics["Value (%)"] = (
                        profitability_metrics["Value"] * 100
                    )

                    profitability_figure = px.bar(
                        profitability_metrics,
                        x="Ticker",
                        y="Value (%)",
                        color="Metric",
                        text="Value (%)",
                        barmode="group",
                        title="Peer Profitability",
                        color_discrete_map={
                            "Operating Margin": "#2F6690",
                            "Net Margin": "#2A7F72",
                            "FCF Margin": "#C07A3D",
                        },
                    )

                    apply_report_chart_style(
                        profitability_figure
                    )

                    profitability_figure.update_traces(
                        texttemplate="%{text:,.1f}%",
                        textposition="outside",
                        cliponaxis=False,
                        marker_line_color="#FFFFFF",
                        marker_line_width=0.8,
                    )

                    profitability_figure.update_layout(
                        height=450,
                        bargap=0.28,
                        bargroupgap=0.08,
                    )

                    st.plotly_chart(
                        profitability_figure,
                        use_container_width=True,
                        theme=None,
                    )

                target_row = peer_data[
                    peer_data["Ticker"] == ticker
                ]

                peer_only_data = peer_data[
                    peer_data["Ticker"] != ticker
                ]

                peer_median_pe = peer_only_data["P/E"].dropna()
                peer_median_ev_ebitda = peer_only_data[
                    "EV/EBITDA"
                ].dropna()

                implied_pe_value = None
                implied_ev_ebitda_value = None

                if not target_row.empty:
                    target = target_row.iloc[0]

                    if (
                        not peer_median_pe.empty
                        and target["EPS"] is not None
                        and not pd.isna(target["EPS"])
                        and target["EPS"] > 0
                    ):
                        implied_pe_value = (
                            float(peer_median_pe.median())
                            * float(target["EPS"])
                        )

                    if (
                        not peer_median_ev_ebitda.empty
                        and target["EBITDA"] is not None
                        and not pd.isna(target["EBITDA"])
                        and target["EBITDA"] > 0
                        and target["Shares"] is not None
                        and not pd.isna(target["Shares"])
                        and target["Shares"] > 0
                    ):
                        implied_enterprise_value = (
                            float(
                                peer_median_ev_ebitda.median()
                            )
                            * float(target["EBITDA"])
                        )

                        target_cash = (
                            float(target["Cash"])
                            if target["Cash"] is not None
                            and not pd.isna(target["Cash"])
                            else 0
                        )
                        target_debt = (
                            float(target["Debt"])
                            if target["Debt"] is not None
                            and not pd.isna(target["Debt"])
                            else 0
                        )

                        implied_equity_value = (
                            implied_enterprise_value
                            + target_cash
                            - target_debt
                        )

                        implied_ev_ebitda_value = (
                            implied_equity_value
                            / float(target["Shares"])
                        )

                st.divider()
                st.markdown("#### Peer-Implied Valuation")

                implied1, implied2, implied3 = st.columns(3)

                implied1.metric(
                    "Peer Median P/E",
                    (
                        f"{peer_median_pe.median():,.2f}x"
                        if not peer_median_pe.empty
                        else "N/A"
                    ),
                )

                implied2.metric(
                    "P/E-Implied Share Value",
                    (
                        f"{implied_pe_value:,.2f} {currency}"
                        if implied_pe_value is not None
                        else "N/A"
                    ),
                )

                implied3.metric(
                    "EV/EBITDA-Implied Share Value",
                    (
                        f"{implied_ev_ebitda_value:,.2f} "
                        f"{currency}"
                        if implied_ev_ebitda_value is not None
                        else "N/A"
                    ),
                )

                st.caption(
                    "Peer-implied values are reference estimates, "
                    "not price targets. Peer selection and differences "
                    "in growth, risk, accounting, and business mix can "
                    "materially affect the comparison."
                )

        st.divider()

        st.subheader("Download Company Analysis Report")
        st.caption(
            "Generate a PDF containing the current company overview, "
            "financial metrics, quarterly cash flow, DCF scenarios, "
            "peer comparison, and SEC filing references."
        )

        report_payload = {
            "ticker": ticker,
            "company_name": company_name,
            "currency": currency,
            "generated_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "sector": sector,
            "industry": industry,
            "headquarters": headquarters or "N/A",
            "employees": (
                f"{employees:,}"
                if employees is not None
                else "N/A"
            ),
            "website": website or "N/A",
            "overview": short_overview,
            "current_price": current_price,
            "market_cap": market_cap,
            "trailing_pe": trailing_pe,
            "dividend_yield": dividend_yield,
            "cash": cash,
            "debt": debt,
            "current_ratio": current_ratio,
            "debt_to_equity_ratio": (
                debt_to_equity / 100
                if debt_to_equity is not None
                else None
            ),
            "revenue_cagr": revenue_cagr,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "free_cash_flow_margin": free_cash_flow_margin,
            "return_on_assets": return_on_assets,
            "return_on_equity": return_on_equity,
            "annual_financials": financial_data.copy(),
            "quarterly_cash_flow": quarterly_data.copy(),
            "dcf_scenarios": scenario_data.copy(),
            "dcf_fcf_source": dcf_fcf_source,
            "peer_comparison": available_rows.copy(),
            "implied_pe_value": implied_pe_value,
            "implied_ev_ebitda_value": (
                implied_ev_ebitda_value
            ),
            "filings": selected_filings,
        }

        try:
            pdf_report = build_pdf_report(report_payload)

            st.download_button(
                label="Download PDF Report",
                data=pdf_report,
                file_name=(
                    f"{ticker.lower()}_company_analysis.pdf"
                ),
                mime="application/pdf",
                type="primary",
                key=f"download_report_{ticker}",
            )

        except ImportError:
            st.error(
                "PDF generation requires ReportLab. Install it "
                "with: pip install reportlab"
            )

        except Exception as report_error:
            st.error(
                "The PDF report could not be generated."
            )
            st.caption(
                f"Report details: {report_error}"
            )

    except Exception as error:
        st.error(
            f"Unable to retrieve data for {ticker}. "
            "Check the ticker and try again."
        )
        st.caption(f"Technical details: {error}")