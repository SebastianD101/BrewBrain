"""CSV import and export for espresso shots.

Imports accept the current export format as well as the original BrewBrain format, which put
the bean name and roast level in a short preamble above the table instead of in columns.
"""

import csv
import io
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from .forms import ShotForm
from .models import EspressoShot

EXPORT_COLUMNS = [
    ("Date", "brewed_on"),
    ("Bean Name", "bean_name"),
    ("Roast Level", "roast_level"),
    ("Grind Size", "grind_size"),
    ("Dose (g)", "dose"),
    ("Yield (g)", "yield_amount"),
    ("Extraction Time (s)", "extraction_time"),
    ("Water Temp (°C)", "water_temperature"),
    ("Taste (1 sour - 5 bitter)", "taste"),
    ("Strength (1 weak - 5 strong)", "strength"),
    ("Notes", "notes"),
]

# Header spellings accepted on import, normalised with _normalise().
HEADER_ALIASES = {
    **{_header.lower(): _field for _header, _field in EXPORT_COLUMNS},
    "roast": "roast_level",
    "yield": "yield_amount",
    "water temp": "water_temperature",
    "water temp (c)": "water_temperature",
    "sourness/bitterness": "taste",
    "taste": "taste",
    "strength": "strength",
}

MAX_REPORTED_ERRORS = 10


@dataclass
class ImportResult:
    created: int = 0
    errors: list[str] = field(default_factory=list)


def _normalise(header: str) -> str:
    return header.strip().lstrip("﻿").lower()


def export_shots(shots: Iterable[EspressoShot], out: io.TextIOBase) -> None:
    writer = csv.writer(out)
    writer.writerow(header for header, _ in EXPORT_COLUMNS)
    for shot in shots:
        writer.writerow(getattr(shot, name) for _, name in EXPORT_COLUMNS)


def import_shots(raw: bytes) -> ImportResult:
    result = ImportResult()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        result.errors.append("File is not UTF-8 encoded text.")
        return result

    rows = list(csv.reader(io.StringIO(text)))
    header_index = _find_header_row(rows)
    if header_index is None:
        result.errors.append("Couldn't find a header row with Grind Size, Dose and Yield columns.")
        return result

    defaults = _read_preamble(rows[:header_index])
    fields = [HEADER_ALIASES.get(_normalise(cell)) for cell in rows[header_index]]

    for line_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if not any(cell.strip() for cell in row):
            continue
        data = {**defaults}
        data.update((name, value.strip()) for name, value in zip(fields, row, strict=False) if name)
        data["brewed_on"] = data.get("brewed_on") or date.today().isoformat()

        form = ShotForm(data)
        if form.is_valid():
            form.save()
            result.created += 1
        else:
            problems = "; ".join(
                f"{name.replace('_', ' ')}: {' '.join(messages)}"
                for name, messages in form.errors.items()
            )
            result.errors.append(f"Line {line_number}: {problems}")

    if len(result.errors) > MAX_REPORTED_ERRORS:
        hidden = len(result.errors) - MAX_REPORTED_ERRORS
        result.errors = result.errors[:MAX_REPORTED_ERRORS] + [f"…and {hidden} more."]
    return result


def _find_header_row(rows: list[list[str]]) -> int | None:
    required = {"grind_size", "dose", "yield_amount"}
    for index, row in enumerate(rows):
        if required <= {HEADER_ALIASES.get(_normalise(cell)) for cell in row}:
            return index
    return None


def _read_preamble(rows: list[list[str]]) -> dict[str, str]:
    """Read 'Bean Name,<value>' style lines from the legacy format."""
    defaults = {}
    for row in rows:
        if len(row) >= 2 and (name := HEADER_ALIASES.get(_normalise(row[0]))):
            defaults[name] = row[1].strip()
    return defaults
