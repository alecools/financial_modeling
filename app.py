"""Kokoda Fund Model — Streamlit Application."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from model.assumptions import Assumptions
from model.kokoda_fund import run_kokoda_fund, summarise_kokoda_fund
from model.underwriting_fund import run_underwriting_fund
from model.sensitivity import run_sensitivity_analysis, PREDEFINED_SCENARIOS

st.set_page_config(page_title="Kokoda Fund Model", layout="wide")
st.title("Kokoda High-Level Fund Model")

# =====================================================================
# Sidebar — Editable Assumptions
# =====================================================================
st.sidebar.header("Model Assumptions")

with st.sidebar.expander("Fundraising", expanded=False):
    capital_raise_y1 = st.number_input("Year 1 Raise ($M)", value=50.0, step=5.0)
    capital_raise_y2 = st.number_input("Year 2 Raise ($M)", value=100.0, step=5.0)
    capital_raise_y3 = st.number_input("Year 3 Raise ($M)", value=150.0, step=5.0)
    st.markdown("**Quarterly Raise Pattern**")
    rp1 = st.number_input("Q1 %", value=0.25, step=0.05, format="%.2f")
    rp2 = st.number_input("Q2 %", value=0.25, step=0.05, format="%.2f")
    rp3 = st.number_input("Q3 %", value=0.25, step=0.05, format="%.2f")
    rp4 = st.number_input("Q4 %", value=0.25, step=0.05, format="%.2f")

with st.sidebar.expander("Investment Parameters", expanded=False):
    cash_rate = st.number_input("Cash Rate", value=0.0435, step=0.005, format="%.4f")
    investment_margin = st.number_input("Investment Margin", value=0.0665, step=0.005, format="%.4f")
    establishment_fee_rate = st.number_input("Establishment Fee", value=0.01, step=0.005, format="%.3f")
    admin_fee_rate = st.number_input("Admin Fee", value=0.005, step=0.001, format="%.3f")
    fund_term_years = st.number_input("Fund Term (years)", value=3, min_value=1, max_value=10, step=1)

with st.sidebar.expander("Portfolio Management", expanded=False):
    net_deployment_rate = st.number_input("Net Deployment Rate", value=0.80, step=0.05, format="%.2f")
    cash_at_bank_rate = st.number_input("Cash at Bank Rate", value=0.045, step=0.005, format="%.3f")
    lending_rate_to_spvs = st.number_input("Lending Rate to SPVs", value=0.15, step=0.01, format="%.2f")
    max_redemption_pct = st.number_input("Max Redemption %", value=0.025, step=0.005, format="%.3f")

with st.sidebar.expander("Underwriting Fund", expanded=False):
    uw_fund_term_months = st.number_input("UW Fund Term (months)", value=36, min_value=6, max_value=60, step=6)
    sell_down_months = st.number_input("Sell-Down Period (months)", value=3, min_value=1, max_value=12, step=1)
    gross_fund_size = st.number_input("Gross Fund Size ($M)", value=50.0, step=5.0)
    loc_pct_of_fund = st.number_input("LOC % of Fund", value=0.50, step=0.05, format="%.2f")
    margin_share_net_uw = st.number_input("Margin Share Net UW", value=0.35, step=0.05, format="%.2f")
    margin_share_loc = st.number_input("Margin Share LOC", value=0.15, step=0.05, format="%.2f")
    uw_interest_undrawn = st.number_input("UW Interest on Undrawn", value=0.035, step=0.005, format="%.3f")
    loc_unused_charge = st.number_input("LOC Unused Charge", value=0.01, step=0.005, format="%.3f")
    uw_admin_fee = st.number_input("UW Admin Fee", value=0.005, step=0.001, format="%.3f")

with st.sidebar.expander("Property Lending (Sensitivity Base)", expanded=False):
    gross_return_debt = st.number_input("Gross Return (Debt)", value=0.2436, step=0.01, format="%.4f")
    net_investor_return_debt = st.number_input("Net Investor Return (Debt)", value=0.19, step=0.01, format="%.2f")

# ── Build Assumptions object ──
a = Assumptions(
    capital_raise_y1=capital_raise_y1,
    capital_raise_y2=capital_raise_y2,
    capital_raise_y3=capital_raise_y3,
    raise_pattern_q1=rp1,
    raise_pattern_q2=rp2,
    raise_pattern_q3=rp3,
    raise_pattern_q4=rp4,
    cash_rate=cash_rate,
    investment_margin=investment_margin,
    establishment_fee_rate=establishment_fee_rate,
    admin_fee_rate=admin_fee_rate,
    fund_term_years=fund_term_years,
    net_deployment_rate=net_deployment_rate,
    cash_at_bank_rate=cash_at_bank_rate,
    lending_rate_to_spvs=lending_rate_to_spvs,
    max_redemption_pct=max_redemption_pct,
    uw_fund_term_months=uw_fund_term_months,
    sell_down_months=sell_down_months,
    gross_fund_size=gross_fund_size,
    loc_pct_of_fund=loc_pct_of_fund,
    margin_share_net_uw=margin_share_net_uw,
    margin_share_loc=margin_share_loc,
    uw_interest_undrawn=uw_interest_undrawn,
    loc_unused_charge=loc_unused_charge,
    uw_admin_fee=uw_admin_fee,
    gross_return_debt=gross_return_debt,
    net_investor_return_debt=net_investor_return_debt,
)

# =====================================================================
# Run Models
# =====================================================================
kokoda_df = run_kokoda_fund(a)
kokoda_summary = summarise_kokoda_fund(kokoda_df)
uw_result = run_underwriting_fund(a, kokoda_df)
uw_summary = uw_result["summary"]
uw_monthly = uw_result["monthly_df"]

# =====================================================================
# Tabs
# =====================================================================
tab_dash, tab_kokoda, tab_uw, tab_sens = st.tabs(
    ["Dashboard", "Kokoda Fund", "Underwriting Fund", "Sensitivities"]
)

# ─────────────────────────────────────────────────────────────────────
# TAB 1 — Dashboard
# ─────────────────────────────────────────────────────────────────────
with tab_dash:
    st.subheader("Key Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peak Fund Size ($M)", f"{kokoda_summary['peak_fund_size']:.2f}")
    c2.metric("Total Funds Raised ($M)", f"{kokoda_summary['total_funds_raised']:.2f}")
    c3.metric("Gross IRR", f"{a.gross_irr:.2%}")
    c4.metric("Final Net Asset ($M)", f"{kokoda_summary['final_net_asset_position']:.2f}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total Estab Fees ($M)", f"{kokoda_summary['total_establishment_fee']:.2f}")
    c6.metric("Total Admin Fees ($M)", f"{kokoda_summary['total_admin_fee']:.2f}")
    c7.metric("UW Fund IRR", f"{uw_summary['uw_irr']:.2%}")
    c8.metric("Manager Profit ($M)", f"{uw_summary['manager_profit']:.2f}")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=kokoda_df.index, y=kokoda_df["fund_closing"],
            mode="lines+markers", name="Fund Balance",
            fill="tozeroy", line=dict(color="#1f77b4"),
        ))
        fig.update_layout(title="Kokoda Fund Balance Over Time",
                          xaxis_title="Quarter", yaxis_title="$M",
                          height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=uw_monthly.index, y=uw_monthly["deployed_uw"],
            name="Net UW Fund", marker_color="#2ca02c",
        ))
        fig2.add_trace(go.Bar(
            x=uw_monthly.index, y=uw_monthly["deployed_loc"],
            name="LOC", marker_color="#ff7f0e",
        ))
        fig2.update_layout(title="UW Warehouse Deployment (Monthly)",
                           xaxis_title="Month", yaxis_title="$M",
                           barmode="stack", height=350)
        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────
# TAB 2 — Kokoda Fund
# ─────────────────────────────────────────────────────────────────────
with tab_kokoda:
    st.subheader("Quarterly Projection")

    # Display columns of interest
    display_cols = [
        "fund_opening", "fund_inflow", "fund_estab_fee",
        "fund_coupon_entitlement", "fund_redemptions", "fund_closing",
        "loan_closing", "cash_closing", "net_asset_position",
    ]
    st.dataframe(
        kokoda_df[display_cols].style.format("{:.2f}"),
        use_container_width=True,
    )

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=kokoda_df.index, y=kokoda_df["fund_closing"],
            name="Fund Closing", mode="lines+markers",
        ))
        fig_fc.add_trace(go.Scatter(
            x=kokoda_df.index, y=kokoda_df["loan_closing"],
            name="Loan Balance", mode="lines+markers",
        ))
        fig_fc.add_trace(go.Scatter(
            x=kokoda_df.index, y=kokoda_df["cash_closing"],
            name="Cash Balance", mode="lines+markers",
        ))
        fig_fc.update_layout(title="Fund, Loan & Cash Balances",
                             xaxis_title="Quarter", yaxis_title="$M", height=400)
        st.plotly_chart(fig_fc, use_container_width=True)

    with col_b:
        fig_na = go.Figure()
        fig_na.add_trace(go.Bar(
            x=kokoda_df.index, y=kokoda_df["net_asset_position"],
            name="Net Asset Position", marker_color="#9467bd",
        ))
        fig_na.update_layout(title="Net Asset Position",
                             xaxis_title="Quarter", yaxis_title="$M", height=400)
        st.plotly_chart(fig_na, use_container_width=True)

    st.markdown("---")
    # Cumulative fees
    fig_fees = go.Figure()
    fig_fees.add_trace(go.Scatter(
        x=kokoda_df.index, y=kokoda_df["estab_fee_cumulative"],
        name="Estab Fee (Cumul)", fill="tozeroy",
    ))
    fig_fees.add_trace(go.Scatter(
        x=kokoda_df.index, y=kokoda_df["admin_fee_cumulative"],
        name="Admin Fee (Cumul)", fill="tozeroy",
    ))
    fig_fees.update_layout(title="Cumulative Management Fees",
                           xaxis_title="Quarter", yaxis_title="$M", height=350)
    st.plotly_chart(fig_fees, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────
# TAB 3 — Underwriting Fund
# ─────────────────────────────────────────────────────────────────────
with tab_uw:
    st.subheader("UW Fund Performance")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("UW Peak Deployed ($M)", f"{uw_summary['uw_peak_size']:.2f}")
    m2.metric("UW Total Profit ($M)", f"{uw_summary['uw_total_profit']:.2f}")
    m3.metric("UW Multiple (x)", f"{uw_summary['uw_multiple']:.3f}")
    m4.metric("UW IRR", f"{uw_summary['uw_irr']:.2%}")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("LOC Peak Deployed ($M)", f"{uw_summary['loc_peak_size']:.2f}")
    m6.metric("LOC Total Profit ($M)", f"{uw_summary['loc_total_profit']:.2f}")
    m7.metric("LOC Multiple (x)", f"{uw_summary['loc_multiple']:.3f}")
    m8.metric("LOC Ret on Avg Drawn", f"{uw_summary['loc_return_on_avg_drawn']:.2%}")

    st.markdown(f"**Manager Total Profit:** ${uw_summary['manager_profit']:.2f}M")
    st.markdown(f"**UW Pref Return:** {uw_summary['uw_preferred_return']:.2%} | "
                f"**LOC Pref Return:** {uw_summary['loc_preferred_return']:.2%}")

    st.markdown("---")
    st.subheader("Monthly Detail")

    uw_display_cols = [
        "deployed_total", "deployed_uw", "deployed_loc",
        "uw_profit", "loc_profit", "mgr_profit",
    ]
    st.dataframe(
        uw_monthly[uw_display_cols].style.format("{:.4f}"),
        use_container_width=True,
    )

    st.markdown("---")
    col_u1, col_u2 = st.columns(2)

    with col_u1:
        fig_uwp = go.Figure()
        fig_uwp.add_trace(go.Scatter(
            x=uw_monthly.index, y=uw_monthly["uw_profit"].cumsum(),
            name="UW Fund", mode="lines",
        ))
        fig_uwp.add_trace(go.Scatter(
            x=uw_monthly.index, y=uw_monthly["loc_profit"].cumsum(),
            name="LOC", mode="lines",
        ))
        fig_uwp.add_trace(go.Scatter(
            x=uw_monthly.index, y=uw_monthly["mgr_profit"].cumsum(),
            name="Manager", mode="lines",
        ))
        fig_uwp.update_layout(title="Cumulative Profit by Participant",
                              xaxis_title="Month", yaxis_title="$M", height=400)
        st.plotly_chart(fig_uwp, use_container_width=True)

    with col_u2:
        fig_util = go.Figure()
        fig_util.add_trace(go.Scatter(
            x=uw_monthly.index, y=uw_monthly["deployed_uw"],
            name="UW Deployed", fill="tozeroy", line=dict(color="#2ca02c"),
        ))
        total_uw = a.net_uw_fund_size
        fig_util.add_hline(y=total_uw, line_dash="dash",
                           annotation_text=f"UW Fund Size: {total_uw:.0f}M")
        fig_util.add_trace(go.Scatter(
            x=uw_monthly.index, y=uw_monthly["deployed_loc"],
            name="LOC Deployed", fill="tozeroy", line=dict(color="#ff7f0e"),
        ))
        fig_util.update_layout(title="Deployment vs Capacity",
                               xaxis_title="Month", yaxis_title="$M", height=400)
        st.plotly_chart(fig_util, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────
# TAB 4 — Sensitivities
# ─────────────────────────────────────────────────────────────────────
with tab_sens:
    st.subheader("Multi-Scenario Sensitivity Analysis")
    st.caption("Runs 7 predefined scenarios (Base + 6 variations) using the "
               "sensitivity base margin shares of 0.20 / 0.05.")

    sens_df = run_sensitivity_analysis(a)

    # Format for display
    fmt = {
        "UW Peak Size ($M)": "{:.2f}",
        "UW Profit ($M)": "{:.2f}",
        "UW Multiple (x)": "{:.3f}",
        "UW IRR (%)": "{:.2f}",
        "LOC Peak Size ($M)": "{:.2f}",
        "LOC Profit ($M)": "{:.2f}",
        "LOC Multiple (x)": "{:.3f}",
        "LOC Return on Avg Drawn (%)": "{:.2f}",
        "Manager Profit ($M)": "{:.2f}",
        "UW Pref Return (%)": "{:.2f}",
        "LOC Pref Return (%)": "{:.2f}",
    }
    st.dataframe(sens_df.style.format(fmt), use_container_width=True)

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        fig_irr = px.bar(
            sens_df.reset_index(), x="Scenario", y="UW IRR (%)",
            title="UW Fund IRR by Scenario",
            color="UW IRR (%)", color_continuous_scale="Viridis",
        )
        fig_irr.update_layout(height=400)
        st.plotly_chart(fig_irr, use_container_width=True)

    with col_s2:
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Bar(
            x=sens_df.index, y=sens_df["UW Profit ($M)"],
            name="UW Profit", marker_color="#1f77b4",
        ))
        fig_profit.add_trace(go.Bar(
            x=sens_df.index, y=sens_df["LOC Profit ($M)"],
            name="LOC Profit", marker_color="#ff7f0e",
        ))
        fig_profit.add_trace(go.Bar(
            x=sens_df.index, y=sens_df["Manager Profit ($M)"],
            name="Manager Profit", marker_color="#2ca02c",
        ))
        fig_profit.update_layout(title="Profit Breakdown by Scenario",
                                 barmode="group", height=400,
                                 xaxis_title="Scenario", yaxis_title="$M")
        st.plotly_chart(fig_profit, use_container_width=True)

    # Multiple comparison
    fig_mult = go.Figure()
    fig_mult.add_trace(go.Bar(
        x=sens_df.index, y=sens_df["UW Multiple (x)"],
        name="UW Multiple", marker_color="#9467bd",
    ))
    fig_mult.add_trace(go.Bar(
        x=sens_df.index, y=sens_df["LOC Multiple (x)"],
        name="LOC Multiple", marker_color="#d62728",
    ))
    fig_mult.update_layout(title="Investment Multiples by Scenario",
                           barmode="group", height=400,
                           xaxis_title="Scenario", yaxis_title="Multiple (x)")
    st.plotly_chart(fig_mult, use_container_width=True)
