# Analysis of the problem

## From model to digital twin

The conceptual distinction between a model and a digital twin is foundational to this work. Wright and Davidson (2020) argue that the difference lies not in the sophistication of the underlying model but in the coupling: while a conventional model represents a system in a static or unidirectional manner, a digital twin maintains a bidirectional link with its physical counterpart, continuously updating itself from observed data [3].

Rasheed et al. (2020) propose an operative definition: a digital twin is a virtual representation of a physical asset enabled by data and simulators for prediction, optimisation and real-time monitoring [1]; Verdouw et al. (2021) emphasise the temporal dimension, describing it as a dynamic representation mirroring states and behaviour throughout the object's life cycle [2]. Both formulations converge on three constitutive elements: a physical counterpart, a computational model and a data flow keeping them synchronised. Durão et al. (2018) systematise the requirements the literature imposes on the concept — representing not only the asset's geometry and structure but also its operative behaviour under changing conditions [18] — which translates directly to the environmental domain: a digital twin of an ecosystem must represent its dynamics, not merely its state.

## Architectures and implementation frameworks

Ecosystem-scale digital twins require architectures integrating heterogeneous sources. Nativi et al. (2021) describe the Destination Earth digital ecosystem [19]; Picone et al. (2023) propose modular edge twins to reduce latency [20]; and Raes et al. (2022) present DUET, an interoperable smart-city framework [21].

Chen et al. (2025) propose game-theoretic optimisation for federated twins, noting sensor-number and cost constraints relevant to resource-limited environmental deployments [22]. Khan et al. (2025) propose TwinEco for ecological digital twins [23], while Qamsane et al. (2021) define scope, modelling and validation phases [16], paralleling CRISP-DM.

## Modelling, emulation and informed physics

A central challenge is balancing physical fidelity and computational cost. Jiang et al. (2021) used physics-informed neural operators to emulate coastal flood models, achieving up to 45-fold speed-ups while predicting sea-surface height accurately [6].

Yang et al. (2024) note that physics-informed approaches often use only 1–10 % of available simulation points [24]. Zia et al. (2025) propose physics-encoded residual blocks and note missing operational data from power and sensor failures or adverse weather [25]; Dilip (2024) applies physics-informed networks to asphalt pavements [26]. More broadly, Reichstein et al. (2019) call for integrating deep learning and process understanding in Earth-system science [27].

## Data, sensors and uncertainty

Digital-twin quality is bounded by data quality. Guo et al. (2017) review wetland remote sensing, including aerial photography’s resolution advantages and coverage limits [11]; Jafarzadeh et al. (2022) synthesise three decades of wetland-monitoring practices [12].

Ecological data have structural biases. Meyer et al. (2015) set global priorities for biodiversity-distribution information [28]; Meyer et al. (2016) identify taxonomic, spatial and temporal gaps in occurrence data [13]. Mollenhauer et al. (2018) find geographical gaps in European long-term monitoring [14], while Jeffery et al. (2021) note that data-infrastructure convergence remains unresolved [29].

Uncertainty must be propagated explicitly. Buffington et al. (2021) show salinity scenarios and productivity functions determine carbon projections under sea-level rise [15]. Cabrera et al. (2021) caution that smartphone-weather results from one device model cannot be generalised beyond the observed domain [30].

## Environmental applications and governance

The recent literature insists that the value of an environmental digital twin is decided by its usefulness for decision-making, not its technical sophistication. Durden (2025) identifies four challenges conditioning the generation of products meaningful to user needs, arguing that use-case development must focus explicitly on those outcomes and that incorporating stakeholders beyond decision-makers broadens collaborative capacity [17]. Data may also come from non-professional sources: Brown and Williams (2019) argue that confirmatory hypothesis testing is entirely possible with large-scale internet-based citizen science projects designed for that purpose, though such projects remain scarce [31].

De Koning et al. (2023) warn that adopting the concept in ecology must be accompanied by a frank discussion of its inherent limitations, to avoid expectations that mislead modellers, researchers and policy-makers [5]; Tzachor et al. (2023) extend that warning to the oceanic domain [7]. Governance work examines where urban digital twins are effective [32], proposes frameworks for aligning standards [33], and addresses privacy and data sovereignty [34] and the role of data governance in the sustainable transition [35].

Applications include climate-adaptation and water-management twins, where water-table depth determines peat-soil carbon emissions and hydrological variability guides restoration [36]; microservices platforms for water treatment [37]; edge twins for off-grid water systems [38]; and smart-farming deployments, still relatively scarce [2].

## Coastal wetlands and blue carbon

Twomey et al. (2024) argue that blue-carbon-oriented restoration renews the impetus for recovering hydrologically modified coastal plains, but warn that guidance remains limited and frequently focused on particular regions or risks [10]. They stress that hydrologically influenced ecosystem functions determine services such as habitat provision, water quality, carbon capture and coastal protection; that models may not be transferable across sites, with predictive capacity restricted to the construction data's conditions; and that elevation-data uncertainty and soil surface change are key limitations for projecting restoration-site impacts [10].

Lu et al. (2026) explore specifically the concept of wetland digital twins for monitoring and management, noting that the ecosystem's state and dynamics under future scenarios are essential for proactive stakeholder management, and that wetlands have suffered significant global losses and degradation over the last centuries [9].

## The CRISP-DM methodology

CRISP-DM —*Cross-Industry Standard Process for Data Mining*— organises an analytical project into six iterative phases: business understanding, data understanding, preparation, modelling, evaluation and deployment. Unlike algorithm-centred approaches, the standard demands that every analytical artefact be traceable to an explicit business objective with success criteria defined beforehand — a structure paralleling the frameworks proposed for digital twin development [16] and the insistence that use cases start from user needs rather than available technical capabilities [17]. The present work adopts the framework and documents each phase with verifiable products.
