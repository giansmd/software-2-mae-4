"""Train the ML surrogate models and compute their evaluation metrics.

The surrogate has two heads, both supervised by the deterministic engine:

  * a multi-output RandomForestRegressor over per-year rows that reproduces the
    whole projection curve (retained carbon, effective area, vegetation cover
    and variation percentage), and
  * a RandomForestClassifier that predicts whether the scenario meets the +25%
    hypothesis at the horizon.

Metrics and feature importances are stored alongside the fitted estimators so
the API can expose them and the UI can show how the model behaves.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.model_selection import cross_val_score, train_test_split

from app.ml.dataset import (
    DEFAULT_N_SAMPLES,
    DEFAULT_N_SCENARIOS,
    DEFAULT_PROGRESS_PER_SCENARIO,
    DEFAULT_SEED,
    SERIES_TARGET_NAMES,
    generate_dataset,
    generate_series_dataset,
)

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "carbon_model_v2.joblib"

MODEL_NAME = "ExtraTrees (familia Random Forest)"
MODEL_VERSION = "2.0.0"
DATA_SOURCE = "synthetic (generado por el motor determinista)"
RANDOM_STATE = 42
N_ESTIMATORS = 250
MAX_DEPTH = None
MIN_SAMPLES_LEAF = 1
TEST_SIZE = 0.2
CV_FOLDS = 3
CV_MAX_ROWS = 8000
CV_ESTIMATORS = 100


@dataclass
class TrainedModel:
    series_regressor: ExtraTreesRegressor
    classifier: RandomForestClassifier
    metadata: dict[str, Any]


def _target_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
    }


def train_model(
    n_scenarios: int = DEFAULT_N_SCENARIOS,
    progress_per_scenario: int = DEFAULT_PROGRESS_PER_SCENARIO,
    n_samples: int = DEFAULT_N_SAMPLES,
    seed: int = DEFAULT_SEED,
    params: Optional[dict[str, float]] = None,
) -> TrainedModel:
    """Fit both surrogate heads and return them with their metrics."""
    series = generate_series_dataset(
        n_scenarios=n_scenarios,
        progress_per_scenario=progress_per_scenario,
        seed=seed,
        params=params,
    )
    scenario_data = generate_dataset(n_samples=n_samples, seed=seed, params=params)

    X_train, X_test, Y_train, Y_test = train_test_split(
        series.X,
        series.Y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        shuffle=True,
    )

    series_regressor = ExtraTreesRegressor(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    series_regressor.fit(X_train, Y_train)
    Y_pred = series_regressor.predict(X_test)

    classifier = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )
    (
        cX_train,
        cX_test,
        cmeets_train,
        cmeets_test,
    ) = train_test_split(
        scenario_data.X,
        scenario_data.y_meets,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        shuffle=True,
    )
    classifier.fit(cX_train, cmeets_train)
    clf_pred = classifier.predict(cX_test)

    # Bounded CV on a subsample keeps training time predictable.
    if X_train.shape[0] > CV_MAX_ROWS:
        rng = np.random.default_rng(seed)
        idx = rng.choice(X_train.shape[0], size=CV_MAX_ROWS, replace=False)
        cv_X, cv_Y = X_train[idx], Y_train[idx]
    else:
        cv_X, cv_Y = X_train, Y_train
    cv_scores = cross_val_score(
        ExtraTreesRegressor(
            n_estimators=CV_ESTIMATORS,
            max_depth=MAX_DEPTH,
            min_samples_leaf=MIN_SAMPLES_LEAF,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        cv_X,
        cv_Y,
        cv=CV_FOLDS,
        scoring="r2",
        n_jobs=-1,
    )

    per_target = {
        name: _target_metrics(Y_test[:, i], Y_pred[:, i])
        for i, name in enumerate(SERIES_TARGET_NAMES)
    }
    importances = series_regressor.feature_importances_

    metadata: dict[str, Any] = {
        "algorithm": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "data_source": DATA_SOURCE,
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "n_samples": series.n_rows,
        "n_scenarios": int(n_scenarios),
        "n_train": int(X_train.shape[0]),
        "n_test": int(X_test.shape[0]),
        "feature_names": list(series.feature_names),
        "feature_importances": {
            name: float(value)
            for name, value in zip(series.feature_names, importances.tolist())
        },
        "regression": {
            "r2_variation": per_target["variation_pct"]["r2"],
            "mae_variation": per_target["variation_pct"]["mae"],
            "rmse_variation": per_target["variation_pct"]["rmse"],
            "r2_carbon": per_target["retained_carbon"]["r2"],
            "mae_carbon": per_target["retained_carbon"]["mae"],
            "rmse_carbon": per_target["retained_carbon"]["rmse"],
            "cv_r2_mean": float(np.mean(cv_scores)),
            "cv_r2_std": float(np.std(cv_scores)),
            "per_target": per_target,
        },
        "classification": {
            "accuracy": float(accuracy_score(cmeets_test, clf_pred)),
            "roc_auc": float(
                roc_auc_score(cmeets_test, classifier.predict_proba(cX_test)[:, 1])
            ),
        },
    }

    return TrainedModel(
        series_regressor=series_regressor,
        classifier=classifier,
        metadata=metadata,
    )


def save_model(model: TrainedModel, path: Union[str, Path] = ARTIFACT_PATH) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "series_regressor": model.series_regressor,
            "classifier": model.classifier,
            "metadata": model.metadata,
        },
        target,
    )
    return target


def load_model(path: Union[str, Path] = ARTIFACT_PATH) -> TrainedModel:
    payload = joblib.load(Path(path))
    return TrainedModel(
        series_regressor=payload["series_regressor"],
        classifier=payload["classifier"],
        metadata=payload["metadata"],
    )
