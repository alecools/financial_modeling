"""Monthly cashflow assembly — the main entry point for the Feaso model.

Calls all sub-modules (costs, revenue, funding, debt, equity, GST)
and assembles the complete monthly cashflow as a pandas DataFrame.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from .config import period_to_date
from .inputs import FeasoInputs
from .funding import FundingResult, run_funding_waterfall


def run_model(inputs: FeasoInputs) -> FundingResult:
    """Run the complete Feaso model and return the funding result.

    This is the primary entry point. It runs the iterative funding
    waterfall which internally calls costs, revenue, debt, equity,
    and GST sub-modules.

    Parameters
    ----------
    inputs : FeasoInputs
        All model assumptions.

    Returns
    -------
    FundingResult
        Complete model result with all sub-schedules.
    """
    return run_funding_waterfall(inputs)


def build_cashflow_dataframe(result: FundingResult) -> pd.DataFrame:
    """Build a detailed monthly cashflow DataFrame from the funding result.

    Returns a DataFrame with periods as columns (1..N) and rows for
    each cashflow line item, grouped by section.

    Parameters
    ----------
    result : FundingResult
        Output from run_model() or run_funding_waterfall().

    Returns
    -------
    pd.DataFrame
        Monthly cashflow with labelled rows and period columns.
    """
    n = result.inputs.num_periods
    periods = list(range(1, n + 1))

    # Build period date labels
    date_labels = []
    for p in range(n):
        dt = period_to_date(result.inputs.date_of_first_period, p)
        date_labels.append(dt.strftime("%b-%Y"))

    rows = {}

    # ── Revenue Section ─────────────────────────────────────────────
    rows["Revenue (inc GST)"] = result.revenue.total_settlement_revenue
    for code, arr in result.revenue.settlements.items():
        item = next(
            (r for r in result.inputs.revenue_items if r.code == code), None
        )
        label = f"  {item.description}" if item else f"  Revenue {code}"
        rows[label] = arr

    rows["GST on Revenue"] = -result.gst.gst_collected
    rows["Selling Costs (Frontend)"] = -result.revenue.selling_costs_frontend
    rows["Selling Costs (Backend)"] = -result.revenue.selling_costs_backend
    rows["Total Selling Costs"] = -result.revenue.total_selling_costs
    rows["Net Revenue (inc GST)"] = result.revenue.net_revenue

    # ── Presale / Deposit Section ───────────────────────────────────
    rows["---"] = np.zeros(n)  # separator
    rows["Presale Exchanges"] = result.revenue.total_presale_exchange
    rows["Deposits Received"] = result.revenue.deposits_received
    rows["Deposits Released"] = -result.revenue.deposits_released

    # ── Cost Section ────────────────────────────────────────────────
    rows["--- "] = np.zeros(n)  # separator
    rows["Land Costs"] = -result.costs.land
    rows["PRSV Uplift"] = -result.costs.prsv_uplift
    rows["Acquisition Costs"] = -result.costs.acquisition
    rows["Stamp Duty"] = -result.costs.stamp_duty
    rows["Development Costs"] = -result.costs.development
    rows["Construction Costs"] = -result.costs.construction
    rows["Marketing & Advertising"] = -result.costs.marketing
    rows["Other Standard Costs"] = -result.costs.other_standard
    rows["Dev & Project Management"] = -result.costs.dev_management
    rows["Total Costs (exc GST, exc Financing)"] = -result.costs.total_exc_gst

    # ── GST Section ─────────────────────────────────────────────────
    rows["GST Paid on Costs"] = -result.gst.gst_paid_on_costs
    rows["Net GST Position"] = -result.gst.net_gst
    rows["GST Cashflow"] = -result.gst.gst_cashflow

    # ── Financing Section ───────────────────────────────────────────
    rows["----"] = np.zeros(n)  # separator
    for name, fac_sched in result.debt.facilities.items():
        rows[f"{name} - Drawdowns"] = fac_sched.drawdowns
        rows[f"{name} - Interest"] = -fac_sched.interest_charged
        rows[f"{name} - Fees"] = -fac_sched.total_fees
        rows[f"{name} - Repayments"] = -fac_sched.repayments
        rows[f"{name} - Balance"] = fac_sched.closing_balance

    rows["Total Debt Drawdowns"] = result.debt.total_drawdowns
    rows["Total Interest"] = -result.debt.total_interest
    rows["Total Fees"] = -result.debt.total_fees
    rows["Total Debt Repayments"] = -result.debt.total_repayments
    rows["Total Debt Balance"] = result.debt.total_closing_balance

    # ── Equity Section ──────────────────────────────────────────────
    rows["-----"] = np.zeros(n)  # separator
    for name, partner_sched in result.equity.partners.items():
        rows[f"Equity - {name} Injection"] = -partner_sched.injections
        rows[f"Equity - {name} Repatriation"] = partner_sched.repatriations
        rows[f"Equity - {name} Profit Dist"] = partner_sched.profit_distributions
        rows[f"Equity - {name} Balance"] = partner_sched.balance

    rows["Total Equity Injections"] = -result.equity.total_injections
    rows["Total Equity Repatriations"] = result.equity.total_repatriations

    # ── Net Cashflow ────────────────────────────────────────────────
    rows["------"] = np.zeros(n)  # separator
    rows["Net Cashflow"] = result.net_cashflow
    rows["Cumulative Cashflow"] = result.cumulative_cashflow

    # Build DataFrame
    df = pd.DataFrame(rows, index=periods).T
    df.columns = [f"P{p}" for p in periods]

    # Add total column
    df["Total"] = df.sum(axis=1)

    return df


def build_summary_table(result: FundingResult) -> pd.DataFrame:
    """Build a summary KPI table from the funding result.

    Returns a single-column DataFrame with key metrics.
    """
    revenue = result.revenue
    costs = result.costs
    debt = result.debt
    equity = result.equity
    inputs = result.inputs

    grv_inc = inputs.total_grv_inc_gst
    grv_exc = inputs.total_grv_exc_gst
    total_selling = float(revenue.total_selling_costs.sum())
    nrv_inc = grv_inc - total_selling
    nrv_exc = grv_exc - total_selling / (1 + inputs.gst_rate)

    total_costs_exc_financing = float(costs.total_exc_gst.sum())
    total_financing = float(debt.total_financing_cost.sum())
    total_costs_all = total_costs_exc_financing + total_financing + total_selling

    profit_inc = grv_inc - total_costs_all
    roi = (profit_inc / total_costs_all * 100) if total_costs_all > 0 else 0

    metrics = {
        "GRV (inc GST)": f"${grv_inc:,.0f}",
        "GRV (exc GST)": f"${grv_exc:,.0f}",
        "NRV (inc GST)": f"${nrv_inc:,.0f}",
        "Total Selling Costs": f"${total_selling:,.0f}",
        "Total Costs (exc financing)": f"${total_costs_exc_financing:,.0f}",
        "Total Financing Costs": f"${total_financing:,.0f}",
        "Total Costs (all-in)": f"${total_costs_all:,.0f}",
        "Net Development Profit": f"${profit_inc:,.0f}",
        "ROI": f"{roi:.1f}%",
        "Peak Debt": f"${debt.peak_debt:,.0f}",
        "Total Equity Injected": f"${equity.total_equity_injected:,.0f}",
        "Convergence Iterations": str(result.iterations),
        "Project Lots": str(inputs.project_lots),
        "GFA (sqm)": f"{inputs.project_gfa_sqm:,.0f}",
    }

    # Per-facility details
    for name, fac in debt.facilities.items():
        if fac.total_drawn > 0:
            metrics[f"{name} - Total Drawn"] = f"${fac.total_drawn:,.0f}"
            metrics[f"{name} - Total Interest"] = f"${fac.total_interest:,.0f}"
            metrics[f"{name} - Peak Balance"] = f"${fac.peak_balance:,.0f}"

    return pd.DataFrame(
        list(metrics.items()), columns=["Metric", "Value"]
    ).set_index("Metric")
