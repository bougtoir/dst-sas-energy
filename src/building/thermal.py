"""Building thermal models: transparent degree-hour and first-order RC.

Degree-hour: instantaneous cooling/heating proportional to outdoor
temperature exceedance over balance temperatures, only during occupied hours.

RC model: single-zone first-order ODE
  C_th dT_in/dt = (T_out - T_in)/R + Q_int + Q_hvac
with a thermostat: Q_hvac heats to T_heat_sp when occupied, cools to
T_cool_sp; a deadband applies when unoccupied (setback ±3 degC).
Energy use = |Q_hvac| / COP accumulated per hour (kWh-equivalent units).
"""
import numpy as np


def degree_hour_load(T_out, occupancy, t_bal_cool=18.0, t_bal_heat=15.0,
                     k_cool=1.0, k_heat=1.0):
    """Instantaneous loads (365,24): (cool_kw, heat_kw) in arbitrary kW units.

    occupancy (365,24) in [0,1] scales the conditioning requirement.
    """
    occ = np.clip(occupancy, 0, 1)
    cool = k_cool * np.maximum(T_out - t_bal_cool, 0.0) * occ
    heat = k_heat * np.maximum(t_bal_heat - T_out, 0.0) * occ
    return cool, heat


def rc_load(T_out, occupancy, cop_cool=3.0, cop_heat=2.5,
            t_cool_sp=26.0, t_heat_sp=20.0, setback=3.0,
            c_th=10.0, r_th=2.0, q_int=0.5, dt_h=1.0, occ_thresh=0.3):
    """First-order RC thermal model.

    T_out, occupancy: (365,24) degC and fraction.
    c_th: effective heat capacity (kWh/degC), r_th: degC/(kW) overall conductance
    time constant tau = c_th*r_th (hours). q_int: internal gains (kW).
    Returns (cool_kwh, heat_kwh) arrays (365,24) of HVAC electricity.
    """
    days, hrs = T_out.shape
    cool_e = np.zeros_like(T_out)
    heat_e = np.zeros_like(T_out)
    t_in = t_heat_sp
    tau = c_th * r_th
    beta = 1.0 - np.exp(-dt_h / tau)
    for d in range(days):
        for h in range(hrs):
            occ = occupancy[d, h] > occ_thresh
            hi = t_cool_sp if occ else t_cool_sp + setback
            lo = t_heat_sp if occ else t_heat_sp - setback
            # free float with internal gains
            t_free = t_in + beta * (T_out[d, h] + q_int * r_th - t_in)
            if t_free > hi:
                q = -(t_free - hi) * c_th / dt_h   # kW cooling delivered
                cool_e[d, h] = -q / cop_cool * dt_h
                t_in = hi
            elif t_free < lo:
                q = (lo - t_free) * c_th / dt_h
                heat_e[d, h] = q / cop_heat * dt_h
                t_in = lo
            else:
                t_in = t_free
    return cool_e, heat_e
