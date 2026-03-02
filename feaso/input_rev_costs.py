"""Revenue & Costs input page — cost and revenue line items.

Maps to the Excel "Rev_Costs actual" sheet. Contains all development /
construction / marketing cost line items and all revenue line items
(apartments, management rights, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .types import CostLineItem, RevenueLineItem


# ── Default factory functions ────────────────────────────────────────


def _default_cost_items() -> List[CostLineItem]:
    """Cost line items matching Excel category totals."""
    return [
        # ── Development costs (~$5.32M exc GST) ──
        CostLineItem(2001, "Accounting Fees",           "Development", 150_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2002, "Bank & Financial Fees",     "Development", 100_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2003, "Council Rates / Charges",   "Development", 350_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2004, "Design Consultants",        "Development", 1_200_000, "Manual S-curve 1", 10, 32, True),
        CostLineItem(2005, "Insurance",                 "Development", 250_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2006, "Legal Fees",                "Development", 500_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2007, "Levies / Contributions",    "Development", 1_350_000, "Manual S-curve 1", 10, 32, True),
        CostLineItem(2008, "Project Contingency",       "Development", 800_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2009, "Statutory Authority Fees",  "Development", 300_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2010, "Survey & Investigation",    "Development", 200_000,   "Manual S-curve 1", 10, 32, True),
        CostLineItem(2011, "Town Planning",             "Development", 120_000,   "Manual S-curve 1", 10, 32, True),
        # ── Construction costs (~$64,878 exc GST in cashflow) ──
        CostLineItem(3001, "Construction (Living)",     "Construction", 64_878,   "Evenly Split",     41, 35, True),
        # ── Marketing & Advertising (~$1.87M) ──
        CostLineItem(5001, "Marketing & Advertising",   "Marketing", 1_500_000,   "Evenly Split",     20, 50, True),
        CostLineItem(5002, "Display Suite",             "Marketing",   370_000,   "Evenly Split",     20, 50, True),
        # ── Other Standard Costs (~$4.39M) ──
        CostLineItem(6001, "Body Corp / OC Setup",     "Other Standard", 500_000, "Evenly Split",    60, 15, True),
        CostLineItem(6002, "Council Rates (Holding)",   "Other Standard", 890_000, "Evenly Split",    1,  75, True),
        CostLineItem(6003, "Land Tax",                  "Other Standard", 2_500_000,"Evenly Split",   1,  75, False),
        CostLineItem(6004, "Strata / Subdivision",      "Other Standard", 500_000, "Evenly Split",    55, 20, True),
        # ── Dev & Project Management (~$5.66M) ──
        CostLineItem(7001, "Development Management Fee","Dev Management", 3_400_000,"Evenly Split",   1,  75, True),
        CostLineItem(7002, "Project Management Fee",    "Dev Management", 2_260_000,"Evenly Split",   1,  75, True),
    ]


def _default_revenue_items() -> List[RevenueLineItem]:
    """Revenue line items from !!! - Input sheet."""
    return [
        RevenueLineItem(
            code=9001,
            description="Apartment Revenue - Standard SP1",
            revenue_type="Residential",
            num_units=166,
            total_area_sqm=12_204.0,
            sale_price_inc_gst=203_098_324.0,
            presale_exchange_start=20,
            presale_exchange_span=50,
            settlement_start=70,
            settlement_span=1,
            gst_on_sales=True,
        ),
        RevenueLineItem(
            code=9002,
            description="Apartment Revenue - Premium SP2",
            revenue_type="Residential",
            num_units=11,
            total_area_sqm=1_980.0,
            sale_price_inc_gst=56_434_569.0,
            presale_exchange_start=20,
            presale_exchange_span=50,
            settlement_start=70,
            settlement_span=1,
            gst_on_sales=True,
        ),
        RevenueLineItem(
            code=9003,
            description="Management Rights",
            revenue_type="Management Rights",
            num_units=1,
            total_area_sqm=0.0,
            sale_price_inc_gst=2_892_500.0,
            presale_exchange_start=70,
            presale_exchange_span=1,
            settlement_start=75,
            settlement_span=1,
            gst_on_sales=True,
        ),
    ]


# ── Revenue & Costs input page dataclass ─────────────────────────────


@dataclass
class RevCostsInputs:
    """Cost and revenue line items from the Rev_Costs actual sheet."""

    cost_items: List[CostLineItem] = field(default_factory=_default_cost_items)
    revenue_items: List[RevenueLineItem] = field(default_factory=_default_revenue_items)
