"""Phase 6: representative-location analysis with empirical Open-Meteo weather
(ERA5-based reanalysis, CC-BY) + synthetic fallback where fetch fails.

Cities span latitude/climate/hemispheres. Outputs:
  analysis/geography.csv, data/raw/openmeteo/*.json + ACQUISITION_LEDGER.csv
"""
import sys, os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.climate.synthetic import synthetic_temps
from src.climate.openmeteo import fetch_hourly
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime
from src.optimization import sas as O
from src.solar.solar import hourly_daylight

OUT = os.path.join(os.path.dirname(__file__), "..", "analysis")

CITIES = [
    # name, lat, lon (approx), tz, hemisphere, climate label, ac_prev proxy
    ("Singapore", 1.35, 103.8, 8, "N", "equatorial", 0.8),
    ("Miami", 25.8, -80.2, -5, "N", "subtropical humid", 0.95),
    ("Sydney", -33.9, 151.2, 10, "S", "temperate maritime", 0.6),
    ("Tokyo", 35.7, 139.7, 9, "N", "humid subtropical", 0.9),
    ("Phoenix", 33.4, -112.1, -7, "N", "hot arid", 0.95),
    ("Berlin", 52.5, 13.4, 1, "N", "temperate continental", 0.15),
    ("Oslo", 59.9, 10.7, 1, "N", "cold maritime", 0.05),
    ("Santiago", -33.5, -70.7, -4, "S", "mediterranean", 0.3),
    ("London", 51.5, -0.1, 0, "N", "temperate maritime", 0.2),
    ("Moscow", 55.8, 37.6, 3, "N", "continental", 0.15),
]


def main():
    rows = []
    for name, lat, lon, tz, hemi, clim, ac in CITIES:
        try:
            T = fetch_hourly(lat, lon)
            if T.shape != (365, 24):
                raise ValueError(T.shape)
            src = "openmeteo-2023"
        except Exception as e:
            print(name, "fetch failed:", e)
            T = synthetic_temps(lat)
            src = "synthetic-fallback"
        CI = ci_profile("solar_duck")
        tech = dict(p_light_scale=0.55, ac_prevalence=ac, cop_cool=3.0,
                    cop_heat=2.5, heat_electric_share=0.5)
        st = simulate_regime(lat, T, "ST", tech=tech, CI=CI,
                             lon_deg=lon, tz_offset=tz)
        dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI,
                              lon_deg=lon, tz_offset=tz, hemisphere=hemi)
        dark = 1 - hourly_daylight(lat, lon, tz)
        J = O.daily_objective(lat, T, dark, tech, CI, "degree_hour",
                              "energy")
        ts = O.sas_tstart_daily(J, max_shift=2.0)
        sas = simulate_regime(lat, T, t_start_arr=ts, tech=tech, CI=CI,
                              lon_deg=lon, tz_offset=tz)
        for reg, r in [("ST", st), ("DST", dst), ("SAS_daily_2h", sas)]:
            m = r["metrics"]
            rows.append(dict(city=name, lat=lat, climate=clim,
                             ac_prevalence=ac, source=src, regime=reg,
                             E_annual=m["E_annual"], C_annual=m["C_annual"],
                             dE_pct=100*(m["E_annual"]-st["metrics"]["E_annual"])/st["metrics"]["E_annual"],
                             dC_pct=100*(m["C_annual"]-st["metrics"]["C_annual"])/st["metrics"]["C_annual"],
                             peak=m["peak_annual"], par=m["par"],
                             wake_dark=m["wake_dark"]))
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/geography.csv", index=False)
    print(df.pivot_table(index="city", columns="regime",
                         values="dE_pct").round(2))


if __name__ == "__main__":
    main()
