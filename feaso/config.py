"""Configuration constants and date utilities for the Feaso model."""

from datetime import date, timedelta

# ── Model constants ───────────────────────────────────────────────────
NUM_PERIODS = 80          # Maximum periods in cashflow (0-79)
GST_RATE = 0.10           # Australian GST rate
MONTHS_PER_YEAR = 12

# Excel serial-date epoch (Windows convention: day 1 = 1900-01-01,
# but Excel has the 1900-02-29 bug so we offset by 2).
_EXCEL_EPOCH = date(1899, 12, 30)


def excel_serial_to_date(serial: float) -> date:
    """Convert an Excel serial date number to a Python date."""
    return _EXCEL_EPOCH + timedelta(days=int(serial))


def period_to_date(first_period_serial: float, period_index: int) -> date:
    """Return the date for *period_index* (0-based) given the serial date of period 0."""
    base = excel_serial_to_date(first_period_serial)
    # Each period is one calendar month
    year = base.year + (base.month - 1 + period_index) // 12
    month = (base.month - 1 + period_index) % 12 + 1
    return date(year, month, 1)


def months_between(start: int, end: int) -> int:
    """Inclusive count of months between two period indices."""
    return max(0, end - start + 1)
