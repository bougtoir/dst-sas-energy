"""Phase 2/5 core: regime comparison incl. SAS variants.

For each configuration computes ST, DST, SAS-daily(C1), SAS-monthly(C2),
SAS-seasonal(C3), SAS-threshold(C4) under both energy and carbon objectives.
Outputs:
  analysis/regime_comparison.csv   — outcomes per regime per config
  analysis/load_shape_metrics.csv  — peak metrics per regime per config
  analysis/discrete_sas_efficiency_retention.csv
  analysis/energy_carbon_divergence.csv — energy-optimal vs carbon-optimal SAS
  analysis/sas_constraint_sensitivity.csv — sweep of max_shift & threshold
"""
import sys, os, itertools, time
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime
from src.solar.solar import hourly_daylight
from src.optimization import sas as O

OUT = os.path.join(os.path.dirname(__file__), "..", "analysis")
os.makedirs(OUT, exist_ok=True)

LATS = [20, 30, 40, 50]
CONFIGS = []
for lat in LATS:
    for w in [0, 2, 4]:
        for ac in [0.25, 0.75]:
            CONFIGS.append(dict(lat=lat, warming=w, ac_prevalence=ac,
                                p_light_scale=0.55, cop_cool=3.0,
                                cop_heat=2.5, heat_electric_share=0.5))


def run_config(cfg, ci_kind="solar_duck", thermal="degree_hour"):
    lat = cfg["lat"]
    T = synthetic_temps(lat, warming=cfg["warming"])
    CI = ci_profile(ci_kind)
    tech = {k: v for k, v in cfg.items() if k != "lat" and k != "warming"}
    darkness = 1.0 - hourly_daylight(lat)
    res = {}
    for reg in ["ST", "DST"]:
        res[reg] = simulate_regime(lat, T, reg, tech=tech, CI=CI,
                                   thermal_model=thermal)
    # SAS variants under both objectives
    out = {}
    Je = O.daily_objective(lat, T, darkness, tech, CI, thermal, "energy")
    Jc = O.daily_objective(lat, T, darkness, tech, CI, thermal, "carbon")
    Jm = O.daily_objective(lat, T, darkness, tech, CI, thermal,
                           "energy_morning", lambda_dark=3.0)
    variants = {}
    for obj, J in [("energy", Je), ("carbon", Jc), ("morning", Jm)]:
        ms = cfg.get("max_shift", 2.0)
        ts_daily = O.sas_tstart_daily(J, max_shift=ms)
        ts_month = O.sas_tstart_grouped(J, O.MONTH_OF, max_shift=ms)
        ts_seas = O.sas_tstart_grouped(J, O.SEASON_OF, max_shift=ms)
        ts_thr = O.sas_tstart_threshold(J, threshold=0.001, max_shift=ms)
        for name, ts in [("daily", ts_daily), ("monthly", ts_month),
                         ("seasonal", ts_seas), ("threshold", ts_thr)]:
            out[f"SAS_{name}_{obj}"] = simulate_regime(
                lat, T, t_start_arr=ts, tech=tech, CI=CI,
                thermal_model=thermal)
            out[f"SAS_{name}_{obj}"]["t_start_out"] = ts
    res.update(out)
    return res, dict(Je=Je, Jc=Jc)


def main():
    rows, peak_rows, ret_rows, div_rows, t0s = [], [], [], [], time.time()
    for cfg in CONFIGS:
        res, J = run_config(cfg)
        E_ST = res["ST"]["metrics"]["E_annual"]
        C_ST = res["ST"]["metrics"]["C_annual"]
        for reg, r in res.items():
            m = r["metrics"]
            rows.append(dict(**cfg, regime=reg,
                             E_annual=m["E_annual"],
                             C_annual=m["C_annual"],
                             dE_pct=100*(m["E_annual"]-E_ST)/E_ST,
                             dC_pct=100*(m["C_annual"]-C_ST)/C_ST))
            peak_rows.append(dict(**cfg, regime=reg,
                                  **{k: m[k] for k in
                                     ["peak_annual","peak_summer","peak_winter",
                                      "p95","p99","par","peak_hour","peak_doy"]}))
        # efficiency retention relative to daily SAS (energy objective)
        for obj in ["energy", "carbon", "morning"]:
            ben_daily = E_ST - res[f"SAS_daily_{obj}"]["metrics"]["E_annual"]
            for v in ["monthly", "seasonal", "threshold"]:
                ben = E_ST - res[f"SAS_{v}_{obj}"]["metrics"]["E_annual"]
                ret_rows.append(dict(**cfg, objective=obj, variant=v,
                                     retention=(ben/ben_daily if ben_daily else np.nan),
                                     ben_daily=ben_daily, ben=ben))
        # energy vs carbon divergence
        de = res["SAS_daily_energy"]["metrics"]; dc = res["SAS_daily_carbon"]["metrics"]
        div_rows.append(dict(**cfg,
            dE_energy_opt=de["E_annual"]-E_ST, dE_carbon_opt=dc["E_annual"]-E_ST,
            dC_energy_opt=de["C_annual"]-C_ST, dC_carbon_opt=dc["C_annual"]-C_ST,
            schedule_corr=(lambda a,b: float(__import__("scipy.stats",fromlist=["spearmanr"]).spearmanr(a,b).statistic) if np.std(a)>0 and np.std(b)>0 else np.nan)(
                res["SAS_daily_energy"]["t_start_out"],
                res["SAS_daily_carbon"]["t_start_out"])))
    pd.DataFrame(rows).to_csv(f"{OUT}/regime_comparison.csv", index=False)
    pd.DataFrame(peak_rows).to_csv(f"{OUT}/load_shape_metrics.csv", index=False)
    pd.DataFrame(ret_rows).to_csv(
        f"{OUT}/discrete_sas_efficiency_retention.csv", index=False)
    pd.DataFrame(div_rows).to_csv(
        f"{OUT}/energy_carbon_divergence.csv", index=False)

    # constraint sensitivity at one representative config
    cfg = dict(lat=40, warming=2, ac_prevalence=0.5, p_light_scale=0.55,
               cop_cool=3.0, cop_heat=2.5, heat_electric_share=0.5)
    lat = cfg["lat"]; T = synthetic_temps(lat, warming=cfg["warming"])
    CI = ci_profile("solar_duck")
    darkness = 1.0 - hourly_daylight(lat)
    tech = {k: v for k, v in cfg.items() if k not in ("lat", "warming")}
    J = O.daily_objective(lat, T, darkness, tech, CI, "degree_hour", "energy")
    srows = []
    for ms in [0.5, 1.0, 1.5, 2.0, 3.0]:
        for thr in [0.0, 0.0005, 0.001, 0.002, 0.005]:
            ts = O.sas_tstart_threshold(J, max_shift=ms, threshold=thr)
            r = simulate_regime(lat, T, t_start_arr=ts, tech=tech, CI=CI)
            st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
            dis = O.disruption(ts)
            srows.append(dict(max_shift=ms, threshold=thr,
                              dE_pct=100*(r["metrics"]["E_annual"]
                                          - st["metrics"]["E_annual"])
                                     / st["metrics"]["E_annual"],
                              **dis))
    pd.DataFrame(srows).to_csv(f"{OUT}/sas_constraint_sensitivity.csv",
                               index=False)
    print(f"done in {time.time()-t0s:.0f}s")


if __name__ == "__main__":
    main()
