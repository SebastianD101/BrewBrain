"""Learns how recipe choices affect a shot, and uses that to predict and suggest recipes.

A random forest maps the four recipe inputs a barista controls (grind, dose, time,
temperature) to three outcomes (yield, taste, strength). Forests suit this problem: the
datasets are small, the relationships are non-linear, and no feature scaling is needed.
"""

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold, cross_val_predict

from .models import EspressoShot

FEATURES = ("grind_size", "dose", "extraction_time", "water_temperature")
TARGETS = ("yield_amount", "taste", "strength")
FEATURE_LABELS = {
    "grind_size": "Grind size",
    "dose": "Dose",
    "extraction_time": "Extraction time",
    "water_temperature": "Water temperature",
}

MIN_SHOTS = 5  # Below this, predictions are noise.
MIN_SHOTS_FOR_CV = 10  # Below this, cross-validated error is too unstable to show.
BALANCED = 3.0  # Middle of the 1–5 taste and strength scales.
SUGGESTION_GRID_STEPS = 25


class NotEnoughData(Exception):
    pass


def describe_taste(score: float) -> str:
    return _describe(score, ("Very sour", "Sour", "Balanced", "Bitter", "Very bitter"))


def describe_strength(score: float) -> str:
    return _describe(score, ("Very weak", "Weak", "Balanced", "Strong", "Very strong"))


def _describe(score: float, labels: tuple[str, ...]) -> str:
    for upper, label in zip((1.75, 2.5, 3.5, 4.25), labels, strict=False):
        if score < upper:
            return label
    return labels[-1]


@dataclass(frozen=True)
class Recipe:
    grind_size: float
    dose: float
    extraction_time: float
    water_temperature: float

    def as_row(self) -> list[float]:
        return [getattr(self, name) for name in FEATURES]


@dataclass(frozen=True)
class Prediction:
    recipe: Recipe
    yield_amount: float
    taste: float
    strength: float

    @property
    def taste_label(self) -> str:
        return describe_taste(self.taste)

    @property
    def strength_label(self) -> str:
        return describe_strength(self.strength)

    @property
    def brew_ratio(self) -> float:
        return self.yield_amount / self.recipe.dose

    @property
    def distance_from_balanced(self) -> float:
        return float(np.hypot(self.taste - BALANCED, self.strength - BALANCED))


@dataclass
class BrewModel:
    estimator: RandomForestRegressor
    n_shots: int
    feature_ranges: dict[str, tuple[float, float]]
    mean_absolute_error: dict[str, float] | None

    @property
    def feature_importance(self) -> list[tuple[str, float]]:
        """Recipe inputs ranked by how much they drive the outcomes in this user's data."""
        pairs = zip(FEATURES, self.estimator.feature_importances_, strict=True)
        return sorted(
            ((FEATURE_LABELS[name], float(weight)) for name, weight in pairs),
            key=lambda pair: pair[1],
            reverse=True,
        )

    def predict(self, recipe: Recipe) -> Prediction:
        return self._predict_many([recipe])[0]

    def suggest(self, dose: float, water_temperature: float) -> Prediction:
        """Search grind size and shot time for the recipe predicted closest to balanced.

        The search stays inside the ranges the user has actually brewed, since a forest
        cannot extrapolate beyond the data it was trained on.
        """
        grind_values = np.linspace(*self.feature_ranges["grind_size"], SUGGESTION_GRID_STEPS)
        time_values = np.linspace(*self.feature_ranges["extraction_time"], SUGGESTION_GRID_STEPS)
        candidates = [
            Recipe(float(grind), dose, float(seconds), water_temperature)
            for grind in grind_values
            for seconds in time_values
        ]
        return min(self._predict_many(candidates), key=lambda p: p.distance_from_balanced)

    def _predict_many(self, recipes: list[Recipe]) -> list[Prediction]:
        outputs = self.estimator.predict(np.array([r.as_row() for r in recipes]))
        return [
            Prediction(recipe, float(y), float(taste), float(strength))
            for recipe, (y, taste, strength) in zip(recipes, outputs, strict=True)
        ]


def train(shots: Iterable[EspressoShot]) -> BrewModel:
    shots = list(shots)
    if len(shots) < MIN_SHOTS:
        raise NotEnoughData(
            f"Log at least {MIN_SHOTS} shots to train a model ({len(shots)} so far)."
        )

    X = np.array([[getattr(shot, name) for name in FEATURES] for shot in shots], dtype=float)
    y = np.array([[getattr(shot, name) for name in TARGETS] for shot in shots], dtype=float)

    estimator = _new_estimator().fit(X, y)
    return BrewModel(
        estimator=estimator,
        n_shots=len(shots),
        feature_ranges={
            name: (float(X[:, i].min()), float(X[:, i].max())) for i, name in enumerate(FEATURES)
        },
        mean_absolute_error=_cross_validated_error(X, y),
    )


def _new_estimator() -> RandomForestRegressor:
    # min_samples_leaf=2 smooths predictions on the small datasets home baristas produce.
    return RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42)


def _cross_validated_error(X: np.ndarray, y: np.ndarray) -> dict[str, float] | None:
    if len(X) < MIN_SHOTS_FOR_CV:
        return None
    folds = KFold(n_splits=5, shuffle=True, random_state=42)
    predicted = cross_val_predict(_new_estimator(), X, y, cv=folds)
    errors = mean_absolute_error(y, predicted, multioutput="raw_values")
    return dict(zip(TARGETS, (float(e) for e in errors), strict=True))
