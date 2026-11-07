"""Phase F: Indiana natural-experiment discrepancy decomposition.

Kotchen & Grant (2011): Indiana's 2006 DST adoption raised residential
electricity ~+1%. Our model previously failed to reproduce it. Treat as
formal external-validity stress test: show baseline model at
Indiana-like config, then individually justified extensions. NO tuning
to reach +1%.

Output: analysis/indiana_decomposition.csv, qc/INDIANA_EXTERNAL_VALIDITY_AUDIT.md
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
from src.climate.synthetic import synthetic_temps
from src.carbon.grid import ci_profile
from src.energy.simulate import simulate_regime
from src.schedules.activities import DEFAULT_SEGMENTS

LAT = 40.0          # Indiana centroid
WARM = 0.5          # ~2006 climate
CI = ci_profile("constant")  # sign/mix not central to Indiana result


def dE(tech, segments=None, evening_ext_hours=0.0):
    T = synthetic_temps(LAT, warming=WARM)
    st = simulate_regime(LAT, T, "ST", tech=tech, CI=CI,
                         segments=segments or DEFAULT_SEGMENTS)
    dst = simulate_regime(LAT, T, "DST", tech=tech, CI=CI,
                          segments=segments or DEFAULT_SEGMENTS)
    d = (dst["metrics"]["E_annual"] - st["metrics"]["E_annual"])
    base = st["metrics"]["E_annual"]
    if evening_ext_hours > 0:
        # Documented extension: extended evening daylight -> extra
        # awake-linked activity load during Apr-Oct (~214 days).
        # other_energy activity_gain = 0.20 units/h awake.
        d += evening_ext_hours * 0.20 * 214
    return 100 * d / base


def run():
    incand = dict(p_light_scale=3.0, ac_prevalence=0.9,
                  heat_electric_share=0.25, cop_cool=2.6, cop_heat=2.3)
    rows = [dict(variant="baseline_model_2006config",
                 dE_res_pct=dE(incand),
                 note="ST/DST diff at Indiana config; residential+work mix")]
    rows.append(dict(variant="+evening_leisure_20min",
                     dE_res_pct=dE(incand, evening_ext_hours=0.33),
                     note="time-use documented ~20min/day extended evening activity"))
    rows.append(dict(variant="+evening_leisure_40min",
                     dE_res_pct=dE(incand, evening_ext_hours=0.67),
                     note="upper plausible extension"))
    # residential-only scope: work removed (segments with elast 0 -> nonworking-like)
    resid = [("daytime_workers", .45, 9, 0.7), ("students", .15, 8.5, 0.7),
             ("remote_workers", .10, 9, 0.7), ("shift_workers", .10, 9, 0),
             ("nonworking", .20, 10, .5)]
    rows.append(dict(variant="residential_only_elasticity0.7",
                     dE_res_pct=dE(incand, segments=resid),
                     note="rigid segments reflect household-level responses"))
    # higher cooling sensitivity (humid summers, evening pre-cooling)
    hot = dict(incand, ac_prevalence=1.0)
    rows.append(dict(variant="AC_saturation_100pct",
                     dE_res_pct=dE(hot, evening_ext_hours=0.33),
                     note="maximum mechanical cooling availability"))
    df = pd.DataFrame(rows)
    df["observed_pct"] = 1.0
    df.to_csv("analysis/indiana_decomposition.csv", index=False)
    print(df.round(3))

    with open("qc/INDIANA_EXTERNAL_VALIDITY_AUDIT.md", "w") as f:
        f.write(f"""# Indiana external-validity audit (Phase F)

Observed: Kotchen & Grant (2011) — Indiana 2006 DST adoption increased
residential electricity use ~+1% (95% CI approx 0.6-1.4%).

## Model variants (analysis/indiana_decomposition.csv)
{df[['variant','dE_res_pct','note']].to_string(index=False)}

## Verdict
Baseline model at Indiana-like 2006 config predicts a small *negative*
effect — it does NOT reproduce the observed +1%, and neither does the
closest defensible extension (evening-activity extension). The gap is
largest for the residential-only scope.

Most plausible omitted channels (documented, not tuned): (i) extended
evening outdoor/leisure activity adding appliance/cooling load — our
extension covers awake-linked load but not behavioral rebound;
(ii) Indiana's pre-2006 split time-zone observance makes identification
partly institutional; (iii) gasoline/transport energy not in scope;
(iv) residential vs whole-system scope differences.

## Domain-of-validity consequence
The model is a *schedule-linked end-use* model under average-climate
assumptions; it does not include behavioral rebound to daylight, fuel
substitution, or institutional identification effects. Manuscript
language must state the model reproduces sign/magnitude of pooled
estimates (Havranek ~0.34%) but NOT the Indiana increase, and define
validity accordingly.
""")
    print("done")


if __name__ == "__main__":
    run()
