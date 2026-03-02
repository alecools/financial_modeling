"""FeasoInputs — All model assumptions with defaults from Feaso Model Draft v22."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Helper dataclasses ────────────────────────────────────────────────

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


@dataclass
class LandPaymentStage:
    """A staged land payment."""
    description: str
    amount: float           # Payment amount
    month: int              # Period index when payment occurs


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


# ── Default data from Excel ───────────────────────────────────────────

def _default_land_stages() -> List[LandPaymentStage]:
    """Staged land payments from !!! - Input sheet."""
    return [
        LandPaymentStage("Deposit (10%)", 1_120_920.0, 1),
        LandPaymentStage("Settlement Balance", 10_088_275.0, 23),
    ]


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


def _default_equity_partners() -> List[EquityPartner]:
    """Equity partners from !!! - Input sheet."""
    return [
        EquityPartner(
            name="Kokoda Property Group",
            fixed_amount=-115_722_322.88,  # Progressive injection
            interest_rate=0.0,
            compound_interest=False,
            equity_contribution_pct=1.0,
            profit_share_pct=1.0,
        ),
        EquityPartner(
            name="JV Partner",
            fixed_amount=0.0,
            interest_rate=0.0,
            compound_interest=False,
            equity_contribution_pct=0.0,
            profit_share_pct=0.0,
        ),
        EquityPartner(
            name="Preferred Equity",
            fixed_amount=0.0,
            interest_rate=0.13,
            compound_interest=True,
            equity_contribution_pct=0.0,
            profit_share_pct=0.0,
        ),
        EquityPartner(
            name="Additional Equity",
            fixed_amount=0.0,
            interest_rate=0.0,
            compound_interest=False,
            equity_contribution_pct=0.0,
            profit_share_pct=0.0,
        ),
    ]


def _default_senior_rate_schedule() -> Dict[int, float]:
    """Senior Construction variable interest rate schedule (period → annual rate).

    Extracted from Excel !!! - Cashflow row 158. Rates represent BBSY + margin.
    """
    schedule: Dict[int, float] = {}
    # Rates change roughly every 2-3 periods, declining from ~5.55% to 4.11%
    rate_bands = [
        (43, 44, 0.0555),
        (45, 47, 0.0620),
        (48, 50, 0.0595),
        (51, 53, 0.0575),
        (54, 56, 0.0550),
        (57, 59, 0.0535),
        (60, 62, 0.0520),
        (63, 65, 0.0511),
        (66, 68, 0.0455),
        (69, 79, 0.0411),
    ]
    for start, end, rate in rate_bands:
        for p in range(start, end + 1):
            schedule[p] = rate
    return schedule


def _default_debt_facilities() -> List[DebtFacility]:
    """Debt facilities from !!! - Input sheet."""
    return [
        DebtFacility(
            name="Land Loan",
            facility_limit=8_400_000.0,
            is_fixed_amount=True,
            ltc_target=0.0,
            lvr_target=0.0,
            interest_rate=0.10135,       # 10.135% fixed annual
            compound_interest=True,
            start_month=23,
            end_month=43,                # Repaid when Senior starts (P43, same period Senior draws)
            application_fee_pct=0.01,
            line_fee_pct=0.005,
            standby_fee_pct=0.0,
            fees_capitalised=True,
            refinanced_by="Senior Construction",
            active=True,
        ),
        DebtFacility(
            name="Mezzanine",
            facility_limit=0.0,
            is_fixed_amount=False,
            ltc_target=0.0,
            lvr_target=0.0,
            interest_rate=0.15,
            compound_interest=True,
            start_month=1,
            end_month=75,
            application_fee_pct=0.0,
            line_fee_pct=0.0,
            standby_fee_pct=0.0,
            fees_capitalised=True,
            active=False,
        ),
        DebtFacility(
            name="Senior Construction",
            facility_limit=154_546_628.0,
            is_fixed_amount=False,        # Progressive draws
            ltc_target=0.84,
            lvr_target=0.754,
            interest_rate=0.0215,         # Base margin (added to BBSY)
            compound_interest=True,
            start_month=43,
            end_month=79,                 # Bullet repayment
            application_fee_pct=0.01,
            line_fee_pct=0.005,
            standby_fee_pct=0.0025,
            fees_capitalised=True,
            interest_rate_schedule=None,  # Populated from factory fn
            active=True,
        ),
        DebtFacility(
            name="Additional Debt",
            facility_limit=0.0,
            is_fixed_amount=False,
            ltc_target=0.0,
            lvr_target=0.0,
            interest_rate=0.10,
            compound_interest=True,
            start_month=1,
            end_month=75,
            application_fee_pct=0.0,
            line_fee_pct=0.0,
            standby_fee_pct=0.0,
            fees_capitalised=True,
            active=False,
        ),
    ]


# ── Main inputs dataclass ─────────────────────────────────────────────

@dataclass
class FeasoInputs:
    """All model assumptions for the Feaso Property Development Feasibility Model.

    Defaults are baked in from the *Feaso Model Draft v22* Excel workbook.
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
