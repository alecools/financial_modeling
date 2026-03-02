"""Summary KPIs — comprehensive metrics matching the Excel !!! - Summary sheet.

Provides both a dict of key metrics and a formatted DataFrame
suitable for display in Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .funding import FundingResult
from .irr import (
    calc_project_irr,
    calc_equity_irr,
    calc_roi,
    calc_cost_per_lot,
    calc_cost_per_sqm,
    calc_revenue_per_sqm,
)


@dataclass
class FeasoSummary:
    """All summary KPIs in a structured object."""

    # ── Revenue ──────────────────────────────────────────────────────
    grv_inc_gst: float
    grv_exc_gst: float
    total_selling_costs: float
    nrv_inc_gst: float
    nrv_exc_gst: float

    # ── Costs ─────────────────────────────────────────────────────────
    land_costs: float
    prsv_uplift: float
    acquisition_costs: float
    stamp_duty: float
    development_costs: float
    construction_costs: float
    marketing_costs: float
    other_standard_costs: float
    dev_management_costs: float
    total_costs_exc_financing: float
    total_financing_costs: float
    total_costs_all_in: float

    # ── Profit & Returns ──────────────────────────────────────────────
    net_development_profit: float
    roi_pct: float
    project_irr: float
    equity_irr: float

    # ── Funding ───────────────────────────────────────────────────────
    peak_debt: float
    total_equity_injected: float
    land_loan_drawn: float
    land_loan_interest: float
    senior_drawn: float
    senior_interest: float
    senior_peak: float

    # ── Per-unit metrics ──────────────────────────────────────────────
    cost_per_lot: float
    cost_per_sqm: float
    revenue_per_sqm: float
    profit_per_lot: float

    # ── Project info ──────────────────────────────────────────────────
    project_lots: int
    project_gfa_sqm: float
    convergence_iterations: int

    def to_dict(self) -> Dict[str, float]:
        """Return flat dict of all metrics (for serialisation / comparison)."""
        return {
            "GRV (inc GST)": self.grv_inc_gst,
            "GRV (exc GST)": self.grv_exc_gst,
            "Total Selling Costs": self.total_selling_costs,
            "NRV (inc GST)": self.nrv_inc_gst,
            "NRV (exc GST)": self.nrv_exc_gst,
            "Land Costs": self.land_costs,
            "PRSV Uplift": self.prsv_uplift,
            "Acquisition Costs": self.acquisition_costs,
            "Stamp Duty": self.stamp_duty,
            "Development Costs": self.development_costs,
            "Construction Costs": self.construction_costs,
            "Marketing Costs": self.marketing_costs,
            "Other Standard Costs": self.other_standard_costs,
            "Dev Management Costs": self.dev_management_costs,
            "Total Costs (exc financing)": self.total_costs_exc_financing,
            "Total Financing Costs": self.total_financing_costs,
            "Total Costs (all-in)": self.total_costs_all_in,
            "Net Development Profit": self.net_development_profit,
            "ROI (%)": self.roi_pct,
            "Project IRR (%)": self.project_irr * 100 if not np.isnan(self.project_irr) else float("nan"),
            "Equity IRR (%)": self.equity_irr * 100 if not np.isnan(self.equity_irr) else float("nan"),
            "Peak Debt": self.peak_debt,
            "Total Equity Injected": self.total_equity_injected,
            "Land Loan Drawn": self.land_loan_drawn,
            "Land Loan Interest": self.land_loan_interest,
            "Senior Drawn": self.senior_drawn,
            "Senior Interest": self.senior_interest,
            "Senior Peak Balance": self.senior_peak,
            "Cost per Lot": self.cost_per_lot,
            "Cost per sqm": self.cost_per_sqm,
            "Revenue per sqm": self.revenue_per_sqm,
            "Profit per Lot": self.profit_per_lot,
            "Project Lots": self.project_lots,
            "GFA (sqm)": self.project_gfa_sqm,
            "Convergence Iterations": self.convergence_iterations,
        }


def build_summary(result: FundingResult) -> FeasoSummary:
    """Build a comprehensive summary from the completed funding result.

    Parameters
    ----------
    result : FundingResult
        Output from run_model() / run_funding_waterfall().

    Returns
    -------
    FeasoSummary
        All key metrics.
    """
    inputs = result.inputs
    costs = result.costs
    revenue = result.revenue
    debt = result.debt
    equity = result.equity

    # ── Revenue metrics ──────────────────────────────────────────────
    grv_inc = inputs.total_grv_inc_gst
    grv_exc = inputs.total_grv_exc_gst
    total_selling = float(revenue.total_selling_costs.sum())
    nrv_inc = grv_inc - total_selling
    nrv_exc = grv_exc - total_selling / (1 + inputs.gst_rate)

    # ── Cost metrics by category ─────────────────────────────────────
    land_costs = float(costs.land.sum())
    prsv_uplift = float(costs.prsv_uplift.sum())
    acquisition_costs = float(costs.acquisition.sum())
    stamp_duty = float(costs.stamp_duty.sum())
    development = float(costs.development.sum())
    construction = float(costs.construction.sum())
    marketing = float(costs.marketing.sum())
    other_standard = float(costs.other_standard.sum())
    dev_management = float(costs.dev_management.sum())

    total_costs_exc_fin = float(costs.total_exc_gst.sum())
    total_financing = float(debt.total_financing_cost.sum())
    total_costs_all = total_costs_exc_fin + total_financing + total_selling

    # ── Profit ────────────────────────────────────────────────────────
    profit = grv_inc - total_costs_all
    roi = calc_roi(result)
    project_irr = calc_project_irr(result)
    equity_irr = calc_equity_irr(result)

    # ── Debt facility details ─────────────────────────────────────────
    land_loan = debt.get("Land Loan")
    senior = debt.get("Senior Construction")

    land_drawn = land_loan.total_drawn if land_loan else 0.0
    land_interest = land_loan.total_interest if land_loan else 0.0
    senior_drawn = senior.total_drawn if senior else 0.0
    senior_interest = senior.total_interest if senior else 0.0
    senior_peak = senior.peak_balance if senior else 0.0

    # ── Per-unit metrics ──────────────────────────────────────────────
    cost_lot = calc_cost_per_lot(result)
    cost_sqm = calc_cost_per_sqm(result)
    rev_sqm = calc_revenue_per_sqm(result)
    lots = inputs.project_lots
    profit_per_lot = profit / lots if lots > 0 else 0.0

    return FeasoSummary(
        grv_inc_gst=grv_inc,
        grv_exc_gst=grv_exc,
        total_selling_costs=total_selling,
        nrv_inc_gst=nrv_inc,
        nrv_exc_gst=nrv_exc,
        land_costs=land_costs,
        prsv_uplift=prsv_uplift,
        acquisition_costs=acquisition_costs,
        stamp_duty=stamp_duty,
        development_costs=development,
        construction_costs=construction,
        marketing_costs=marketing,
        other_standard_costs=other_standard,
        dev_management_costs=dev_management,
        total_costs_exc_financing=total_costs_exc_fin,
        total_financing_costs=total_financing,
        total_costs_all_in=total_costs_all,
        net_development_profit=profit,
        roi_pct=roi,
        project_irr=project_irr,
        equity_irr=equity_irr,
        peak_debt=debt.peak_debt,
        total_equity_injected=equity.total_equity_injected,
        land_loan_drawn=land_drawn,
        land_loan_interest=land_interest,
        senior_drawn=senior_drawn,
        senior_interest=senior_interest,
        senior_peak=senior_peak,
        cost_per_lot=cost_lot,
        cost_per_sqm=cost_sqm,
        revenue_per_sqm=rev_sqm,
        profit_per_lot=profit_per_lot,
        project_lots=lots,
        project_gfa_sqm=inputs.project_gfa_sqm,
        convergence_iterations=result.iterations,
    )


def format_summary_for_display(summary: FeasoSummary) -> Dict[str, str]:
    """Format summary metrics as display-ready strings.

    Returns a dict of label → formatted value suitable for
    Streamlit metric cards or tables.
    """
    def _dollar(v: float) -> str:
        return f"${v:,.0f}"

    def _pct(v: float) -> str:
        if np.isnan(v):
            return "N/A"
        return f"{v:.1f}%"

    def _irr(v: float) -> str:
        if np.isnan(v):
            return "N/A"
        return f"{v * 100:.1f}%"

    return {
        "GRV (inc GST)": _dollar(summary.grv_inc_gst),
        "GRV (exc GST)": _dollar(summary.grv_exc_gst),
        "NRV (inc GST)": _dollar(summary.nrv_inc_gst),
        "Total Selling Costs": _dollar(summary.total_selling_costs),
        "Total Costs (exc financing)": _dollar(summary.total_costs_exc_financing),
        "Total Financing Costs": _dollar(summary.total_financing_costs),
        "Total Costs (all-in)": _dollar(summary.total_costs_all_in),
        "Net Development Profit": _dollar(summary.net_development_profit),
        "ROI": _pct(summary.roi_pct),
        "Project IRR": _irr(summary.project_irr),
        "Kokoda IRR": _irr(summary.equity_irr),
        "Peak Debt": _dollar(summary.peak_debt),
        "Total Equity Injected": _dollar(summary.total_equity_injected),
        "Land Loan Drawn": _dollar(summary.land_loan_drawn),
        "Land Loan Interest": _dollar(summary.land_loan_interest),
        "Senior Facility Drawn": _dollar(summary.senior_drawn),
        "Senior Interest": _dollar(summary.senior_interest),
        "Senior Peak Balance": _dollar(summary.senior_peak),
        "Cost per Lot": _dollar(summary.cost_per_lot),
        "Cost per sqm": _dollar(summary.cost_per_sqm),
        "Revenue per sqm": _dollar(summary.revenue_per_sqm),
        "Profit per Lot": _dollar(summary.profit_per_lot),
        "Project Lots": str(summary.project_lots),
        "GFA (sqm)": f"{summary.project_gfa_sqm:,.0f}",
    }
