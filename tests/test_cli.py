"""Tests for the Click CLI (cli.py)."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from saturation_meter.cli import cli

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURE_DIR / "sample_coded.csv"
SAMPLE_JSON = FIXTURE_DIR / "sample_coded.json"


# ---------------------------------------------------------------------------
# analyze command
# ---------------------------------------------------------------------------


class TestAnalyzeCommand:
    def test_analyze_csv_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV)])
        assert result.exit_code == 0, result.output

    def test_analyze_json_file_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_JSON)])
        assert result.exit_code == 0, result.output

    def test_json_output_flag_emits_valid_json(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--json-output"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "is_saturated" in data

    def test_json_output_contains_saturation_curve(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--json-output"])
        data = json.loads(result.output)
        assert "saturation_curve" in data
        assert len(data["saturation_curve"]) == 10

    def test_json_output_total_interviews_correct(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--json-output"])
        data = json.loads(result.output)
        assert data["total_interviews"] == 10

    def test_custom_threshold_accepted(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--threshold", "0.10", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "is_saturated" in data

    def test_custom_window_accepted(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--window", "2", "--json-output"])
        assert result.exit_code == 0

    def test_nonexistent_file_fails_gracefully(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "/tmp/does_not_exist.csv"])
        assert result.exit_code != 0

    def test_unsupported_extension_fails(self, tmp_path):
        f = tmp_path / "data.xlsx"
        f.write_text("dummy")
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(f)])
        assert result.exit_code != 0

    def test_output_contains_saturation_status(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV)])
        output = result.output.upper()
        assert "SATURATED" in output or "NOT YET" in output

    def test_json_output_warnings_is_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--json-output"])
        data = json.loads(result.output)
        assert isinstance(data["warnings"], list)

    def test_json_output_narrative_is_none_without_llm(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", str(SAMPLE_CSV), "--json-output"])
        data = json.loads(result.output)
        assert data["narrative"] is None


# ---------------------------------------------------------------------------
# curve command
# ---------------------------------------------------------------------------


class TestCurveCommand:
    def test_curve_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["curve", str(SAMPLE_CSV)])
        assert result.exit_code == 0, result.output

    def test_curve_emits_valid_json_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["curve", str(SAMPLE_CSV)])
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_curve_length_matches_dataset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["curve", str(SAMPLE_CSV)])
        data = json.loads(result.output)
        assert len(data) == 10

    def test_curve_point_contains_required_keys(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["curve", str(SAMPLE_CSV)])
        data = json.loads(result.output)
        point = data[0]
        assert "interview_index" in point
        assert "participant_id" in point
        assert "new_themes" in point
        assert "cumulative_themes" in point
        assert "new_theme_rate" in point

    def test_curve_interview_indices_sequential(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["curve", str(SAMPLE_CSV)])
        data = json.loads(result.output)
        indices = [p["interview_index"] for p in data]
        assert indices == list(range(1, len(data) + 1))

    def test_curve_with_json_input(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["curve", str(SAMPLE_JSON)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 10
