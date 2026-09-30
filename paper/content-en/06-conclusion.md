# Conclusion

This work developed a digital twin of the Los Manglares de Tumbes National Sanctuary and applied CRISP-DM to model, explain and communicate blue carbon variation under hydrological restoration and sea-level rise scenarios through 2050. Conclusions follow the four business-phase success criteria.

**Predictive performance.** The criterion of an out-of-sample R² greater than or equal to 0.85 was comfortably met. The three evaluated tree ensembles exceeded the threshold, and the Extra Trees model reached R² = 1.000 with a mean absolute error of 0.014 percentage points and a 95 % confidence interval of [0.012; 0.016]. The null standard deviation across the ten cross-validation folds confirms the stability of performance. The criterion of an MAE equal to or below 3 percentage points was also satisfied.

**Statistical superiority.** The criterion of significant difference from the reference linear model was met in all comparisons: the paired t test yielded p < 0.001 against the linear models (t = 25.91) and against the remaining ensembles (t between 5.23 and 7.49); the Wilcoxon test converges in the same direction, and the verified non-normality of the residuals (Shapiro-Wilk, p < 0.001) justifies its inclusion.

**Explainability.** Permutation importance identified the sea-level rise scenario (mean importance = 1.071) and the hydrological restoration level (0.839) as the only variables with relevant contribution, with reduced standard deviations. This result coincides exactly with the algebraic structure of the engine, which constitutes an indirect validation of the attribution procedure and a practical demonstration that interpretability can audit black-box models.

**Hypothesis contrast.** The hypothesis that hydrological restoration can increase carbon retention by at least 25 % by 2050 **is not verified in general**. It is met conditionally: in the highest restoration band (75–100 %), 34.85 % of scenarios exceed the threshold, with a mean gain of 11.24 %. In contrast, the medium restoration bands produce the transition from net loss to net gain without reaching the aspirational threshold.

These findings must be interpreted in light of the study's main limitation: the target variable is simulated. The conclusions describe the emulator's fidelity to the deterministic engine and the physical model's internal coherence, not predictive capacity over field observations. Substituting the calibrated parameters with SNLMT measurements —currently under way through the region's blue carbon certification process [9]— is the necessary step to confer empirical validity on the projections.

Beyond the numerical results, the work contributes three reusable products: a hybrid dataset anchored in published real data with explicit component traceability; an analytical module implementing the six CRISP-DM phases reproducibly and verifiably; and an interactive dashboard exposing interpretability as a first-class capability, allowing non-specialised managers to interrogate the model and understand each variable's contribution.

The approach sustains management decisions with quantified evidence: an instrument that estimates the restoration level required to transition from net loss to net carbon gain, and makes explicit that response's dependence on the climate scenario, has direct value for conservation planning, investment prioritisation and the technical substantiation of blue carbon certification.

Finally, version control —39 commits linking changes to motivating findings— makes each result traceable to its code state, an essential condition for reproducible computational research.
