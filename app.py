"""Financial Modelling — Streamlit Application.

Supports two models:
  1. Kokoda Fund Model (quarterly fund projections)
  2. Feaso Development Model (property development feasibility)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Financial Modelling Suite", layout="wide")

# =====================================================================
# Top-Level Model Selector
# =====================================================================
model_choice = st.selectbox(
    "Select Model",
    ["Kokoda Fund Model", "Feaso Development Model"],
    index=0,
)

# =====================================================================
# MODEL 1 — Kokoda Fund
# =====================================================================
if model_choice == "Kokoda Fund Model":
    from model.assumptions import Assumptions
    from model.kokoda_fund import run_kokoda_fund, summarise_kokoda_fund
    from model.underwriting_fund import run_underwriting_fund
    from model.sensitivity import run_sensitivity_analysis, PREDEFINED_SCENARIOS

    st.title("Kokoda High-Level Fund Model")

    # ── Sidebar ──
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

    # ── Run Models ──
    kokoda_df = run_kokoda_fund(a)
    kokoda_summary = summarise_kokoda_fund(kokoda_df)
    uw_result = run_underwriting_fund(a, kokoda_df)
    uw_summary = uw_result["summary"]
    uw_monthly = uw_result["monthly_df"]

    # ── Tabs ──
    tab_dash, tab_kokoda, tab_uw, tab_sens = st.tabs(
        ["Dashboard", "Kokoda Fund", "Underwriting Fund", "Sensitivities"]
    )

    # TAB 1 — Dashboard
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

    # TAB 2 — Kokoda Fund
    with tab_kokoda:
        st.subheader("Quarterly Projection")
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

    # TAB 3 — Underwriting Fund
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

    # TAB 4 — Sensitivities
    with tab_sens:
        st.subheader("Multi-Scenario Sensitivity Analysis")
        st.caption("Runs 7 predefined scenarios (Base + 6 variations) using the "
                   "sensitivity base margin shares of 0.20 / 0.05.")

        sens_df = run_sensitivity_analysis(a)
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


# =====================================================================
# MODEL 2 — Feaso Development Model
# =====================================================================
elif model_choice == "Feaso Development Model":
    from copy import deepcopy

    from feaso.inputs import FeasoInputs
    from feaso.cashflow import run_model, build_cashflow_dataframe
    from feaso.summary import build_summary, format_summary_for_display, FeasoSummary
    from feaso.checks import checks_summary
    from feaso.scenario import (
        run_all_scenarios,
        build_comparison_table,
        get_predefined_scenarios,
        ScenarioOverride,
    )
    from feaso.config import period_to_date

    st.title("Feaso Development Feasibility Model")

    # ── Helper formatters ──
    def _dollar(v: float) -> str:
        if abs(v) >= 1e6:
            return f"${v / 1e6:,.1f}M"
        return f"${v:,.0f}"

    def _pct(v: float) -> str:
        if np.isnan(v):
            return "N/A"
        return f"{v:.1f}%"

    def _irr_fmt(v: float) -> str:
        if np.isnan(v):
            return "N/A"
        return f"{v * 100:.1f}%"

    # ─────────────────────────────────────────────────────────────────
    # Sidebar — Feaso Assumptions & Overrides
    # ─────────────────────────────────────────────────────────────────
    st.sidebar.header("Feaso Assumptions")

    with st.sidebar.expander("Project Overview", expanded=True):
        st.sidebar.markdown(f"**Project:** Fake House")
        st.sidebar.markdown(f"**Lots:** 178 | **GFA:** 32,133 sqm")
        st.sidebar.markdown(f"**Land Purchase:** $11.2M")

    with st.sidebar.expander("Revenue Adjustments", expanded=False):
        revenue_mult = st.number_input(
            "Revenue Multiplier",
            value=1.00, min_value=0.50, max_value=2.00,
            step=0.05, format="%.2f",
            help="Multiply all sale prices (1.0 = no change, 1.1 = +10%)",
        )
        settlement_delay = st.number_input(
            "Settlement Delay (months)",
            value=0, min_value=0, max_value=12, step=1,
            help="Delay all settlement starts by N months",
        )

    with st.sidebar.expander("Cost Adjustments", expanded=False):
        cost_mult = st.number_input(
            "Cost Multiplier",
            value=1.00, min_value=0.50, max_value=2.00,
            step=0.05, format="%.2f",
            help="Multiply all cost items (1.0 = no change, 1.2 = +20%)",
        )
        land_price_override = st.number_input(
            "Land Purchase Price ($)",
            value=11_209_195, step=500_000, format="%d",
            help="Override the land purchase price",
        )

    with st.sidebar.expander("Financing Adjustments", expanded=False):
        interest_rate_adj = st.number_input(
            "Interest Rate Adjustment (pp)",
            value=0.00, min_value=-0.05, max_value=0.10,
            step=0.005, format="%.3f",
            help="Add/subtract percentage points to all debt rates",
        )
        senior_limit_override = st.number_input(
            "Senior Facility Limit ($)",
            value=154_546_628, step=1_000_000, format="%d",
            help="Override the Senior Construction facility limit",
        )

    # ── Build adjusted inputs ──
    @st.cache_data(show_spinner="Running Feaso model...")
    def _run_feaso(
        rev_mult: float,
        settle_delay: int,
        cost_mult: float,
        land_price: int,
        rate_adj: float,
        senior_limit: int,
    ):
        inputs = FeasoInputs()

        # Apply revenue multiplier
        if rev_mult != 1.0:
            for item in inputs.revenue_items:
                item.sale_price_inc_gst *= rev_mult

        # Apply settlement delay
        if settle_delay > 0:
            for item in inputs.revenue_items:
                item.settlement_start += settle_delay

        # Apply cost multiplier
        if cost_mult != 1.0:
            for item in inputs.cost_items:
                item.total_cost *= cost_mult

        # Apply land price override
        if land_price != 11_209_195:
            ratio = land_price / 11_209_195
            inputs.land_purchase_price = float(land_price)
            for stage in inputs.land_payment_stages:
                stage.amount *= ratio

        # Apply interest rate adjustment
        if rate_adj != 0.0:
            for fac in inputs.debt_facilities:
                fac.interest_rate += rate_adj
                if fac.interest_rate_schedule:
                    fac.interest_rate_schedule = {
                        k: v + rate_adj
                        for k, v in fac.interest_rate_schedule.items()
                    }

        # Apply senior limit override
        if senior_limit != 154_546_628:
            for fac in inputs.debt_facilities:
                if "Senior" in fac.name:
                    fac.facility_limit = float(senior_limit)

        # Run the model
        result = run_model(inputs)
        summary = build_summary(result)
        display = format_summary_for_display(summary)
        passed, total, check_results = checks_summary(result)
        cf_df = build_cashflow_dataframe(result)

        return result, summary, display, passed, total, check_results, cf_df

    result, summary, display_metrics, checks_passed, checks_total, check_results, cf_df = _run_feaso(
        revenue_mult, settlement_delay, cost_mult,
        land_price_override, interest_rate_adj, senior_limit_override,
    )

    # ─────────────────────────────────────────────────────────────────
    # Tabs
    # ─────────────────────────────────────────────────────────────────
    tab_dash, tab_cf, tab_fund, tab_summ, tab_sens = st.tabs(
        ["Dashboard", "Cashflow", "Funding", "Summary", "Sensitivity"]
    )

    # ─── TAB 1 — Dashboard ────────────────────────────────────────────
    with tab_dash:
        st.subheader("Key Performance Indicators")

        # Model checks indicator
        if checks_passed == checks_total:
            st.success(f"✅ All {checks_total} model integrity checks passed")
        else:
            st.warning(f"⚠️ {checks_passed}/{checks_total} checks passed")
            with st.expander("View check details"):
                for cr in check_results:
                    icon = "✅" if cr.passed else "❌"
                    st.markdown(f"{icon} **{cr.name}**: {cr.message}")

        # Row 1 — Revenue & Profit
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GRV (inc GST)", _dollar(summary.grv_inc_gst))
        c2.metric("NRV (inc GST)", _dollar(summary.nrv_inc_gst))
        c3.metric("Net Dev Profit", _dollar(summary.net_development_profit))
        c4.metric("ROI", _pct(summary.roi_pct))

        # Row 2 — Returns & Funding
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Project IRR", _irr_fmt(summary.project_irr))
        c6.metric("Kokoda IRR", _irr_fmt(summary.equity_irr))
        c7.metric("Peak Debt", _dollar(summary.peak_debt))
        c8.metric("Total Equity", _dollar(summary.total_equity_injected))

        # Row 3 — Per-unit & Costs
        c9, c10, c11, c12 = st.columns(4)
        c9.metric("Cost per Lot", _dollar(summary.cost_per_lot))
        c10.metric("Profit per Lot", _dollar(summary.profit_per_lot))
        c11.metric("Total Costs (all-in)", _dollar(summary.total_costs_all_in))
        c12.metric("Financing Costs", _dollar(summary.total_financing_costs))

        st.markdown("---")

        # Charts row
        col_left, col_right = st.columns(2)

        with col_left:
            # Capital stack waterfall
            categories = [
                "Land", "Acquisition", "Development", "Construction",
                "Marketing", "Other", "Dev Mgmt", "Selling", "Financing"
            ]
            values = [
                summary.land_costs + summary.prsv_uplift,
                summary.acquisition_costs + summary.stamp_duty,
                summary.development_costs,
                summary.construction_costs,
                summary.marketing_costs,
                summary.other_standard_costs,
                summary.dev_management_costs,
                summary.total_selling_costs,
                summary.total_financing_costs,
            ]

            fig_stack = go.Figure(go.Bar(
                x=categories, y=values,
                marker_color=[
                    "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78",
                    "#2ca02c", "#98df8a", "#d62728", "#ff9896", "#9467bd",
                ],
                text=[_dollar(v) for v in values],
                textposition="outside",
            ))
            fig_stack.update_layout(
                title="Cost Breakdown by Category",
                yaxis_title="$", height=420,
                showlegend=False,
            )
            st.plotly_chart(fig_stack, use_container_width=True)

        with col_right:
            # Funding sources pie
            funding_sources = {
                "Equity": summary.total_equity_injected,
                "Land Loan": summary.land_loan_drawn,
                "Senior Facility": summary.senior_drawn,
            }
            # Only include non-zero
            labels = [k for k, v in funding_sources.items() if v > 0]
            sizes = [v for v in funding_sources.values() if v > 0]

            fig_pie = go.Figure(go.Pie(
                labels=labels, values=sizes,
                hole=0.4,
                textinfo="label+percent",
                marker_colors=["#2ca02c", "#1f77b4", "#ff7f0e"],
            ))
            fig_pie.update_layout(title="Funding Sources", height=420)
            st.plotly_chart(fig_pie, use_container_width=True)

    # ─── TAB 2 — Cashflow ─────────────────────────────────────────────
    with tab_cf:
        st.subheader("Monthly Cashflow Schedule")

        # Show summary cashflow table
        st.dataframe(
            cf_df.style.format("{:,.0f}", na_rep="-"),
            use_container_width=True,
            height=600,
        )

        st.markdown("---")
        st.subheader("Cashflow Charts")

        n = result.inputs.num_periods
        periods = list(range(1, n + 1))
        period_labels = [f"P{p}" for p in periods]

        col_a, col_b = st.columns(2)

        with col_a:
            # Revenue vs Costs over time
            fig_rc = go.Figure()
            fig_rc.add_trace(go.Bar(
                x=period_labels,
                y=result.revenue.total_settlement_revenue,
                name="Revenue",
                marker_color="#2ca02c",
            ))
            fig_rc.add_trace(go.Bar(
                x=period_labels,
                y=-result.costs.total_exc_gst,
                name="Costs (exc fin)",
                marker_color="#d62728",
            ))
            fig_rc.update_layout(
                title="Monthly Revenue vs Costs",
                xaxis_title="Period", yaxis_title="$",
                barmode="relative", height=400,
            )
            st.plotly_chart(fig_rc, use_container_width=True)

        with col_b:
            # Cumulative cashflow
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=period_labels,
                y=result.cumulative_cashflow,
                mode="lines+markers",
                name="Cumulative CF",
                line=dict(color="#1f77b4", width=2),
                fill="tozeroy",
            ))
            fig_cum.add_hline(y=0, line_dash="dash", line_color="grey")
            fig_cum.update_layout(
                title="Cumulative Cashflow",
                xaxis_title="Period", yaxis_title="$",
                height=400,
            )
            st.plotly_chart(fig_cum, use_container_width=True)

        # Net cashflow bar chart
        fig_net = go.Figure()
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in result.net_cashflow]
        fig_net.add_trace(go.Bar(
            x=period_labels,
            y=result.net_cashflow,
            marker_color=colors,
            name="Net Cashflow",
        ))
        fig_net.update_layout(
            title="Net Cashflow per Period",
            xaxis_title="Period", yaxis_title="$",
            height=350,
        )
        st.plotly_chart(fig_net, use_container_width=True)

    # ─── TAB 3 — Funding ──────────────────────────────────────────────
    with tab_fund:
        st.subheader("Funding & Debt Analysis")

        n = result.inputs.num_periods
        periods = list(range(1, n + 1))
        period_labels = [f"P{p}" for p in periods]

        # KPI row
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Land Loan Drawn", _dollar(summary.land_loan_drawn))
        f2.metric("Land Loan Interest", _dollar(summary.land_loan_interest))
        f3.metric("Senior Drawn", _dollar(summary.senior_drawn))
        f4.metric("Senior Interest", _dollar(summary.senior_interest))

        f5, f6, f7, f8 = st.columns(4)
        f5.metric("Senior Peak Balance", _dollar(summary.senior_peak))
        f6.metric("Peak Total Debt", _dollar(summary.peak_debt))
        f7.metric("Total Equity", _dollar(summary.total_equity_injected))
        f8.metric("Convergence Iters", str(summary.convergence_iterations))

        st.markdown("---")
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            # Debt balances by facility
            fig_debt = go.Figure()
            for name, fac_sched in result.debt.facilities.items():
                if fac_sched.total_drawn > 0:
                    fig_debt.add_trace(go.Scatter(
                        x=period_labels,
                        y=fac_sched.closing_balance,
                        mode="lines",
                        name=name,
                        stackgroup="debt",
                    ))
            fig_debt.update_layout(
                title="Debt Facility Balances",
                xaxis_title="Period", yaxis_title="$",
                height=420,
            )
            st.plotly_chart(fig_debt, use_container_width=True)

        with col_d2:
            # Equity vs Debt stacked area
            fig_ed = go.Figure()
            fig_ed.add_trace(go.Scatter(
                x=period_labels,
                y=result.equity.total_injections.cumsum(),
                mode="lines", name="Cumul. Equity",
                fill="tozeroy", line=dict(color="#2ca02c"),
            ))
            fig_ed.add_trace(go.Scatter(
                x=period_labels,
                y=result.debt.total_drawdowns.cumsum(),
                mode="lines", name="Cumul. Debt Draws",
                fill="tozeroy", line=dict(color="#1f77b4"),
            ))
            fig_ed.update_layout(
                title="Cumulative Equity vs Debt Drawdowns",
                xaxis_title="Period", yaxis_title="$",
                height=420,
            )
            st.plotly_chart(fig_ed, use_container_width=True)

        # Interest and fees chart
        st.markdown("---")
        fig_int = go.Figure()
        fig_int.add_trace(go.Bar(
            x=period_labels,
            y=result.debt.total_interest,
            name="Interest", marker_color="#ff7f0e",
        ))
        fig_int.add_trace(go.Bar(
            x=period_labels,
            y=result.debt.total_fees,
            name="Fees", marker_color="#d62728",
        ))
        fig_int.update_layout(
            title="Monthly Interest & Fees",
            xaxis_title="Period", yaxis_title="$",
            barmode="stack", height=350,
        )
        st.plotly_chart(fig_int, use_container_width=True)

        # Equity partner detail
        st.markdown("---")
        st.subheader("Equity Partner Detail")
        for name, partner_sched in result.equity.partners.items():
            if partner_sched.total_injected > 0:
                st.markdown(f"**{name}**")
                ep1, ep2, ep3 = st.columns(3)
                ep1.metric("Total Injected", _dollar(partner_sched.total_injected))
                ep2.metric("Total Repatriated", _dollar(partner_sched.total_repatriated))
                ep3.metric("Total Profit Dist", _dollar(partner_sched.total_profit_distributed))

    # ─── TAB 4 — Summary ──────────────────────────────────────────────
    with tab_summ:
        st.subheader("Detailed Project Summary")

        # Revenue section
        st.markdown("### Revenue")
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("GRV (inc GST)", display_metrics.get("GRV (inc GST)", ""))
        rc2.metric("GRV (exc GST)", display_metrics.get("GRV (exc GST)", ""))
        rc3.metric("NRV (inc GST)", display_metrics.get("NRV (inc GST)", ""))

        rc4, rc5 = st.columns(2)
        rc4.metric("Total Selling Costs", display_metrics.get("Total Selling Costs", ""))
        rc5.metric("Lots", str(summary.project_lots))

        # Costs section
        st.markdown("---")
        st.markdown("### Costs")

        cost_data = {
            "Category": [
                "Land (inc PRSV Uplift)",
                "Acquisition + Stamp Duty",
                "Development",
                "Construction",
                "Marketing & Advertising",
                "Other Standard Costs",
                "Dev & Project Management",
                "Total (exc financing)",
                "Financing Costs",
                "Total (all-in)",
            ],
            "Amount": [
                summary.land_costs + summary.prsv_uplift,
                summary.acquisition_costs + summary.stamp_duty,
                summary.development_costs,
                summary.construction_costs,
                summary.marketing_costs,
                summary.other_standard_costs,
                summary.dev_management_costs,
                summary.total_costs_exc_financing,
                summary.total_financing_costs,
                summary.total_costs_all_in,
            ],
        }
        cost_df = pd.DataFrame(cost_data)
        cost_df["Amount ($)"] = cost_df["Amount"].apply(lambda x: f"${x:,.0f}")
        cost_df["% of Total"] = (cost_df["Amount"] / summary.total_costs_all_in * 100).apply(lambda x: f"{x:.1f}%")
        st.dataframe(
            cost_df[["Category", "Amount ($)", "% of Total"]].set_index("Category"),
            use_container_width=True,
        )

        # Returns section
        st.markdown("---")
        st.markdown("### Returns")
        ret1, ret2, ret3, ret4 = st.columns(4)
        ret1.metric("Net Dev Profit", display_metrics.get("Net Development Profit", ""))
        ret2.metric("ROI", display_metrics.get("ROI", ""))
        ret3.metric("Project IRR", display_metrics.get("Project IRR", ""))
        ret4.metric("Kokoda IRR", display_metrics.get("Kokoda IRR", ""))

        # Per-unit section
        st.markdown("---")
        st.markdown("### Per-Unit Metrics")
        pu1, pu2, pu3, pu4 = st.columns(4)
        pu1.metric("Cost per Lot", display_metrics.get("Cost per Lot", ""))
        pu2.metric("Profit per Lot", display_metrics.get("Profit per Lot", ""))
        pu3.metric("Cost per sqm", display_metrics.get("Cost per sqm", ""))
        pu4.metric("Revenue per sqm", display_metrics.get("Revenue per sqm", ""))

        # Financing section
        st.markdown("---")
        st.markdown("### Financing Detail")
        fin1, fin2, fin3 = st.columns(3)
        fin1.metric("Land Loan Drawn", display_metrics.get("Land Loan Drawn", ""))
        fin2.metric("Land Loan Interest", display_metrics.get("Land Loan Interest", ""))
        fin3.metric("Peak Debt", display_metrics.get("Peak Debt", ""))

        fin4, fin5, fin6 = st.columns(3)
        fin4.metric("Senior Drawn", display_metrics.get("Senior Facility Drawn", ""))
        fin5.metric("Senior Interest", display_metrics.get("Senior Interest", ""))
        fin6.metric("Senior Peak", display_metrics.get("Senior Peak Balance", ""))

        # Cost breakdown pie
        st.markdown("---")
        cost_categories = [
            "Land", "Acquisition", "Development", "Construction",
            "Marketing", "Other", "Dev Mgmt",
        ]
        cost_values = [
            summary.land_costs + summary.prsv_uplift,
            summary.acquisition_costs + summary.stamp_duty,
            summary.development_costs,
            summary.construction_costs,
            summary.marketing_costs,
            summary.other_standard_costs,
            summary.dev_management_costs,
        ]
        # Filter out zero categories
        non_zero = [(c, v) for c, v in zip(cost_categories, cost_values) if v > 0]
        if non_zero:
            cats, vals = zip(*non_zero)
            fig_cpie = go.Figure(go.Pie(
                labels=list(cats), values=list(vals),
                hole=0.35, textinfo="label+percent",
            ))
            fig_cpie.update_layout(title="Cost Category Distribution", height=400)
            st.plotly_chart(fig_cpie, use_container_width=True)

    # ─── TAB 5 — Sensitivity ──────────────────────────────────────────
    with tab_sens:
        st.subheader("Scenario Sensitivity Analysis")
        st.caption("Compares Base Case against 10 predefined scenarios covering "
                   "revenue, cost, settlement, interest rate, and combined variations.")

        # Build base inputs (using current sidebar overrides)
        @st.cache_data(show_spinner="Running scenarios...")
        def _run_scenarios(
            rev_mult: float,
            settle_delay: int,
            cost_mult: float,
            land_price: int,
            rate_adj: float,
            senior_limit: int,
        ):
            inputs = FeasoInputs()

            # Apply sidebar overrides to base
            if rev_mult != 1.0:
                for item in inputs.revenue_items:
                    item.sale_price_inc_gst *= rev_mult
            if settle_delay > 0:
                for item in inputs.revenue_items:
                    item.settlement_start += settle_delay
            if cost_mult != 1.0:
                for item in inputs.cost_items:
                    item.total_cost *= cost_mult
            if land_price != 11_209_195:
                ratio = land_price / 11_209_195
                inputs.land_purchase_price = float(land_price)
                for stage in inputs.land_payment_stages:
                    stage.amount *= ratio
            if rate_adj != 0.0:
                for fac in inputs.debt_facilities:
                    fac.interest_rate += rate_adj
                    if fac.interest_rate_schedule:
                        fac.interest_rate_schedule = {
                            k: v + rate_adj
                            for k, v in fac.interest_rate_schedule.items()
                        }
            if senior_limit != 154_546_628:
                for fac in inputs.debt_facilities:
                    if "Senior" in fac.name:
                        fac.facility_limit = float(senior_limit)

            summaries = run_all_scenarios(inputs)
            comp_df = build_comparison_table(summaries)
            return summaries, comp_df

        scenario_summaries, comp_df = _run_scenarios(
            revenue_mult, settlement_delay, cost_mult,
            land_price_override, interest_rate_adj, senior_limit_override,
        )

        # Display comparison table
        st.dataframe(
            comp_df.style.format("{:,.0f}", na_rep="N/A"),
            use_container_width=True,
            height=500,
        )

        st.markdown("---")
        col_t1, col_t2 = st.columns(2)

        # Extract key metrics for charts
        scenario_names = list(scenario_summaries.keys())
        profits = [s.net_development_profit for s in scenario_summaries.values()]
        rois = [s.roi_pct for s in scenario_summaries.values()]
        peak_debts = [s.peak_debt for s in scenario_summaries.values()]

        with col_t1:
            # Profit comparison bar
            colors = ["#2ca02c" if p >= 0 else "#d62728" for p in profits]
            fig_sp = go.Figure(go.Bar(
                x=scenario_names, y=profits,
                marker_color=colors,
                text=[_dollar(p) for p in profits],
                textposition="outside",
            ))
            fig_sp.update_layout(
                title="Net Development Profit by Scenario",
                xaxis_title="Scenario", yaxis_title="$",
                height=450,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_sp, use_container_width=True)

        with col_t2:
            # ROI comparison
            fig_roi = go.Figure(go.Bar(
                x=scenario_names, y=rois,
                marker_color="#1f77b4",
                text=[f"{r:.1f}%" for r in rois],
                textposition="outside",
            ))
            fig_roi.update_layout(
                title="ROI (%) by Scenario",
                xaxis_title="Scenario", yaxis_title="%",
                height=450,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_roi, use_container_width=True)

        # Tornado chart — impact on profit relative to base case
        st.markdown("---")
        st.subheader("Tornado Chart — Profit Impact vs Base Case")

        base_profit = scenario_summaries.get("Base Case")
        if base_profit is not None:
            base_val = base_profit.net_development_profit
            tornado_data = []
            for name, s in scenario_summaries.items():
                if name == "Base Case":
                    continue
                delta = s.net_development_profit - base_val
                tornado_data.append({"Scenario": name, "Profit Delta ($)": delta})

            if tornado_data:
                tornado_df = pd.DataFrame(tornado_data)
                tornado_df = tornado_df.sort_values("Profit Delta ($)")

                colors_t = ["#d62728" if d < 0 else "#2ca02c" for d in tornado_df["Profit Delta ($)"]]
                fig_tornado = go.Figure(go.Bar(
                    y=tornado_df["Scenario"],
                    x=tornado_df["Profit Delta ($)"],
                    orientation="h",
                    marker_color=colors_t,
                    text=[_dollar(d) for d in tornado_df["Profit Delta ($)"]],
                    textposition="outside",
                ))
                fig_tornado.add_vline(x=0, line_dash="dash", line_color="grey")
                fig_tornado.update_layout(
                    title=f"Profit Deviation from Base Case ({_dollar(base_val)})",
                    xaxis_title="$ Change in Profit",
                    height=450,
                )
                st.plotly_chart(fig_tornado, use_container_width=True)

        # Peak debt comparison
        fig_pd = go.Figure(go.Bar(
            x=scenario_names, y=peak_debts,
            marker_color="#ff7f0e",
            text=[_dollar(d) for d in peak_debts],
            textposition="outside",
        ))
        fig_pd.update_layout(
            title="Peak Debt by Scenario",
            xaxis_title="Scenario", yaxis_title="$",
            height=400,
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_pd, use_container_width=True)
