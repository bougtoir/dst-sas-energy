"""Phase B: physical-unit calibration and legacy-vs-physical comparison."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.solar.solar import hourly_daylight
from src.energy.simulate import simulate_regime
from src.energy import physical as ph
from src.optimization import sas as O


def tech_dict(ps=0.6, ac=0.87, hs=0.35, coc=3.0, coh=2.5):
    return dict(p_light_scale=ps, ac_prevalence=ac, cop_cool=coc,
                cop_heat=coh, heat_electric_share=hs)


def run():
    cal = ph.calibrate()
    k = cal["kwh_per_unit"]
    pd.DataFrame([
        dict(component=c, model_share=cal["model_shares"][c],
             benchmark_share=cal["benchmark_shares"][c])
        for c in ["light", "cool", "heat", "other"]
    ]).to_csv("analysis/physical_unit_calibration.csv", index=False)

    out = []
    CI = ci_profile("solar_duck")
    for lat in [25, 35, 45, 55]:
        T = synthetic_temps(lat, warming=1.2)
        tech = tech_dict()
        darkness = 1.0 - hourly_daylight(lat)
        st = simulate_regime(lat, T, "ST", tech=tech, CI=CI)
        dst = simulate_regime(lat, T, "DST", tech=tech, CI=CI)
        J = O.daily_objective(lat, T, darkness, tech, CI, "degree_hour",
                              "energy_morning", lambda_dark=3.0)
        ts = O.sas_tstart_daily(J, max_shift=2.0)
        sas = simulate_regime(lat, T, ts, tech=tech, CI=CI)
        for name, (a, b) in [("DST-ST", (dst, st)), ("SAS-ST", (sas, st))]:
            dE = a["metrics"]["E_annual"] - b["metrics"]["E_annual"]
            dC = a["metrics"]["C_annual"] - b["metrics"]["C_annual"]
            out.append(dict(lat=lat, contrast=name,
                            dE_pct=100 * dE / b["metrics"]["E_annual"],
                            dE_kwh_per_hh=dE * k,
                            dC_kgco2_per_hh=dC * k,
                            baseline_kwh_per_hh=b["metrics"]["E_annual"] * k))
    pd.DataFrame(out).to_csv("analysis/legacy_vs_physical_model.csv",
                             index=False)
    with open("qc/PHYSICAL_UNITS_AUDIT.md", "w") as f:
        f.write(f"""# Physical units audit (Phase B)

Model energy units are internally consistent; Phase B supplements them
with physical units via one calibration constant.

## Calibration
- Anchor: EIA RECS 2020 mean US household site electricity
  {ph.RECS_TOTAL_KWH:.0f} kWh/household-yr at US-reference config
  (lat {ph.REF['lat']}N, AC {ph.REF['ac_prevalence']}, lighting scale
  {ph.REF['p_light_scale']}, electric heat share
  {ph.REF['heat_electric_share']}, warming +{ph.REF['warming']} C).
- Scale factor: 1 model unit = {k:.1f} kWh/household-yr.
- End-use shares vs RECS anchors: analysis/physical_unit_calibration.csv.
  Shares are plausibility checks only — the model covers schedule-linked
  end uses and is not calibrated component-by-component.

## Interpretation rule
Percent contrasts are primary (unit-invariant). kWh/household-yr and
kgCO2e/household-yr are calibrated magnitudes for interpretation, not
metered forecasts; they inherit the anchor's uncertainty.
Carbon: CI in kgCO2/kWh, so dC* k = kgCO2e directly.
""")
    print("k =", round(k, 1), "shares:",
          {c: round(v, 3) for c, v in cal["model_shares"].items()})


if __name__ == "__main__":
    run()
