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

All comparisons were statistically significant with p < 0.01. The difference from the linear models reached a t statistic of 25.91, and from *Random Forest* and *Gradient Boosting* values of 5.23 and 7.49 respectively. It is important to note that the Wilcoxon test, operating on only ten folds, presents the maximum possible granularity (p = 0.0625), an intrinsic limitation of the fold sample size and not evidence of absence of effect.

The 95 % confidence interval for the mean absolute error, obtained by bootstrap resampling with 500 replicates, was [0.012; 0.016] percentage points, with a mean of 0.014. The narrowness of the interval confirms the stability of performance across resamples.

The Shapiro-Wilk test on the residuals was significant (W = 0.768; p < 0.001), indicating that the errors do not follow a normal distribution. This finding justifies the inclusion of the non-parametric Wilcoxon test as a complementary contrast and reinforces the robustness of the conclusion: despite the non-normality, both tests converge on the superiority of the ensemble.

The magnitude of that non-normality deserves precision. Given that the residuals present a distribution with markedly concentrated tails —with most errors close to zero—, the deviation from normality reflects a precision superior to what the parametric assumption would anticipate, not a defect of the model. This pattern is characteristic of emulators over deterministic models, where the response surface lacks the random noise that usually produces Gaussian residuals.

## Interpretability and explainability

**Table 6** presents the permutation importance of each variable, with its variability over ten repetitions.

[[TABLA:tab07_importancia_variables.csv|Permutation importance of the variables of the Extra Trees model (10 repetitions). The reduced standard deviation in the relevant variables confirms the stability of the estimation.]]

**Figure 5** graphically represents that hierarchy of contributions, with error bars corresponding to the ten repetitions.

[[FIG:fig07_importancia.png|Permutation importance of the variables of the Extra Trees model, with error bars corresponding to ten repetitions.]]

The sea-level rise scenario led the contribution (mean importance = 1.071), followed by the hydrological restoration level (0.839). Both variables exhibited small standard deviations (0.053 and 0.046), which indicates stability of the estimation. The time-horizon, baseline-area, carbon-density and NDVI variables presented importance indistinguishable from zero.

This result is substantively relevant and not an artefact. In the engine's formulation, the percentage variation depends exclusively on the restoration level and the sea-level scenario, while the baseline area and density determine the absolute carbon but cancel out in the percentage ratio. The coherence between the empirical importance and the structure of the physical model constitutes an indirect validation of the attribution procedure.

The distinction is not merely technical. The discarded variables —baseline area and density— are precisely those that determine the absolute carbon at risk, information critical for the economic valorisation of the ecosystem. A model optimised solely to predict percentage variation is blind to that dimension, which reinforces the need to expose both metrics jointly in any decision-support instrument.

## Hypothesis contrast

**Figure 6** disaggregates the response by hydrological restoration band, contrasting it with the +25 % threshold postulated in the hypothesis.

[[FIG:fig08_hipotesis.png|Mean variation of retained carbon by hydrological restoration band, contrasted with the +25 % hypothesis threshold. The monotonically increasing relationship indicates diminishing but sustained returns.]]

The results show a monotonically increasing relationship between restoration level and carbon variation. In the low-restoration band (0–25 %), the mean variation was −17.64 %, with a net loss of carbon. In the mid-low band (25–50 %) practical equilibrium was reached (−1.92 %). The mid-high band (50–75 %) recorded a mean gain of 5.79 %, with 17.06 % of scenarios exceeding the threshold. The high band (75–100 %) reached a mean gain of 11.24 %, with 34.85 % of scenarios exceeding the +25 % threshold.

**The +25 % hypothesis is not verified in general**, but conditionally: only the highest restoration band produces, in approximately one third of the scenarios, increases that exceed the threshold. The mean variation of that band (11.24 %) falls below the postulated value, which indicates that exceeding the threshold depends on the interaction with the sea-level scenario and the time horizon.

## Emulator performance

The tree ensembles reproduced the deterministic engine with practically exact fidelity. The Extra Trees model reached a coefficient of determination of 1.000 with a mean absolute error of 0.014 percentage points. This level of precision is characteristic of emulators trained on the output of a deterministic model: the response surface is smooth, free of measurement noise and fully observable.

The literature on emulation of physical models allows situating this result. Jiang et al. (2021) obtained speed-ups of up to forty-five times relative to the reference numerical model via physics-informed neural operators, maintaining precision in the prediction of sea surface height [6]. The difference in approach is revealing: while there the objective was to replace a high-computational-cost hydrodynamic model while preserving its fidelity, here the emulator fulfils a different function —enabling exhaustive exploration of the scenario space and feeding an interactive interface.

