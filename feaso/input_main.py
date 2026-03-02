"""Main input page — project details, land, selling costs, equity & debt.

Maps to the Excel "!!! - Input" sheet. Contains the core project
assumptions: identity, land, acquisition, selling parameters,
equity partners, and debt facilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .types import (
    DebtFacility,
    EquityPartner,
    LandPaymentStage,
)


# ── Default factory functions ────────────────────────────────────────


def _default_land_stages() -> List[LandPaymentStage]:
    """Staged land payments from !!! - Input sheet."""
    return [
        LandPaymentStage("Deposit (10%)", 1_120_920.0, 1),
        LandPaymentStage("Settlement Balance", 10_088_275.0, 23),
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


def _default_debt_facilities() -> List[DebtFacility]:
    """Debt facilities from !!! - Input sheet.

    NOTE: The Senior Construction facility's ``interest_rate_schedule``
    is set to ``None`` here and populated later via
    :class:`~feaso.input_td_actual.TDActualInputs` when
    :meth:`FeasoInputs.from_pages` is called.
    """
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
            end_month=43,
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
            interest_rate_schedule=None,  # Populated from TDActualInputs
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


# ── Main input page dataclass ────────────────────────────────────────


@dataclass
class MainInputs:
    """Core project assumptions from the !!! - Input sheet."""

    # ── Project identity ──────────────────────────────────────────────
    project_name: str = "Fake House"
    address: str = "123 Fake Street, Fakeville VIC 3000"
    developer: str = "Kokoda Property Group"
    revision: str = "REV #1 June 2025"

    # ── Site / GFA ────────────────────────────────────────────────────
    project_lots: int = 178
    project_gfa_sqm: float = 32_133.0
    site_area_sqm: float = 2_000.0

    # ── Land ──────────────────────────────────────────────────────────
    land_purchase_price: float = 11_209_195.0
    prsv_uplift: float = 2_290_805.0
    prsv_month: int = 23                      # When PRSV is recognised
    gst_applicable_land_value: float = 8_990_177.27
    stamp_duty_amount: float = 625_053.655
    land_payment_stages: List[LandPaymentStage] = field(
        default_factory=_default_land_stages
    )

    # ── Acquisition costs ─────────────────────────────────────────────
    acquisition_costs_total: float = 673_000.0
    acquisition_month: int = 23               # Paid at land settlement

    # ── Selling costs ─────────────────────────────────────────────────
    selling_commission_rate: float = 0.027247  # Applied to inc-GST GRV
    presale_commission_pct: float = 0.50       # 50% front-end at exchange
    deposit_pct: float = 0.10                  # 10% deposit at exchange
    selling_other_costs: float = 0.0           # Extra selling costs exc GST

    # ── Equity partners ───────────────────────────────────────────────
    equity_partners: List[EquityPartner] = field(
        default_factory=_default_equity_partners
    )

    # ── Debt facilities ───────────────────────────────────────────────
    debt_facilities: List[DebtFacility] = field(
        default_factory=_default_debt_facilities
    )
