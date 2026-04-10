"""Tests for CSV/JSON loading and report serialisation (io.py)."""

import json
from pathlib import Path

import pytest

from saturation_meter.io import load_csv, load_file, load_json, report_to_dict
from saturation_meter.core import analyze_saturation
from saturation_meter.models import InterviewEntry


FIXTURE_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------


class TestLoadCSV:
    def test_loads_fixture_file(self):
        interviews = load_csv(FIXTURE_DIR / "sample_coded.csv")
        assert len(interviews) == 10

    def test_participant_ids_preserved(self):
        interviews = load_csv(FIXTURE_DIR / "sample_coded.csv")
        pids = [i.participant_id for i in interviews]
        assert "P01" in pids
        assert "P10" in pids

    def test_codes_parsed_from_quoted_csv(self, tmp_path):
        f = tmp_path / "t.csv"
        f.write_text('participant_id,codes\nP01,"a,b,c"\nP02,"b,c,d"\n')
        interviews = load_csv(f)
        assert len(interviews) == 2
        assert "a" in interviews[0].codes
        assert "d" in interviews[1].codes

    def test_skips_empty_participant_id(self, tmp_path):
        f = tmp_path / "t.csv"
        f.write_text('participant_id,codes\n,"a,b"\nP01,"a,b"\n')
        interviews = load_csv(f)
        assert len(interviews) == 1
        assert interviews[0].participant_id == "P01"

    def test_empty_codes_row_still_loads(self, tmp_path):
        f = tmp_path / "t.csv"
        f.write_text("participant_id,codes\nP01,\n")
        interviews = load_csv(f)
        assert len(interviews) == 1
        assert interviews[0].codes == []

    def test_whitespace_in_codes_stripped(self, tmp_path):
        f = tmp_path / "t.csv"
        f.write_text('participant_id,codes\nP01," a , b , c "\n')
        interviews = load_csv(f)
        assert "a" in interviews[0].codes


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------


class TestLoadJSON:
    def test_loads_fixture_file(self):
        interviews = load_json(FIXTURE_DIR / "sample_coded.json")
        assert len(interviews) == 10

    def test_codes_as_list(self, tmp_path):
        f = tmp_path / "t.json"
        f.write_text(json.dumps([{"participant_id": "P01", "codes": ["a", "b", "c"]}]))
        interviews = load_json(f)
        assert "a" in interviews[0].codes

    def test_codes_as_string_comma_separated(self, tmp_path):
        f = tmp_path / "t.json"
        f.write_text(json.dumps([{"participant_id": "P01", "codes": "a,b,c"}]))
        interviews = load_json(f)
        assert "a" in interviews[0].codes
        assert "c" in interviews[0].codes

    def test_skips_missing_participant_id(self, tmp_path):
        f = tmp_path / "t.json"
        f.write_text(json.dumps([{"codes": ["a", "b"]}, {"participant_id": "P01", "codes": ["a"]}]))
        interviews = load_json(f)
        assert len(interviews) == 1


# ---------------------------------------------------------------------------
# load_file dispatcher
# ---------------------------------------------------------------------------


class TestLoadFile:
    def test_dispatches_csv(self):
        interviews = load_file(FIXTURE_DIR / "sample_coded.csv")
        assert len(interviews) == 10

    def test_dispatches_json(self):
        interviews = load_file(FIXTURE_DIR / "sample_coded.json")
        assert len(interviews) == 10

    def test_raises_on_unsupported_extension(self, tmp_path):
        f = tmp_path / "data.xlsx"
        f.write_text("dummy")
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_file(f)


# ---------------------------------------------------------------------------
# report_to_dict serialisation
# ---------------------------------------------------------------------------


class TestReportToDict:
    def _make_report(self):
        from saturation_meter.models import InterviewEntry
        interviews = [
            InterviewEntry("P01", ["a", "b", "c"]),
            InterviewEntry("P02", ["a", "b"]),
            InterviewEntry("P03", ["a", "b"]),
            InterviewEntry("P04", ["a", "b"]),
        ]
        return analyze_saturation(interviews)

    def test_required_keys_present(self):
        d = report_to_dict(self._make_report())
        for key in ("total_interviews", "total_unique_themes", "is_saturated",
                    "confidence", "stop_recommendation", "saturation_curve",
                    "warnings", "narrative"):
            assert key in d

    def test_saturation_curve_length_matches_interviews(self):
        report = self._make_report()
        d = report_to_dict(report)
        assert len(d["saturation_curve"]) == report.total_interviews

    def test_saturation_curve_point_keys(self):
        d = report_to_dict(self._make_report())
        point = d["saturation_curve"][0]
        for key in ("interview_index", "participant_id", "new_themes",
                    "cumulative_themes", "new_theme_rate", "marginal_discovery_rate"):
            assert key in point

    def test_serialisable_to_json(self):
        d = report_to_dict(self._make_report())
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded["total_interviews"] == d["total_interviews"]
