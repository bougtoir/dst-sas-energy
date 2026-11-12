"""Phase 5/K: Monte Carlo uncertainty over uncertain parameters.

10,000 draws varying lighting scale, AC prevalence, COPs, elasticity,
heat electric share, night setback, envelope conductivity, grid-carbon
shape, and latitude (scenario uncertainty included).
Outputs analysis/monte_carlo.csv and analysis/mc_sensitivity.csv
(Spearman rank correlation of each input with dE_DST%).
SAS variant = constraint-bound 2h-earlier daily schedule (t_start=7);
documented as constraint-bound. Uncertainties are model/parameter +
scenario uncertainty, NOT population probabilities.
"""
import sys, os, time
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime
from src.schedules.activities import DEFAULT_SEGMENTS
from scipy.stats import spearmanr

OUT = os.path.join(os.path.dirname(__file__), "..", "analysis")
N = 10000
SEED = 20260924


def main():
    rng = np.random.default_rng(SEED)
    t0 = time.time()

    lat = rng.uniform(25, 55, N)
    light = rng.uniform(0.2, 1.5, N)
    ac = rng.beta(3, 3, N)
    cop_c = rng.uniform(1.5, 5.0, N)
    cop_h = rng.uniform(1.0, 4.5, N)
    elast = rng.uniform(0.4, 1.0, N)
    solar_pen = rng.uniform(0.0, 0.5, N)
    hshare = rng.uniform(0.0, 0.8, N)
    nsetb = rng.uniform(0.2, 0.6, N)
    kheat = rng.uniform(0.15, 0.4, N)

    rows = []
    for i in range(N):
        T = synthetic_temps(lat[i], warming=2)
        tech = dict(p_light_scale=light[i], ac_prevalence=ac[i],
                    cop_cool=cop_c[i], cop_heat=cop_h[i],
                    heat_electric_share=hshare[i],
                    night_setback=nsetb[i], k_heat=kheat[i])
        CI = ci_profile("solar_duck", solar_pen=float(solar_pen[i]))
        segs = [(n, s, b, elast[i] if e > 0 else 0.0)
                for (n, s, b, e) in DEFAULT_SEGMENTS]
        st = simulate_regime(lat[i], T, "ST", tech=tech, CI=CI,
                             segments=segs)
        dst = simulate_regime(lat[i], T, "DST", tech=tech, CI=CI,
                              segments=segs)
        sas2 = simulate_regime(lat[i], T, np.full(365, 7.0), tech=tech,
                               CI=CI, segments=segs)
        rows.append(dict(
            lat=lat[i], light=light[i], ac=ac[i], cop_c=cop_c[i],
            cop_h=cop_h[i], elast=elast[i], solar_pen=solar_pen[i],
            hshare=hshare[i], nsetb=nsetb[i], kheat=kheat[i],
            E_ST=st["metrics"]["E_annual"], E_DST=dst["metrics"]["E_annual"],
            E_SAS=sas2["metrics"]["E_annual"],
            C_ST=st["metrics"]["C_annual"], C_DST=dst["metrics"]["C_annual"],
            C_SAS=sas2["metrics"]["C_annual"]))
        if i % 2000 == 0:
            print(i, f"{time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/monte_carlo.csv", index=False)

    d_dst = 100 * (df["E_DST"] - df["E_ST"]) / df["E_ST"]
    params = ["lat", "light", "ac", "cop_c", "cop_h", "elast",
              "solar_pen", "hshare", "nsetb", "kheat"]
    sens = pd.DataFrame([dict(param=p,
                              spearman_rho=spearmanr(df[p], d_dst).statistic)
                         for p in params]).sort_values(
        "spearman_rho", key=abs, ascending=False)
    sens.to_csv(f"{OUT}/mc_sensitivity.csv", index=False)
    print(sens.round(3))

    for col in ["E", "C"]:
        d_dst = 100 * (df[f"{col}_DST"] - df[f"{col}_ST"]) / df[f"{col}_ST"]
        d_sas = 100 * (df[f"{col}_SAS"] - df[f"{col}_ST"]) / df[f"{col}_ST"]
        print(col,
              "P(DST<ST)=%.3f" % (df[f"{col}_DST"] < df[f"{col}_ST"]).mean(),
              "P(SAS<ST)=%.3f" % (df[f"{col}_SAS"] < df[f"{col}_ST"]).mean(),
              "P(SAS<DST)=%.3f" % (df[f"{col}_SAS"] < df[f"{col}_DST"]).mean(),
              "median dDST%%=%.2f [%.2f,%.2f]" % (d_dst.median(),
                  d_dst.quantile(0.025), d_dst.quantile(0.975)),
              "median dSAS%%=%.2f [%.2f,%.2f]" % (d_sas.median(),
                  d_sas.quantile(0.025), d_sas.quantile(0.975)))


if __name__ == "__main__":
    main()
