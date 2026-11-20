"""Hourly grid carbon intensity scenarios.

CI(h) daily profile shapes:
- 'constant': flat (sanity test; carbon ranking must equal energy ranking)
- 'fossil_peak': higher morning/evening ramps (gas peakers)
- 'solar_duck': low midday (solar), steep evening ramp; depth scaled by
  `solar_pen` (solar share proxy)
Values in kgCO2e/kWh arbitrary-consistent units.
"""
import numpy as np

HOURS = np.arange(24)


def ci_profile(kind="solar_duck", base=0.45, solar_pen=0.3,
               seasonal_amp=0.0, doy=None):
    """Return (365,24) or (24,) CI profile."""
    h = HOURS
    if kind == "constant":
        prof = np.full(24, base)
    elif kind == "fossil_peak":
        prof = base + 0.15 * np.exp(-((h - 8) / 2.5) ** 2) \
                    + 0.20 * np.exp(-((h - 19) / 2.5) ** 2)
    elif kind == "solar_duck":
        duck = solar_pen * np.exp(-((h - 13) / 3.5) ** 2)
        ramp = 0.10 * np.exp(-((h - 8) / 2.5) ** 2) \
             + 0.25 * np.exp(-((h - 19.5) / 2.5) ** 2)
        prof = base - duck + ramp
        prof = np.clip(prof, 0.05, None)
    else:
        raise ValueError(kind)
    if seasonal_amp and doy is not None:
        seas = 1.0 + seasonal_amp * np.cos(2 * np.pi * (doy - 15) / 365.0)
        return prof[None, :] * seas[:, None]
    return np.tile(prof, (365, 1))


def carbon(E, CI):
    """Elementwise operational carbon; returns (365,24)."""
    return E * CI
