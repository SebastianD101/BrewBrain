"""Fill the database with realistic synthetic shots so the predictor can be tried immediately."""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from espresso_log.models import EspressoShot


def make_demo_shots(count: int, seed: int = 7) -> list[EspressoShot]:
    """Simulate a home barista dialling in, using rough rules of thumb for espresso.

    Finer grinds slow the shot and pull more out of the coffee (more bitter); coarser
    grinds run fast and under-extract (more sour). A shorter ratio tastes stronger.
    """
    rng = random.Random(seed)
    shots = []
    for i in range(count):
        grind = rng.uniform(8, 20)
        dose = rng.choice([17.0, 18.0, 18.0, 19.0])
        temperature = rng.choice([90.0, 92.0, 93.0, 94.0, 96.0])
        time = max(12.0, 52 - 1.9 * grind + rng.gauss(0, 2.5))
        yield_amount = max(dose, dose * (2.6 - 0.025 * time) + rng.gauss(0, 1.5))
        ratio = yield_amount / dose

        taste = 3 + 0.12 * (time - 28) + 0.15 * (temperature - 93) + rng.gauss(0, 0.4)
        strength = 3 + 2.0 * (2.0 - ratio) + rng.gauss(0, 0.4)

        shots.append(
            EspressoShot(
                brewed_on=date.today() - timedelta(days=count - i),
                bean_name=rng.choice(["Klatch Belle Espresso", "Ethiopia Guji", "House Blend"]),
                roast_level=rng.choice(EspressoShot.RoastLevel.values),
                grind_size=round(grind, 1),
                dose=dose,
                yield_amount=round(yield_amount, 1),
                extraction_time=round(time),
                water_temperature=temperature,
                taste=min(5, max(1, round(taste))),
                strength=min(5, max(1, round(strength))),
            )
        )
    return shots


class Command(BaseCommand):
    help = "Add synthetic espresso shots for demos (use --replace to clear existing shots)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=60)
        parser.add_argument("--replace", action="store_true", help="Delete existing shots first.")

    def handle(self, *args, count, replace, **options):
        if replace:
            EspressoShot.objects.all().delete()
        EspressoShot.objects.bulk_create(make_demo_shots(count))
        self.stdout.write(self.style.SUCCESS(f"Added {count} demo shots."))
