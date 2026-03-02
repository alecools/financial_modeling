"""Scenario Manager input page — scenario selection and adjustment parameters.

Maps to the Excel "Scenario Manager" sheet. Provides controls for
selecting a predefined scenario and applying percentage-based
adjustments to key model parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScenarioManagerInputs:
    """Scenario adjustment parameters from the Scenario Manager sheet."""

    active_scenario: Optional[str] = None     # Name of active scenario, None = Base Case
    revenue_adjustment_pct: float = 0.0       # e.g. -0.10 for -10%
    cost_adjustment_pct: float = 0.0          # e.g.  0.10 for +10%
    settlement_delay_months: int = 0          # Additional months to delay settlement
    interest_rate_adjustment_pct: float = 0.0 # e.g.  0.02 for +2%
    land_cost_adjustment_pct: float = 0.0     # e.g.  0.20 for +20%
