import numpy as np
import pandas as pd
import numpy_financial as npf
from .assumptions import Assumptions


def run_underwriting_fund(a: Assumptions, kokoda_df: pd.DataFrame) -> dict:
    """Run the Underwriting Fund monthly model.

    The UW Fund is a wholesale warehouse facility that originates property
    loans, holds them for ``sell_down_months``, then sells them to the Kokoda
    Fund.  Capital is split between the Net UW Fund and a Line of Credit (LOC).

    Parameters
    ----------
    a : Assumptions
        Model assumptions (may be modified for sensitivity scenarios).
    kokoda_df : pd.DataFrame
        Output from ``run_kokoda_fund`` (quarterly, indexed by quarter number).

    Returns
    -------
    dict with keys:
        monthly_df : pd.DataFrame  — monthly detail rows
        summary    : dict          — headline metrics
        uw_cashflows : list[float] — monthly cash-flow series for UW IRR
    """
    nm = a.uw_fund_term_months          # 36
    nq = a.num_quarters                 # 12
    sd = a.sell_down_months             # 3

    # --- Dynamic preferred returns from margin shares ---
    spread = a.gross_return_debt - a.net_investor_return_debt
    uw_pref = a.net_investor_return_debt + spread * a.margin_share_net_uw
    loc_pref = a.net_investor_return_debt + spread * a.margin_share_loc

    # ------------------------------------------------------------------
    # Step 1: Spread Kokoda quarterly loan purchases into monthly amounts
    # ------------------------------------------------------------------
    monthly_buy = np.zeros(nm + sd + 1)     # extra room for look-ahead
    for q in range(1, nq + 1):
        if q not in kokoda_df.index:
            continue
        fa = max(0.0, float(kokoda_df.loc[q, "loan_further_advance"]))
        for off in range(3):
            m = (q - 1) * 3 + off + 1
            if 1 <= m <= nm:
                monthly_buy[m] = fa / 3.0

    # ------------------------------------------------------------------
    # Step 2: Warehouse (deployed) balance
    # ------------------------------------------------------------------
    # At any month m the warehouse holds loans originated in the last
    # ``sell_down_months`` that haven't yet been sold to Kokoda.
    #
    # origination[m] = monthly_buy[m + sd]   (what Kokoda buys sd months later)
    # sell_down[m]   = monthly_buy[m]         (Kokoda buys today's aged stock)
    #
    # Pre-fund originations (for Kokoda purchases in months 1..sd) mean the
    # warehouse starts with an initial balance at month 0.
    deployed = np.zeros(nm + 1)
    deployed[0] = float(np.sum(monthly_buy[1: sd + 1]))

    for m in range(1, nm + 1):
        orig = monthly_buy[m + sd] if (m + sd) <= nm else 0.0
        sell = monthly_buy[m]
        deployed[m] = max(0.0, deployed[m - 1] + orig - sell)

    # Split between Net UW Fund and LOC
    dep_uw = np.minimum(deployed, a.net_uw_fund_size)
    dep_loc = np.maximum(0.0, deployed - a.net_uw_fund_size)
    unused_uw = np.maximum(0.0, a.net_uw_fund_size - dep_uw)
    unused_loc = np.maximum(0.0, a.loc_size - dep_loc)

    # ------------------------------------------------------------------
    # Step 3: Monthly income (use average of opening/closing balances)
    # ------------------------------------------------------------------
    avg_dep_uw = np.zeros(nm + 1)
    avg_dep_loc = np.zeros(nm + 1)
    avg_unused_uw = np.zeros(nm + 1)
    avg_unused_loc = np.zeros(nm + 1)
    for m in range(1, nm + 1):
        avg_dep_uw[m] = (dep_uw[m - 1] + dep_uw[m]) / 2.0
        avg_dep_loc[m] = (dep_loc[m - 1] + dep_loc[m]) / 2.0
        avg_unused_uw[m] = (unused_uw[m - 1] + unused_uw[m]) / 2.0
        avg_unused_loc[m] = (unused_loc[m - 1] + unused_loc[m]) / 2.0

    # --- UW Fund P&L ---
    uw_interest = avg_dep_uw * uw_pref / 12.0
    uw_bank_int = avg_unused_uw * a.uw_interest_undrawn / 12.0
    loc_unused_amt = avg_unused_loc * a.loc_unused_charge / 12.0
    uw_loc_fee = -loc_unused_amt           # UW pays LOC for unused capacity
    uw_admin = -avg_dep_uw * a.uw_admin_fee / 12.0
    uw_profit = uw_interest + uw_bank_int + uw_loc_fee + uw_admin

    # --- LOC P&L ---
    loc_interest = avg_dep_loc * loc_pref / 12.0
    loc_unused_inc = loc_unused_amt.copy()  # received from UW
    loc_admin = -avg_dep_loc * a.loc_admin_fee / 12.0
    loc_profit = loc_interest + loc_unused_inc + loc_admin

    # --- Manager P&L ---
    mgr_uw_margin = avg_dep_uw * (a.gross_return_debt - uw_pref) / 12.0
    mgr_loc_margin = avg_dep_loc * (a.gross_return_debt - loc_pref) / 12.0
    mgr_admin = -(uw_admin + loc_admin)    # manager receives admin fees
    mgr_profit = mgr_uw_margin + mgr_loc_margin + mgr_admin

    # Zero-out seed row (month 0 is not an actual period)
    for arr in (uw_interest, uw_bank_int, uw_loc_fee, uw_admin, uw_profit,
                loc_interest, loc_unused_inc, loc_admin, loc_profit,
                mgr_uw_margin, mgr_loc_margin, mgr_admin, mgr_profit):
        arr[0] = 0.0

    # ------------------------------------------------------------------
    # Step 4: Cash flows & IRR
    # ------------------------------------------------------------------
    dist_period = 12 // a.uw_distribution_freq   # 6 for semi-annual

    # --- UW Fund cash flows ---
    uw_cf = np.zeros(nm + 1)
    uw_cf[0] = -a.net_uw_fund_size               # initial capital commitment

    # Semi-annual distributions of accumulated profit
    for m in range(dist_period, nm + 1, dist_period):
        start = m - dist_period + 1
        uw_cf[m] = float(np.sum(uw_profit[start: m + 1]))

    # Return principal at maturity
    uw_cf[nm] += a.net_uw_fund_size

    # Stub period if maturity doesn't fall on a distribution date
    last_dist_m = (nm // dist_period) * dist_period
    if last_dist_m < nm:
        uw_cf[nm] += float(np.sum(uw_profit[last_dist_m + 1: nm + 1]))

    # Annualised IRR
    uw_irr = 0.0
    try:
        mirr = npf.irr(uw_cf)
        if not np.isnan(mirr) and mirr > -1:
            uw_irr = (1 + mirr) ** 12 - 1
    except Exception:
        pass

    # ------------------------------------------------------------------
    # Step 5: Summary metrics
    # ------------------------------------------------------------------
    peak_uw = float(np.max(dep_uw))
    peak_loc = float(np.max(dep_loc))

    total_uw_profit = float(np.sum(uw_profit[1:]))
    total_loc_profit = float(np.sum(loc_profit[1:]))
    total_mgr_profit = float(np.sum(mgr_profit[1:]))

    uw_multiple = ((a.net_uw_fund_size + total_uw_profit) / a.net_uw_fund_size
                   if a.net_uw_fund_size > 0 else 0.0)

    loc_multiple = ((peak_loc + total_loc_profit) / peak_loc
                    if peak_loc > 0 else 0.0)

    avg_drawn_loc = float(np.mean(dep_loc[1:])) if nm > 0 else 0.0
    loc_ret_avg = (total_loc_profit / avg_drawn_loc / (nm / 12.0)
                   if avg_drawn_loc > 0 else 0.0)

    summary = {
        "uw_peak_size": peak_uw,
        "uw_total_profit": total_uw_profit,
        "uw_multiple": uw_multiple,
        "uw_irr": uw_irr,
        "loc_peak_size": peak_loc,
        "loc_total_profit": total_loc_profit,
        "loc_multiple": loc_multiple,
        "loc_return_on_avg_drawn": loc_ret_avg,
        "manager_profit": total_mgr_profit,
        "uw_preferred_return": uw_pref,
        "loc_preferred_return": loc_pref,
    }

    # ------------------------------------------------------------------
    # Step 6: Monthly DataFrame
    # ------------------------------------------------------------------
    months = list(range(1, nm + 1))
    monthly_df = pd.DataFrame({
        "month": months,
        "deployed_total": deployed[1: nm + 1],
        "deployed_uw": dep_uw[1: nm + 1],
        "deployed_loc": dep_loc[1: nm + 1],
        "unused_uw": unused_uw[1: nm + 1],
        "unused_loc": unused_loc[1: nm + 1],
        "uw_interest": uw_interest[1: nm + 1],
        "uw_bank_interest": uw_bank_int[1: nm + 1],
        "uw_loc_fee": uw_loc_fee[1: nm + 1],
        "uw_admin_fee": uw_admin[1: nm + 1],
        "uw_profit": uw_profit[1: nm + 1],
        "loc_interest": loc_interest[1: nm + 1],
        "loc_unused_fee": loc_unused_inc[1: nm + 1],
        "loc_admin_fee": loc_admin[1: nm + 1],
        "loc_profit": loc_profit[1: nm + 1],
        "mgr_margin": (mgr_uw_margin + mgr_loc_margin)[1: nm + 1],
        "mgr_admin": mgr_admin[1: nm + 1],
        "mgr_profit": mgr_profit[1: nm + 1],
    }).set_index("month")

    return {
        "monthly_df": monthly_df,
        "summary": summary,
        "uw_cashflows": uw_cf.tolist(),
    }
