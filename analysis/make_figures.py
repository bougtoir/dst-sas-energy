"""Generate all manuscript figures from analysis CSVs (300 dpi PNG)."""
import sys, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

A = os.path.dirname(__file__)
F = os.path.join(A, "..", "figures")
os.makedirs(F, exist_ok=True)
plt.rcParams.update({"font.size": 9, "figure.dpi": 300})


def fig1_concept():
    """Conceptual ST/DST/SAS architecture."""
    fig, axes = plt.subplots(3, 1, figsize=(6.5, 5.0), sharex=True)
    hours = np.arange(24)
    daylight = (hours >= 6) & (hours <= 18)
    for ax, (title, sched) in zip(axes, [
        ("A  Standard Time: fixed clock, fixed schedule", 9.0 * np.ones(24)),
        ("B  DST: clock +1h Apr-Oct, activity shifts earlier vs sun", 8.0 * np.ones(24)),
        ("C  SAS: clock fixed, activity start adapts (example)", None)]):
        ax.axvspan(6, 18, color="#fff3b0", alpha=0.6, label="daylight")
        if sched is not None:
            ax.axvspan(sched[0], sched[0] + 8, color="#4d96ff", alpha=0.7,
                       label="work block")
        else:
            for lo, hi, c in [(7, 15, "#4d96ff"), (8, 16, "#4d96ff"),
                              (8.5, 16.5, "#4d96ff")]:
                ax.axvspan(lo, hi, color=c, alpha=0.35)
            ax.annotate("season-dependent", xy=(8, 0.5), fontsize=8)
        ax.set_ylim(0, 1); ax.set_yticks([])
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_xlim(0, 24)
    axes[2].set_xlabel("local civil hour (standard time)")
    fig.tight_layout()
    fig.savefig(f"{F}/fig1_concept.png"); plt.close(fig)


