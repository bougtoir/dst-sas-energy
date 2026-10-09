"""Synthetic hourly climate: latitude-dependent seasonal + diurnal temperature.

Transparent MVP climate; NOT a substitute for observed data. Daily mean follows
a sinusoid between winter/summer extremes scaled by latitude; diurnal cycle is
a sinusoid peaking ~15:00 solar time. Warming scenarios add a uniform offset
(documented simplification).
"""
import numpy as np


def synthetic_temps(lat_deg, warming=0.0, amplitude=None, t_annual=None,
                    hours=np.arange(24), seed=None):
    """Return (365,24) hourly temperature in degC under STANDARD civil time.

    Defaults: t_annual = 27 - 0.6*|lat|  (rough global mean gradient)
              amplitude(seasonal) = 12 * |lat|/60 clamped [3, 12]
    Diurnal amplitude 4 degC, peaking at 15:00.
    """
    if t_annual is None:
        t_annual = 34.0 - 0.55 * abs(lat_deg)
    if amplitude is None:
        amplitude = min(13.0, max(2.0, 12.0 * abs(lat_deg) / 45.0))
    doy = np.arange(1, 366)
    # seasonal: warmest ~day 197 (mid-July NH); flip for SH
    phase = 0.0 if lat_deg >= 0 else 182.0
    daily_mean = t_annual + amplitude * np.cos(2 * np.pi * (doy - 197 - phase) / 365.0)
    diurnal = 6.0 * np.cos(2 * np.pi * (np.asarray(hours) - 15.0) / 24.0)
    return daily_mean[:, None] + diurnal[None, :] + warming
