"""Solar geometry: NOAA-style solar position / sunrise-sunset calculations.

Validated against NOAA Solar Calculator (approx. +/-1 min for sunrise/sunset
at mid-latitudes). Returns solar elevation and daylight flags for each hour of
a non-leap year. Polar day/night is handled explicitly: when the sun never
rises (cos_zenith argument outside [-1,1] with negative declination-geometry),
sunrise/sunset are NaN and daylight flags are computed directly from hourly
solar elevation instead of sunrise/sunset interpolation.
"""
import numpy as np

DEG = np.pi / 180.0


def _solar_times(day_of_year, lat_deg, lon_deg, tz_offset):
    """Return (sunrise_h, sunset_h, solar_noon_offset_h) in local civil time.

    sunrise/sunset are NaN for polar day/night.
    tz_offset: hours of local standard time east of UTC (e.g. JST=9).
    """
    lat = lat_deg * DEG
    # fractional year gamma (radians), equation of time & declination (NOAA)
    gamma = 2.0 * np.pi / 365.0 * (day_of_year - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
                       - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
            - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
            - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma))
    cos_ha = (np.cos(90.833 * DEG) / (np.cos(lat) * np.cos(decl))
              - np.tan(lat) * np.tan(decl))
    solar_noon_min = 720.0 - 4.0 * lon_deg - eqtime + tz_offset * 60.0
    if cos_ha > 1.0:   # polar night
        return np.nan, np.nan, solar_noon_min / 60.0, eqtime, decl
    if cos_ha < -1.0:  # polar day
        return np.nan, np.nan, solar_noon_min / 60.0, eqtime, decl
    ha = np.arccos(cos_ha) / DEG  # degrees
    sunrise = solar_noon_min - 4.0 * ha
    sunset = solar_noon_min + 4.0 * ha
    return sunrise / 60.0, sunset / 60.0, solar_noon_min / 60.0, eqtime, decl


def solar_elevation(day_of_year, hour_local, lat_deg, lon_deg, tz_offset):
    """Solar elevation angle (degrees) at a local civil hour."""
    lat = lat_deg * DEG
    gamma = 2.0 * np.pi / 365.0 * (day_of_year - 1 + (hour_local - 12) / 24.0)
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
                       - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
            - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
            - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma))
    time_offset = eqtime + 4.0 * lon_deg - 60.0 * tz_offset
    tst = hour_local * 60.0 + time_offset  # true solar time, minutes
    ha = (tst / 4.0 - 180.0) * DEG
    sin_elev = (np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha))
    return np.arcsin(np.clip(sin_elev, -1, 1)) / DEG


def daylight_hours_year(lat_deg, lon_deg=0.0, tz_offset=0.0):
    """Return arrays (365,): sunrise_h, sunset_h in local civil time (NaN polar)."""
    sr = np.empty(365); ss = np.empty(365)
    for d in range(365):
        s1, s2, _, _, _ = _solar_times(d + 1, lat_deg, lon_deg, tz_offset)
        sr[d] = s1; ss[d] = s2
    return sr, ss


def hourly_daylight(lat_deg, lon_deg=0.0, tz_offset=0.0, hours=np.arange(24)):
    """(365,24) daylight fraction per civil hour under STANDARD time."""
    out = np.zeros((365, len(hours)))
    for d in range(365):
        sr, ss, _, _, _ = _solar_times(d + 1, lat_deg, lon_deg, tz_offset)
        for j, h in enumerate(hours):
            if np.isnan(sr):
                # polar day/night: use elevation at mid-hour
                out[d, j] = 1.0 if solar_elevation(d + 1, h + 0.5, lat_deg, lon_deg, tz_offset) > 0 else 0.0
            else:
                lo, hi = max(h, sr), min(h + 1, ss)
                out[d, j] = max(0.0, hi - lo)
    return out


def solar_noon_year(lat_deg, lon_deg=0.0, tz_offset=0.0):
    """(365,) local civil time of solar noon."""
    return np.array([_solar_times(d + 1, lat_deg, lon_deg, tz_offset)[2]
                     for d in range(365)])
