from datetime import date

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

SCALE = [MinValueValidator(1), MaxValueValidator(5)]


class EspressoShot(models.Model):
    class RoastLevel(models.TextChoices):
        LIGHT = "Light"
        LIGHT_MEDIUM = "Light-Medium"
        MEDIUM = "Medium"
        MEDIUM_DARK = "Medium-Dark"
        DARK = "Dark"

    class Taste(models.IntegerChoices):
        VERY_SOUR = 1, "1 – Very sour"
        SOUR = 2, "2 – Sour"
        BALANCED = 3, "3 – Balanced"
        BITTER = 4, "4 – Bitter"
        VERY_BITTER = 5, "5 – Very bitter"

    class Strength(models.IntegerChoices):
        VERY_WEAK = 1, "1 – Very weak"
        WEAK = 2, "2 – Weak"
        BALANCED = 3, "3 – Balanced"
        STRONG = 4, "4 – Strong"
        VERY_STRONG = 5, "5 – Very strong"

    brewed_on = models.DateField(default=date.today)
    bean_name = models.CharField(max_length=100, blank=True)
    roast_level = models.CharField(max_length=20, choices=RoastLevel.choices, blank=True)

    # Recipe inputs: these are the features the model learns from.
    grind_size = models.FloatField(
        validators=[MinValueValidator(0)], help_text="Grinder setting (machine-specific)"
    )
    dose = models.FloatField(validators=[MinValueValidator(1)], help_text="Dry coffee in grams")
    extraction_time = models.FloatField(
        validators=[MinValueValidator(1)], help_text="Shot time in seconds"
    )
    water_temperature = models.FloatField(
        validators=[MinValueValidator(70), MaxValueValidator(100)],
        help_text="Brew temperature in °C",
    )

    # Outcomes: what the model predicts.
    yield_amount = models.FloatField(
        validators=[MinValueValidator(1)], help_text="Liquid espresso out in grams"
    )
    taste = models.PositiveSmallIntegerField(
        choices=Taste.choices, validators=SCALE, help_text="1 = sour, 5 = bitter"
    )
    strength = models.PositiveSmallIntegerField(
        choices=Strength.choices, validators=SCALE, help_text="1 = weak, 5 = strong"
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-brewed_on", "-created_at"]

    def __str__(self) -> str:
        bean = self.bean_name or "Unnamed bean"
        return f"{bean}: {self.dose:g}g → {self.yield_amount:g}g in {self.extraction_time:g}s"

    @property
    def brew_ratio(self) -> float:
        """Yield divided by dose, e.g. 2.0 for a classic 1:2 shot."""
        return self.yield_amount / self.dose
