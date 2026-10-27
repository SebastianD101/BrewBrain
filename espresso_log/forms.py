from django import forms

from .models import EspressoShot


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)


class ShotForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EspressoShot
        fields = [
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
            "notes",
        ]
        labels = {
            "brewed_on": "Date",
            "dose": "Dose (g)",
            "yield_amount": "Yield (g)",
            "extraction_time": "Time (s)",
            "water_temperature": "Temp (°C)",
        }
        widgets = {
            "brewed_on": forms.DateInput(attrs={"type": "date"}),
            "grind_size": forms.NumberInput(attrs={"step": "any"}),
            "dose": forms.NumberInput(attrs={"step": "0.1"}),
            "yield_amount": forms.NumberInput(attrs={"step": "0.1"}),
            "extraction_time": forms.NumberInput(attrs={"step": "1"}),
            "water_temperature": forms.NumberInput(attrs={"step": "0.5"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class RecipeForm(BootstrapFormMixin, forms.Form):
    grind_size = forms.FloatField(min_value=0, label="Grind size")
    dose = forms.FloatField(min_value=1, label="Dose (g)")
    extraction_time = forms.FloatField(min_value=1, label="Time (s)")
    water_temperature = forms.FloatField(min_value=70, max_value=100, label="Temp (°C)")


class ImportForm(BootstrapFormMixin, forms.Form):
    file = forms.FileField(
        label="CSV file", widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"})
    )
