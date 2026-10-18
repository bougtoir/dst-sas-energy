"""Hourly energy model: E = E_light + E_cool + E_heat + E_other.

Lighting: power_needed ∝ darkness(hour) x occupied fraction, split between
home and work occupancy with separate per-lumen technology efficacies.
Cooling/heating: from building thermal model (degree-hour or RC), scaled by
AC prevalence and heating-system shares.
Other: baseload + activity-proportional appliance load (does NOT shift with
schedule beyond the elasticity already applied to profiles).

All outputs in consistent arbitrary kWh units (scale cancels in deltas).
"""
import numpy as np
from src.building.thermal import degree_hour_load, rc_load


def lighting_energy(darkness, home_occ, work_occ,
                    p_light_home=0.10, p_light_work=0.15):
    """(365,24) lighting energy. darkness in [0,1] = 1 - daylight fraction."""
    return darkness * (p_light_home * home_occ + p_light_work * work_occ)


def hvac_energy(T_out, home_occ, work_occ, ac_prevalence=0.5,
                model="degree_hour", cop_cool=3.0, cop_heat=2.5,
                k_cool=0.15, k_heat=0.25, t_bal_cool=18.0, t_bal_heat=15.0,
                sleep=None, night_setback=0.4,
                **rc_kw):
    """Cooling + heating electricity (365,24).

    Conditioning need = home_occ (residential) + 0.8*work_occ (workplace,
    slightly lower per-capita density proxy). ac_prevalence scales cooling
    (fraction of conditioned floor area with mechanical cooling).
    """
    home = np.asarray(home_occ, dtype=float)
    if sleep is not None:
        # occupied-but-asleep hours run at reduced conditioning (setback)
        home = home * (1.0 - night_setback * np.clip(sleep, 0, 1))
    occ = np.clip(home + 0.8 * work_occ, 0, 1.5)
    if model == "degree_hour":
        cool, heat = degree_hour_load(T_out, occ, t_bal_cool, t_bal_heat,
                                      k_cool, k_heat)
        cool_e = cool / cop_cool
        heat_e = heat / cop_heat
    elif model == "rc":
        cool_e, heat_e = rc_load(T_out, occ, cop_cool=cop_cool,
                                 cop_heat=cop_heat, **rc_kw)
    else:
        raise ValueError(model)
    return ac_prevalence * cool_e, heat_e


def other_energy(awake, base=0.30, activity_gain=0.20):
    """Baseload + activity. awake = 1 - sleep profile."""
    return base + activity_gain * np.clip(awake, 0, 1)


def total_energy(darkness, T_out, profiles, tech, thermal_model="degree_hour"):
    """Aggregate one year's hourly energy components.

    profiles: dict with work/home/sleep (365,24)
    tech: dict with keys p_light_scale (1.0 = reference LED-era efficacy scale
          relative to fluorescent baseline 1.0; incandescent ~3.3x),
          ac_prevalence, cop_cool, cop_heat, heat_electric_share.
    Returns dict of (365,24) arrays + 'total'.
    """
    light = tech.get("p_light_scale", 1.0) * lighting_energy(
        darkness, profiles["home"], profiles["work"])
    cool_e, heat_e = hvac_energy(
        T_out, profiles["home"], profiles["work"],
        ac_prevalence=tech.get("ac_prevalence", 0.5),
        model=thermal_model,
        cop_cool=tech.get("cop_cool", 3.0), cop_heat=tech.get("cop_heat", 2.5),
        k_cool=tech.get("k_cool", 0.15), k_heat=tech.get("k_heat", 0.25),
        sleep=profiles.get("sleep"),
        night_setback=tech.get("night_setback", 0.4),
        c_th=tech.get("c_th", 10.0), r_th=tech.get("r_th", 2.0),
        setback=tech.get("setback", 3.0))
    # only the electric share of heating counts toward electricity
    heat_e = heat_e * tech.get("heat_electric_share", 0.5)
    oth = other_energy(1.0 - profiles["sleep"])
    total = light + cool_e + heat_e + oth
    return dict(light=light, cool=cool_e, heat=heat_e, other=oth, total=total)
