import pytest

from espresso_log import ml
from espresso_log.management.commands.seed_demo_shots import make_demo_shots


@pytest.mark.parametrize(
    ("score", "label"),
    [(1.0, "Very sour"), (2.0, "Sour"), (3.0, "Balanced"), (3.9, "Bitter"), (5.0, "Very bitter")],
)
def test_describe_taste(score, label):
    assert ml.describe_taste(score) == label


def test_training_requires_minimum_shots():
    with pytest.raises(ml.NotEnoughData, match="at least 5"):
        ml.train(make_demo_shots(ml.MIN_SHOTS - 1))


def test_cross_validation_only_runs_with_enough_shots():
    assert ml.train(make_demo_shots(ml.MIN_SHOTS)).mean_absolute_error is None

    errors = ml.train(make_demo_shots(40)).mean_absolute_error
    assert set(errors) == set(ml.TARGETS)


def test_model_learns_that_finer_grind_is_more_bitter():
    model = ml.train(make_demo_shots(80))
    fine = model.predict(ml.Recipe(grind_size=9, dose=18, extraction_time=36, water_temperature=93))
    coarse = model.predict(
        ml.Recipe(grind_size=19, dose=18, extraction_time=18, water_temperature=93)
    )

    assert fine.taste > coarse.taste
    assert fine.taste_label in {"Bitter", "Very bitter"}
    assert coarse.taste_label in {"Sour", "Very sour"}


def test_suggestion_is_more_balanced_and_stays_within_brewed_range():
    model = ml.train(make_demo_shots(80))
    sour = model.predict(
        ml.Recipe(grind_size=19, dose=18, extraction_time=18, water_temperature=93)
    )
    suggestion = model.suggest(dose=18, water_temperature=93)

    assert suggestion.distance_from_balanced < sour.distance_from_balanced
    low, high = model.feature_ranges["grind_size"]
    assert low <= suggestion.recipe.grind_size <= high
    assert suggestion.recipe.dose == 18


def test_feature_importance_is_ranked_and_sums_to_one():
    weights = [w for _, w in ml.train(make_demo_shots(40)).feature_importance]
    assert weights == sorted(weights, reverse=True)
    assert sum(weights) == pytest.approx(1.0)
