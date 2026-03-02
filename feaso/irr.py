"""IRR and return metric calculations.

Uses numpy_financial for IRR computation.
Converts monthly IRR to annualised returns.
"""

from __future__ import annotations

import numpy as np

try:
    import numpy_financial as npf
except ImportError:
    npf = None  # type: ignore

from .funding import FundingResult


def _irr_monthly(cashflows: np.ndarray) -> float:
    """Compute monthly IRR from a cashflow array.

    Returns NaN if IRR cannot be computed.
    """
    if npf is None:
        return float("nan")

    # Need at least one positive and one negative cashflow
    if not (np.any(cashflows > 0) and np.any(cashflows < 0)):
        return float("nan")

    try:
        monthly = npf.irr(cashflows)
        if np.isnan(monthly):
            return float("nan")
        return float(monthly)
    except Exception:
        return float("nan")


def _annualise_monthly_irr(monthly_irr: float) -> float:
    """Convert monthly IRR to annualised IRR."""
    if np.isnan(monthly_irr):
        return float("nan")
    return (1 + monthly_irr) ** 12 - 1


def calc_project_irr(result: FundingResult) -> float:
    """Calculate annualised project IRR from net cashflows.

    The project IRR is computed on the ungeared (all-equity) cashflow:
    costs out → revenue in.

    Parameters
    ----------
    result : FundingResult
        Complete model result.

    Returns
    -------
    float
        Annualised project IRR, or NaN if cannot be computed.
    """
    # Project cashflow: revenue in, base costs + selling out (ungeared — no financing)
    revenue = result.revenue.total_settlement_revenue
    base_costs = result.costs.total_exc_gst
    selling = result.revenue.total_selling_costs

    project_cf = revenue - base_costs - selling
    monthly = _irr_monthly(project_cf)
    return _annualise_monthly_irr(monthly)


def calc_equity_irr(result: FundingResult, partner_name: str = "Kokoda Property Group") -> float:
    """Calculate annualised equity IRR for a specific partner.

    The equity IRR is computed on the partner's cashflows:
    injections out → repatriations + profit distributions in.

    Parameters
    ----------
    result : FundingResult
        Complete model result.
    partner_name : str
        Name of the equity partner.

    Returns
    -------
    float
        Annualised equity IRR, or NaN if cannot be computed.
    """
    partner = result.equity.get(partner_name)
    if partner is None:
        return float("nan")

    equity_cf = partner.net_cashflow
    monthly = _irr_monthly(equity_cf)
    return _annualise_monthly_irr(monthly)


def calc_roi(result: FundingResult) -> float:
    """Calculate simple ROI = profit / total costs.

    Parameters
    ----------
    result : FundingResult
        Complete model result.

    Returns
    -------
    float
        ROI as a percentage (e.g., 337.0 for 337%).
    """
    total_rev = float(result.revenue.total_settlement_revenue.sum())
    # total_costs_inc_financing already includes base costs + selling + financing
    total_outflow = float(result.total_costs_inc_financing.sum())

    if total_outflow == 0:
        return 0.0

    profit = total_rev - total_outflow
    return (profit / total_outflow) * 100


def calc_cost_per_lot(result: FundingResult) -> float:
    """Total cost per lot."""
    total_cost = float(result.total_costs_inc_financing.sum())
    lots = result.inputs.project_lots
    return total_cost / lots if lots > 0 else 0.0


def calc_cost_per_sqm(result: FundingResult) -> float:
    """Total cost per square metre of GFA."""
    total_cost = float(result.total_costs_inc_financing.sum())
    gfa = result.inputs.project_gfa_sqm
    return total_cost / gfa if gfa > 0 else 0.0


def calc_revenue_per_sqm(result: FundingResult) -> float:
    """Revenue per square metre of GFA."""
    total_rev = float(result.revenue.total_settlement_revenue.sum())
    gfa = result.inputs.project_gfa_sqm
    return total_rev / gfa if gfa > 0 else 0.0
