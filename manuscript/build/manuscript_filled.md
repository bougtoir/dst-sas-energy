# Human activity timing as building energy flexibility: standard time, daylight saving time, and solar-adaptive scheduling under climate change

Onishi Tatsuki
Data Science and AI Innovation Research Promotion Center, Shiga University, Hikone, Japan

Correspondence to: Onishi Tatsuki; Data Science and AI Innovation Research Promotion Center, Shiga University; 1-1-1, Bamba, Hikone, Shiga, 522-8522, Japan; Telephone: +81-749-27-1023; FAX: +81-749-27-1132; E-mail: bougtoir@gmail.com; ORCID: 0000-0001-7261-9062

## Abstract

Buildings are temporally coupled systems: occupancy schedules set when lighting, heating and cooling actually run, so shifting the timing of occupant activity is a candidate source of building energy flexibility — but its magnitude is bounded by thermal inertia, climate, HVAC technology and realistic scheduling constraints. We quantify how much flexibility activity retiming can deliver, and how strongly the estimate depends on model structure. We build an hourly, location-resolved simulation coupling solar geometry, synthetic and reanalysis weather, heterogeneous occupant schedules, and lighting/cooling/heating end uses under both a degree-hour model and a first-order RC thermal model, with hourly grid carbon intensity from scenarios and EIA-930 generation mix. Alongside fixed standard time (ST) and daylight saving time (DST) we introduce solar-adaptive scheduling (SAS): civil time is invariant while activity start times are optimized under displacement and morning-darkness constraints. Under contemporary conditions the DST effect is approximately zero on average (Monte Carlo median +0.05%, 95% interval [-0.09, 0.22]): a heating reduction in electrically heated stock is nearly cancelled by lighting and cooling increases, and under RC thermal inertia DST becomes a net cost — the headline benefit is therefore sensitive to thermal-model structure, a result building-flexibility simulations should heed. The sign is latitude- and stock-dependent (-0.29% to 0.12%), and warming flips DST to a cost in a mid-latitude high-AC band within +0.50–2.75 °C. SAS saves at most ~0.5% under relaxed constraints and ~0 under strict ones. Activity timing is at most a marginal, conditional building flexibility resource.

Keywords: daylight saving time; occupant behavior; building energy flexibility; thermal inertia; demand response; climate change

## 1. Introduction

Buildings draw energy on the schedule of their occupants. Lighting, heating and cooling loads are gated by when people are present, awake and active, so the temporal placement of occupant activity is a first-order determinant of building energy demand [1]. Occupant schedules are increasingly recognized as uncertain, stochastic inputs whose representation materially changes simulated energy use [2]. Yet most building-flexibility studies treat the occupancy schedule as fixed and ask how storage, thermostats or controllable loads can move energy within it. Here we ask the inverse question: how much energy flexibility is available in the schedule itself?

Building energy flexibility — the capacity to reshape demand in time — is an active research program anchored in demand response and smart-grid harmonized operation [3-6]. Physical flexibility channels (thermal storage, setpoint modulation, controllable loads) have been quantified extensively, but the behavioral side — the schedule the building serves — is usually held constant or modeled as an exogenous occupancy profile. One real-world intervention does move the schedule itself, at population scale: daylight saving time (DST) is a coarse, twice-yearly, one-hour rescheduling of daily life motivated by lighting savings.

DST therefore functions as an imperfect but informative natural experiment on activity-timing flexibility in buildings. The empirical record is heterogeneous: a ~1% *increase* in residential electricity in Indiana [7]; no net change but a large intraday load shift in Australia [8]; a meta-analytic mean saving of 0.34% on DST days that decreases toward the equator [9]; and country studies with mixed sign — Turkey [10], Spain [11], Chile [12], the UK [13], and the extended-DST episode in the US [14]. The effect is conditioned by weather and air-conditioning penetration [15], and recent hourly-load evidence from Iran reports the same weather conditioning [16].

Three structural changes have altered the load the clock shifts. LED lighting has collapsed the lighting share that motivated DST [17]. Air-conditioning diffusion has made cooling the marginal load in many climates [18,19], so a schedule that saves lighting can cost cooling. And hourly grid carbon intensity now varies strongly with solar penetration, so the timing of load — not only its total — matters for operational emissions [20-22]. None of these changes is well captured by the lighting-centric framing in which the DST debate is usually conducted.

