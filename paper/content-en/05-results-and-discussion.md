# Results and Discussion

## Model comparison

**Table 4** summarises the performance of the five evaluated algorithms, with test-set metrics and the results of ten-fold cross-validation.

[[TABLA:tab05_comparacion_modelos.csv|Comparison of the five evaluated models. R², MAE and RMSE on the test set, and mean R² with its deviation across cross-validation folds. The three ensembles exceed the success criterion of R² ≥ 0.85.]]

The three tree ensembles exceeded the established success criterion (R² ≥ 0.85), while the linear models remained at R² = 0.963. The **Extra Trees** ensemble obtained the best performance: R² = 1.000 on the test set, MAE = 0.014 percentage points and RMSE = 0.026, with a standard deviation of zero across the ten cross-validation folds. *Random Forest* reached identical R² values but with an MAE more than three times higher (0.048). *Gradient Boosting* fell slightly below (R² = 0.9996).

**Figure 3** visually compares the coefficient of determination on the test set and in cross-validation. The equivalence between both metrics for each model rules out overfitting: performance remains stable outside the training partition.

[[FIG:fig04_comparacion_modelos.png|Comparison of the coefficient of determination on the test set and in cross-validation for the five evaluated models. The proximity between both bars in each model indicates absence of overfitting.]]

**Figure 4** presents the scatter of predicted versus observed values for the selected model, with practically perfect alignment to the identity line and no patterns of systematic deviation in any segment of the range.

