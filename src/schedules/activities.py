"""Activity schedules under ST / DST / SAS.

A schedule is defined by a work-block start time t_start (local civil hour)
for the schedule-following fraction of the population. From t_start we derive:
  wake      = t_start - 2  (commute+morning routine)
  work      = [t_start, t_start+8)
  sleep     = [t_start+15, t_start+23) i.e. 23:00 -> 7:00 when t_start=9
Profiles (365,24) give the fraction of the schedule-following population in
each state per civil hour. A heterogeneous split of the population into
segments with different t_start is supported via `segments`.

Elasticity: `elasticity` in [0,1] is the fraction of each flexible load that
follows the schedule shift; (1-elasticity) stays fixed at the ST schedule.
"""
import numpy as np

HOURS = np.arange(24)


def _block(hour, lo, hi):
    h = hour % 24
    lo, hi = lo % 24, hi % 24
    if lo <= hi:
        return (h >= lo) & (h < hi)
    return (h >= lo) | (h < hi)


def profiles_for_tstart(t_start):
    """Return dict of (24,) profiles: work, home, sleep, evening."""
    work = _block(HOURS, t_start, t_start + 8).astype(float)
    # taper first/last work hour (commute)
    home = 1.0 - work
    home -= 0.3 * (_block(HOURS, t_start - 1, t_start).astype(float)
                   + _block(HOURS, t_start + 8, t_start + 9).astype(float))
    home = np.clip(home, 0, 1)
    sleep = _block(HOURS, t_start + 15, t_start + 23).astype(float)
    evening = _block(HOURS, t_start + 9, t_start + 13).astype(float) * 0.7
    evening += _block(HOURS, t_start + 13, t_start + 14).astype(float) * 0.4
    wake = _block(HOURS, t_start - 2, t_start - 1).astype(float)
    return dict(work=work, home=np.clip(home, 0, 1), sleep=sleep,
                evening=np.clip(evening, 0, 1), wake=wake)


def schedule_profiles(t_start, elasticity=1.0, base_tstart=9.0):
    """Blend shifted and fixed profiles by elasticity."""
    shifted = profiles_for_tstart(t_start)
    if elasticity >= 1.0:
        return shifted
    fixed = profiles_for_tstart(base_tstart)
    return {k: elasticity * shifted[k] + (1 - elasticity) * fixed[k]
            for k in shifted}


def daily_schedule_year(t_start_by_day):
    """(365,) t_start -> dict of (365,24) profiles."""
    out = {k: np.zeros((365, 24)) for k in
           ["work", "home", "sleep", "evening", "wake"]}
    for d in range(365):
        p = profiles_for_tstart(float(t_start_by_day[d]))
        for k in out:
            out[k][d] = p[k]
    return out


def dst_clock_shift(doy, hemisphere="N", dst_start=None, dst_end=None):
    """Hours of DST clock shift on day-of-year. Default: Apr 1 - Oct 31 (N),
    Oct 1 - Mar 31 (S stylized)."""
    if dst_start is None:
        dst_start, dst_end = (91, 304) if hemisphere == "N" else (274, 90)
    if dst_start < dst_end:
        return 1.0 if dst_start <= doy <= dst_end else 0.0
    return 1.0 if (doy >= dst_start or doy <= dst_end) else 0.0


def t_start_year(regime, lat_deg=40.0, doy=None, hemisphere="N",
                 base_tstart=9.0, sas_rule=None):
    """(365,) t_start per day for a regime.

    regime: 'ST' | 'DST' | array-like (SAS precomputed t_start per day)
    sas_rule: callable(doy, lat) -> t_start, used when regime == 'SAS'
    """
    if doy is None:
        doy = np.arange(1, 366)
    if isinstance(regime, str):
        if regime == "ST":
            return np.full(len(doy), base_tstart)
        if regime == "DST":
            shift = np.array([dst_clock_shift(int(d), hemisphere) for d in doy])
            # displayed schedule fixed at base_tstart -> solar-relative
            # schedule shifts earlier by 1h in standard-time coordinates
            return np.full(len(doy), base_tstart) - shift
        if regime == "SAS":
            return np.array([sas_rule(int(d), lat_deg) for d in doy], dtype=float)
        raise ValueError(regime)
    arr = np.asarray(regime, dtype=float)
    assert arr.shape == (len(doy),)
    return arr


DEFAULT_SEGMENTS = [
    # name, population share, base t_start, elasticity (schedule flexibility)
    ("daytime_workers", 0.45, 9.0, 1.0),
    ("students", 0.15, 8.5, 1.0),
    ("remote_workers", 0.10, 9.0, 1.0),
    ("shift_workers", 0.10, 9.0, 0.0),    # fixed shifts
    ("nonworking", 0.20, 10.0, 0.5),      # partial flexibility
]
