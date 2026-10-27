import io

import pytest

from espresso_log.csv_io import export_shots, import_shots
from espresso_log.models import EspressoShot

pytestmark = pytest.mark.django_db

LEGACY_HEADER = (
    "Date,Grind Size,Dose (g),Yield (g),Extraction Time (s),"
    "Water Temp,Sourness/Bitterness,Strength\n"
)

LEGACY_PREAMBLE = "Bean Name,Klatch\nRoast,Light-Medium\n\n"
LEGACY_EXPORT = (
    LEGACY_PREAMBLE
    + LEGACY_HEADER
    + "2024-06-01,12,18,36,28,93,3,3\n2024-06-02,10,18,32,34,93,4,4\n"
)


def test_imports_original_brewbrain_format():
    result = import_shots(LEGACY_EXPORT.encode())

    assert result.created == 2
    assert result.errors == []
    shot = EspressoShot.objects.get(brewed_on="2024-06-02")
    assert shot.bean_name == "Klatch"
    assert shot.roast_level == "Light-Medium"
    assert (shot.grind_size, shot.yield_amount, shot.taste) == (10, 32, 4)


def test_export_then_import_round_trips(demo_shots):
    buffer = io.StringIO()
    export_shots(EspressoShot.objects.all(), buffer)
    EspressoShot.objects.all().delete()

    result = import_shots(buffer.getvalue().encode("utf-8-sig"))

    assert result.created == len(demo_shots)
    assert result.errors == []


def test_invalid_rows_are_reported_and_skipped():
    valid = "2024-06-01,12,18,36,28,93,3,3\n"
    bad_dose_and_taste = "2024-06-01,12,abc,36,28,93,9,3\n"
    blank = ",,,,,,,\n"
    csv_text = LEGACY_HEADER + valid + bad_dose_and_taste + blank

    result = import_shots(csv_text.encode())

    assert result.created == 1
    assert len(result.errors) == 1
    assert result.errors[0].startswith("Line 3:")
    assert "dose" in result.errors[0] and "taste" in result.errors[0]


def test_missing_date_defaults_to_today():
    csv_text = "Grind Size,Dose (g),Yield (g),Extraction Time (s),Water Temp,Taste,Strength\n"
    csv_text += "12,18,36,28,93,3,3\n"

    assert import_shots(csv_text.encode()).created == 1


@pytest.mark.parametrize(
    ("raw", "message"),
    [(b"just,some,columns\n1,2,3\n", "header row"), (b"\xff\xfe\x00bad", "UTF-8")],
)
def test_unreadable_files_are_rejected(raw, message):
    result = import_shots(raw)
    assert result.created == 0
    assert message in result.errors[0]
