"""Revenue calculation engine — presale exchanges, settlements, selling costs.

Produces monthly arrays for:
- Presale exchanges (contracts exchanged, deposits held)
- Settlements (cash received)
- Selling costs (front-end at exchange, back-end at settlement)
- GST on revenue
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np

from .inputs import FeasoInputs
from .scurve import distribute


@dataclass
class RevenueSchedule:
    """Monthly revenue and selling cost arrays."""

    num_periods: int

    # Revenue (inc GST) arrays per line item code
    presale_exchanges: Dict[int, np.ndarray] = field(default_factory=dict)
    settlements: Dict[int, np.ndarray] = field(default_factory=dict)

    # Aggregated arrays
    total_presale_exchange: np.ndarray = field(default_factory=lambda: np.zeros(0))
    total_settlement_revenue: np.ndarray = field(default_factory=lambda: np.zeros(0))

    # Deposits held (10% of exchange price, held until settlement)
    deposits_received: np.ndarray = field(default_factory=lambda: np.zeros(0))
    deposits_released: np.ndarray = field(default_factory=lambda: np.zeros(0))

    # Selling costs
    selling_costs_frontend: np.ndarray = field(default_factory=lambda: np.zeros(0))
    selling_costs_backend: np.ndarray = field(default_factory=lambda: np.zeros(0))

    # GST on revenue
    gst_on_revenue: np.ndarray = field(default_factory=lambda: np.zeros(0))

    @property
    def total_selling_costs(self) -> np.ndarray:
        """Total selling costs per period."""
        return self.selling_costs_frontend + self.selling_costs_backend

    @property
    def net_revenue(self) -> np.ndarray:
        """Net revenue = settlement revenue - selling costs (all inc GST)."""
        return self.total_settlement_revenue - self.total_selling_costs

    @property
    def net_revenue_exc_gst(self) -> np.ndarray:
        """Net revenue exc GST = net revenue - GST on revenue."""
        return self.net_revenue - self.gst_on_revenue


def build_revenue_schedule(inputs: FeasoInputs) -> RevenueSchedule:
    """Build the complete monthly revenue schedule from model inputs.

    Revenue recognition:
    - Pre-sale exchange: contracts are exchanged over [presale_start, presale_start+presale_span)
    - Settlement: cash received at [settlement_start, settlement_start+settlement_span)
    - Deposits: 10% collected at exchange, released at settlement
    - Selling costs: 50% front-end at exchange, 50% back-end at settlement

    All amounts are inc GST unless noted otherwise.
    """
    n = inputs.num_periods
    gst_rate = inputs.gst_rate
    commission_rate = inputs.selling_commission_rate
    presale_commission_pct = inputs.presale_commission_pct
    deposit_pct = inputs.deposit_pct

    # Accumulators
    total_presale = np.zeros(n)
    total_settlement = np.zeros(n)
    total_deposits_received = np.zeros(n)
    total_deposits_released = np.zeros(n)
    total_selling_frontend = np.zeros(n)
    total_selling_backend = np.zeros(n)
    total_gst = np.zeros(n)

    presale_dict: Dict[int, np.ndarray] = {}
    settlement_dict: Dict[int, np.ndarray] = {}

    for item in inputs.revenue_items:
        sale_inc_gst = item.sale_price_inc_gst

        # ── Presale exchanges ────────────────────────────────────────
        presale_arr = distribute(
            total=sale_inc_gst,
            scurve_type="Evenly Split",
            start=item.presale_exchange_start,
            span=item.presale_exchange_span,
            num_periods=n,
        )
        presale_dict[item.code] = presale_arr
        total_presale += presale_arr

        # ── Settlement revenue (actual cash) ─────────────────────────
        settlement_arr = distribute(
            total=sale_inc_gst,
            scurve_type="Evenly Split",
            start=item.settlement_start,
            span=item.settlement_span,
            num_periods=n,
        )
        settlement_dict[item.code] = settlement_arr
        total_settlement += settlement_arr

        # ── Deposits ─────────────────────────────────────────────────
        # Deposits received at exchange (10% of exchange amount)
        deposits_in = presale_arr * deposit_pct
        total_deposits_received += deposits_in

        # Deposits released at settlement (total deposits for this item)
        total_deposits_for_item = sale_inc_gst * deposit_pct
        deposits_out = distribute(
            total=total_deposits_for_item,
            scurve_type="Evenly Split",
            start=item.settlement_start,
            span=item.settlement_span,
            num_periods=n,
        )
        total_deposits_released += deposits_out

        # ── Selling costs ────────────────────────────────────────────
        total_commission = sale_inc_gst * commission_rate

        # Front-end: presale_commission_pct of total commission, spread over exchange period
        frontend_total = total_commission * presale_commission_pct
        frontend_arr = distribute(
            total=frontend_total,
            scurve_type="Evenly Split",
            start=item.presale_exchange_start,
            span=item.presale_exchange_span,
            num_periods=n,
        )
        total_selling_frontend += frontend_arr

        # Back-end: remainder at settlement
        backend_total = total_commission * (1.0 - presale_commission_pct)
        backend_arr = distribute(
            total=backend_total,
            scurve_type="Evenly Split",
            start=item.settlement_start,
            span=item.settlement_span,
            num_periods=n,
        )
        total_selling_backend += backend_arr

        # ── GST on revenue ───────────────────────────────────────────
        if item.gst_on_sales:
            # GST = 1/11 of inc-GST revenue, recognised at settlement
            gst_arr = settlement_arr * (gst_rate / (1 + gst_rate))
            total_gst += gst_arr

    return RevenueSchedule(
        num_periods=n,
        presale_exchanges=presale_dict,
        settlements=settlement_dict,
        total_presale_exchange=total_presale,
        total_settlement_revenue=total_settlement,
        deposits_received=total_deposits_received,
        deposits_released=total_deposits_released,
        selling_costs_frontend=total_selling_frontend,
        selling_costs_backend=total_selling_backend,
        gst_on_revenue=total_gst,
    )