That distinction also explains the performance gap relative to the linear models. Yang et al. (2024) warn that many physics-informed approaches restrict their scope to the use of sparse guide data, inefficiently exploiting the available simulation results [24]. In the present case the surface is fully accessible, a condition that favours recursive partitioning methods and that is not verified in applications where direct simulation is prohibitive.

Consequently, these results **must not be interpreted as evidence that machine learning outperforms mechanistic models in predicting blue carbon**. The relevant comparison in the literature involves field observations with noise, where differences between model families are substantially smaller. The value of the emulator is instrumental and must be declared as such.

## Interpretability and coherence with the physical model

The most informative finding of the explainability analysis was not which variables turned out to be important, but that the attribution coincided exactly with the algebraic structure of the engine. The sea-level rise scenario and the restoration level dominate the prediction; the baseline variables cancel out in the percentage ratio.

This coincidence fulfils an audit function. Had permutation importance assigned spurious relevance to variables with no algebraic effect, it would have revealed a problem in the estimator or in the data partition. The observed consistency constitutes an indirect validation of the procedure and supports its use as a verification instrument in systems where the opacity of the model hinders direct inspection.

The result further illustrates a frequently neglected principle of interpretability: **the distinction between variables relevant to the absolute state of the system and variables relevant to its relative change**. Area and carbon density determine the total stock —decisive information for the economic valorisation of the ecosystem [10]— but are irrelevant to the modelled percentage variation. Zia et al. (2025) warn that operational datasets commonly present missing values due to sensor failures and adverse weather conditions [25]; a model that discards variables for their null contribution to a specific metric may be discarding precisely those that sustain other dimensions of the decision.

Durden (2025) insists that the development of environmental digital twins must focus on outcomes meaningful to user needs and not on isolated technical capabilities [17]. The foregoing distinction is a concrete application of that principle: a Sanctuary manager who consults only the percentage variation will obtain no information about the absolute carbon at risk, and vice versa. The developed dashboard exposes both dimensions explicitly to avoid that partial reading.

## Implications for the restoration hypothesis

The hypothesis contrast yielded a more nuanced result than the initial postulate. The claim that hydrological restoration can increase carbon retention by at least 25 % by 2050 is not sustained in general, but conditionally in the highest intervention band and with an approximate probability of one third.

This result dialogues directly with the literature on coastal wetland restoration. Twomey et al. (2024) note that guidance for hydrological restoration remains limited and is frequently focused on particular regions, activities or risks [10], which suggests that aspirational thresholds of general scope are difficult to sustain on the available evidence. The same authors document that ecosystem functions influenced by the hydrological regime determine services such as carbon capture and coastal protection, but that this relationship is not uniform across sites [10].

Buffington et al. (2021) provide convergent evidence by demonstrating that both salinity scenarios and productivity functions are determinant in projecting how carbon capture may change under sea-level rise [15]. The present work reproduces that pattern: exceeding the threshold depends on the interaction between restoration level, sea-level rise scenario and time horizon.

The operative reading of the finding deserves emphasis. The intermediate restoration bands, far from being ineffective, produce the transition from net loss to net gain —from −17.64 % to −1.92 %—, which represents a substantial benefit even though it does not reach the aspirational threshold. Lu et al. (2026) stress that the state and dynamics of the ecosystem under future scenarios are essential for stakeholders to carry out proactive management oriented towards conserving the ecosystem and supporting its restoration [9]; an instrument that quantifies that transition serves that purpose even if its result does not confirm the initial hypothesis.

## Traceability, architecture and governance

The explicit separation between the empirical and the simulated portions of the dataset responds to a requirement that the literature formulates clearly. De Koning et al. (2023) warn that the concept of the digital twin in ecology must be accompanied by a frank discussion of its inherent limitations, so as not to generate expectations that mislead modellers, researchers, policy-makers and resource managers [5]. Tzachor et al. (2023) extend the warning to the oceanic domain, anticipating ethical concerns and uncertainties in the digital representation of marine ecosystem services [7]. Declaring which part of the result rests on observation and which part on projection is a direct response to that requirement.

Version control discipline sustained the traceability of the artefact. The 39 recorded commits document not only the incorporation of functionality, but the complete review cycle: every detected quality finding was associated with a commit recording its correction. Jeffery et al. (2021) argue that convergence between data infrastructures is not yet resolved [29]; the systematic record of changes constitutes a modest but effective contribution to reproducibility in a context where such mechanisms are scarce.

