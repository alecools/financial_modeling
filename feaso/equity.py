"""Equity modelling — injection, repatriation, profit distribution.

Tracks per-partner:
- Progressive equity injections (residual funding after debt)
- Interest accrual (preferred equity)
- Equity repatriation from settlement proceeds
- Profit distribution after all debt/equity repaid
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from .inputs import EquityPartner, FeasoInputs


@dataclass
class EquityPartnerSchedule:
    """Monthly arrays for a single equity partner."""

    name: str
    num_periods: int

    injections: np.ndarray = field(default_factory=lambda: np.zeros(0))
    interest_accrued: np.ndarray = field(default_factory=lambda: np.zeros(0))
    repatriations: np.ndarray = field(default_factory=lambda: np.zeros(0))
    profit_distributions: np.ndarray = field(default_factory=lambda: np.zeros(0))
    balance: np.ndarray = field(default_factory=lambda: np.zeros(0))

    @property
    def total_injected(self) -> float:
        return float(self.injections.sum())

    @property
    def total_repatriated(self) -> float:
        return float(self.repatriations.sum())

    @property
    def total_profit_distributed(self) -> float:
        return float(self.profit_distributions.sum())

    @property
    def total_interest(self) -> float:
        return float(self.interest_accrued.sum())

    @property
    def net_cashflow(self) -> np.ndarray:
        """Net equity cashflow per period (injection is negative, returns positive)."""
        return -self.injections + self.repatriations + self.profit_distributions


@dataclass
class EquitySchedule:
    """Aggregated equity schedule across all partners."""

    num_periods: int
    partners: Dict[str, EquityPartnerSchedule] = field(default_factory=dict)

    @property
    def total_injections(self) -> np.ndarray:
        arr = np.zeros(self.num_periods)
        for ps in self.partners.values():
            arr += ps.injections
        return arr

    @property
    def total_repatriations(self) -> np.ndarray:
        arr = np.zeros(self.num_periods)
        for ps in self.partners.values():
            arr += ps.repatriations
        return arr

    @property
    def total_profit_distributions(self) -> np.ndarray:
        arr = np.zeros(self.num_periods)
        for ps in self.partners.values():
            arr += ps.profit_distributions
        return arr

    @property
    def total_balance(self) -> np.ndarray:
        arr = np.zeros(self.num_periods)
        for ps in self.partners.values():
            arr += ps.balance
        return arr

    @property
    def peak_equity(self) -> float:
        """Peak total equity outstanding."""
        bal = self.total_balance
        return float(bal.max()) if len(bal) > 0 else 0.0

    @property
    def total_equity_injected(self) -> float:
        return float(self.total_injections.sum())

    def get(self, name: str) -> Optional[EquityPartnerSchedule]:
        return self.partners.get(name)


def build_equity_schedule(
    inputs: FeasoInputs,
    net_funding_requirement: np.ndarray,
    net_revenue_after_debt: np.ndarray,
    project_profit: float,
    equity_cutoff_period: Optional[int] = None,
) -> EquitySchedule:
    """Build equity schedules for all partners.

    Parameters
    ----------
    inputs : FeasoInputs
        Model inputs including equity partner configurations.
    net_funding_requirement : np.ndarray
        Per-period funding requirement after debt (positive = needs equity).
        This is the residual that equity must cover.
    net_revenue_after_debt : np.ndarray
        Per-period revenue available after debt repayment (for repatriation).
    project_profit : float
        Total project profit for distribution.
    equity_cutoff_period : int, optional
        0-based period index up to which equity can be injected (exclusive).
        If None, equity can be injected in any period.
        Typically set to the Senior Construction start index so equity
        only covers the pre-Senior period.

    Returns
    -------
    EquitySchedule
        Aggregated equity schedule with per-partner breakdowns.
    """
    n = inputs.num_periods
    partners: Dict[str, EquityPartnerSchedule] = {}

    dist_start = inputs.equity_dist_start - 1  # 0-based
    dist_end = inputs.equity_dist_end - 1

    # Default cutoff: all periods
    cutoff = equity_cutoff_period if equity_cutoff_period is not None else n

    for partner in inputs.equity_partners:
        injections = np.zeros(n)
        interest_accrued = np.zeros(n)
        repatriations = np.zeros(n)
        profit_dist = np.zeros(n)
        balance = np.zeros(n)

        contrib_pct = partner.equity_contribution_pct

        if contrib_pct > 0 or partner.fixed_amount != 0:
            # ── Injections ─────────────────────────────────────────
            # Only inject up to the cutoff period (pre-Senior)
            if partner.fixed_amount < 0:
                # Fixed total injection — distribute proportionally to costs
                total_injection = abs(partner.fixed_amount)
                req_pre = np.maximum(net_funding_requirement[:cutoff], 0)
                total_req = float(req_pre.sum())
                if total_req > 0:
                    for t in range(cutoff):
                        if req_pre[t] > 0:
                            injections[t] = total_injection * (req_pre[t] / total_req)
                elif cutoff > 0:
                    # Fallback: evenly spread if no cost requirement
                    per_period = total_injection / cutoff
                    for t in range(cutoff):
                        injections[t] = per_period
            else:
                # Progressive injection: partner's share of funding requirement
                for t in range(cutoff):
                    if net_funding_requirement[t] > 0:
                        injections[t] = net_funding_requirement[t] * contrib_pct

            # ── Interest accrual (for preferred equity) ────────────
            monthly_rate = partner.interest_rate / 12.0
            for t in range(n):
                if t == 0:
                    balance[t] = injections[t]
                else:
                    balance[t] = balance[t - 1] + injections[t]

                if partner.compound_interest and monthly_rate > 0 and balance[t] > 0:
                    int_amt = balance[t] * monthly_rate
                    interest_accrued[t] = int_amt
                    balance[t] += int_amt

            # ── Repatriation from settlement proceeds ──────────────
            # Repay equity during the distribution window
            equity_to_repay = balance.copy()
            for t in range(n):
                if dist_start <= t <= dist_end and net_revenue_after_debt[t] > 0:
                    # Repay this partner's share
                    repay_available = net_revenue_after_debt[t] * contrib_pct
                    repay_amount = min(repay_available, max(0, equity_to_repay[t]))
                    repatriations[t] = repay_amount
                    # Update remaining balance
                    for future_t in range(t, n):
                        equity_to_repay[future_t] -= repay_amount

            # Recalculate balance including repatriations
            for t in range(n):
                if t == 0:
                    balance[t] = injections[t] - repatriations[t]
                else:
                    balance[t] = balance[t - 1] + injections[t] - repatriations[t]
                if partner.compound_interest and monthly_rate > 0 and balance[t] > 0:
                    balance[t] += interest_accrued[t]

            # ── Profit distribution ────────────────────────────────
            partner_profit = project_profit * partner.profit_share_pct
            if partner_profit > 0 and dist_end < n:
                # Distribute profit in the last period of distribution window
                profit_dist[min(dist_end, n - 1)] = partner_profit

        partners[partner.name] = EquityPartnerSchedule(
            name=partner.name,
            num_periods=n,
            injections=injections,
            interest_accrued=interest_accrued,
            repatriations=repatriations,
            profit_distributions=profit_dist,
            balance=balance,
        )

    return EquitySchedule(num_periods=n, partners=partners)
