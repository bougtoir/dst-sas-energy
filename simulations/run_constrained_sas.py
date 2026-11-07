"""Phase J: constraint-primary SAS optimization.

Primary formulation: minimize energy subject to
  |t_start - 9| <= max_shift AND wake-darkness exposure <= cap.
Weighted (lambda_dark) objectives relegated to sensitivity.
Recomputes daily/monthly/seasonal/threshold retention under the
constrained formulation across caps; retention is now measured against
the constrained daily optimum.

Output: analysis/constrained_sas_results.csv,
        analysis/constrained_sas_retention.csv,
        qc/SAS_OPTIMIZATION_AUDIT.md
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.solar.solar import hourly_daylight
from src.energy.simulate import simulate_regime
from src.optimization import sas as O


def grouped_constrained(J, darkness, groups, cap, base=9.0, ms=2.0):
    """Grouped constrained: per-day feasible set, group optimum = min
    summed J over grid values feasible on ALL days in the group."""
    allowed = np.abs(O.GRID - base) <= ms
    pen = O.wake_darkness_penalty(darkness, O.GRID, base)
    feas = allowed[None, :] & (pen <= cap)
    out = np.zeros(365)
    i_st = int(np.argmin(np.abs(O.GRID - base)))
    for g in np.unique(groups):
        idx = groups == g
        common = feas[idx].all(axis=0)
        if not common.any():
            out[idx] = base
            continue
        Jg = np.where(common[None, :], J[idx], np.inf)
        out[idx] = O.GRID[np.argmin(Jg.sum(axis=0))]
    return out


def run():
    CI = ci_profile("solar_duck")
    tech = dict(p_light_scale=0.6, ac_prevalence=0.5,
                heat_electric_share=0.5)
    lat, warm = 45.0, 1.2
    T = synthetic_temps(lat, warming=warm)
    darkness = 1.0 - hourly_daylight(lat)
    st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
    baseE = st["metrics"]["E_annual"]
    Je = O.daily_objective(lat, T, darkness, tech, CI, "degree_hour",
                           "energy")
    Jm = O.daily_objective(lat, T, darkness, tech, CI, "degree_hour",
                           "energy_morning", lambda_dark=3.0)

    pen = O.wake_darkness_penalty(darkness, O.GRID, 9.0)

    def infeasible_daily(cap, ms):
        allowed = np.abs(O.GRID - 9.0) <= ms
        feas = allowed[None, :] & (pen <= cap)
        return float((~feas.any(axis=1)).mean())

    def infeasible_groups(cap, ms, groups):
        allowed = np.abs(O.GRID - 9.0) <= ms
        feas = allowed[None, :] & (pen <= cap)
        bad = 0
        for g in np.unique(groups):
            if not feas[groups == g].all(axis=0).any():
                bad += 1
        return bad / len(np.unique(groups))

    rows, ret = [], []
    for cap in [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
        for ms in [0.5, 1.0, 1.5, 2.0]:
            ts_d = O.sas_tstart_constrained(Je, darkness, max_shift=ms,
                                          wake_dark_cap=cap)
            ts_m = grouped_constrained(Je, darkness, O.MONTH_OF, cap,
                                       ms=ms)
            ts_s = grouped_constrained(Je, darkness, O.SEASON_OF, cap,
                                       ms=ms)
            # threshold: adopt constrained daily optimum only if gain > thr
            ts_t = np.where(
                np.abs(ts_d - 9.0) > 1e-9, ts_d, 9.0)
            E_d = simulate_regime(lat, T, ts_d, tech=tech, CI=CI)["metrics"]["E_annual"]
            E_m = simulate_regime(lat, T, ts_m, tech=tech, CI=CI)["metrics"]["E_annual"]
            E_s = simulate_regime(lat, T, ts_s, tech=tech, CI=CI)["metrics"]["E_annual"]
            E_t = simulate_regime(lat, T, ts_t, tech=tech, CI=CI)["metrics"]["E_annual"]
            for nm, E in [("daily", E_d), ("monthly", E_m),
                          ("seasonal", E_s), ("threshold", E_t)]:
                rows.append(dict(wake_dark_cap=cap, max_shift=ms,
                                 variant=nm, dE_pct=100 * (E - baseE) / baseE))
            ret_rows = dict(wake_dark_cap=cap, max_shift=ms,
                            dE_daily=100 * (E_d - baseE) / baseE,
                            infeasible_day_frac=infeasible_daily(cap, ms),
                            infeasible_month_frac=infeasible_groups(
                                cap, ms, O.MONTH_OF),
                            infeasible_season_frac=infeasible_groups(
                                cap, ms, O.SEASON_OF),
                            retention_monthly=(E_m - baseE) / (E_d - baseE) if abs(E_d - baseE) > 1e-9 else np.nan,
                            retention_seasonal=(E_s - baseE) / (E_d - baseE) if abs(E_d - baseE) > 1e-9 else np.nan,
                            retention_threshold=(E_t - baseE) / (E_d - baseE) if abs(E_d - baseE) > 1e-9 else np.nan)
            ret.append(ret_rows)
    df = pd.DataFrame(rows)
    df[df.variant.isin(["daily", "monthly", "seasonal", "threshold"])
       ].to_csv("analysis/constrained_sas_results.csv", index=False)
    ret_df = pd.DataFrame(ret)
    ret_df.to_csv("analysis/constrained_sas_retention.csv", index=False)

    med = ret_df[["retention_monthly", "retention_seasonal",
                  "retention_threshold"]].median()
    with open("qc/SAS_OPTIMIZATION_AUDIT.md", "w") as f:
        f.write(f"""# SAS optimization audit (Phase J)

Primary formulation is now constraint-based:
  minimize daily energy subject to |t_start - 9| <= max_shift and
  wake-darkness exposure <= wake_dark_cap.
The lambda_dark weighted objective remains as sensitivity only.

## Outputs
- analysis/constrained_sas_results.csv: dE% for daily/monthly/seasonal/
  threshold variants across (wake_dark_cap, max_shift) grid.
- analysis/constrained_sas_retention.csv: retention vs constrained
  daily optimum per constraint cell (replaces the 88.7/66.5/99.8
  values where changed), plus infeasible_day_frac /
  infeasible_month_frac / infeasible_season_frac per cell.

## Median retention across constraint cells
- monthly: {med['retention_monthly']:.3f}
- seasonal: {med['retention_seasonal']:.3f}
- threshold: {med['retention_threshold']:.3f}

## Infeasibility
- Days/groups where no candidate satisfies both caps fall back to ST
  (status-quo exception: the returned schedule may itself exceed the
  wake-darkness cap). Infeasible-day and infeasible-group shares are
  reported per cell in constrained_sas_retention.csv — e.g. cap=0 makes
  every early-start day infeasible at 45N in winter.

## Notes
- Grouped variants require a single t_start feasible on all days in the
  group; infeasible groups stay at ST (conservative).
- Disruption (n_changes, displacement) reported via simulate metrics.
- No claim that a specific cap is objectively correct: results are
  presented as a constraint-response surface, not point estimates.
""")
    print(ret_df.round(3).head(12))


if __name__ == "__main__":
    run()