Regarding governance, Haraguchi et al. (2024) examine the specific areas where urban digital twins are effective and those where their impact is bounded [32], while Hananto and Veza (2025) propose aligning standards and practices through explicit governance frameworks [33]. DeVries (2024) identifies the privacy and data sovereignty challenges that emerge from these technologies [34], and Garske et al. (2024) analyse the role of data governance in the sustainable transition [35]. The present work does not address these dimensions, which constitutes a limitation relative to the state of the art in the matter.

## Comparison with related applications

It is worth contrasting the case presented here with implementations documented in neighbouring domains. Henriksen et al. (2023) developed a digital twin for climate adaptation and water management, and established that the depth of the water table is the determining variable of carbon emissions in peat soils, with knowledge of hydrological variability being decisive for guiding the restoration of drained peatlands [36]. There is here a conceptual convergence: in both cases the hydrological variable governs the carbon response, although the ecosystems differ.

Rodríguez-Alonso et al. (2024) implemented a platform for water treatment plants on a microservices architecture, oriented towards optimising operation and maintenance through machine learning and simulation [37]. Alenezi and Alabaiadly (2026) review the application of digital twins and edge computing to small off-grid water systems [38]. The architecture of the present work is substantially simpler: a monolithic analytical module with an interactive interface, without the separation into services that characterises production platforms. That simplicity is deliberate and responds to the scope of the prototype, but it should be recognised as a difference relative to the architectural state of the art.

On the data plane, Aguzzi et al. (2025) demonstrate that robotic platforms generate high-resolution marine data, but note that challenges of spatial coverage, temporal continuity and ecological representativeness persist [8]. The present work depends on open satellite data and published literature, which guarantees extensive temporal coverage but limits spatial resolution to the site scale and restricts updating to the frequency of the available series.

## Limitations

The present work presents five limitations that must be considered when interpreting its results.

The first and most important is that **the target variable is simulated**. Although the covariates come from published literature and the structure of the engine is coherent with the available evidence, the performance metrics quantify the fidelity of the emulator relative to the engine, not the predictive capacity over field observations. Twomey et al. (2024) warn that hydrological restoration models may not be transferable to other sites and that their predictive capacity is restricted to the specific conditions of the data used in their construction [10]; that warning applies in full here.

The second is the **absence of spatial structure**. The model operates on values aggregated at the site scale, without representing topographic heterogeneity or salinity gradients. Twomey et al. (2024) identify precisely the uncertainty in elevation data as a key limitation of restoration models [10], and Buffington et al. (2021) demonstrate the sensitivity of carbon projections to salinity scenarios [15].

The third is the **simplified representation of temporal dynamics**, which employs a linear progression between the initial year and the horizon when the real trajectories of accretion and accumulation follow asymptotic patterns.

The fourth is the **granularity of the statistical contrast**. With ten cross-validation folds, the Wilcoxon test reaches its minimum possible probability value without being able to cross the conventional 0.05 threshold. This limitation is intrinsic to the design and not to the magnitude of the effect; the paired t test, which exploits the magnitude of the differences, reaches significance with p < 0.001 in all comparisons.

The fifth is the **absence of stakeholder participation**. Durden (2025) stresses that the incorporation of stakeholders broadens the capacity for collaborative decision-making [17], and DeVries (2024) highlights the governance challenges that emerge from these technologies [34]. The present work defines its success criteria without consulting the Sanctuary's managers, which constitutes a gap relative to the recommendations of the state of the art.

## Future work

Four lines of continuity derive from these limitations. The incorporation of field measurements from the SNLMT would allow recalibrating the engine and validating the projections against independent observations, heeding the transferability requirement noted by Twomey et al. (2024) [10]. The integration of raster layers of cover and elevation would enable the representation of spatial heterogeneity and the exploration of scenarios differentiated by band, responding to the limitation identified by Buffington et al. (2021) regarding salinity [15].

On the architectural plane, migration towards a services architecture —following the patterns documented by Picone et al. (2023) for edge deployments [20] and by Rodríguez-Alonso et al. (2024) for water platforms [37]— would allow scaling the system and facilitating its interoperability with other data infrastructures. Finally, the incorporation of a structured stakeholder participation process, in line with the recommendations of Durden (2025) [17] and the governance frameworks of Hananto and Veza (2025) [33], would allow aligning the system's success criteria with the effective needs of the Sanctuary's managers.