A gap remains between the DST literature, which estimates policy effects on metered electricity, and the building-energy literature, which models how schedules interact with thermal dynamics and end uses. Building-level simulation studies of DST find component trade-offs between lighting and HVAC whose net sign depends on climate and building stock [23-26], but they typically hold thermal model structure fixed and rarely test whether the estimated benefit survives thermal inertia — the fact that a building's temperature, and hence its heating and cooling demand, does not follow the occupancy schedule instantaneously [27,28]. Whether activity retiming is a real flexibility resource therefore depends on a modeling choice, not only on climate.

We compare three scheduling regimes within a single hourly framework. Fixed standard time (ST) is the invariant-clock reference. Conventional DST holds displayed-clock schedules fixed while the civil clock shifts +1 h seasonally. Solar-adaptive scheduling (SAS) keeps civil time — timestamps, computing, transport, medical and legal records — permanently fixed while selected activity schedules adapt seasonally to solar and climatic conditions within explicit constraints; it is inspired by, but not identical to, historical unequal hours [29], and separates an invariant synchronization layer from an adaptive activity layer. We drive the model with synthetic and reanalysis weather, calibrated physical-unit scaling, heterogeneous behavioral schedules, and a constrained-optimization formulation of SAS.

Contributions: (i) an integrated solar–climate–building–grid–activity hourly model, calibrated to physical household units, that decomposes the DST effect into lighting/cooling/heating channels; (ii) a structural-sensitivity result — first-order RC thermal inertia largely collapses the HVAC channel, making the estimated benefit model-structure dependent — reported explicitly rather than averaged away; (iii) SAS formulated as constraint-primary multi-objective scheduling with daily, monthly, seasonal, and threshold-triggered implementations; (iv) climate/technology regime boundaries including warming reversal thresholds; (v) energy-versus-carbon divergence testing under real hourly grid carbon intensity; and (vi) external benchmarking against the DST natural-experiment literature, including a documented failure to reproduce the Indiana increase.

## 2. Methods

### 2.1 Model

For location i, day d, hour h, electricity is E = E_light + E_cool + E_heat + E_other and operational carbon C = E·CI with hourly carbon intensity CI. Primary contrasts are Δ_DST = DST − ST, Δ_SAS = SAS − ST, and Δ_SAS−DST, reported separately for energy (both as % and as calibrated kWh/household-yr, anchored to EIA RECS 2020) and carbon (kgCO2e). Figure 1 summarizes the three scheduling regimes.

**Solar geometry.** Solar elevation, sunrise, and sunset use the NOAA solar position equations [30] (declination, equation of time, hour angle), validated to within ~1 minute of sunrise/sunset against mid-latitude references; polar day/night is handled by direct elevation testing rather than sunrise interpolation.

**Climate.** A transparent synthetic hourly temperature field (latitude-dependent seasonal and diurnal cycles, uniform warming offsets 0–4 °C) supports broad parameter sweeps; ten representative cities additionally use hourly 2023 temperature from the Open-Meteo archive API (ERA5-based reanalysis, CC-BY 4.0) [31,32], with raw JSON and checksums archived in an acquisition ledger.

**Schedules.** The schedule-following population is split into five segments (daytime workers, students, remote workers, shift workers, non-working adults) with segment base times and elasticity — the fraction of each flexible load that follows a schedule shift; shift workers are inflexible. From each work-block start t_start we derive wake, work, home-occupancy, sleep, and evening-leisure profiles at hourly resolution. ST fixes t_start = 9:00 year-round. DST holds displayed-clock schedules fixed, equivalently shifting t_start one hour earlier in standard-time coordinates during April–October (NH; mirrored SH). SAS chooses t_start per day, month, season, or by benefit threshold, within a maximum allowed shift.

**Energy.** Lighting energy is proportional to darkness hours weighted by occupancy and scaled by a lighting-efficacy factor (incandescent-like 3.3× to full-LED 0.4× a mixed reference). Cooling and heating are computed under two deliberately contrasting thermal models: (a) a transparent degree-hour model (balance temperatures 18 °C cooling / 15 °C heating, occupancy-scaled) — a steady-state screening model in which load follows the occupancy schedule immediately; and (b) a first-order RC model with thermostat setpoints and unoccupied setback [27,28] — a reduced-order dynamic model in which envelope thermal inertia delays and attenuates the load response to schedule shifts. Cooling is scaled by AC prevalence and divided by COP, heating by COP and an electric-heat share; asleep occupants run at a reduced conditioning level (night setback). Other load is baseload plus wake-activity-proportional demand. Neither model is a validated whole-building simulator: the pair brackets the sensitivity of the result to thermal-model structure, which is the point of the comparison. Physical-unit calibration maps model units to kWh/household-yr via an EIA RECS 2020 anchor [33] (documented in the accompanying repository). This is *calibration*, not validation: it fixes the units and magnitudes but does not establish predictive accuracy at building level. The empirical-weather sites and the Indiana comparison provide *benchmarking* against published estimates, not *validation* of building-level predictions.

