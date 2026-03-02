"""FeasoInputs — All model assumptions with defaults from Feaso Model Draft v22.

This module is the single entry point for consumer modules. It composes
inputs from five separate "page" modules that mirror the Excel sheet tabs:

  Admin              → :class:`~feaso.input_admin.AdminInputs`
  !!! - Input        → :class:`~feaso.input_main.MainInputs`
  Inputs_TD_Actual   → :class:`~feaso.input_td_actual.TDActualInputs`
  Rev_Costs actual   → :class:`~feaso.input_rev_costs.RevCostsInputs`
  Scenario Manager   → :class:`~feaso.input_scenario.ScenarioManagerInputs`

Backward-compatible: consumer modules can still do
``from .inputs import FeasoInputs, DebtFacility, EquityPartner`` etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ── Shared helper types (re-exported for backward compat) ──────────────
from .types import (
    CostLineItem,
    DebtFacility,
    EquityPartner,
    LandPaymentStage,
    RevenueLineItem,
)

# ── Page-level input dataclasses ───────────────────────────────────────
from .input_admin import AdminInputs
from .input_main import MainInputs
from .input_rev_costs import RevCostsInputs
from .input_scenario import ScenarioManagerInputs
from .input_td_actual import TDActualInputs

# ── Default factory functions (delegated to page modules) ──────────────
from .input_main import (
    _default_debt_facilities,
    _default_equity_partners,
    _default_land_stages,
)
from .input_rev_costs import _default_cost_items, _default_revenue_items
from .input_td_actual import _default_senior_rate_schedule

# Re-export everything consumers might need
__all__ = [
    "FeasoInputs",
    "CostLineItem",
    "RevenueLineItem",
    "LandPaymentStage",
    "EquityPartner",
    "DebtFacility",
    "AdminInputs",
    "MainInputs",
    "TDActualInputs",
    "RevCostsInputs",
    "ScenarioManagerInputs",
]


# ── Main inputs dataclass ─────────────────────────────────────────────


@dataclass
class FeasoInputs:
    """All model assumptions for the Feaso Property Development Feasibility Model.

    Defaults are baked in from the *Feaso Model Draft v22* Excel workbook.
    Individual page defaults come from the five input-page modules.

    Use :meth:`from_pages` to construct from explicit page dataclass instances.
    """

    # ── Project General ──────────────────────────────────────────────
    project_name: str = "Fake House"
    address: str = "123 Fake Street, Fakeville VIC 3000"
    developer: str = "Kokoda Property Group"
    revision: str = "REV #1 June 2025"
    date_of_first_period: float = 44652.0     # Excel serial date
    project_lots: int = 178
    project_gfa_sqm: float = 32_133.0
    site_area_sqm: float = 2_000.0
    project_start_month: int = 41             # Construction/main works start
    project_span_months: int = 35
    project_end_month: int = 75
    equity_dist_start: int = 70               # Equity repatriation window
    equity_dist_end: int = 75
    num_periods: int = 80                     # Max cashflow periods

    # ── Land ─────────────────────────────────────────────────────────
    land_purchase_price: float = 11_209_195.0
    prsv_uplift: float = 2_290_805.0
    prsv_month: int = 23                      # When PRSV is recognised
    gst_rate: float = 0.10
    gst_applicable_land_value: float = 8_990_177.27
    stamp_duty_state: str = "QLD"
    stamp_duty_amount: float = 625_053.655
    land_payment_stages: List[LandPaymentStage] = field(
        default_factory=_default_land_stages
    )

    # ── Acquisition costs ────────────────────────────────────────────
    acquisition_costs_total: float = 673_000.0
    acquisition_month: int = 23               # Paid at land settlement

    # ── Cost line items ──────────────────────────────────────────────
    cost_items: List[CostLineItem] = field(default_factory=_default_cost_items)

    # ── Revenue ──────────────────────────────────────────────────────
    revenue_items: List[RevenueLineItem] = field(
        default_factory=_default_revenue_items
    )

    # ── Selling costs ────────────────────────────────────────────────
    selling_commission_rate: float = 0.027247  # Applied to inc-GST GRV → NRV $255,275,054
    presale_commission_pct: float = 0.50       # 50% front-end at exchange
    deposit_pct: float = 0.10                  # 10% deposit at exchange
    # Additional selling cost items (legal, settlement agents, etc.)
    selling_other_costs: float = 0.0           # Extra selling costs exc GST

    # ── Equity partners ──────────────────────────────────────────────
    equity_partners: List[EquityPartner] = field(
        default_factory=_default_equity_partners
    )

    # ── Debt facilities ──────────────────────────────────────────────
    debt_facilities: List[DebtFacility] = field(
        default_factory=_default_debt_facilities
    )

    def __post_init__(self) -> None:
        """Populate derived defaults that reference other fields."""
        # Attach variable rate schedule to Senior Construction facility
        for fac in self.debt_facilities:
            if fac.name == "Senior Construction" and fac.interest_rate_schedule is None:
                fac.interest_rate_schedule = _default_senior_rate_schedule()

    # ── Factory: construct from individual page dataclasses ──────────

    @classmethod
    def from_pages(
        cls,
        admin: Optional[AdminInputs] = None,
        main: Optional[MainInputs] = None,
        td_actual: Optional[TDActualInputs] = None,
        rev_costs: Optional[RevCostsInputs] = None,
        scenario: Optional[ScenarioManagerInputs] = None,
    ) -> "FeasoInputs":
        """Build a :class:`FeasoInputs` from five page-level dataclasses.

        Any page left as *None* uses its own defaults. The *scenario*
        page is accepted but not applied here — scenario adjustments
        are handled externally by the scenario engine.
        """
        adm = admin or AdminInputs()
        mn = main or MainInputs()
        td = td_actual or TDActualInputs()
        rc = rev_costs or RevCostsInputs()

        # Attach variable rate schedule to Senior Construction in main's debt
        for fac in mn.debt_facilities:
            if fac.name == "Senior Construction" and fac.interest_rate_schedule is None:
                fac.interest_rate_schedule = dict(td.senior_rate_schedule)

        return cls(
            # ── From AdminInputs ──
            num_periods=adm.num_periods,
            date_of_first_period=adm.date_of_first_period,
            gst_rate=adm.gst_rate,
            project_start_month=adm.project_start_month,
            project_span_months=adm.project_span_months,
            project_end_month=adm.project_end_month,
            equity_dist_start=adm.equity_dist_start,
            equity_dist_end=adm.equity_dist_end,
            stamp_duty_state=adm.stamp_duty_state,
            # ── From MainInputs ──
            project_name=mn.project_name,
            address=mn.address,
            developer=mn.developer,
            revision=mn.revision,
            project_lots=mn.project_lots,
            project_gfa_sqm=mn.project_gfa_sqm,
            site_area_sqm=mn.site_area_sqm,
            land_purchase_price=mn.land_purchase_price,
            prsv_uplift=mn.prsv_uplift,
            prsv_month=mn.prsv_month,
            gst_applicable_land_value=mn.gst_applicable_land_value,
            stamp_duty_amount=mn.stamp_duty_amount,
            land_payment_stages=mn.land_payment_stages,
            acquisition_costs_total=mn.acquisition_costs_total,
            acquisition_month=mn.acquisition_month,
            selling_commission_rate=mn.selling_commission_rate,
            presale_commission_pct=mn.presale_commission_pct,
            deposit_pct=mn.deposit_pct,
            selling_other_costs=mn.selling_other_costs,
            equity_partners=mn.equity_partners,
            debt_facilities=mn.debt_facilities,
            # ── From RevCostsInputs ──
            cost_items=rc.cost_items,
            revenue_items=rc.revenue_items,
        )

    # ── Convenience accessors ────────────────────────────────────────

    @property
    def total_grv_inc_gst(self) -> float:
        """Total Gross Realisable Value (inc GST)."""
        return sum(r.sale_price_inc_gst for r in self.revenue_items)

    @property
    def total_grv_exc_gst(self) -> float:
        """Total Gross Realisable Value (exc GST)."""
        total = 0.0
        for r in self.revenue_items:
            if r.gst_on_sales:
                total += r.sale_price_inc_gst / (1 + self.gst_rate)
            else:
                total += r.sale_price_inc_gst
        return total

    @property
    def total_selling_costs(self) -> float:
        """Total selling costs (inc GST GRV × commission rate + other)."""
        return self.total_grv_inc_gst * self.selling_commission_rate + self.selling_other_costs

    def get_facility(self, name: str) -> Optional[DebtFacility]:
        """Look up a debt facility by name."""
        for f in self.debt_facilities:
            if f.name == name:
                return f
        return None

    def get_equity_partner(self, name: str) -> Optional[EquityPartner]:
        """Look up an equity partner by name."""
        for p in self.equity_partners:
            if p.name == name:
                return p
        return None
