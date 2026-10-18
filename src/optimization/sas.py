"""Solar-Adaptive Scheduling (SAS) optimizer.

For each day, choose work-block t_start minimizing a selected component
objective (energy or carbon), subject to:
  - |t_start - base| <= max_shift
  - t_start on a grid (e.g. 0.25h)
Discrete implementations:
  C1 daily: per-day optimum
  C2 monthly: single t_start per calendar month minimizing monthly total
  C3 seasonal: per fixed seasons (DJF/MAM/JJA/SON)
  C4 threshold: adopt daily optimum only where improvement over ST exceeds
     `threshold` fraction; elsewhere ST.
Efficiency retention = realized benefit / daily-continuous benefit.
"""
import numpy as np
from src.energy.simulate import simulate_regime

GRID = np.arange(5.0, 13.01, 0.25)
DOY = np.arange(1, 366)
MONTH_OF = np.array([int(d) for d in
    np.floor((np.arange(365) ) / 30.437)])  # approx month index 0..11
MONTH_OF = np.clip(MONTH_OF, 0, 11)
SEASON_OF = ((np.arange(365) + 10) // 91) % 4  # rough seasons


def _evaluate_day(args):
    """Helper: simulate one t_start value for one day is too expensive via
    full-year sims; instead evaluate objective per (day, t_start) by
    vectorized single-day simulation."""
    raise NotImplementedError


def daily_objective(lat_deg, T_out, darkness, tech, CI, thermal_model,
                    objective="energy", segments=None, base_tstart=9.0,
                    grid=GRID, **kwargs):
    """Compute objective value J(d, t) for each day d and t_start in grid.

    Returns (365, len(grid)) array. Uses the same energy pipeline restricted
    to one day (day loop inside simulate_day)."""
    from src.energy.model import total_energy
    from src.schedules.activities import schedule_profiles, DEFAULT_SEGMENTS
    segments = segments or DEFAULT_SEGMENTS
    ng = len(grid)
    J = np.zeros((365, ng))
    for gi, t0 in enumerate(grid):
        E_tot = np.zeros((365, 24))
        for name, share, seg_base, elast in segments:
            p = schedule_profiles(t0 + (seg_base - base_tstart),
                                  elasticity=elast, base_tstart=seg_base)
            prof_day = {k: np.tile(p[k], (365, 1)) for k in p}
            comp = total_energy(darkness, T_out, prof_day, tech, thermal_model)
            E_tot += share * comp["total"]
        if objective == "energy":
            J[:, gi] = E_tot.sum(axis=1)
        elif objective == "carbon":
            J[:, gi] = (E_tot * CI).sum(axis=1)
        elif objective == "energy_morning":
            # energy + penalty on wake/commute darkness (circadian proxy);
            # lambda_dark converts darkness-hour exposure to energy units
            lam = kwargs.get("lambda_dark", 2.0)
            wh = np.clip(np.round(t0 - 2).astype(int), 0, 23)
            wh2 = np.clip(np.round(t0 - 1).astype(int), 0, 23)
            pen = darkness[:, wh] + darkness[:, wh2]
            J[:, gi] = E_tot.sum(axis=1) + lam * pen
        else:
            raise ValueError(objective)
    return J


def sas_tstart_daily(J, base_tstart=9.0, grid=GRID, max_shift=np.inf):
    allowed = np.abs(grid - base_tstart) <= max_shift
    Jm = np.where(allowed[None, :], J, np.inf)
    return grid[np.argmin(Jm, axis=1)]


def sas_tstart_grouped(J, groups, base_tstart=9.0, grid=GRID, max_shift=np.inf):
    """One t_start per group (month/season) minimizing summed objective."""
    allowed = np.abs(grid - base_tstart) <= max_shift
    Jm = np.where(allowed[None, :], J, np.inf)
    out = np.zeros(365)
    for g in np.unique(groups):
        idx = groups == g
        out[idx] = grid[np.argmin(Jm[idx].sum(axis=0))]
    return out


def sas_tstart_threshold(J, base_tstart=9.0, grid=GRID, max_shift=np.inf,
                         threshold=0.001):
    """Adopt daily optimum only where relative improvement over ST > threshold."""
    allowed = np.abs(grid - base_tstart) <= max_shift
    Jm = np.where(allowed[None, :], J, np.inf)
    i_st = int(np.argmin(np.abs(grid - base_tstart)))
    best = np.argmin(Jm, axis=1)
    gain = (J[:, i_st] - J[np.arange(365), best]) / np.maximum(J[:, i_st], 1e-9)
    out = grid[best]
    out[gain < threshold] = base_tstart
    return out


def disruption(t_start_arr, base_tstart=9.0):
    """Schedule-disruption metrics."""
    arr = np.asarray(t_start_arr, dtype=float)
    changes = int(np.sum(np.abs(np.diff(arr)) > 1e-9))
    return dict(
        n_changes=changes,
        mean_abs_shift=float(np.mean(np.abs(arr - base_tstart))),
        max_abs_shift=float(np.max(np.abs(arr - base_tstart))),
        mean_abs_daystep=float(np.mean(np.abs(np.diff(arr)))),
    )


def wake_darkness_penalty(darkness, grid, base_tstart=9.0):
    """(365,len(grid)) penalty = darkness at the two pre-work hours."""
    pen = np.zeros((365, len(grid)))
    for gi, t in enumerate(grid):
        h1 = int(np.clip(round(t - 2), 0, 23))
        h2 = int(np.clip(round(t - 1), 0, 23))
        pen[:, gi] = darkness[:, h1] + darkness[:, h2]
    return pen


def sas_tstart_constrained(J, darkness, base_tstart=9.0, grid=GRID,
                           max_shift=np.inf, wake_dark_cap=np.inf):
    """Constraint-primary SAS: minimize J subject to |t-base|<=max_shift
    AND wake-darkness exposure <= wake_dark_cap. Days where no candidate
    satisfies the caps fall back to the ST baseline (base_tstart), which
    may itself exceed the cap: ST is treated as the status-quo exception,
    and callers should report the infeasible-day share alongside results."""
    allowed = np.abs(grid - base_tstart) <= max_shift
    pen = wake_darkness_penalty(darkness, grid, base_tstart)
    feas = allowed[None, :] & (pen <= wake_dark_cap)
    i_st = int(np.argmin(np.abs(grid - base_tstart)))
    Jm = np.where(feas, J, np.inf)
    best = np.argmin(Jm, axis=1)
    infeasible = ~np.isfinite(Jm).any(axis=1)
    out = grid[best]
    out[infeasible] = base_tstart
    return out
