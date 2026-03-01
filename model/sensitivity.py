from dataclasses import replace
from typing import List, Dict, Any, Optional
import pandas as pd

from .assumptions import Assumptions
from .kokoda_fund import run_kokoda_fund, summarise_kokoda_fund
from .underwriting_fund import run_underwriting_fund


# ── Predefined scenarios matching Excel Sensitivities sheet ──────────────
# The base scenario uses margin_share 0.20 / 0.05 (not the Assumptions
# defaults of 0.35 / 0.15).  Each scenario dict contains only the fields
# that differ from the base.

SENSITIVITY_BASE_OVERRIDES = {
    "margin_share_net_uw": 0.20,
    "margin_share_loc": 0.05,
}

PREDEFINED_SCENARIOS: List[Dict[str, Any]] = [
    {
        "name": "Base Case",
        "overrides": {},
    },
    {
        "name": "S1: Smaller Fund ($30M)",
        "overrides": {"gross_fund_size": 30.0},
    },
    {
        "name": "S2: Faster Sell-Down (2mo)",
        "overrides": {"sell_down_months": 2},
    },
    {
        "name": "S3: Shorter Term (24mo)",
        "overrides": {"uw_fund_term_months": 24},
    },
    {
        "name": "S4: Higher LOC Charge (1.25%)",
        "overrides": {"loc_unused_charge": 0.0125},
    },
    {
        "name": "S5: Lower LOC Ratio (30%)",
        "overrides": {"loc_pct_of_fund": 0.30},
    },
    {
        "name": "S6: Higher Margin Share (0.35/0.15)",
        "overrides": {"margin_share_net_uw": 0.35, "margin_share_loc": 0.15},
    },
]


def run_scenario(
    base: Assumptions,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the full model (Kokoda + UW Fund) with optional assumption overrides.

    Returns a dict with kokoda_df, kokoda_summary, uw_result, and the
    Assumptions object used.
    """
    # Apply sensitivity base overrides then scenario-specific overrides
    merged = {**SENSITIVITY_BASE_OVERRIDES, **(overrides or {})}
    a = replace(base, **merged)

    kokoda_df = run_kokoda_fund(a)
    kokoda_summary = summarise_kokoda_fund(kokoda_df)
    uw_result = run_underwriting_fund(a, kokoda_df)

    return {
        "assumptions": a,
        "kokoda_df": kokoda_df,
        "kokoda_summary": kokoda_summary,
        "uw_result": uw_result,
    }


def run_sensitivity_analysis(
    base: Assumptions,
    scenarios: Optional[List[Dict[str, Any]]] = None,
) -> pd.DataFrame:
    """Run multiple scenarios and return a comparison DataFrame.

    Parameters
    ----------
    base : Assumptions
        Default assumptions (before sensitivity base overrides).
    scenarios : list[dict], optional
        Each dict has 'name' and 'overrides'.  Defaults to PREDEFINED_SCENARIOS.

    Returns
    -------
    pd.DataFrame indexed by scenario name with columns for key UW metrics.
    """
    if scenarios is None:
        scenarios = PREDEFINED_SCENARIOS

    rows = []
    for sc in scenarios:
        result = run_scenario(base, sc["overrides"])
        s = result["uw_result"]["summary"]
        rows.append({
            "Scenario": sc["name"],
            # Net UW Fund
            "UW Peak Size ($M)": s["uw_peak_size"],
            "UW Profit ($M)": s["uw_total_profit"],
            "UW Multiple (x)": s["uw_multiple"],
            "UW IRR (%)": s["uw_irr"] * 100,
            # LOC
            "LOC Peak Size ($M)": s["loc_peak_size"],
            "LOC Profit ($M)": s["loc_total_profit"],
            "LOC Multiple (x)": s["loc_multiple"],
            "LOC Return on Avg Drawn (%)": s["loc_return_on_avg_drawn"] * 100,
            # Manager
            "Manager Profit ($M)": s["manager_profit"],
            # Pref returns
            "UW Pref Return (%)": s["uw_preferred_return"] * 100,
            "LOC Pref Return (%)": s["loc_preferred_return"] * 100,
        })

    df = pd.DataFrame(rows).set_index("Scenario")
    return df
