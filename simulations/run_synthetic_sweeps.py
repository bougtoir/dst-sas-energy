"""Phase 2: synthetic parameter sweeps for DST/ST contrast and phase diagrams.

Outputs:
  analysis/dst_sweep.csv  — Delta_DST (DST-ST) for energy & carbon over
                            lat x warming x ac_prev x light_scale
  analysis/load_shape_metrics.csv — hourly load metrics per regime at
                            representative configurations
"""
import sys, os, itertools, time
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime
from src.solar.solar import hourly_daylight
from src.optimization.sas import daily_objective, sas_tstart_daily, GRID

OUT = os.path.join(os.path.dirname(__file__), "..", "analysis")
os.makedirs(OUT, exist_ok=True)

LATS = [20, 30, 40, 50, 60]
WARMING = [0, 1, 2, 3, 4]
AC = [0.0, 0.25, 0.5, 0.75, 1.0]
LIGHT = {"incandescent": 3.3, "fluorescent": 1.4, "mixed": 1.0,
         "led": 0.55, "full_led": 0.4}  # scale vs reference efficacy
CI_KIND = "solar_duck"


def main():
    rows = []
    t0 = time.time()
    for lat, w, ac, (lname, lsc) in itertools.product(LATS, WARMING, AC, LIGHT.items()):
        T = synthetic_temps(lat, warming=w)
        CI = ci_profile(CI_KIND)
        tech = dict(p_light_scale=lsc, ac_prevalence=ac, cop_cool=3.0,
                    cop_heat=2.5, heat_electric_share=0.5)
        st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
        dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI)
        rows.append(dict(
            lat=lat, warming=w, ac_prevalence=ac, lighting=lname,
            E_ST=st["metrics"]["E_annual"], E_DST=dst["metrics"]["E_annual"],
            dE_DST=dst["metrics"]["E_annual"] - st["metrics"]["E_annual"],
            dE_DST_pct=100 * (dst["metrics"]["E_annual"] - st["metrics"]["E_annual"])
                       / st["metrics"]["E_annual"],
            C_ST=st["metrics"]["C_annual"], C_DST=dst["metrics"]["C_annual"],
            dC_DST=dst["metrics"]["C_annual"] - st["metrics"]["C_annual"],
            dC_DST_pct=100 * (dst["metrics"]["C_annual"] - st["metrics"]["C_annual"])
                       / st["metrics"]["C_annual"],
            dE_light=dst["metrics"]["E_light"] - st["metrics"]["E_light"],
            dE_cool=dst["metrics"]["E_cool"] - st["metrics"]["E_cool"],
            dE_heat=dst["metrics"]["E_heat"] - st["metrics"]["E_heat"],
            peak_ST=st["metrics"]["peak_annual"],
            peak_DST=dst["metrics"]["peak_annual"],
            dpeak=dst["metrics"]["peak_annual"] - st["metrics"]["peak_annual"],
            par_ST=st["metrics"]["par"], par_DST=dst["metrics"]["par"],
        ))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "dst_sweep.csv"), index=False)
    print(f"dst_sweep.csv: {len(df)} rows in {time.time()-t0:.0f}s")
    print(df.groupby(["lat", "ac_prevalence"]).dE_DST_pct.mean()
          .unstack().round(2).loc[:, :].to_string())


if __name__ == "__main__":
    main()
