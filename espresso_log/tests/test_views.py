import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from espresso_log.models import EspressoShot

pytestmark = pytest.mark.django_db


def test_shot_list_shows_empty_state(client):
    response = client.get(reverse("shot_list"))
    assert response.status_code == 200
    assert b"No shots yet" in response.content


def test_logging_a_shot_saves_it(client, shot_data):
    response = client.post(reverse("shot_list"), shot_data, follow=True)

    assert response.redirect_chain[-1][0] == reverse("shot_list")
    shot = EspressoShot.objects.get()
    assert shot.brew_ratio == 2.0
    assert b"Shot logged" in response.content


def test_invalid_shot_shows_errors_and_saves_nothing(client, shot_data):
    response = client.post(reverse("shot_list"), {**shot_data, "dose": "", "taste": "7"})

    assert response.status_code == 400
    assert not EspressoShot.objects.exists()
    assert response.context["form"].errors.keys() == {"dose", "taste"}


def test_new_shot_form_is_prefilled_from_last_shot(client, demo_shots):
    initial = client.get(reverse("shot_list")).context["form"].initial
    assert initial["dose"] == EspressoShot.objects.first().dose


def test_delete_requires_post(client, demo_shots):
    url = reverse("shot_delete", args=[demo_shots[0].pk])

    assert client.get(url).status_code == 405
    client.post(url)
    assert not EspressoShot.objects.filter(pk=demo_shots[0].pk).exists()


def test_export_downloads_csv(client, demo_shots):
    response = client.get(reverse("shots_export"))

    assert response["Content-Type"].startswith("text/csv")
    assert "attachment" in response["Content-Disposition"]
    assert len(response.content.decode().strip().splitlines()) == len(demo_shots) + 1


def test_import_upload(client):
    upload = SimpleUploadedFile(
        "shots.csv",
        b"Grind Size,Dose (g),Yield (g),Extraction Time (s),Water Temp,Taste,Strength\n"
        b"12,18,36,28,93,3,3\n",
        content_type="text/csv",
    )
    response = client.post(reverse("shots_import"), {"file": upload}, follow=True)

    assert EspressoShot.objects.count() == 1
    assert b"Imported 1 shot" in response.content


def test_predict_explains_when_there_is_not_enough_data(client):
    response = client.get(reverse("predict"))
    assert b"Log at least 5 shots" in response.content


def test_predict_returns_prediction_and_suggestion(client, demo_shots):
    recipe = {"grind_size": 18, "dose": 18, "extraction_time": 20, "water_temperature": 93}
    response = client.post(reverse("predict"), recipe)

    assert response.status_code == 200
    assert response.context["prediction"].recipe.grind_size == 18
    assert response.context["suggestion"].recipe.dose == 18
    assert b"Suggested adjustment" in response.content


def test_predict_rejects_out_of_range_input(client, demo_shots):
    recipe = {"grind_size": 18, "dose": 18, "extraction_time": 20, "water_temperature": 150}
    response = client.post(reverse("predict"), recipe)

    assert response.status_code == 400
    assert "prediction" not in response.context
