"""Generate LaTeX-style + CSV tables and the manuscript-values registry.

Every number used in the manuscript is written to
analysis/manuscript_values.csv with its source script/file.
"""
import sys, os
import numpy as np
import pandas as pd

A = os.path.dirname(__file__)
T = os.path.join(A, "..", "tables")
os.makedirs(T, exist_ok=True)
REG = []


def reg(key, value, source, note=""):
    REG.append(dict(key=key, value=value, source=source, note=note))


def main():
    d = pd.read_csv(f"{A}/dst_sweep.csv")
    rc = pd.read_csv(f"{A}/regime_comparison.csv")
    ret = pd.read_csv(f"{A}/discrete_sas_efficiency_retention.csv")
    geo = pd.read_csv(f"{A}/geography.csv")
    hist = pd.read_csv(f"{A}/historical.csv")
    par = pd.read_csv(f"{A}/pareto_frontier.csv")
    th = pd.read_csv(f"{A}/thermal_model_sensitivity.csv")
    rev = pd.read_csv(f"{A}/reversal_thresholds.csv")
    lsm = pd.read_csv(f"{A}/load_shape_metrics.csv")

    # headline values
    e = d[(d.lighting == "led") & (d.ac_prevalence == 0.5)]
    g = e.groupby("lat").dE_DST_pct.mean()
    reg("dst_dE_pct_lat20", g.loc[20], "dst_sweep.csv")
    reg("dst_dE_pct_lat40", g.loc[40], "dst_sweep.csv")
    reg("dst_dE_pct_lat60", g.loc[60], "dst_sweep.csv")
    reg("dst_dE_pct_mean", g.mean(), "dst_sweep.csv",
        "mean over lats, warming, LED, ac=0.5")
    reg("sweep_dE_min", d.dE_DST_pct.min(), "dst_sweep.csv",
        "min over 625 synthetic cells")
    reg("sweep_dE_max", d.dE_DST_pct.max(), "dst_sweep.csv",
        "max over 625 synthetic cells")
    base = rc[(rc.warming == 0) & (rc.ac_prevalence == 0.75)]
    g2 = base.groupby("regime").dE_pct.mean()
    for r in ["DST", "SAS_daily_energy", "SAS_monthly_energy",
              "SAS_daily_carbon"]:
        reg(f"dE_{r}_mean", g2.get(r, np.nan), "regime_comparison.csv",
            "mean over lats, warming=0, ac=0.75")
    retm = ret[ret.objective == "morning"]
    reg("sas_monthly_retention", retm[retm.variant == "monthly"].retention.mean(),
        "discrete_sas_efficiency_retention.csv")
    reg("sas_seasonal_retention",
        retm[retm.variant == "seasonal"].retention.mean(),
        "discrete_sas_efficiency_retention.csv")
    reg("sas_threshold_retention",
        retm[retm.variant == "threshold"].retention.mean(),
        "discrete_sas_efficiency_retention.csv")
    gp = geo.pivot_table(index="city", columns="regime", values="dE_pct")
    reg("geo_dst_min", gp["DST"].min(), "geography.csv")
    reg("geo_dst_max", gp["DST"].max(), "geography.csv")
    reg("geo_sas_mean", gp["SAS_daily_2h"].mean(), "geography.csv")
    reg("geo_sas_min", gp["SAS_daily_2h"].min(), "geography.csv")
    reg("geo_sas_max", gp["SAS_daily_2h"].max(), "geography.csv")
    reg("hist_dE_1970s_lat45", hist[(hist.era == "1970s") & (hist.lat == 45)]
        .dE_pct.iloc[0], "historical.csv")
    reg("hist_dE_contemp_lat45", hist[(hist.era == "contemporary")
        & (hist.lat == 45)].dE_pct.iloc[0], "historical.csv")
    reg("hist_dE_future_lat45", hist[(hist.era == "future+2C")
        & (hist.lat == 45)].dE_pct.iloc[0], "historical.csv")
    reg("rev_Tstar_nonNaN_frac",
        rev.T_star_energy.notna().mean(), "reversal_thresholds.csv")
    reg("thermal_sign_preserved", int((
        np.sign(th[th.model == "rc"].dE_DST_pct.values) ==
        np.sign(th[th.model == "degree_hour"].dE_DST_pct.values)).all()),
        "thermal_model_sensitivity.csv")
    if os.path.exists(f"{A}/monte_carlo.csv"):
        mc = pd.read_csv(f"{A}/monte_carlo.csv")
        for col, lab in [("E", "energy"), ("C", "carbon")]:
            reg(f"mc_P_DST_better_{lab}",
                (mc[f"{col}_DST"] < mc[f"{col}_ST"]).mean(), "monte_carlo.csv")
            reg(f"mc_P_SAS_better_{lab}",
                (mc[f"{col}_SAS"] < mc[f"{col}_ST"]).mean(), "monte_carlo.csv")
            reg(f"mc_P_SAS_better_DST_{lab}",
                (mc[f"{col}_SAS"] < mc[f"{col}_DST"]).mean(), "monte_carlo.csv")
            dd = 100 * (mc[f"{col}_DST"] - mc[f"{col}_ST"]) / mc[f"{col}_ST"]
            ds = 100 * (mc[f"{col}_SAS"] - mc[f"{col}_ST"]) / mc[f"{col}_ST"]
            reg(f"mc_dDST_{lab}_median", dd.median(), "monte_carlo.csv")
            reg(f"mc_dDST_{lab}_q025", dd.quantile(0.025), "monte_carlo.csv")
            reg(f"mc_dDST_{lab}_q975", dd.quantile(0.975), "monte_carlo.csv")
            reg(f"mc_dSAS_{lab}_median", ds.median(), "monte_carlo.csv")
            reg(f"mc_dSAS_{lab}_q025", ds.quantile(0.025), "monte_carlo.csv")
            reg(f"mc_dSAS_{lab}_q975", ds.quantile(0.975), "monte_carlo.csv")
    # SAS optimum saturation finding
    tsr = par[par.variant == "daily"]
    reg("pareto_maxshift4_dE", tsr[tsr.max_shift == 4].dE_pct.mean(),
        "pareto_frontier.csv")
    reg("pareto_maxshift1_dE", tsr[tsr.max_shift == 1].dE_pct.mean(),
        "pareto_frontier.csv")
    reg("pareto_maxshift05_dE", tsr[tsr.max_shift == 0.5].dE_pct.mean(),
        "pareto_frontier.csv")
    reg("wake_dark_sas_4h", tsr[tsr.max_shift == 4].wake_dark.mean(),
        "pareto_frontier.csv")
    reg("wake_dark_sas_1h", tsr[tsr.max_shift == 1].wake_dark.mean(),
        "pareto_frontier.csv")

    # percent-format convenience keys for retention fractions
    # strengthening-phase keys (Phase E/F/C/K)
    try:
        evc = pd.read_csv(f"{A}/energy_vs_carbon_optima.csv")
        ciso = evc[evc.ba == "CISO"].iloc[0]
        reg("ciso_tstart_divergence_h",
            round(float(ciso.mean_abs_tstart_divergence), 2),
            "energy_vs_carbon_optima.csv")
        reg("ciso_carbon_cost_of_Eopt_pct",
            round(float(ciso.C_sasE_minus_sasC), 2),
            "energy_vs_carbon_optima.csv")
    except Exception:
        pass
    try:
        ind = pd.read_csv(f"{A}/indiana_decomposition.csv")
        reg("indiana_model_baseline_pct",
            round(float(ind.dE_res_pct.iloc[0]), 2),
            "indiana_decomposition.csv")
        reg("indiana_model_max_pct",
            round(float(ind.dE_res_pct.max()), 2),
            "indiana_decomposition.csv")
        reg("indiana_observed_pct", float(ind.observed_pct.iloc[0]),
            "indiana_decomposition.csv",
            "observed value from Kotchen & Grant 2011")
    except Exception:
        pass
    try:
        rev = pd.read_csv(f"{A}/reversal_thresholds.csv")
        tstar = rev["T_star_energy"].dropna()
        reg("rev_Tstar_min", round(float(tstar.min()), 2),
            "reversal_thresholds.csv")
        reg("rev_Tstar_max", round(float(tstar.max()), 2),
            "reversal_thresholds.csv")
        reg("rev_Tstar_count", int(len(tstar)), "reversal_thresholds.csv")
    except Exception:
        pass
    try:
        sens = pd.read_csv(f"{A}/mc_sensitivity.csv").set_index("param")
        for p in ["lat", "ac", "hshare", "light"]:
            reg(f"mc_rho_{p}", round(float(sens.loc[p, "spearman_rho"]), 2),
                "mc_sensitivity.csv")
    except Exception:
        pass
    for k in ["sas_monthly_retention","sas_seasonal_retention","sas_threshold_retention"]:
        row = [r for r in REG if r["key"] == k]
        if row:
            reg(k + "_pct", round(100 * float(row[0]["value"]), 1),
                row[0]["source"], "percent of daily-optimum benefit")
    pd.DataFrame(REG).to_csv(f"{A}/manuscript_values.csv", index=False)

    # Table 1: regime comparison
    tab = base.groupby("regime")[["dE_pct", "dC_pct"]].mean().reindex(
        ["ST", "DST", "SAS_daily_energy", "SAS_monthly_energy",
         "SAS_seasonal_energy", "SAS_threshold_energy",
         "SAS_daily_carbon"]).round(3)
    tab.to_csv(f"{T}/table1_regime_comparison.csv")
    # Table 2: peak metrics
    lsm[lsm.warming == 0].groupby("regime")[
        ["peak_annual", "par", "p95", "p99", "peak_hour"]].mean().round(3)\
        .to_csv(f"{T}/table5_load_shape.csv")
    # Table 3: geography
    gp.round(2).to_csv(f"{T}/table2_geography.csv")
    # Table 4: historical
    hist.pivot_table(index="era", columns="lat", values="dE_pct").round(2)\
        .to_csv(f"{T}/table3_historical.csv")
    # Table 5: pareto
    par.pivot_table(index=["variant", "max_shift"], values="dE_pct",
                    aggfunc="mean").round(3).to_csv(f"{T}/table4_pareto.csv")
    print("tables + registry:", len(REG), "values")


if __name__ == "__main__":
    main()
