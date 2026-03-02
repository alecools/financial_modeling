"""Debt facility modelling — monthly tracking of draws, interest, fees, repayments.

Models each debt facility independently:
- Land Loan: lump sum draw, fixed rate, capitalised interest, bullet repay
- Senior Construction: progressive/bulk draw, variable rate, capitalised interest
- Mezzanine / Additional: placeholder slots

Each facility tracks:
  opening_balance → drawdowns → interest → fees → repayments → closing_balance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from .inputs import DebtFacility, FeasoInputs


@dataclass
class DebtFacilitySchedule:
    """Monthly arrays for a single debt facility."""

    name: str
    num_periods: int

    opening_balance: np.ndarray = field(default_factory=lambda: np.zeros(0))
    drawdowns: np.ndarray = field(default_factory=lambda: np.zeros(0))
    interest_charged: np.ndarray = field(default_factory=lambda: np.zeros(0))
    application_fees: np.ndarray = field(default_factory=lambda: np.zeros(0))
    line_fees: np.ndarray = field(default_factory=lambda: np.zeros(0))
    standby_fees: np.ndarray = field(default_factory=lambda: np.zeros(0))
    repayments: np.ndarray = field(default_factory=lambda: np.zeros(0))
    closing_balance: np.ndarray = field(default_factory=lambda: np.zeros(0))

    @property
    def total_fees(self) -> np.ndarray:
        """Total fees per period."""
        return self.application_fees + self.line_fees + self.standby_fees

    @property
    def total_financing_cost(self) -> np.ndarray:
        """Interest + fees per period (the financing cost to the project)."""
        return self.interest_charged + self.total_fees

    @property
    def peak_balance(self) -> float:
        """Maximum closing balance across all periods."""
        if len(self.closing_balance) == 0:
            return 0.0
        return float(self.closing_balance.max())

    @property
    def total_interest(self) -> float:
        return float(self.interest_charged.sum())

    @property
    def total_drawn(self) -> float:
        return float(self.drawdowns.sum())

    @property
    def total_repaid(self) -> float:
        return float(self.repayments.sum())


@dataclass
class DebtSchedule:
    """Aggregated debt schedule across all facilities."""

    num_periods: int
    facilities: Dict[str, DebtFacilitySchedule] = field(default_factory=dict)

    @property
    def total_drawdowns(self) -> np.ndarray:
        """Total drawdowns across all facilities per period."""
        arr = np.zeros(self.num_periods)
        for fs in self.facilities.values():
            arr += fs.drawdowns
        return arr

    @property
    def total_repayments(self) -> np.ndarray:
        """Total repayments across all facilities per period."""
        arr = np.zeros(self.num_periods)
        for fs in self.facilities.values():
            arr += fs.repayments
        return arr

    @property
    def total_interest(self) -> np.ndarray:
        """Total interest across all facilities per period."""
        arr = np.zeros(self.num_periods)
        for fs in self.facilities.values():
            arr += fs.interest_charged
        return arr

    @property
    def total_fees(self) -> np.ndarray:
        """Total fees across all facilities per period."""
        arr = np.zeros(self.num_periods)
        for fs in self.facilities.values():
            arr += fs.total_fees
        return arr

    @property
    def total_financing_cost(self) -> np.ndarray:
        """Total financing cost (interest + fees) per period."""
        return self.total_interest + self.total_fees

    @property
    def total_closing_balance(self) -> np.ndarray:
        """Total debt balance across all facilities per period."""
        arr = np.zeros(self.num_periods)
        for fs in self.facilities.values():
            arr += fs.closing_balance
        return arr

    @property
    def peak_debt(self) -> float:
        """Peak total debt across all facilities."""
        total = self.total_closing_balance
        return float(total.max()) if len(total) > 0 else 0.0

    def get(self, name: str) -> Optional[DebtFacilitySchedule]:
        return self.facilities.get(name)


# ── Facility-level builders ─────────────────────────────────────────


def _build_land_loan(
    fac: DebtFacility,
    n: int,
) -> DebtFacilitySchedule:
    """Build Land Loan schedule.

    Lump sum draw at start_month, fixed interest capitalised monthly,
    bullet repayment at end_month.
    """
    opening = np.zeros(n)
    draws = np.zeros(n)
    interest = np.zeros(n)
    app_fees = np.zeros(n)
    line_fees = np.zeros(n)
    standby_fees = np.zeros(n)
    repayments = np.zeros(n)
    closing = np.zeros(n)

    if not fac.active or fac.facility_limit <= 0:
        return DebtFacilitySchedule(
            name=fac.name, num_periods=n,
            opening_balance=opening, drawdowns=draws,
            interest_charged=interest, application_fees=app_fees,
            line_fees=line_fees, standby_fees=standby_fees,
            repayments=repayments, closing_balance=closing,
        )

    monthly_rate = fac.interest_rate / 12.0
    draw_idx = fac.start_month - 1  # 0-based
    end_idx = fac.end_month - 1

    # Application fee at draw
    app_fee_amt = fac.facility_limit * fac.application_fee_pct
    if 0 <= draw_idx < n:
        app_fees[draw_idx] = app_fee_amt

    for t in range(n):
        # Opening balance
        if t == 0:
            opening[t] = 0.0
        else:
            opening[t] = closing[t - 1]

        # Drawdown: lump sum at start_month
        if t == draw_idx:
            draws[t] = fac.facility_limit

        # Interest (capitalised)
        if opening[t] + draws[t] > 0:
            balance_for_interest = opening[t] + draws[t]
            if fac.fees_capitalised:
                balance_for_interest += app_fees[t]
            interest[t] = balance_for_interest * monthly_rate

        # Line fee on drawn balance
        if opening[t] + draws[t] > 0:
            line_fees[t] = (opening[t] + draws[t]) * (fac.line_fee_pct / 12.0)

        # Repayment: bullet at end_month
        if t == end_idx:
            total_owed = (
                opening[t] + draws[t] + interest[t]
                + app_fees[t] + line_fees[t] + standby_fees[t]
            )
            repayments[t] = total_owed

        # Closing balance
        closing[t] = (
            opening[t] + draws[t] + interest[t]
            + app_fees[t] + line_fees[t] + standby_fees[t]
            - repayments[t]
        )

    return DebtFacilitySchedule(
        name=fac.name, num_periods=n,
        opening_balance=opening, drawdowns=draws,
        interest_charged=interest, application_fees=app_fees,
        line_fees=line_fees, standby_fees=standby_fees,
        repayments=repayments, closing_balance=closing,
    )


def _build_senior_construction(
    fac: DebtFacility,
    n: int,
    cumulative_costs: np.ndarray,
    cumulative_revenue: np.ndarray,
    land_loan_repayment: np.ndarray,
    cumulative_equity: float = 0.0,
    land_loan_balance_at_senior_start: float = 0.0,
) -> DebtFacilitySchedule:
    """Build Senior Construction schedule.

    At the start period, Senior draws a bulk amount that refinances:
      cumulative_equity + land_loan_balance_owed
    After that, progressive draws based on LTC target against costs.
    Variable interest rate from schedule. Interest capitalised.
    Repaid as revenue comes in (settlements), with bullet at end_month.

    Parameters
    ----------
    cumulative_costs : np.ndarray
        Cumulative total project costs (exc financing) per period.
    cumulative_revenue : np.ndarray
        Cumulative settlement revenue per period.
    land_loan_repayment : np.ndarray
        Land loan repayment array (refinanced into senior).
    cumulative_equity : float
        Total equity injected up to the Senior start period.
        Senior initial draw refinances this amount.
    land_loan_balance_at_senior_start : float
        Land loan closing balance just before Senior starts.
        Senior initial draw also refinances this amount.
    """
    opening = np.zeros(n)
    draws = np.zeros(n)
    interest = np.zeros(n)
    app_fees = np.zeros(n)
    line_fees = np.zeros(n)
    standby_fees = np.zeros(n)
    repayments = np.zeros(n)
    closing = np.zeros(n)

    if not fac.active or fac.facility_limit <= 0:
        return DebtFacilitySchedule(
            name=fac.name, num_periods=n,
            opening_balance=opening, drawdowns=draws,
            interest_charged=interest, application_fees=app_fees,
            line_fees=line_fees, standby_fees=standby_fees,
            repayments=repayments, closing_balance=closing,
        )

    start_idx = fac.start_month - 1
    end_idx = fac.end_month - 1
    rate_schedule = fac.interest_rate_schedule or {}

    # Application fee at start
    app_fee_amt = fac.facility_limit * fac.application_fee_pct
    if 0 <= start_idx < n:
        app_fees[start_idx] = app_fee_amt

    cum_principal_drawn = 0.0  # Track cumulative principal draws (excl interest/fees)

    for t in range(n):
        # Opening balance
        if t == 0:
            opening[t] = 0.0
        else:
            opening[t] = closing[t - 1]

        # Drawdowns: bulk refinance at start, then progressive
        if t == start_idx:
            # Initial bulk draw: refinance all prior equity + land loan balance
            initial_draw = max(0, cumulative_equity + land_loan_balance_at_senior_start)
            # Also include this period's incremental costs (P43 gap fix)
            if t > 0:
                period_cost_at_start = cumulative_costs[t] - cumulative_costs[t - 1]
            else:
                period_cost_at_start = cumulative_costs[t]
            initial_draw += max(0, period_cost_at_start)
            draws[t] = min(initial_draw, fac.facility_limit)
            cum_principal_drawn += draws[t]
        elif start_idx < t <= end_idx:
            # Cost-based progressive draw: fund each period's incremental cost
            if t > 0:
                period_cost = cumulative_costs[t] - cumulative_costs[t - 1]
            else:
                period_cost = cumulative_costs[t]
            draw_for_costs = max(0, period_cost)
            # Cap at facility limit using cumulative principal draws
            remaining = max(0, fac.facility_limit - cum_principal_drawn)
            draws[t] = min(draw_for_costs, remaining)
            cum_principal_drawn += draws[t]

        # Interest (variable rate from schedule, or base rate)
        period_1based = t + 1
        annual_rate = rate_schedule.get(period_1based, fac.interest_rate)
        monthly_rate = annual_rate / 12.0

        balance_for_interest = opening[t] + draws[t]
        if fac.fees_capitalised:
            balance_for_interest += app_fees[t]
        if balance_for_interest > 0:
            interest[t] = balance_for_interest * monthly_rate

        # Line fee
        drawn_balance = opening[t] + draws[t]
        if drawn_balance > 0:
            line_fees[t] = drawn_balance * (fac.line_fee_pct / 12.0)

        # Standby fee on undrawn commitment (principal-based)
        if start_idx <= t <= end_idx:
            undrawn = max(0, fac.facility_limit - cum_principal_drawn)
            if undrawn > 0:
                standby_fees[t] = undrawn * (fac.standby_fee_pct / 12.0)

        # Repayments from revenue (settlements reduce balance)
        if t >= start_idx and cumulative_revenue[t] > 0:
            # Revenue-based repayment: if revenue comes in, repay debt
            revenue_this_period = (
                cumulative_revenue[t] - cumulative_revenue[t - 1]
                if t > 0 else cumulative_revenue[t]
            )
            if revenue_this_period > 0 and t != start_idx:
                # Repay from settlement revenue, but not more than balance
                pre_repay_balance = (
                    opening[t] + draws[t] + interest[t]
                    + app_fees[t] + line_fees[t] + standby_fees[t]
                )
                repayments[t] = min(revenue_this_period, max(0, pre_repay_balance))

        # Bullet repayment at maturity for remaining balance
        if t == end_idx:
            pre_repay_balance = (
                opening[t] + draws[t] + interest[t]
                + app_fees[t] + line_fees[t] + standby_fees[t]
                - repayments[t]
            )
            if pre_repay_balance > 0:
                repayments[t] += pre_repay_balance

        # Closing balance
        closing[t] = (
            opening[t] + draws[t] + interest[t]
            + app_fees[t] + line_fees[t] + standby_fees[t]
            - repayments[t]
        )

    return DebtFacilitySchedule(
        name=fac.name, num_periods=n,
        opening_balance=opening, drawdowns=draws,
        interest_charged=interest, application_fees=app_fees,
        line_fees=line_fees, standby_fees=standby_fees,
        repayments=repayments, closing_balance=closing,
    )


def _build_generic_facility(
    fac: DebtFacility,
    n: int,
) -> DebtFacilitySchedule:
    """Build a generic / inactive debt facility (Mezzanine, Additional).

    Returns zero arrays if inactive or zero limit.
    """
    opening = np.zeros(n)
    draws = np.zeros(n)
    interest = np.zeros(n)
    app_fees = np.zeros(n)
    line_fees = np.zeros(n)
    standby_fees = np.zeros(n)
    repayments = np.zeros(n)
    closing = np.zeros(n)

    # Inactive facilities just return zeros
    return DebtFacilitySchedule(
        name=fac.name, num_periods=n,
        opening_balance=opening, drawdowns=draws,
        interest_charged=interest, application_fees=app_fees,
        line_fees=line_fees, standby_fees=standby_fees,
        repayments=repayments, closing_balance=closing,
    )


# ── Public API ───────────────────────────────────────────────────────


def build_debt_schedule(
    inputs: FeasoInputs,
    cumulative_costs: np.ndarray,
    cumulative_revenue: np.ndarray,
    cumulative_equity: float = 0.0,
) -> DebtSchedule:
    """Build debt schedules for all facilities.

    Parameters
    ----------
    inputs : FeasoInputs
        Model inputs including debt facility configurations.
    cumulative_costs : np.ndarray
        Cumulative total project costs (exc financing) per period.
    cumulative_revenue : np.ndarray
        Cumulative settlement revenue per period.
    cumulative_equity : float
        Total equity injected up to the Senior start period.
        Senior initial draw refinances this amount.

    Returns
    -------
    DebtSchedule
        Aggregated debt schedule with per-facility breakdowns.
    """
    n = inputs.num_periods
    facilities: Dict[str, DebtFacilitySchedule] = {}

    # Build Land Loan first (needed for Senior refinancing)
    land_loan_fac = inputs.get_facility("Land Loan")
    land_loan_sched = None
    if land_loan_fac is not None:
        land_loan_sched = _build_land_loan(land_loan_fac, n)
        facilities["Land Loan"] = land_loan_sched

    # Land loan repayment array (Senior refinances this)
    land_repayment = (
        land_loan_sched.repayments if land_loan_sched is not None
        else np.zeros(n)
    )

    # Compute land loan balance at Senior start (for refinancing)
    land_loan_balance_at_senior_start = 0.0
    senior_fac = inputs.get_facility("Senior Construction")
    if senior_fac is not None and land_loan_sched is not None:
        senior_start_idx = senior_fac.start_month - 1  # 0-based
        if senior_start_idx > 0 and senior_start_idx <= n:
            land_loan_balance_at_senior_start = float(
                land_loan_sched.closing_balance[senior_start_idx - 1]
            )

    # Build Senior Construction
    if senior_fac is not None:
        senior_sched = _build_senior_construction(
            senior_fac, n,
            cumulative_costs, cumulative_revenue,
            land_repayment,
            cumulative_equity=cumulative_equity,
            land_loan_balance_at_senior_start=land_loan_balance_at_senior_start,
        )
        facilities["Senior Construction"] = senior_sched

    # Build remaining facilities (Mezzanine, Additional, etc.)
    for fac in inputs.debt_facilities:
        if fac.name not in facilities:
            facilities[fac.name] = _build_generic_facility(fac, n)

    return DebtSchedule(num_periods=n, facilities=facilities)