**Grid carbon.** Hourly CI combines (a) scenario profiles — constant, fossil-peaker, solar-duck — and (b) empirical hourly profiles computed from EIA-930 generation mix for three contrasting balancing authorities: CAISO (solar-heavy), NYISO (mixed), PJM (fossil-heavy) [34], using standard combustion emission factors [35]. Empirical CI is average combustion intensity of net generation, not marginal emissions [20-22].

**SAS optimization.** The primary formulation is constraint-based: minimize daily energy subject to |t_start − 9:00| ≤ max_shift and wake-darkness exposure ≤ cap, swept over a constraint grid; weighted objectives (energy + λ_dark·wake-darkness) appear only as sensitivity analyses. Implementable discretizations (monthly, seasonal, threshold-triggered) are evaluated against the constrained daily optimum. Outcomes include annual/seasonal peak, P95/P99, peak-to-average ratio, ramp metrics, peak timing, change counts, displacement, and wake-darkness exposure. Uncertainty uses 10,000 Monte Carlo draws over lighting efficacy, AC prevalence, COPs, elasticity, heating electric share, envelope conductivity, night setback, latitude, and CI solar share (seed 20260924), reported as parameter/scenario uncertainty.

### 2.2 Benchmarking targets

From a documented literature search of the DST evidence base [7-16,23-26,29] (evidence table in the accompanying repository): historical lighting-intensive conditions should plausibly produce reported DST savings; high-AC scenarios should erode them; solar outputs must match astronomical references; and results should survive behavioral heterogeneity and thermal-model structure.

## 3. Results

### 3.1 Mechanistic decomposition and thermal-model structural sensitivity

Under contemporary conditions the net DST effect is a near-cancellation of opposing channels. At mid-latitude baseline (45°N, 50% electric heating) DST reduces heating electricity but *increases* both lighting (more morning-darkness occupancy than evening-daylight savings) and cooling (earlier return to hot afternoon homes). The balance flips sign across building stock: gas-heated stock shows a net increase (+0.03–0.12% at tested sites), electrically heated stock a net decrease (down to −0.29%). Under the first-order RC thermal model the HVAC channels collapse almost entirely — thermal inertia means occupancy shifts do not translate proportionally into load — leaving only the lighting cost and a net increase everywhere tested (Figure 2, Figure 3; Table 1). The degree-hour result is thus structure-dependent, not robust to thermal dynamics; we report both, and treat this structural sensitivity as a central result rather than a nuisance.

### 3.2 Climate and building-stock boundaries and warming

Across the 625-cell synthetic grid Δ_DST spans -0.15% to 0.27%; across the ten empirical-weather cities it ranges from -0.29% (Phoenix, hot-arid) to 0.12% (Singapore, equatorial). Warming produces sign reversal in a mid-latitude band: reversal thresholds T∗ ∈ [0.50, 2.75] °C exist at 40–50°N, predominantly where AC prevalence ≥ 50% (5 of 28 tested latitude×AC cells) — warming converts a small DST saving into a small cost as cooling grows faster than heating shrinks. No reversal occurs at low latitudes (DST already net-positive) or at high latitudes with low AC. The stylized historical eras show -0.01% (1970s), 0.01% (contemporary), 0.02% (future +2 °C) at 45°N — a transition from a small historical saving to a small contemporary cost, consistent in direction with the empirical literature's heterogeneity (Figure 4, Figure 5, Table 2, Figure 6, Table 3).

### 3.3 SAS: constrained activity-timing flexibility

With an unconstrained energy-only objective the daily optimum saturates at the earliest allowed start — adaptivity degenerates to a permanent shift, which we report as a structural finding rather than a benefit. Under constraint-primary optimization (displacement cap plus wake-darkness exposure cap), achievable savings are bounded tightly: at 45°N, strict caps (wake-darkness ≤ 0.5 h-equivalent, shift ≤ 1 h) yield ~0 to +0.1% — the feasible set contracts to near-ST — while relaxed caps (≤ 2 h shift, generous darkness tolerance) reach -0.38%-scale savings at the largest tested displacement. Monthly implementations retain most of the constrained daily benefit where the daily gain is material; retention ratios are unstable exactly where the gain is near zero and are reported as a constraint-response surface, not a single number (Figure 7, Table 4).

