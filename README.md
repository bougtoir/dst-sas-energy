# dst_sas_energy

**Beyond daylight saving time: human activity timing as a demand-side flexibility resource.**

Simulation study comparing three regimes — fixed Standard Time (ST), conventional Daylight Saving Time (DST), and Solar-Adaptive Scheduling (SAS) — for energy use, operational carbon emissions, and peak electricity demand, across latitude, warming, lighting technology, and AC prevalence.

- ST = invariant-clock reference; DST = coarse seasonal +1 h demand-timing intervention; SAS = constrained activity scheduling with civil time fixed.
- Primary question: *when, where, and under what energy-system conditions can shifting human activity timing reduce energy use, operational carbon, and peak demand?*

## Reproduce

```
make setup   # pip install requirements
make all     # tests + simulations + analysis + manuscript package
```

Artifacts: `analysis/` (CSV results + manuscript-values registry), `figures/`, `tables/`, `manuscript/build/` (submission package), `literature/` (evidence + novelty tables), `qc/` (journal requirements, desk-rejection audit, QC reports), `PHASE_*_HANDOFF.txt`, `FINAL_HANDOFF.txt`.

## Structure

- `src/solar` — NOAA solar position/daylight (validated in tests)
- `src/climate` — synthetic hourly climate + Open-Meteo (ERA5-based) fetcher with acquisition ledger
- `src/schedules` — ST/DST/SAS activity profiles, heterogeneous segments, elasticity
- `src/energy` — lighting/cooling/heating/other decomposition, peak metrics
- `src/building` — degree-hour and first-order RC thermal models
- `src/carbon` — hourly grid-carbon scenarios (constant / fossil-peak / solar-duck)
- `src/optimization` — SAS daily/monthly/seasonal/threshold optimization, Pareto, disruption
- `simulations/` — runnable pipelines writing `analysis/*.csv`
- `tests/` — unit + sanity tests (zero-load pathway removal, ST-equivalence, CI=const ⇒ C∝E, polar handling)

Deterministic seeds everywhere; every manuscript number traces to `analysis/manuscript_values.csv`.

## License
MIT (see LICENSE). Data: Open-Meteo archive API (CC-BY 4.0).
