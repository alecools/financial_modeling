"""TD Actual input page — variable interest-rate schedules.

Maps to the Excel "Inputs_TD_Actual" sheet. Holds the BBSY-based
variable rate schedule for the Senior Construction facility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


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


@dataclass
class TDActualInputs:
    """Variable rate schedule inputs from the Inputs_TD_Actual sheet."""

    senior_rate_schedule: Dict[int, float] = field(
        default_factory=_default_senior_rate_schedule
    )