[[FIG:fig05_predicho_observado.png|Predicted versus observed values for the Extra Trees model. The absence of curvature or heteroscedasticity indicates that the ensemble reproduces the engine's response surface without directional bias.]]

## Statistical validation

**Table 5** reports the contrast of the best model against each alternative, employing the paired Student's t test on the per-fold scores.

[[TABLA:tab06_pruebas_estadisticas.csv|Statistical significance tests of the Extra Trees model against the alternative models (paired t and Wilcoxon on cross-validation folds).]]

All comparisons were statistically significant with p < 0.01. The difference from the linear models reached a t statistic of 25.91, and from *Random Forest* and *Gradient Boosting* values of 5.23 and 7.49 respectively. The Wilcoxon test, operating on only ten folds, presents the maximum possible granularity (p = 0.0625), an intrinsic limitation of the fold sample size and not evidence of absence of effect.

The 95 % confidence interval for the mean absolute error, obtained by bootstrap resampling with 500 replicates, was [0.012; 0.016] percentage points, with a mean of 0.014. 

The Shapiro-Wilk test on the residuals was significant (W = 0.768; p < 0.001), indicating that the errors do not follow a normal distribution. Both tests therefore converge on the ensemble’s superiority despite non-normality. Given that the residuals present markedly concentrated tails —most errors close to zero—, the deviation from normality reflects a precision superior to what the parametric assumption would anticipate, not a defect of the model; this pattern is characteristic of emulators over deterministic models, whose response surface lacks the random noise that usually produces Gaussian residuals.

## Interpretability and explainability

**Table 6** presents the permutation importance of each variable, with its variability over ten repetitions.

[[TABLA:tab07_importancia_variables.csv|Permutation importance of the variables of the Extra Trees model (10 repetitions). The reduced standard deviation in the relevant variables confirms the stability of the estimation.]]

**Figure 5** graphically represents that hierarchy of contributions, with error bars corresponding to the ten repetitions.

[[FIG:fig07_importancia.png|Permutation importance of the variables of the Extra Trees model, with error bars corresponding to ten repetitions.]]

The sea-level rise scenario led the contribution (mean importance = 1.071), followed by the hydrological restoration level (0.839); both exhibited small standard deviations (0.053 and 0.046), indicating stability of the estimation. The time-horizon, baseline-area, carbon-density and NDVI variables presented importance indistinguishable from zero. This is substantively relevant and not an artefact: in the engine's formulation, the percentage variation depends exclusively on the restoration level and the sea-level scenario, while baseline area and density determine the absolute carbon but cancel out in the percentage ratio. This coherence indirectly validates the attribution procedure.

The distinction is not merely technical. The discarded variables —baseline area and density— are precisely those that determine the absolute carbon at risk, information critical for the economic valorisation of the ecosystem. A model optimised solely to predict percentage variation is blind to that dimension, which reinforces the need to expose both metrics jointly in any decision-support instrument.

## Hypothesis contrast

**Figure 6** disaggregates the response by hydrological restoration band, contrasting it with the +25 % threshold postulated in the hypothesis.

[[FIG:fig08_hipotesis.png|Mean variation of retained carbon by hydrological restoration band, contrasted with the +25 % hypothesis threshold. The monotonically increasing relationship indicates diminishing but sustained returns.]]

The results show a monotonically increasing relationship between restoration level and carbon variation. In the low band (0–25 %), the mean variation was −17.64 %, with a net loss of carbon. In the mid-low band (25–50 %) practical equilibrium was reached (−1.92 %). The mid-high band (50–75 %) recorded a mean gain of 5.79 %, with 17.06 % of scenarios exceeding the threshold. The high band (75–100 %) reached a mean gain of 11.24 %, with 34.85 % of scenarios exceeding the +25 % threshold.

**The +25 % hypothesis is not verified in general**, but conditionally: only the highest restoration band produces, in approximately one third of the scenarios, increases that exceed the threshold. The mean variation of that band (11.24 %) falls below the postulated value, indicating that exceeding the threshold depends on the interaction with the sea-level scenario and the time horizon.

## Emulator performance

Extra Trees reproduced the deterministic engine with practically exact fidelity (R² = 1.000; MAE = 0.014 percentage points), as expected for an emulator of a smooth, noise-free and fully observable response surface. Jiang et al. (2021) used physics-informed neural operators to accelerate a costly hydrodynamic model while maintaining fidelity [6]. Here, by contrast, the emulator enables exhaustive scenario exploration through an interactive interface. Unlike approaches with sparse guide data [24], the full surface is accessible, favouring recursive partitioning methods.

Consequently, these results **must not be interpreted as evidence that machine learning outperforms mechanistic models in predicting blue carbon**. The relevant comparison in the literature involves field observations with noise, where differences between model families are substantially smaller. The value of the emulator is instrumental and must be declared as such.

## Interpretability and coherence with the physical model

The key explainability finding is that variable attribution coincides with the engine's algebraic structure. Spurious importance for variables with no algebraic effect would have indicated an estimator or partition problem; the observed consistency supports permutation importance as a verification instrument when model opacity hinders direct inspection.

The result further illustrates a frequently neglected principle: **the distinction between variables relevant to the system's absolute state and variables relevant to its relative change**. Area and carbon density determine the total stock —decisive for economic valorisation [10]— but are irrelevant to the modelled percentage variation. Zia et al. (2025) warn that operational datasets commonly present missing values [25]; a model discarding variables for their null contribution to one metric may discard those sustaining other decision dimensions. Per Durden (2025)'s insistence that development focus on outcomes meaningful to users [17], the dashboard exposes both dimensions explicitly.

## Implications for the restoration hypothesis

The hypothesis contrast yielded a more nuanced result than the initial postulate: the claim that hydrological restoration can increase carbon retention by at least 25 % by 2050 is sustained not in general, but conditionally in the highest intervention band and with an approximate probability of one third.

This dialogues directly with the coastal wetland restoration literature. Twomey et al. (2024) note that hydrological-restoration guidance remains limited and region-specific [10], suggesting that general aspirational thresholds are difficult to sustain on available evidence, and that the underlying function-service relationships are non-uniform across sites [10]. Buffington et al. (2021) provide convergent evidence that salinity scenarios and productivity functions determine carbon-capture projections under sea-level rise [15]; the present work reproduces that pattern — exceeding the threshold depends on the interaction between restoration level, sea-level rise scenario and time horizon.

The intermediate bands are not ineffective: they produce a transition from net loss to net gain (−17.64 % to −1.92 %), a substantial benefit below the aspirational threshold. Quantifying this transition supports the proactive management of future ecosystem dynamics [9].

## Traceability, architecture and governance

Separating empirical from simulated data responds to calls for frank discussion of digital-twin limitations [5, 7]. The 39 version-control commits link quality findings to their corrections, supporting reproducibility where convergence between data infrastructures remains unresolved [29].

On governance, Haraguchi et al. (2024) examine where urban digital twins are effective [32], Hananto and Veza (2025) propose explicit governance frameworks [33], DeVries (2024) identifies privacy and data-sovereignty challenges [34], and Garske et al. (2024) analyse data governance in the sustainable transition [35]. The present work does not address these dimensions — a limitation relative to the state of the art.

## Comparison with related applications

Related applications also link hydrology and carbon: water-table depth determines peat-soil emissions [36]. Other water-system digital twins use microservices or edge architectures [37, 38], whereas this prototype deliberately uses a simpler monolithic analytical module. Robotic platforms can provide high-resolution marine data but face coverage and representativeness challenges [8]; open satellite data offer temporal coverage here, but limit spatial resolution and update frequency.

## Limitations

Five limitations must be considered when interpreting these results.

The first and most important is that **the target variable is simulated**. Although the covariables come from published literature and the engine's structure is coherent with available evidence, the performance metrics quantify the emulator's fidelity to the engine, not predictive capacity over field observations. Twomey et al. (2024) warn that hydrological restoration models may not be transferable and that predictive capacity is restricted to the construction data's conditions [10]; that warning applies in full here.

The second is the **absence of spatial structure**: the model operates on site-scale aggregated values, without representing topographic heterogeneity or salinity gradients — precisely the elevation-uncertainty limitation Twomey et al. (2024) identify as key [10], and Buffington et al. (2021) demonstrate carbon projections' sensitivity to salinity scenarios [15].

The third is the **simplified representation of temporal dynamics**, a linear progression between initial year and horizon when real accretion and accumulation trajectories follow asymptotic patterns.

The fourth is the **granularity of the statistical contrast**: with ten folds, the Wilcoxon test reaches its minimum possible probability without crossing the conventional 0.05 threshold — intrinsic to the design, not to the effect's magnitude; the paired t test, which exploits the differences' magnitude, reaches p < 0.001 in all comparisons.

The fifth is the **absence of stakeholder participation**. Durden (2025) stresses that stakeholder incorporation broadens collaborative decision capacity [17], and DeVries (2024) highlights the governance challenges of these technologies [34]. The present work defines its success criteria without consulting the Sanctuary's managers — a gap relative to state-of-the-art recommendations.

## Future work

Four lines of continuity derive from these limitations. Incorporating SNLMT field measurements would allow recalibrating the engine and validating projections against independent observations, heeding the transferability requirement [10]. Integrating cover and elevation raster layers would enable representing spatial heterogeneity and band-differentiated scenarios, responding to the salinity limitation [15]. On architecture, migration towards services —following Picone et al. (2023) for edge deployments [20] and Rodríguez-Alonso et al. (2024) for water platforms [37]— would allow scaling and interoperability. Finally, a structured stakeholder participation process, per Durden (2025) [17] and Hananto and Veza (2025) [33], would align the system's success criteria with the Sanctuary managers' effective needs.
