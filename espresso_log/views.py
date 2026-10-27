from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import ml
from .csv_io import export_shots, import_shots
from .forms import ImportForm, RecipeForm, ShotForm
from .models import EspressoShot


@require_http_methods(["GET", "POST"])
def shot_list(request):
    form = ShotForm(request.POST or None, initial=_last_recipe())
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Shot logged.")
        return redirect("shot_list")

    return render(
        request,
        "espresso_log/shot_list.html",
        {
            "form": form,
            "import_form": ImportForm(),
            "shots": EspressoShot.objects.all(),
            "min_shots": ml.MIN_SHOTS,
        },
        status=400 if form.errors else 200,
    )


@require_POST
def shot_delete(request, pk):
    get_object_or_404(EspressoShot, pk=pk).delete()
    messages.info(request, "Shot deleted.")
    return redirect("shot_list")


@require_POST
def shots_import(request):
    form = ImportForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Choose a CSV file to import.")
        return redirect("shot_list")

    result = import_shots(form.cleaned_data["file"].read())
    if result.created:
        messages.success(request, f"Imported {result.created} shot(s).")
    for error in result.errors:
        messages.warning(request, error)
    return redirect("shot_list")


@require_GET
def shots_export(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="brewbrain-shots-{date.today().isoformat()}.csv"'
    )
    export_shots(EspressoShot.objects.all(), response)
    return response


@require_http_methods(["GET", "POST"])
def predict(request):
    form = RecipeForm(request.POST or None, initial=_last_recipe())
    context = {"form": form, "min_shots": ml.MIN_SHOTS}

    try:
        model = ml.train(EspressoShot.objects.all())
    except ml.NotEnoughData as exc:
        context["not_enough_data"] = str(exc)
        return render(request, "espresso_log/predict.html", context)

    context["model"] = model
    if request.method == "POST" and form.is_valid():
        recipe = ml.Recipe(**form.cleaned_data)
        context["prediction"] = model.predict(recipe)
        context["suggestion"] = model.suggest(recipe.dose, recipe.water_temperature)

    return render(request, "espresso_log/predict.html", context, status=400 if form.errors else 200)


def _last_recipe() -> dict:
    """Pre-fill forms from the most recent shot, since recipes change a little at a time."""
    last = EspressoShot.objects.first()
    if last is None:
        return {}
    return {
        "bean_name": last.bean_name,
        "roast_level": last.roast_level,
        "grind_size": last.grind_size,
        "dose": last.dose,
        "extraction_time": last.extraction_time,
        "water_temperature": last.water_temperature,
    }
