"""
I/O helpers: loading coded datasets, serialising reports to JSON.

Supported input formats:
  CSV  — columns: participant_id, codes  (codes = comma-separated string)
  JSON — array of {participant_id, codes}  (codes = list or comma-separated string)
"""

import csv
import json
from pathlib import Path

from .models import InterviewEntry, SaturationReport

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_csv(path: Path) -> list[InterviewEntry]:
    """Load a coded dataset from a CSV file."""
    interviews: list[InterviewEntry] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            pid = row.get("participant_id", "").strip()
            codes_raw = row.get("codes", "")
            codes = [c.strip() for c in codes_raw.split(",") if c.strip()]
            if pid:
                interviews.append(InterviewEntry(participant_id=pid, codes=codes))
    return interviews


def load_json(path: Path) -> list[InterviewEntry]:
    """Load a coded dataset from a JSON file."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    interviews: list[InterviewEntry] = []
    for item in data:
        pid = str(item.get("participant_id", "")).strip()
        codes = item.get("codes", [])
        if isinstance(codes, str):
            codes = [c.strip() for c in codes.split(",") if c.strip()]
        if pid:
            interviews.append(InterviewEntry(participant_id=pid, codes=list(codes)))
    return interviews


def load_file(path: Path) -> list[InterviewEntry]:
    """Dispatch to the correct loader based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    raise ValueError(f"Unsupported file type: {path.suffix!r}.  Use .csv or .json")


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------


def report_to_dict(report: SaturationReport) -> dict:
    """Serialise a SaturationReport to a JSON-compatible dict."""
    return {
        "total_interviews": report.total_interviews,
        "total_unique_themes": report.total_unique_themes,
        "all_themes": report.all_themes,
        "is_saturated": report.is_saturated,
        "estimated_saturation_index": report.estimated_saturation_index,
        "estimated_saturation_participant": report.estimated_saturation_participant,
        "confidence": report.confidence,
        "stop_recommendation": report.stop_recommendation,
        "warnings": report.warnings,
        "narrative": report.narrative,
        "saturation_curve": [
            {
                "interview_index": p.interview_index,
                "participant_id": p.participant_id,
                "new_themes": p.new_themes_count,
                "cumulative_themes": p.cumulative_themes_count,
                "new_theme_rate": p.new_theme_rate,
                "marginal_discovery_rate": p.marginal_discovery_rate,
            }
            for p in report.points
        ],
    }
