"""Pareto/constraint analysis: benefit vs allowed schedule shift x granularity.

Outputs analysis/pareto_frontier.csv and analysis/thermal_model_sensitivity.csv
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


def main():
    rows = []
    SHIFTS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    for lat in [20, 30, 40, 50]:
        for w in [0, 4]:
            T = synthetic_temps(lat, warming=w)
            CI = ci_profile("solar_duck")
            dark = 1 - hourly_daylight(lat)
            tech = dict(p_light_scale=0.55, ac_prevalence=0.5, cop_cool=3.0,
                        cop_heat=2.5, heat_electric_share=0.5)
            Je = O.daily_objective(lat, T, dark, tech, CI, "degree_hour",
                                   "energy_morning", lambda_dark=3.0)
            st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
            E_ST, C_ST = (st["metrics"]["E_annual"],
                          st["metrics"]["C_annual"])
            for ms in SHIFTS:
                for v, ts in [("daily", O.sas_tstart_daily(Je, max_shift=ms)),
                              ("monthly", O.sas_tstart_grouped(Je, O.MONTH_OF, max_shift=ms)),
                              ("seasonal", O.sas_tstart_grouped(Je, O.SEASON_OF, max_shift=ms)),
                              ("threshold", O.sas_tstart_threshold(Je, max_shift=ms, threshold=0.001))]:
                    r = simulate_regime(lat, T, t_start_arr=ts, tech=tech,
                                        CI=CI)
                    m = r["metrics"]
                    rows.append(dict(lat=lat, warming=w, max_shift=ms,
                                     variant=v,
                                     dE_pct=100*(m["E_annual"]-E_ST)/E_ST,
                                     dC_pct=100*(m["C_annual"]-C_ST)/C_ST,
                                     wake_dark=m["wake_dark"],
                                     evening_dark=m["evening_dark"],
                                     n_changes=m["n_changes"],
                                     mean_abs_shift=m["mean_abs_shift"],
                                     peak=m["peak_annual"], par=m["par"]))
    pd.DataFrame(rows).to_csv(f"{OUT}/pareto_frontier.csv", index=False)

    # RC vs degree-hour structural sensitivity
    rows = []
    for lat in [30, 40, 50]:
        for tm in ["degree_hour", "rc"]:
            T = synthetic_temps(lat, warming=2)
            CI = ci_profile("solar_duck")
            tech = dict(p_light_scale=0.55, ac_prevalence=0.75, cop_cool=3.0,
                        cop_heat=2.5, heat_electric_share=0.5)
            st = simulate_regime(lat, T, "ST", tech=tech, CI=CI,
                                 thermal_model=tm)
            dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI,
                                  thermal_model=tm)
            rows.append(dict(lat=lat, model=tm,
                             dE_DST_pct=100*(dst["metrics"]["E_annual"]
                                            - st["metrics"]["E_annual"])
                                       / st["metrics"]["E_annual"],
                             dC_DST_pct=100*(dst["metrics"]["C_annual"]
                                            - st["metrics"]["C_annual"])
                                       / st["metrics"]["C_annual"]))
    pd.DataFrame(rows).to_csv(f"{OUT}/thermal_model_sensitivity.csv",
                              index=False)
    print("pareto + thermal sensitivity done")


if __name__ == "__main__":
    main()
