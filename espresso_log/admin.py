from django.contrib import admin

from .models import EspressoShot


@admin.register(EspressoShot)
class EspressoShotAdmin(admin.ModelAdmin):
    list_display = [
        "brewed_on",
        "bean_name",
        "roast_level",
        "grind_size",
        "dose",
        "yield_amount",
        "extraction_time",
        "water_temperature",
        "taste",
        "strength",
    ]
    list_filter = ["roast_level", "bean_name", "brewed_on"]
    search_fields = ["bean_name", "notes"]
    date_hierarchy = "brewed_on"
