"""Phase 6: stylized historical counterfactual eras + warming reversal.

Era parameters are EXPLICIT ASSUMPTIONS (documented, not fabricated data):
  1970s: incandescent-like lighting, low AC, low electric-heat share, flat CI
  1990s: fluorescent transition, moderate AC
  2010s: mixed lighting, high AC
  2030+: LED-dominant, high AC, solar-duck CI, warming
Outputs: analysis/historical.csv, analysis/reversal_thresholds.csv
"""
import sys, os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime

OUT = os.path.join(os.path.dirname(__file__), "..", "analysis")

ERAS = {
    # label: dict(light_scale, ac_prev, heat_elec_share, ci_kind, solar_pen)
    "1970s": dict(p_light_scale=3.3, ac_prevalence=0.15,
                  heat_electric_share=0.25, ci="fossil_peak", solar_pen=0.0),
    "1990s": dict(p_light_scale=1.4, ac_prevalence=0.45,
                  heat_electric_share=0.35, ci="fossil_peak", solar_pen=0.0),
    "2010s": dict(p_light_scale=0.9, ac_prevalence=0.70,
                  heat_electric_share=0.5, ci="solar_duck", solar_pen=0.15),
    "contemporary": dict(p_light_scale=0.55, ac_prevalence=0.80,
                         heat_electric_share=0.55, ci="solar_duck", solar_pen=0.3),
    "future+2C": dict(p_light_scale=0.4, ac_prevalence=0.95,
                      heat_electric_share=0.7, ci="solar_duck", solar_pen=0.45),
}
WARM = {"1970s": -0.5, "1990s": 0.0, "2010s": 0.7, "contemporary": 1.2,
        "future+2C": 2.0}


def main():
    rows = []
    for era, p in ERAS.items():
        for lat in [25, 35, 45, 55]:
            T = synthetic_temps(lat, warming=WARM[era])
            CI = ci_profile(p["ci"], solar_pen=p["solar_pen"])
            tech = dict(p_light_scale=p["p_light_scale"],
                        ac_prevalence=p["ac_prevalence"],
                        cop_cool=3.0, cop_heat=2.5,
                        heat_electric_share=p["heat_electric_share"])
            st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
            dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI)
            rows.append(dict(era=era, lat=lat,
                             dE_pct=100*(dst["metrics"]["E_annual"]
                                        - st["metrics"]["E_annual"])
                                   / st["metrics"]["E_annual"],
                             dC_pct=100*(dst["metrics"]["C_annual"]
                                        - st["metrics"]["C_annual"])
                                   / st["metrics"]["C_annual"],
                             light_share_ST=st["metrics"]["E_light"]
                                           / st["metrics"]["E_annual"],
                             cool_share_ST=st["metrics"]["E_cool"]
                                          / st["metrics"]["E_annual"]))
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/historical.csv", index=False)

    # warming reversal threshold T*: dE_DST(w) = 0 for contemporary tech
    rows = []
    for lat in [20, 25, 30, 35, 40, 45, 50]:
        for ac in [0.25, 0.5, 0.75, 1.0]:
            tech = dict(p_light_scale=0.55, ac_prevalence=ac, cop_cool=3.0,
                        cop_heat=2.5, heat_electric_share=0.5)
            ws = np.arange(0, 4.01, 0.25)
            dE = []
            for w in ws:
                T = synthetic_temps(lat, warming=w)
                CI = ci_profile("solar_duck")
                st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
                dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI)
                dE.append(100*(dst["metrics"]["E_annual"]
                               - st["metrics"]["E_annual"])
                          / st["metrics"]["E_annual"])
            dE = np.array(dE)
            crossing = np.where(np.diff(np.sign(dE)) != 0)[0]
            tstar = float(ws[crossing[0]]) if len(crossing) else np.nan
            rows.append(dict(lat=lat, ac_prevalence=ac,
                             T_star_energy=tstar,
                             dE_at_w0=dE[0], dE_at_w4=dE[-1]))
    rdf = pd.DataFrame(rows)
    rdf.to_csv(f"{OUT}/reversal_thresholds.csv", index=False)
    print(df.pivot_table(index="era", columns="lat", values="dE_pct").round(2))
    print(rdf.head(12).round(2))


if __name__ == "__main__":
    main()
