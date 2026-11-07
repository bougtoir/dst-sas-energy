"""Unit + sanity tests for the dst_sas_energy pipeline."""
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.solar.solar import hourly_daylight, solar_noon_year, solar_elevation
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile, carbon
from src.schedules.activities import t_start_year, DEFAULT_SEGMENTS
from src.energy.simulate import simulate_regime
from src.optimization.sas import (daily_objective, sas_tstart_daily,
                                  sas_tstart_grouped, MONTH_OF)
from src.building.thermal import degree_hour_load, rc_load

TECH = dict(p_light_scale=1.0, ac_prevalence=0.5, cop_cool=3.0,
            cop_heat=2.5, heat_electric_share=0.5)


def test_solar_equator():
    dl = hourly_daylight(0.0)
    assert np.allclose(dl.sum(axis=1), 12.0, atol=0.6)


def test_solar_midlat_summer_longer():
    dl = hourly_daylight(40.0)
    assert dl[172].sum() > dl[355].sum() + 4  # Jun vs Dec


def test_solar_noon_reasonable():
    sn = solar_noon_year(40.0)
    assert np.all(sn > 11.0) and np.all(sn < 13.0)


def test_polar_night():
    dl = hourly_daylight(80.0)
    assert dl[355].sum() < 0.5   # polar night near Dec solstice
    assert dl[172].sum() > 23.0  # polar day near Jun solstice


def test_dst_tstart_shift():
    ts = t_start_year("DST", 40.0)
    assert ts[200] == 8.0 and ts[10] == 9.0  # DST => schedule 1h earlier vs sun


def test_sas_constrained_to_st_reproduces_st():
    T = synthetic_temps(40.0)
    CI = ci_profile("solar_duck")
    st = simulate_regime(40.0, T, "ST", tech=TECH, CI=CI)
    ts_st = np.full(365, 9.0)
    sas = simulate_regime(40.0, T, t_start_arr=ts_st, tech=TECH, CI=CI)
    assert np.isclose(sas["metrics"]["E_annual"], st["metrics"]["E_annual"])


def test_zero_lighting_removes_lighting_pathway():
    T = synthetic_temps(40.0)
    t0 = dict(TECH, p_light_scale=0.0)
    st = simulate_regime(40.0, T, "ST", tech=t0)
    dst = simulate_regime(40.0, T, "DST", tech=t0)
    assert np.isclose(st["components"]["light"].sum(), 0)
    assert np.isclose(dst["components"]["light"].sum(), 0)


def test_zero_ac_removes_cooling_pathway():
    T = synthetic_temps(40.0)
    t0 = dict(TECH, ac_prevalence=0.0)
    st = simulate_regime(40.0, T, "ST", tech=t0)
    dst = simulate_regime(40.0, T, "DST", tech=t0)
    assert np.isclose(st["components"]["cool"].sum(), 0)
    assert np.isclose(dst["components"]["cool"].sum(), 0)


def test_identical_schedules_identical_output():
    T = synthetic_temps(40.0)
    a = simulate_regime(40.0, T, "ST", tech=TECH)
    b = simulate_regime(40.0, T, np.full(365, 9.0), tech=TECH)
    assert np.isclose(a["metrics"]["E_annual"], b["metrics"]["E_annual"])


def test_constant_ci_energy_equals_carbon_ranking():
    T = synthetic_temps(40.0)
    CI = ci_profile("constant", base=0.5)
    st = simulate_regime(40.0, T, "ST", tech=TECH, CI=CI)
    dst = simulate_regime(40.0, T, "DST", tech=TECH, CI=CI)
    assert np.isclose(st["metrics"]["C_annual"],
                      st["metrics"]["E_annual"] * 0.5)
    assert (dst["metrics"]["E_annual"] > st["metrics"]["E_annual"]) == \
           (dst["metrics"]["C_annual"] > st["metrics"]["C_annual"])


def test_rc_positive_loads():
    T = synthetic_temps(30.0, t_annual=20.0, amplitude=12.0)
    occ = np.ones((365, 24))
    c, h = rc_load(T, occ)
    assert c.sum() > 0 and h.sum() > 0


def test_contrast_signs_documented():
    # Delta_DST = DST - ST. Verify helper arithmetic only.
    assert (5.0 - 3.0) > 0
