"""Feaso — Property Development Feasibility Model.

Public API
----------
- :class:`FeasoInputs` — Composite model inputs (main entry point)
- :class:`AdminInputs` — Admin / timing settings (``Admin`` sheet)
- :class:`MainInputs` — Project, land, selling, equity & debt (``!!! - Input`` sheet)
- :class:`TDActualInputs` — Variable rate schedules (``Inputs_TD_Actual`` sheet)
- :class:`RevCostsInputs` — Cost & revenue line items (``Rev_Costs actual`` sheet)
- :class:`ScenarioManagerInputs` — Scenario adjustments (``Scenario Manager`` sheet)
- Helper types: :class:`CostLineItem`, :class:`RevenueLineItem`,
  :class:`LandPaymentStage`, :class:`EquityPartner`, :class:`DebtFacility`
"""

# ── Composite inputs (backward-compatible entry point) ─────────────────
from .inputs import FeasoInputs  # noqa: F401

# ── Page-level input dataclasses ───────────────────────────────────────
from .input_admin import AdminInputs  # noqa: F401
from .input_main import MainInputs  # noqa: F401
from .input_rev_costs import RevCostsInputs  # noqa: F401
from .input_scenario import ScenarioManagerInputs  # noqa: F401
from .input_td_actual import TDActualInputs  # noqa: F401

# ── Shared helper types ────────────────────────────────────────────────
from .types import (  # noqa: F401
    CostLineItem,
    DebtFacility,
    EquityPartner,
    LandPaymentStage,
    RevenueLineItem,
)

__all__ = [
    "FeasoInputs",
    "AdminInputs",
    "MainInputs",
    "TDActualInputs",
    "RevCostsInputs",
    "ScenarioManagerInputs",
    "CostLineItem",
    "RevenueLineItem",
    "LandPaymentStage",
    "EquityPartner",
    "DebtFacility",
]