### 3.4 Load-shape and peak effects

Peak and shape effects are proportionally larger than energy effects across regimes (see accompanying repository): schedule shifts move load in time more than they reduce it, consistent with the intraday-reshaping reported for the Australian DST experiment [8] (Table 5). Reported metrics include annual and seasonal peak, P95/P99, peak-to-average ratio, ramp metrics and peak timing; SAS variants primarily relocate rather than eliminate peaks.

### 3.5 Uncertainty and structural robustness

Monte Carlo (N = 10,000; widened supports including latitude 25–55°N, heat electric share 0–0.8, envelope conductivity, night setback): P(E_DST < E_ST) = 0.26, P(E_SAS < E_ST) = 0.32, P(E_SAS < E_DST) = 0.41; median Δ_DST = 0.05% [-0.09, 0.22], median Δ_SAS(2 h) = 0.07% [-0.41, 0.41]. Carbon: P(C_DST < C_ST) = 0.10, median Δ_DST = 0.11%. Global sensitivity ranks latitude the dominant driver of the DST effect (Spearman ρ = -0.76), followed by AC prevalence (0.33) and heating electric share (-0.28); lighting efficacy is negligible (ρ = 0.01). Figure 8 shows the Monte Carlo distributions.

### 3.6 External benchmarking

The model captures the literature's *sign heterogeneity*: across ten cities spanning equatorial to continental climates under empirical weather, it yields small DST savings at some sites and small increases at others (range -0.29% to 0.12%), bracketing the meta-analytic 0.34% [9] (Figure 5) and producing the correct direction for Indiana [7] (+0.13% baseline at an Indiana-like 2006 configuration, up to +0.57% with a documented evening-activity extension, vs observed +1.00%). The Indiana gap is not closed; the residual is attributed to unmodeled behavioral rebound, institutional identification structure, and non-electric channels — reported as a domain-of-validity boundary, not tuned away.

### 3.7 Energy–carbon divergence (secondary context)

Under flat or scenario CI, energy-optimal and carbon-optimal schedules coincide (divergence ≈ 0). Under empirical hourly CI this splits by grid archetype: on solar-heavy CAISO (hourly mean CI 0.14–0.29 kgCO2/kWh), the carbon-optimal SAS differs from the energy-optimal by 0.17 h on average and the energy-optimal schedule emits ~0.02% more carbon than the carbon-optimal — a detectable but small divergence even where solar creates a strong midday trough. On flat-CI NYISO and PJM (ranges 0.25–0.28, 0.35–0.38) divergence is negligible (≈0.03 h). Across all three grids the energy and carbon objectives produce nearly identical schedules: hourly carbon variation is not a first-order reason to separate the two objectives at household-schedule scale.

## 4. Discussion

How much building flexibility does activity retiming provide? In this model, at most ~0.5% of household electricity under generous scheduling constraints, and effectively zero under strict morning-darkness limits. The benefit attributed to activity retiming is small, conditional, and heavily dependent on model structure.

Thermal inertia is the key structural moderator. In a degree-hour screening model, occupancy shifts translate immediately into heating and cooling loads, so DST can appear to save energy in electrically heated stock; in a first-order RC model the same schedule shift largely fails to move load because the building's thermal state carries over — leaving the lighting cost unopposed. Studies that estimate schedule-shifting benefits with rigid occupancy schedules and instantaneous load coupling will overstate the HVAC channel; building-flexibility models should represent occupancy timing and thermal inertia jointly [27,28]. This is also consistent with the occupant-behavior literature's finding that schedule representation materially alters simulated demand [1,2].

Which stocks and climates change sign? The DST effect is a near-cancellation that is *not* robustly negative: sign depends on latitude, heating fuel, envelope, and thermal model structure. This is consistent with part of the empirically observed heterogeneity — increases in Indiana [7], near-zero net effects in Australia [8] — and with the weather- and AC-conditioned heterogeneity reported in recent hourly-load studies [15,16], though our model captures only the demand-side mechanism, not the full behavioral response. Warming produces a bounded sign reversal in a mid-latitude band: at 40–50°N, predominantly with AC ≥ 50%, warming of 0.5–2.75 °C flips the DST effect from saving to cost — a regime boundary rather than a universal effect, consistent with the documented AC-driven growth of climate sensitivity in electricity demand [18,36].

