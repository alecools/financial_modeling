"""Admin input page — project-level settings and timing parameters.

Maps to the Excel "Admin" sheet. Controls period count, GST rate,
project timing windows, and stamp duty jurisdiction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdminInputs:
    """Project administration and timing settings."""

    num_periods: int = 80                     # Max cashflow periods
    date_of_first_period: float = 44652.0     # Excel serial date for Period 1
    gst_rate: float = 0.10                    # GST rate (10%)
    project_start_month: int = 41             # Construction/main works start period
    project_span_months: int = 35             # Duration of main works
    project_end_month: int = 75               # Final project period
    equity_dist_start: int = 70               # Equity repatriation window start
    equity_dist_end: int = 75                 # Equity repatriation window end
    stamp_duty_state: str = "QLD"             # Stamp duty jurisdiction ("QLD" or "VIC")