def fig2_warming_decomp():
    d = pd.read_csv(f"{A}/dst_sweep.csv")
    s = d[d.lighting == "led"].groupby(["lat", "warming", "ac_prevalence"]
                                     ).mean(numeric_only=True).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.0))
    ac = 0.5
    for lat, mk in [(20, "o"), (40, "s"), (60, "^")]:
        ss = s[(s.lat == lat) & (s.ac_prevalence == ac)]
        axes[0].plot(ss.warming, ss.dE_DST_pct, mk + "-", ms=4,
                     label=f"{lat}°")
    axes[0].axhline(0, color="k", lw=0.5)
    axes[0].set_xlabel("warming (°C)"); axes[0].set_ylabel("ΔE_DST (% of ST)")
    axes[0].legend(title="latitude", fontsize=7)
    axes[0].set_title("A  DST energy effect vs warming", fontsize=9)
    ss = s[(s.lat == 30) & (s.ac_prevalence == 0.5)]
    w = ss.warming
    axes[1].bar(w - 0.25, ss.dE_light, width=0.2, label="lighting")
    axes[1].bar(w - 0.05, ss.dE_cool, width=0.2, label="cooling")
    axes[1].bar(w + 0.15, ss.dE_heat, width=0.2, label="heating")
    axes[1].axhline(0, color="k", lw=0.5)
    axes[1].set_xlabel("warming (°C)"); axes[1].set_ylabel("Δ component (kWh-eq)")
    axes[1].legend(fontsize=7)
    axes[1].set_title("B  component decomposition, 30°N, AC=50%", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{F}/fig2_warming_decomp.png"); plt.close(fig)


def fig3_phase():
    d = pd.read_csv(f"{A}/dst_sweep.csv")
    s = d[(d.warming == 0) & (d.ac_prevalence.isin([0, 0.5, 1.0]))]
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    for ac, mk in [(0.0, "o"), (0.5, "s"), (1.0, "^")]:
        ss = s[s.ac_prevalence == ac]
        piv = ss.pivot_table(index="lat", columns="lighting",
                             values="dE_DST_pct",
                             aggfunc="mean")[["incandescent", "fluorescent",
                                              "mixed", "led", "full_led"]]
        for lat in piv.index:
            ax.plot(range(5), piv.loc[lat], marker=mk, ms=3, lw=0.8,
                    alpha=0.8)
    ax.set_xticks(range(5))
    ax.set_xticklabels(["incand", "fluor", "mixed", "LED", "fullLED"],
                       fontsize=7)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("ΔE_DST (% of ST)")
    ax.set_title("Lighting technology x latitude x AC", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{F}/fig4_phase.png"); plt.close(fig)


def fig4_regimes():
    d = pd.read_csv(f"{A}/regime_comparison.csv")
    s = d[d.warming == 0]
    order = ["ST", "DST", "SAS_daily_energy", "SAS_monthly_energy",
             "SAS_seasonal_energy", "SAS_threshold_energy",
             "SAS_daily_carbon"]
    labs = ["ST", "DST", "SAS-d", "SAS-m", "SAS-s", "SAS-t", "SAS-d(CO2)"]
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    for lat, mk in [(20, "o"), (30, "v"), (40, "s"), (50, "^")]:
        ss = s[s.lat == lat].groupby("regime").dE_pct.mean().reindex(order)
        ax.plot(labs, ss.values, mk + "-", ms=4, label=f"{lat}°")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("ΔE (% of ST)"); ax.legend(title="lat", fontsize=7)
    ax.set_title("Regime comparison (synthetic, warming=0)", fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout(); fig.savefig(f"{F}/fig3_regimes.png"); plt.close(fig)


def fig5_pareto():
    d = pd.read_csv(f"{A}/pareto_frontier.csv")
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    for v, mk in [("daily", "o"), ("monthly", "s"), ("seasonal", "^"),
                  ("threshold", "d")]:
        ss = d[d.variant == v]
        g = ss.groupby("max_shift").agg({"dE_pct": "mean",
                                         "mean_abs_shift": "mean"})
        ax.plot(g.mean_abs_shift, -g.dE_pct, mk + "-", ms=4, label=v)
    ax.set_xlabel("mean |schedule shift| vs ST (h)")
    ax.set_ylabel("energy savings (% of ST)")
    ax.legend(fontsize=8)
    ax.set_title("Benefit vs disruption frontier (mean over lat/warming)",
                 fontsize=9)
    fig.tight_layout(); fig.savefig(f"{F}/fig7_pareto.png"); plt.close(fig)


def fig6_geography():
    d = pd.read_csv(f"{A}/geography.csv")
    p = d.pivot_table(index="city", columns="regime", values="dE_pct")
    p = p.sort_values("DST")
    x = np.arange(len(p))
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    w = 0.35
    ax.bar(x - w / 2, p["DST"], w, label="DST")
    ax.bar(x + w / 2, p["SAS_daily_2h"], w, label="SAS (max 2h shift)")
    ax.set_xticks(x); ax.set_xticklabels(p.index, rotation=45, ha="right",
                                        fontsize=7)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("ΔE (% of ST)")
    ax.legend(fontsize=8)
    ax.set_title("Empirical-weather city results (Open-Meteo 2023)", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{F}/fig5_geography.png"); plt.close(fig)


def fig7_historical():
    d = pd.read_csv(f"{A}/historical.csv")
    fig, ax = plt.subplots(figsize=(4.5, 3.0))
    eras = ["1970s", "1990s", "2010s", "contemporary", "future+2C"]
    for lat in [25, 35, 45, 55]:
        ss = d[d.lat == lat].set_index("era").reindex(eras)
        ax.plot(eras, ss.dE_pct, "o-", ms=4, label=f"{lat}°")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("ΔE_DST (% of ST)")
    ax.legend(title="lat", fontsize=7)
    ax.set_title("Stylized technology/climate eras", fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig.tight_layout(); fig.savefig(f"{F}/fig6_historical.png"); plt.close(fig)


def fig8_mc():
    d = pd.read_csv(f"{A}/monte_carlo.csv")
    fig, ax = plt.subplots(figsize=(4.5, 3.0))
    for col, lab in [("E", "energy"), ("C", "carbon")]:
        v = 100 * (d[f"{col}_SAS"] - d[f"{col}_ST"]) / d[f"{col}_ST"]
        ax.hist(v, bins=60, alpha=0.5, density=True, label=f"SAS {lab}")
        v = 100 * (d[f"{col}_DST"] - d[f"{col}_ST"]) / d[f"{col}_ST"]
        ax.hist(v, bins=60, alpha=0.5, density=True, label=f"DST {lab}")
    ax.axvline(0, color="k", lw=0.5)
    ax.set_xlabel("Δ vs ST (%)"); ax.set_ylabel("density")
    ax.legend(fontsize=7); ax.set_title("Monte Carlo (N=10,000)", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{F}/fig8_montecarlo.png"); plt.close(fig)


if __name__ == "__main__":
    for f in [fig1_concept, fig2_warming_decomp, fig3_phase, fig4_regimes,
              fig5_pareto, fig6_geography, fig7_historical]:
        try:
            f(); print("ok", f.__name__)
        except Exception as e:
            print("FAIL", f.__name__, e)
    if os.path.exists(f"{A}/monte_carlo.csv"):
        try:
            fig8_mc(); print("ok fig8_mc")
        except Exception as e:
            print("FAIL fig8_mc", e)
