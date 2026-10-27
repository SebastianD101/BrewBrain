import pytest

from espresso_log.management.commands.seed_demo_shots import make_demo_shots
from espresso_log.models import EspressoShot


@pytest.fixture
def demo_shots(db):
    return EspressoShot.objects.bulk_create(make_demo_shots(40))


@pytest.fixture
def shot_data():
    return {
        "brewed_on": "2024-06-01",
        "bean_name": "Klatch",
        "roast_level": "Light-Medium",
        "grind_size": "12",
        "dose": "18",
        "yield_amount": "36",
        "extraction_time": "28",
        "water_temperature": "93",
        "taste": "3",
        "strength": "3",
        "notes": "",
    }
