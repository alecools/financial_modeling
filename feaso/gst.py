"""GST calculation engine — net GST payable and BAS reclamation timing.

Computes:
- GST collected on revenue (at settlement)
- GST paid on costs (input tax credits)
- Net GST position per period
- BAS-aligned GST cashflow (quarterly offset)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .costs import CostSchedule
from .revenue import RevenueSchedule


@dataclass
class GSTSchedule:
    """Monthly GST arrays."""

    num_periods: int

    # GST collected from customers at settlement (liability)
    gst_collected: np.ndarray = field(default_factory=lambda: np.zeros(0))

    # GST paid on costs (input tax credits — asset)
    gst_paid_on_costs: np.ndarray = field(default_factory=lambda: np.zeros(0))

    # Net GST payable (positive = owe ATO, negative = refund)
    net_gst: np.ndarray = field(default_factory=lambda: np.zeros(0))

    # GST cashflow effect (when cash actually moves — BAS timing)
    gst_cashflow: np.ndarray = field(default_factory=lambda: np.zeros(0))

    @property
    def total_gst_collected(self) -> float:
        """Total GST collected over the project."""
        return float(self.gst_collected.sum())

    @property
    def total_gst_paid(self) -> float:
        """Total GST paid on costs over the project."""
        return float(self.gst_paid_on_costs.sum())

    @property
    def total_net_gst(self) -> float:
        """Net GST position over the project."""
        return float(self.net_gst.sum())


def build_gst_schedule(
    revenue: RevenueSchedule,
    costs: CostSchedule,
    *,
    bas_offset: int = 1,
) -> GSTSchedule:
    """Build the GST schedule from revenue and cost schedules.

    Parameters
    ----------
    revenue : RevenueSchedule
        Pre-computed revenue schedule (contains gst_on_revenue).
    costs : CostSchedule
        Pre-computed cost schedule (contains gst_on_costs).
    bas_offset : int
        Number of periods to delay GST cashflow settlement
        (BAS lodgement offset, typically 1 period / quarterly).

    Returns
    -------
    GSTSchedule
        Monthly GST arrays including BAS-aligned cashflow.
    """
    n = revenue.num_periods

    # GST collected on revenue (from RevenueSchedule)
    gst_collected = revenue.gst_on_revenue.copy()

    # GST paid on costs (from CostSchedule — input tax credits)
    gst_paid = costs.gst_on_costs.copy()

    # Net GST = collected - paid (positive = payable to ATO)
    net_gst = gst_collected - gst_paid

    # BAS timing: GST cash effect is offset by bas_offset periods
    # (you pay/receive net GST one period after it's incurred)
    gst_cashflow = np.zeros(n)
    for i in range(n):
        target = i + bas_offset
        if 0 <= target < n:
            gst_cashflow[target] += net_gst[i]
        else:
            # If offset pushes past end, settle in last period
            gst_cashflow[min(n - 1, max(0, target))] += net_gst[i]

    return GSTSchedule(
        num_periods=n,
        gst_collected=gst_collected,
        gst_paid_on_costs=gst_paid,
        net_gst=net_gst,
        gst_cashflow=gst_cashflow,
    )