Behavioral constraints erode theoretical flexibility. The unconstrained SAS optimum degenerates to a permanent shift; once displacement and wake-darkness limits are imposed, the feasible savings contract to tenths of a percent or less. Coordination and circadian costs are real but unquantified here — the constraint parameters are evidence-informed ranges, not estimates of tolerable disruption.

Relative to closest prior work: building-level DST simulations report component trade-offs of the same sign structure [24-26] but hold thermal structure fixed; our RC comparison is the new element and it changes the conclusion. Energy–carbon divergence is small even on a solar-heavy grid (0.17 h schedule separation, 0.02% carbon cost) and nil on flat-CI grids: hourly carbon variation is not a first-order reason to separate energy and carbon objectives for activity timing [20-22].

Limitations remain substantial: behavioral elasticities are evidence-informed ranges, not estimates; household aggregation to a single behavioral unit; empirical CI is average combustion intensity of generation, not marginal or consumption-based; the Indiana residual is unexplained by modeled channels; SAS institutional feasibility is proxied only by disruption metrics; historical scenarios are stylized, not observed data. The thermal models bound structural sensitivity rather than reproduce a specific building stock.

## 5. Conclusions

Under contemporary conditions, conventional DST is approximately energy-neutral on average in this model and plausibly energy-increasing on non-electrically-heated or warm stock; the residual saving concentrated in cold, electrically heated buildings is removed by thermal inertia in the RC model. Warming flips DST from saving to cost in a mid-latitude band within +0.50–2.75 °C — a bounded regime reversal, not a universal one. Solar-adaptive scheduling under fixed civil time offers at most ~0.5% savings under relaxed constraints and effectively none under strict circadian constraints; even on solar-heavy grids its energy and carbon objectives differ only slightly. For building energy flexibility, the actionable conclusion is methodological: activity timing is measurable but small, apparent savings depend strongly on thermal-model structure, and realistic timing constraints reduce the exploitable benefit further — flexibility studies should represent occupancy timing and thermal inertia jointly rather than translating rigid schedules.

## Data and code availability

Open-Meteo archive API responses (ERA5-based, CC-BY 4.0) and EIA-930 generation-mix pages (US government, public domain) are persisted with checksums and an acquisition ledger in data/raw/; all other inputs are generated synthetically by the repository code. The simulation code, generated datasets, and analysis scripts that support this article are available at https://github.com/bougtoir/dst-sas-energy. `make all` regenerates every reported number (the EIA-930 fetch requires a free EIA API key and is skipped gracefully without one).

## Acknowledgement

None.

## CRediT authorship contribution statement

Onishi Tatsuki: Conceptualization, Methodology, Software, Formal analysis, Writing - original draft, Writing - review & editing

## Declaration of competing interest

The author declares no competing interests.

## Declaration of Generative Artificial Intelligence (AI) in Scientific Writing

During the preparation of this work the author used Devin (devin.ai) in order to format the text and choose words that suited the tone, and to assist with code development. After using this tool/service, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

## Ethics approval

This study used only publicly available open data containing no individual-level or identifiable information; ethics-committee approval was not required.

## Funding

This research received no specific grant from any funding agency.

## Figure captions

Figure 1. Regime architecture: fixed standard time, daylight saving time, and solar-adaptive scheduling under invariant civil time.
Figure 2. Component decomposition of the DST energy effect (lighting, cooling, heating, other) across latitude and technology.
Figure 3. Comparison of ST, DST, and SAS regimes on energy, carbon, and peak metrics.
Figure 4. Climate/technology regime boundaries of the DST effect across warming, AC prevalence, and lighting efficacy.
Figure 5. Geographic heterogeneity of regime effects across ten cities under empirical weather.
Figure 6. Stylized historical-era comparison of the DST effect.
Figure 7. Pareto frontier between energy benefit and schedule-disruption cost.
Figure 8. Monte Carlo distributions (N=10,000) of DST and SAS energy effects under widened parameter supports.

Table 1. Regime comparison (ST, DST, SAS) on energy, carbon, and load metrics.
Table 2. Geographic heterogeneity of regime effects across ten cities under empirical weather.
Table 3. Stylized historical-era comparison of the DST effect.
Table 4. Constrained SAS frontier: energy benefit versus displacement/wake-darkness constraints.
Table 5. Load-shape metrics: peaks, P95/P99, peak-to-average ratio, and ramp metrics.
