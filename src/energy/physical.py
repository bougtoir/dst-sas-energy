"""Physical-unit calibration: map model's internal consistent units to
kWh/household-year and kgCO2e, anchored to published benchmarks.

Anchors (documented; verify at submission):
- EIA RECS 2020: average US household site electricity ~10,791 kWh/yr.
- RECS 2020 end-use shares (approx, electricity): space cooling ~16%,
  space heating ~12% (electric portion), lighting ~6%,
  remainder "other" ~66%. We calibrate a scale factor so that model
  annual total at a US-reference config matches the benchmark total,
  and report component shares for plausibility (not forced equality).

US reference config: lat 37 N (CONUS population centroid ~37-38N),
ac_prevalence 0.87 (RECS 2020: ~90% AC), heat_electric_share 0.35
(RECS: ~40% electric space heating, some non-space electric heat),
p_light_scale 0.6 (mixed LED transition ~2023), warming 1.2.
"""
import numpy as np
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime

RECS_TOTAL_KWH = 10791.0   # kWh/household-year, EIA RECS 2020
RECS_SHARES = dict(light=0.06, cool=0.16, heat=0.12, other=0.66)

REF = dict(lat=37.0, ac_prevalence=0.87, p_light_scale=0.6,
           cop_cool=3.0, cop_heat=2.5, heat_electric_share=0.35,
           warming=1.2)


def calibrate():
    """Return dict with kwh_per_unit scale + component benchmark shares."""
    T = synthetic_temps(REF["lat"], warming=REF["warming"])
    CI = ci_profile("solar_duck")
    tech = dict(p_light_scale=REF["p_light_scale"],
                ac_prevalence=REF["ac_prevalence"], cop_cool=REF["cop_cool"],
                cop_heat=REF["cop_heat"],
                heat_electric_share=REF["heat_electric_share"])
    st = simulate_regime(REF["lat"], T, "ST", tech=tech, CI=CI)
    m = st["metrics"]
    k = RECS_TOTAL_KWH / m["E_annual"]
    shares = {c: m[f"E_{c}"] / m["E_annual"] for c in
              ["light", "cool", "heat", "other"]}
    return dict(kwh_per_unit=k, model_total=m["E_annual"],
                model_shares=shares, benchmark_shares=RECS_SHARES)


def to_kwh(units):
    cal = calibrate()
    return units * cal["kwh_per_unit"]


def to_kgco2(carbon_units, kwh_per_unit):
    """carbon_units = E_units * CI(kg/kWh consistent) -> kgCO2e."""
    return carbon_units * kwh_per_unit
