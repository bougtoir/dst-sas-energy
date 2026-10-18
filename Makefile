# dst_sas_energy — reproducible pipeline
# One command regenerates simulations, analysis outputs, figures, tables and the manuscript package.
PY ?= python3

.PHONY: all setup test synthetic mc scenarios strengthening manuscript figures clean qc

all: setup test synthetic mc scenarios strengthening manuscript

setup:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest tests/ -q

synthetic:
	$(PY) simulations/run_synthetic_sweeps.py
	$(PY) simulations/run_regime_comparison.py

mc:
	$(PY) simulations/run_monte_carlo.py
	$(PY) simulations/run_pareto.py

scenarios:
	$(PY) simulations/run_geography.py
	$(PY) simulations/run_historical.py

strengthening:
	$(PY) simulations/run_physical_calibration.py
	$(PY) simulations/run_heating_audit.py
	$(PY) simulations/run_archetypes.py
	$(PY) simulations/run_constrained_sas.py
	$(PY) simulations/run_indiana_audit.py
	if [ -n "$$EIA_API_KEY" ]; then $(PY) simulations/fetch_eia930.py; \
	  else echo "EIA_API_KEY not set — skipping empirical grid-CI fetch"; fi

figures:
	$(PY) analysis/make_figures.py
	$(PY) analysis/make_tables.py

manuscript: figures
	$(PY) analysis/build_manuscript.py
	$(PY) analysis/build_submission_package.py

qc:
	$(PY) qc/run_qc.py

clean:
	rm -rf analysis/*.csv figures/*.png tables/*.tex manuscript/build
