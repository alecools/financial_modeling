"""Funding waterfall — iterative convergence to resolve circular dependency.

The circular dependency:
  Total costs include financing costs (interest, fees)
  → Financing costs depend on debt drawn
  → Debt drawn depends on total costs (LTC target)
  → Loop!

Solution: iterate until total equity / debt stabilise (< $1 tolerance).

Waterfall priority:
  1. Equity (residual funder — covers what debt doesn't)
  2. Land Loan (lump sum at land settlement)
  3. Senior Construction (progressive draws based on LTC)
  4. Mezzanine / Additional (if active)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .inputs import FeasoInputs
from .costs import CostSchedule, build_cost_schedule
from .revenue import RevenueSchedule, build_revenue_schedule
from .gst import GSTSchedule, build_gst_schedule
from .debt import DebtSchedule, build_debt_schedule
from .equity import EquitySchedule, build_equity_schedule


@dataclass
class FundingResult:
    """Complete funding waterfall result after convergence."""

    inputs: FeasoInputs
    costs: CostSchedule
    revenue: RevenueSchedule
    gst: GSTSchedule
    debt: DebtSchedule
    equity: EquitySchedule

    # Cashflow arrays
    total_costs_inc_financing: np.ndarray = field(default_factory=lambda: np.zeros(0))
    cumulative_costs: np.ndarray = field(default_factory=lambda: np.zeros(0))
    cumulative_revenue: np.ndarray = field(default_factory=lambda: np.zeros(0))
    net_cashflow: np.ndarray = field(default_factory=lambda: np.zeros(0))
    cumulative_cashflow: np.ndarray = field(default_factory=lambda: np.zeros(0))

    iterations: int = 0

    @property
    def project_profit(self) -> float:
        """Net development profit (total revenue - total costs inc financing).

        Note: total_costs_inc_financing already includes base costs + selling + financing,
        so we must NOT subtract selling again.
        """
        total_rev = float(self.revenue.total_settlement_revenue.sum())
        total_cost = float(self.total_costs_inc_financing.sum())
        return total_rev - total_cost

    @property
    def total_revenue(self) -> float:
        return float(self.revenue.total_settlement_revenue.sum())

    @property
    def total_costs(self) -> float:
        return float(self.total_costs_inc_financing.sum())

    @property
    def total_selling_costs(self) -> float:
        return float(self.revenue.total_selling_costs.sum())


def run_funding_waterfall(
    inputs: FeasoInputs,
    *,
    max_iterations: int = 10,
    tolerance: float = 1.0,
) -> FundingResult:
    """Run the iterative funding waterfall to convergence.

    Parameters
    ----------
    inputs : FeasoInputs
        All model assumptions.
    max_iterations : int
        Maximum convergence iterations.
    tolerance : float
        Convergence tolerance in dollars.

    Returns
    -------
    FundingResult
        Complete funding result with all schedules.
    """
    n = inputs.num_periods

    # Step 1: Build cost and revenue schedules (these don't change)
    costs = build_cost_schedule(inputs)
    revenue = build_revenue_schedule(inputs)
    gst = build_gst_schedule(revenue, costs)

    # Base costs per period (exc financing)
    base_costs = costs.total_exc_gst.copy()

    # Revenue arrays
    settlement_revenue = revenue.total_settlement_revenue.copy()
    selling_costs = revenue.total_selling_costs.copy()

    # Cumulative revenue for debt calculations
    cum_revenue = np.cumsum(settlement_revenue)

    # Determine Senior Construction start (equity cutoff)
    senior_fac = inputs.get_facility("Senior Construction")
    senior_start_idx = senior_fac.start_month - 1 if senior_fac else n  # 0-based

    # Iterative convergence
    financing_costs = np.zeros(n)
    prev_total_financing = 0.0

    debt_schedule = None
    equity_schedule = None

    for iteration in range(max_iterations):
        # Total costs including financing
        total_costs = base_costs + selling_costs + financing_costs
        cum_costs = np.cumsum(total_costs)

        # ── Phase 1: Build Land Loan (independent) ────────────────
        # Land Loan is built inside build_debt_schedule, but we need
        # equity first. So we compute the funding requirement for
        # the pre-Senior period using only base costs + land loan.

        # Net funding requirement per period (what equity must cover)
        # For pre-Senior periods: equity = total costs (debt draws happen
        # inside build_debt_schedule). We compute a preliminary equity
        # as total costs in pre-Senior period (land loan draws are
        # netted out inside the debt builder).
        # For simplicity: equity covers ALL costs in P0..senior_start-1
        # that aren't covered by Land Loan draws.

        # Preliminary: compute equity funding requirement per period
        # In the pre-Senior period, equity covers all costs.
        # Land Loan draw at its start_month is refinanced into Senior later.
        net_funding_req = total_costs.copy()

        # ── Phase 2: Build equity for pre-Senior period ───────────
        # Net revenue after debt (for repatriation) — use previous iteration's
        # debt schedule if available, otherwise assume zero repayments
        if debt_schedule is not None:
            net_revenue_after_debt = settlement_revenue - debt_schedule.total_repayments
        else:
            net_revenue_after_debt = settlement_revenue.copy()
        net_revenue_after_debt = np.maximum(net_revenue_after_debt, 0)

        # Estimated project profit (for equity distribution)
        # Note: total_costs already includes base_costs + selling_costs + financing_costs
        # (see line above), so no need to add financing or subtract selling again.
        total_rev = float(settlement_revenue.sum())
        profit_est = total_rev - float(total_costs.sum())

        # Build equity schedule — only inject in pre-Senior periods
        equity_schedule = build_equity_schedule(
            inputs, net_funding_req, net_revenue_after_debt, max(0, profit_est),
            equity_cutoff_period=senior_start_idx,
        )

        # Cumulative equity injected up to Senior start
        cum_equity = float(equity_schedule.total_injections[:senior_start_idx].sum())

        # ── Phase 3: Build debt schedule (Land Loan + Senior) ─────
        debt_schedule = build_debt_schedule(
            inputs, cum_costs, cum_revenue,
            cumulative_equity=cum_equity,
        )

        # Update financing costs from debt
        new_financing = debt_schedule.total_financing_cost

        # Check convergence
        total_financing_now = float(new_financing.sum())
        if abs(total_financing_now - prev_total_financing) < tolerance:
            financing_costs = new_financing
            break

        prev_total_financing = total_financing_now
        financing_costs = new_financing
    else:
        iteration = max_iterations

    # Final total costs
    total_costs_final = base_costs + selling_costs + financing_costs

    # Net cashflow
    net_cf = settlement_revenue - total_costs_final - gst.gst_cashflow
    cum_cf = np.cumsum(net_cf)

    return FundingResult(
        inputs=inputs,
        costs=costs,
        revenue=revenue,
        gst=gst,
        debt=debt_schedule if debt_schedule else build_debt_schedule(
            inputs, np.cumsum(base_costs), cum_revenue
        ),
        equity=equity_schedule if equity_schedule else build_equity_schedule(
            inputs, np.zeros(n), np.zeros(n), 0.0
        ),
        total_costs_inc_financing=total_costs_final,
        cumulative_costs=np.cumsum(total_costs_final),
        cumulative_revenue=cum_revenue,
        net_cashflow=net_cf,
        cumulative_cashflow=cum_cf,
        iterations=iteration + 1,
    )
