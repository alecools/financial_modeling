"""Scenario manager — run multiple feasibility scenarios with parameter overrides.

Supports up to 10 named scenarios, each with specific parameter adjustments
to the base FeasoInputs. Useful for sensitivity analysis.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from .inputs import FeasoInputs
from .cashflow import run_model
from .summary import FeasoSummary, build_summary


@dataclass
class ScenarioOverride:
    """A single scenario definition with parameter overrides."""
    name: str
    description: str = ""
    # Override functions modify a copy of inputs
    apply_overrides: Optional[Callable[[FeasoInputs], None]] = None
    # Simple overrides as key-value pairs (field_name → value)
    field_overrides: Dict[str, object] = field(default_factory=dict)
    # Multiplier adjustments (field_name → multiplier)
    multipliers: Dict[str, float] = field(default_factory=dict)


def _apply_scenario(base: FeasoInputs, scenario: ScenarioOverride) -> FeasoInputs:
    """Create a modified copy of inputs with scenario overrides applied."""
    inputs = deepcopy(base)

    # Apply simple field overrides
    for key, value in scenario.field_overrides.items():
        if hasattr(inputs, key):
            setattr(inputs, key, value)

    # Apply multipliers
    for key, mult in scenario.multipliers.items():
        if hasattr(inputs, key):
            current = getattr(inputs, key)
            if isinstance(current, (int, float)):
                setattr(inputs, key, current * mult)

    # Apply custom override function
    if scenario.apply_overrides is not None:
        scenario.apply_overrides(inputs)

    return inputs


def run_scenario(
    base_inputs: FeasoInputs,
    scenario: ScenarioOverride,
) -> FeasoSummary:
    """Run a single scenario and return summary metrics.

    Parameters
    ----------
    base_inputs : FeasoInputs
        Base model assumptions.
    scenario : ScenarioOverride
        Scenario with overrides to apply.

    Returns
    -------
    FeasoSummary
        Summary metrics for this scenario.
    """
    modified_inputs = _apply_scenario(base_inputs, scenario)
    result = run_model(modified_inputs)
    return build_summary(result)


def run_all_scenarios(
    base_inputs: FeasoInputs,
    scenarios: Optional[List[ScenarioOverride]] = None,
) -> Dict[str, FeasoSummary]:
    """Run all scenarios and return dict of name → summary.

    Parameters
    ----------
    base_inputs : FeasoInputs
        Base model assumptions.
    scenarios : List[ScenarioOverride], optional
        Custom scenarios. If None, uses predefined scenarios.

    Returns
    -------
    Dict[str, FeasoSummary]
        Mapping of scenario name to summary results.
    """
    if scenarios is None:
        scenarios = get_predefined_scenarios()

    results: Dict[str, FeasoSummary] = {}

    # Always run base case first
    base_result = run_model(base_inputs)
    results["Base Case"] = build_summary(base_result)

    # Run each scenario
    for scenario in scenarios:
        results[scenario.name] = run_scenario(base_inputs, scenario)

    return results


def build_comparison_table(
    summaries: Dict[str, FeasoSummary],
) -> pd.DataFrame:
    """Build a comparison DataFrame from multiple scenario summaries.

    Parameters
    ----------
    summaries : Dict[str, FeasoSummary]
        Mapping of scenario name to summary.

    Returns
    -------
    pd.DataFrame
        Scenarios as columns, metrics as rows.
    """
    metrics = [
        ("GRV (inc GST)", lambda s: s.grv_inc_gst),
        ("NRV (inc GST)", lambda s: s.nrv_inc_gst),
        ("Total Costs (exc financing)", lambda s: s.total_costs_exc_financing),
        ("Total Financing Costs", lambda s: s.total_financing_costs),
        ("Total Costs (all-in)", lambda s: s.total_costs_all_in),
        ("Net Development Profit", lambda s: s.net_development_profit),
        ("ROI (%)", lambda s: s.roi_pct),
        ("Project IRR (%)", lambda s: s.project_irr * 100 if not np.isnan(s.project_irr) else float("nan")),
        ("Equity IRR (%)", lambda s: s.equity_irr * 100 if not np.isnan(s.equity_irr) else float("nan")),
        ("Peak Debt", lambda s: s.peak_debt),
        ("Total Equity", lambda s: s.total_equity_injected),
        ("Cost per Lot", lambda s: s.cost_per_lot),
        ("Profit per Lot", lambda s: s.profit_per_lot),
    ]

    data = {}
    for scenario_name, summary in summaries.items():
        data[scenario_name] = {
            metric_name: extractor(summary)
            for metric_name, extractor in metrics
        }

    return pd.DataFrame(data)


# ── Predefined scenarios ──────────────────────────────────────────────

def _override_revenue_down_10(inputs: FeasoInputs) -> None:
    """Reduce all revenue by 10%."""
    for item in inputs.revenue_items:
        item.sale_price_inc_gst *= 0.90


def _override_revenue_up_10(inputs: FeasoInputs) -> None:
    """Increase all revenue by 10%."""
    for item in inputs.revenue_items:
        item.sale_price_inc_gst *= 1.10


def _override_costs_up_10(inputs: FeasoInputs) -> None:
    """Increase all costs by 10%."""
    for item in inputs.cost_items:
        item.total_cost *= 1.10


def _override_costs_up_20(inputs: FeasoInputs) -> None:
    """Increase all costs by 20%."""
    for item in inputs.cost_items:
        item.total_cost *= 1.20


def _override_settlement_delay_3m(inputs: FeasoInputs) -> None:
    """Delay all settlements by 3 months."""
    for item in inputs.revenue_items:
        item.settlement_start += 3


def _override_settlement_delay_6m(inputs: FeasoInputs) -> None:
    """Delay all settlements by 6 months."""
    for item in inputs.revenue_items:
        item.settlement_start += 6
    # Extend project end and equity distribution
    inputs.project_end_month += 6
    inputs.equity_dist_start += 6
    inputs.equity_dist_end += 6
    inputs.num_periods = max(inputs.num_periods, inputs.project_end_month + 5)


def _override_interest_rate_up_2(inputs: FeasoInputs) -> None:
    """Increase all debt interest rates by 2%."""
    for fac in inputs.debt_facilities:
        fac.interest_rate += 0.02
        if fac.interest_rate_schedule:
            fac.interest_rate_schedule = {
                k: v + 0.02 for k, v in fac.interest_rate_schedule.items()
            }


def _override_land_cost_up_20(inputs: FeasoInputs) -> None:
    """Increase land purchase price by 20%."""
    increase = inputs.land_purchase_price * 0.20
    inputs.land_purchase_price *= 1.20
    # Adjust staged payments proportionally
    for stage in inputs.land_payment_stages:
        stage.amount *= 1.20


def _override_best_case(inputs: FeasoInputs) -> None:
    """Best case: revenue +10%, costs -5%, faster settlement."""
    for item in inputs.revenue_items:
        item.sale_price_inc_gst *= 1.10
    for item in inputs.cost_items:
        item.total_cost *= 0.95


def _override_worst_case(inputs: FeasoInputs) -> None:
    """Worst case: revenue -15%, costs +15%, settlement delay 3m, rates +1%."""
    for item in inputs.revenue_items:
        item.sale_price_inc_gst *= 0.85
    for item in inputs.cost_items:
        item.total_cost *= 1.15
    for item in inputs.revenue_items:
        item.settlement_start += 3
    for fac in inputs.debt_facilities:
        fac.interest_rate += 0.01
        if fac.interest_rate_schedule:
            fac.interest_rate_schedule = {
                k: v + 0.01 for k, v in fac.interest_rate_schedule.items()
            }


def get_predefined_scenarios() -> List[ScenarioOverride]:
    """Return list of predefined sensitivity scenarios."""
    return [
        ScenarioOverride(
            name="Revenue -10%",
            description="All revenue items reduced by 10%",
            apply_overrides=_override_revenue_down_10,
        ),
        ScenarioOverride(
            name="Revenue +10%",
            description="All revenue items increased by 10%",
            apply_overrides=_override_revenue_up_10,
        ),
        ScenarioOverride(
            name="Costs +10%",
            description="All development/construction costs increased by 10%",
            apply_overrides=_override_costs_up_10,
        ),
        ScenarioOverride(
            name="Costs +20%",
            description="All development/construction costs increased by 20%",
            apply_overrides=_override_costs_up_20,
        ),
        ScenarioOverride(
            name="Settlement Delay 3m",
            description="All settlements delayed by 3 months",
            apply_overrides=_override_settlement_delay_3m,
        ),
        ScenarioOverride(
            name="Settlement Delay 6m",
            description="All settlements delayed by 6 months, project extended",
            apply_overrides=_override_settlement_delay_6m,
        ),
        ScenarioOverride(
            name="Interest Rates +2%",
            description="All debt interest rates increased by 2 percentage points",
            apply_overrides=_override_interest_rate_up_2,
        ),
        ScenarioOverride(
            name="Land Cost +20%",
            description="Land purchase price increased by 20%",
            apply_overrides=_override_land_cost_up_20,
        ),
        ScenarioOverride(
            name="Best Case",
            description="Revenue +10%, costs -5%",
            apply_overrides=_override_best_case,
        ),
        ScenarioOverride(
            name="Worst Case",
            description="Revenue -15%, costs +15%, settlement delay 3m, rates +1%",
            apply_overrides=_override_worst_case,
        ),
    ]
