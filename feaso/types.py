"""Shared helper dataclasses used across Feaso input pages and engine modules.

These types are defined here (rather than in inputs.py) to avoid circular
imports when multiple input-page modules need to reference them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


# ── Cost & Revenue line items ────────────────────────────────────────

@dataclass
class CostLineItem:
    """A single cost line item (exc GST)."""
    code: int
    description: str
    cost_type: str          # "Development", "Construction", "Marketing", etc.
    total_cost: float       # Total cost (exc GST)
    scurve_type: str        # "Evenly Split", "Manual S-curve 1", "36 Month Build", etc.
    month_start: int        # Period index (1-based) when cost begins
    month_span: int         # Number of months to distribute over
    gst_applicable: bool = True   # Whether GST applies to this item


@dataclass
class RevenueLineItem:
    """A single revenue line item (inc GST)."""
    code: int
    description: str
    revenue_type: str       # "Residential", "Management Rights", etc.
    num_units: int
    total_area_sqm: float
    sale_price_inc_gst: float
    presale_exchange_start: int
    presale_exchange_span: int
    settlement_start: int
    settlement_span: int
    gst_on_sales: bool = True


# ── Land ─────────────────────────────────────────────────────────────

@dataclass
class LandPaymentStage:
    """A staged land payment."""
    description: str
    amount: float           # Payment amount
    month: int              # Period index when payment occurs


# ── Equity & Debt ────────────────────────────────────────────────────

@dataclass
class EquityPartner:
    """Configuration for an equity partner."""
    name: str
    fixed_amount: float     # Negative = injection
    interest_rate: float    # Annual rate
    compound_interest: bool
    equity_contribution_pct: float
    profit_share_pct: float
    repay_before_debt_pct: float = 0.0


@dataclass
class DebtFacility:
    """Configuration for a debt facility."""
    name: str
    facility_limit: float
    is_fixed_amount: bool   # True = lump sum draw, False = progressive
    ltc_target: float       # Loan-to-Cost target (for progressive draws)
    lvr_target: float       # Loan-to-Value target
    interest_rate: float    # Annual nominal rate (or base margin)
    compound_interest: bool
    start_month: int        # Period when facility starts
    end_month: int          # Maturity period
    application_fee_pct: float
    line_fee_pct: float
    standby_fee_pct: float
    fees_capitalised: bool
    profit_split_pct: float = 0.0
    # For variable-rate facilities: period → annual rate
    interest_rate_schedule: Optional[Dict[int, float]] = None
    # Refinanced by equity or another loan at end
    refinanced_by: str = "Equity"
    active: bool = True
