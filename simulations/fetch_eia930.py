"""Phase E: fetch EIA-930 hourly net generation by fuel type for
contrasting US balancing authorities, persist raw pages + ledger, and
compute hourly average carbon intensity profiles.

Output:
  data/raw/eia930/<BA>_<start>_<end>_p<NN>.json   (raw pages)
  data/raw/ACQUISITION_LEDGER.csv                 (appended rows)
  analysis/empirical_grid_ci_results.csv          (hour-of-day CI by BA)
  analysis/energy_vs_carbon_optima.csv            (E/C optima divergence)
"""
import sys, os, json, time, hashlib, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
import urllib.request

KEY = os.environ["EIA_API_KEY"]
BAS = {"CISO": "solar-heavy", "NYIS": "mixed", "PJM": "fossil-heavy"}
# EIA-930 `period` is UTC; convert to each BA's local clock time so the
# hour-of-day CI profile aligns with the solar/schedule axis.
TZ = {"CISO": "America/Los_Angeles", "NYIS": "America/New_York",
      "PJM": "America/New_York"}
START, END = "2024-01-01T00", "2025-01-01T00"
# emission factors kgCO2/MWh (IPCC/EIA standard combustion)
EF = {"COL": 1000.0, "NG": 490.0, "OIL": 750.0,
      "NUC": 0.0, "SUN": 0.0, "WND": 0.0, "WAT": 0.0,
      "OTH": 400.0, "UNK": 400.0}
RAW = "data/raw/eia930"
os.makedirs(RAW, exist_ok=True)
LEDGER = "data/raw/ACQUISITION_LEDGER.csv"


def fetch_ba(ba):
    rows = []
    offset, page = 0, 0
    while True:
        url = ("https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
               f"?api_key={KEY}&facets%5Brespondent%5D%5B%5D={ba}"
               f"&start={START}&end={END}&data%5B%5D=value"
               f"&offset={offset}&length=5000")
        with urllib.request.urlopen(url, timeout=120) as r:
            body = r.read()
        path = f"{RAW}/{ba}_{START[:10]}_{END[:10]}_p{page:02d}.json"
        with open(path, "wb") as f:
            f.write(body)
        # ledger
        sha = hashlib.sha256(body).hexdigest()
        led = pd.DataFrame([dict(
            source="EIA-930 fuel-type-data", identifier=f"{ba}/{page}",
            url=url.replace(KEY, "<KEY>"), acquired_utc=datetime.datetime
                .utcnow().isoformat() + "Z",
            path=path, bytes=len(body), sha256=sha,
            license="US government public domain (EIA)")])
        led.to_csv(LEDGER, mode="a", header=not os.path.exists(LEDGER),
                   index=False)
        data = json.loads(body)["response"]["data"]
        rows.extend(data)
        if len(data) < 5000:
            break
        offset += 5000
        page += 1
        time.sleep(1)
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    local = pd.to_datetime(df["period"], utc=True).dt.tz_convert(TZ[ba])
    df["hour"] = local.dt.hour
    df["ef"] = df["fueltype"].map(EF).fillna(0)
    piv = df.pivot_table(index=["period", "hour"], columns="fueltype",
                         values="value", aggfunc="sum").fillna(0)
    emis = sum(piv.get(ft, 0) * ef for ft, ef in EF.items()
               if ft in piv.columns)
    gen = piv.sum(axis=1).clip(lower=1)
    ci = (emis / gen) / 1000.0  # kgCO2/kWh
    out = ci.groupby(level="hour").mean().reindex(range(24)).bfill()
    return out, df


def run():
    ci_profiles = {}
    for ba, tag in BAS.items():
        ci24, df = fetch_ba(ba)
        ci_profiles[ba] = ci24.values
        print(ba, tag, "rows", len(df),
              "CI range", round(ci24.min(), 3), "-", round(ci24.max(), 3))
    pd.DataFrame({ba: prof for ba, prof in ci_profiles.items()},
                 index=pd.Index(range(24), name="hour")).to_csv(
        "analysis/empirical_grid_ci_results.csv")

    # recompute energy vs carbon optima at matching latitudes
    from src.climate.synthetic import synthetic_temps
    from src.solar.solar import hourly_daylight
    from src.energy.simulate import simulate_regime
    from src.optimization import sas as O
    lats = {"CISO": 38, "NYIS": 42, "PJM": 40}
    tech = dict(p_light_scale=0.6, ac_prevalence=0.85,
                heat_electric_share=0.4, cop_cool=3.0, cop_heat=2.5)
    rows = []
    for ba, lat in lats.items():
        CI24 = np.tile(ci_profiles[ba], (365, 1))
        T = synthetic_temps(lat, warming=1.2)
        darkness = 1.0 - hourly_daylight(lat)
        st = simulate_regime(lat, T, "ST", tech=tech, CI=CI24)
        dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI24)
        Je = O.daily_objective(lat, T, darkness, tech, CI24,
                               "degree_hour", "energy")
        Jc = O.daily_objective(lat, T, darkness, tech, CI24,
                               "degree_hour", "carbon")
        tse = O.sas_tstart_daily(Je, max_shift=2.0)
        tsc = O.sas_tstart_daily(Jc, max_shift=2.0)
        sase = simulate_regime(lat, T, tse, tech=tech, CI=CI24)
        sasc = simulate_regime(lat, T, tsc, tech=tech, CI=CI24)
        div = float(np.mean(np.abs(tse - tsc)))
        rows.append(dict(
            ba=ba, lat=lat,
            ci_annual_mean=float(np.mean(ci_profiles[ba])),
            dE_dst_pct=100 * (dst["metrics"]["E_annual"] - st["metrics"]["E_annual"]) / st["metrics"]["E_annual"],
            dC_dst_pct=100 * (dst["metrics"]["C_annual"] - st["metrics"]["C_annual"]) / st["metrics"]["C_annual"],
            dE_sasE_pct=100 * (sase["metrics"]["E_annual"] - st["metrics"]["E_annual"]) / st["metrics"]["E_annual"],
            dC_sasC_pct=100 * (sasc["metrics"]["C_annual"] - st["metrics"]["C_annual"]) / st["metrics"]["C_annual"],
            C_sasE_minus_sasC=(sase["metrics"]["C_annual"] - sasc["metrics"]["C_annual"]) / st["metrics"]["C_annual"] * 100,
            mean_abs_tstart_divergence=div))
    pd.DataFrame(rows).to_csv("analysis/energy_vs_carbon_optima.csv",
                              index=False)
    print(pd.DataFrame(rows).round(3))


if __name__ == "__main__":
    run()
