"""Cost calculation engine — distributes cost line items over periods.

Produces monthly arrays for each cost category:
- Land (staged payments)
- Acquisition costs
- Development costs (S-curved)
- Construction costs (S-curved)
- Marketing & Advertising
- Other Standard costs
- Dev & Project Management fees
- Stamp Duty
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np

from .inputs import FeasoInputs
from .scurve import distribute, distribute_lump_sum
from .taxes import calc_stamp_duty


@dataclass
class CostSchedule:
    """Monthly cost arrays (exc GST) grouped by category, plus GST on costs."""

    num_periods: int
    land: np.ndarray              # Staged land payments
    prsv_uplift: np.ndarray       # PRSV uplift (recognised at prsv_month)
    acquisition: np.ndarray       # Acquisition costs (paid at land settlement)
    stamp_duty: np.ndarray        # Stamp duty (paid at land settlement)
    development: np.ndarray       # Development costs (S-curved)
    construction: np.ndarray      # Construction costs (S-curved)
    marketing: np.ndarray         # Marketing & advertising
    other_standard: np.ndarray    # Other standard costs
    dev_management: np.ndarray    # Dev & project management fees
    # Per-item breakdown for detailed reporting
    item_schedules: Dict[int, np.ndarray] = field(default_factory=dict)

    @property
    def total_exc_gst(self) -> np.ndarray:
        """Total costs exc GST per period (before selling & financing)."""
        return (
            self.land
            + self.prsv_uplift
            + self.acquisition
            + self.stamp_duty
            + self.development
            + self.construction
            + self.marketing
            + self.other_standard
            + self.dev_management
        )

    @property
    def total_exc_gst_exc_land(self) -> np.ndarray:
        """Total costs exc GST and exc land (for LTC calculations)."""
        return (
            self.prsv_uplift
            + self.acquisition
            + self.stamp_duty
            + self.development
            + self.construction
            + self.marketing
            + self.other_standard
            + self.dev_management
        )

    @property
    def gst_on_costs(self) -> np.ndarray:
        """GST paid on costs (input tax credits).

        GST applies to all categories except land (margin scheme) and
        items explicitly flagged as GST-free.  For simplicity we compute
        GST on the GST-applicable portion at 10%.
        """
        return self._gst_applicable * 0.10

    # Private helper — set during build
    _gst_applicable: np.ndarray = field(default_factory=lambda: np.zeros(0))

    def category_total(self, category: str) -> float:
        """Sum of a named category across all periods."""
        arr = getattr(self, category, None)
        if arr is not None:
            return float(arr.sum())
        return 0.0


def build_cost_schedule(inputs: FeasoInputs) -> CostSchedule:
    """Build the complete monthly cost schedule from model inputs.

    Returns a :class:`CostSchedule` with per-category monthly arrays.
    """
    n = inputs.num_periods

    # ── Land (staged payments) ───────────────────────────────────────
    land = np.zeros(n)
    for stage in inputs.land_payment_stages:
        land += distribute_lump_sum(stage.amount, stage.month, n)

    # ── PRSV uplift (recognised at prsv_month) ──────────────────────
    prsv_uplift = distribute_lump_sum(inputs.prsv_uplift, inputs.prsv_month, n)

    # ── Acquisition costs (lump sum at land settlement month) ───────
    acquisition = distribute_lump_sum(
        inputs.acquisition_costs_total, inputs.acquisition_month, n
    )

    # ── Stamp duty ──────────────────────────────────────────────────
    stamp_duty_amt = inputs.stamp_duty_amount
    # Place at land settlement month (same as acquisition)
    stamp_duty = distribute_lump_sum(stamp_duty_amt, inputs.acquisition_month, n)

    # ── Cost line items by category ─────────────────────────────────
    development = np.zeros(n)
    construction = np.zeros(n)
    marketing = np.zeros(n)
    other_standard = np.zeros(n)
    dev_management = np.zeros(n)
    gst_applicable = np.zeros(n)   # Accumulate GST-applicable costs
    item_schedules: Dict[int, np.ndarray] = {}

    for item in inputs.cost_items:
        arr = distribute(
            total=item.total_cost,
            scurve_type=item.scurve_type,
            start=item.month_start,
            span=item.month_span,
            num_periods=n,
        )
        item_schedules[item.code] = arr

        # Add to category
        cat = item.cost_type.lower()
        if cat == "development":
            development += arr
        elif cat == "construction":
            construction += arr
        elif cat == "marketing":
            marketing += arr
        elif cat in ("other standard", "other"):
            other_standard += arr
        elif cat in ("dev management", "dev & project management"):
            dev_management += arr
        else:
            # Catch-all: treat as development
            development += arr

        # Track GST-applicable amounts
        if item.gst_applicable:
            gst_applicable += arr

    # Acquisition costs are typically GST-applicable
    gst_applicable += acquisition

    cs = CostSchedule(
        num_periods=n,
        land=land,
        prsv_uplift=prsv_uplift,
        acquisition=acquisition,
        stamp_duty=stamp_duty,
        development=development,
        construction=construction,
        marketing=marketing,
        other_standard=other_standard,
        dev_management=dev_management,
        item_schedules=item_schedules,
    )
    # Attach GST-applicable array (private)
    object.__setattr__(cs, "_gst_applicable", gst_applicable)
    return cs
