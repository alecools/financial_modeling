# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python/Streamlit rebuild of the "Kokoda High Level Fund Model" Excel workbook. Models a multi-fund property debt investment structure: a primary Kokoda Fund (quarterly cashflows), an Underwriting warehouse facility (monthly), and multi-scenario sensitivity analysis.

## Commands

```bash
pip install -r requirements.txt   # Install dependencies
streamlit run app.py               # Launch the app
```

No test suite exists yet.

## Architecture

**Data flow:** `Assumptions` → `run_kokoda_fund()` → `run_underwriting_fund()` → UI / `run_sensitivity_analysis()`

- **`model/assumptions.py`** — Single `@dataclass` holding all model inputs. Derived properties (`gross_irr`, `loc_size`, `net_uw_fund_size`, `num_quarters`) are computed via `@property`. Sensitivity scenarios use `dataclasses.replace()` to override fields.

- **`model/kokoda_fund.py`** — Quarterly cashflow waterfall (default 12 quarters). Handles a circular dependency in redemptions by using prior-quarter loan closing balances. Returns a DataFrame indexed by quarter. `summarise_kokoda_fund()` aggregates KPIs.

- **`model/underwriting_fund.py`** — Monthly warehouse model (default 36 months). Derives originations from Kokoda's quarterly `loan_further_advance` spread into monthly buckets. Tracks deployed balances split between Net UW Fund (capped) and LOC (overflow). Computes profit waterfalls for UW Fund, LOC, and Manager. IRR is annualised from monthly cashflows via `numpy_financial.irr()`.

- **`model/sensitivity.py`** — Defines 7 predefined scenarios. `SENSITIVITY_BASE_OVERRIDES` applies different margin shares (0.20/0.05) vs the sidebar defaults (0.35/0.15). `run_scenario()` applies overrides and runs the full Kokoda → UW pipeline.

- **`app.py`** — Streamlit UI with sidebar inputs and 4 tabs (Dashboard, Kokoda Fund, Underwriting Fund, Sensitivities). All charts use Plotly.

## Key Design Decisions

- Kokoda model is quarterly; UW model is monthly. The UW model converts quarterly Kokoda data to monthly by dividing each quarter's `loan_further_advance` by 3.
- Warehouse balance formula: `deployed[m] = deployed[m-1] + origination[m] - selldown[m]`, where origination is forward-looking (what Kokoda buys `sell_down_months` later) and selldown is current Kokoda purchases.
- UW preferred returns are computed dynamically from margin shares: `net_investor_return + spread × margin_share`, not from stored defaults.
- The source Excel has broken `#REF!` errors in the UW Fund section (deleted pipeline sheet). This Python model reconstructs the UW logic from economic principles and formula patterns.
