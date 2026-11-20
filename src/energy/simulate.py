"""Simulation engine: location x regime x tech x climate -> hourly outcomes."""
import numpy as np
from src.solar.solar import hourly_daylight
from src.schedules.activities import (daily_schedule_year, t_start_year,
                                      schedule_profiles, DEFAULT_SEGMENTS)
from src.energy.model import total_energy
from src.carbon.grid import carbon, ci_profile

DOY = np.arange(1, 366)


def _profiles_for_tstart_array(t_start_arr, elasticity=1.0, base=9.0):
    out = {k: np.zeros((365, 24)) for k in ["work", "home", "sleep", "evening", "wake"]}
    arr = np.asarray(t_start_arr, dtype=float)
    for val in np.unique(arr):
        p = schedule_profiles(float(val), elasticity=elasticity,
                              base_tstart=base)
        idx = arr == val
        for k in out:
            out[k][idx] = p[k]
    return out


def simulate_regime(lat_deg, T_out, regime="ST", t_start_arr=None,
                    tech=None, CI=None, thermal_model="degree_hour",
                    segments=DEFAULT_SEGMENTS, hemisphere=None,
                    base_tstart=9.0, lon_deg=0.0, tz_offset=0.0):
    """Simulate one regime for one location-year.

    Returns dict with hourly components (365,24), scalar metrics.
    Darkness is computed in TRUE solar geometry (independent of clocks);
    schedule profiles are placed on the civil clock (ST: fixed; DST: civil
    clock shifted +1 -> schedules effectively 1h earlier in standard-time
    coordinates; SAS: t_start array in standard time).
    """
    tech = dict(tech or {})
    if hemisphere is None:
        hemisphere = "N" if lat_deg >= 0 else "S"
    if CI is None:
        CI = ci_profile("solar_duck")
    daylight = hourly_daylight(lat_deg, lon_deg, tz_offset)
    darkness = 1.0 - daylight

    if t_start_arr is None:
        t_start_arr = t_start_year(regime, lat_deg, DOY, hemisphere,
                                   base_tstart)

    comp_sum = None
    wake_prof = np.zeros((365, 24))
    eve_prof = np.zeros((365, 24))
    for name, share, seg_base, elast in segments:
        seg_t = np.where(np.isclose(t_start_arr, base_tstart),
                         t_start_arr + (seg_base - base_tstart),
                         t_start_arr + (seg_base - base_tstart))
        prof = _profiles_for_tstart_array(seg_t, elasticity=elast,
                                          base=seg_base)
        comp = total_energy(darkness, T_out, prof, tech, thermal_model)
        wake_prof += share * prof["wake"]
        eve_prof += share * prof["evening"]
        for k in comp:
            comp[k] = comp[k] * share
        if comp_sum is None:
            comp_sum = comp
        else:
            for k in comp_sum:
                comp_sum[k] += comp[k]

    E = comp_sum["total"]
    C = carbon(E, CI)
    metrics = load_metrics(E, C)
    metrics.update(_timing_metrics(darkness, wake_prof, eve_prof,
                                   t_start_arr, base_tstart))
    metrics["E_annual"] = float(E.sum())
    metrics["C_annual"] = float(C.sum())
    metrics["E_light"] = float(comp_sum["light"].sum())
    metrics["E_cool"] = float(comp_sum["cool"].sum())
    metrics["E_heat"] = float(comp_sum["heat"].sum())
    metrics["E_other"] = float(comp_sum["other"].sum())
    return dict(components=comp_sum, C=C, CI=CI, darkness=darkness,
              t_start=t_start_arr, metrics=metrics)


def _timing_metrics(darkness, wake_prof, eve_prof, t_start_arr, base_tstart):
    """Circadian/disruption proxies.

    wake_dark: population-weighted mean darkness during the wake hour.
    eve_light: population-weighted mean darkness during evening leisure
    (higher = more evening activity in darkness).
    Also schedule-disruption metrics from the t_start trajectory.
    """
    wake_dark = float((darkness * wake_prof).sum()
                      / np.maximum(wake_prof.sum(), 1e-9))
    eve_dark = float((darkness * eve_prof).sum()
                     / np.maximum(eve_prof.sum(), 1e-9))
    arr = np.asarray(t_start_arr, dtype=float)
    return dict(
        wake_dark=wake_dark,
        evening_dark=eve_dark,
        n_changes=int(np.sum(np.abs(np.diff(arr)) > 1e-9)),
        mean_abs_shift=float(np.mean(np.abs(arr - base_tstart))),
        max_abs_shift=float(np.max(np.abs(arr - base_tstart))),
    )


def load_metrics(E, C):
    """Peak/flexibility metrics on hourly load (365,24)."""
    flat = E.ravel()
    daily_peak = E.max(axis=1)
    return dict(
        peak_annual=float(flat.max()),
        peak_summer=float(E[151:273].max()),   # Jun-Sep approx
        peak_winter=float(np.concatenate([E[:59], E[334:]]).max()),
        p95=float(np.percentile(flat, 95)),
        p99=float(np.percentile(flat, 99)),
        par=float(flat.max() / flat.mean()),
        peak_hour=int(np.argmax(flat) % 24),
        peak_doy=int(np.argmax(flat) // 24 + 1),
        mean_daily_peak=float(daily_peak.mean()),
        ramp_max=float(np.abs(np.diff(E, axis=1)).max()),
        ramp_mean_p95=float(np.percentile(np.abs(np.diff(E, axis=1)), 95)),
        morning_ramp_mean=float(np.abs(np.diff(E[:, 5:11], axis=1)).mean()),
        evening_ramp_mean=float(np.abs(np.diff(E[:, 16:22], axis=1)).mean()),
    )
