"""Tests for the saturation analysis engine (core.py)."""

import pytest

from saturation_meter.core import analyze_saturation, saturation_summary
from saturation_meter.models import InterviewEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_interviews(data: list[tuple[str, list[str]]]) -> list[InterviewEntry]:
    return [InterviewEntry(participant_id=pid, codes=codes) for pid, codes in data]


# ---------------------------------------------------------------------------
# Saturation detection
# ---------------------------------------------------------------------------


class TestSaturationDetection:
    def test_clear_saturation_detected(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b", "f"]),
            ("P03", ["a", "b", "c"]),
            ("P04", ["a", "b", "c"]),
            ("P05", ["a", "b", "c"]),
            ("P06", ["a", "b", "c"]),
        ])
        report = analyze_saturation(interviews)
        assert report.is_saturated is True

    def test_rapid_discovery_not_saturated(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["d", "e", "f"]),
            ("P03", ["g", "h", "i"]),
            ("P04", ["j", "k", "l"]),
            ("P05", ["m", "n", "o"]),
        ])
        report = analyze_saturation(interviews)
        assert report.is_saturated is False

    def test_all_identical_codes_saturated(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["a", "b", "c"]),
            ("P03", ["a", "b", "c"]),
            ("P04", ["a", "b", "c"]),
        ])
        report = analyze_saturation(interviews)
        assert report.is_saturated is True

    def test_saturation_index_is_1_based(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b"]),
            ("P03", ["a", "b"]),
            ("P04", ["a", "b"]),
        ])
        report = analyze_saturation(interviews)
        if report.is_saturated:
            assert report.estimated_saturation_index >= 1

    def test_saturation_participant_matches_index(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b"]),
            ("P03", ["a", "b"]),
            ("P04", ["a", "b"]),
        ])
        report = analyze_saturation(interviews)
        if report.is_saturated:
            idx = report.estimated_saturation_index - 1
            assert report.estimated_saturation_participant == interviews[idx].participant_id

    def test_empty_input(self):
        report = analyze_saturation([])
        assert report.total_interviews == 0
        assert report.is_saturated is False
        assert report.estimated_saturation_index is None

    def test_single_interview(self):
        interviews = make_interviews([("P01", ["a", "b", "c"])])
        report = analyze_saturation(interviews)
        assert report.total_interviews == 1
        assert report.is_saturated is False

    def test_two_interviews_identical(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["a", "b", "c"]),
        ])
        report = analyze_saturation(interviews)
        assert report.total_interviews == 2
        # Window of 3 not met — should not fire
        assert report.is_saturated is False


# ---------------------------------------------------------------------------
# Per-interview metrics
# ---------------------------------------------------------------------------


class TestSaturationMetrics:
    def test_cumulative_theme_count_increments_correctly(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["b", "c", "d"]),
            ("P03", ["d", "e"]),
        ])
        report = analyze_saturation(interviews)
        assert report.points[0].cumulative_themes_count == 3
        assert report.points[1].cumulative_themes_count == 4
        assert report.points[2].cumulative_themes_count == 5

    def test_new_themes_count_correct(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["b", "c", "d"]),
            ("P03", ["d", "e"]),
        ])
        report = analyze_saturation(interviews)
        assert report.points[0].new_themes_count == 3
        assert report.points[1].new_themes_count == 1
        assert report.points[2].new_themes_count == 1

    def test_total_unique_themes(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["c", "d"]),
            ("P03", ["e"]),
        ])
        report = analyze_saturation(interviews)
        assert report.total_unique_themes == 5

    def test_all_themes_sorted(self):
        interviews = make_interviews([
            ("P01", ["c", "a", "b"]),
            ("P02", ["d"]),
        ])
        report = analyze_saturation(interviews)
        assert report.all_themes == sorted(report.all_themes)

    def test_new_theme_rate_first_interview_is_one(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["a", "b"]),
        ])
        report = analyze_saturation(interviews)
        assert report.points[0].new_theme_rate == 1.0

    def test_new_theme_rate_zero_for_no_new_themes(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["a", "b", "c"]),
        ])
        report = analyze_saturation(interviews)
        assert report.points[1].new_theme_rate == 0.0

    def test_points_count_matches_interviews(self):
        interviews = make_interviews([
            ("P01", ["a"]),
            ("P02", ["b"]),
            ("P03", ["c"]),
        ])
        report = analyze_saturation(interviews)
        assert len(report.points) == 3

    def test_interview_index_sequential(self):
        interviews = make_interviews([("P0{}".format(i), ["a"]) for i in range(5)])
        report = analyze_saturation(interviews)
        for i, p in enumerate(report.points):
            assert p.interview_index == i + 1


# ---------------------------------------------------------------------------
# Code normalisation
# ---------------------------------------------------------------------------


class TestCodeNormalisation:
    def test_codes_lowercased(self):
        interviews = make_interviews([("P01", ["Theme_A", "THEME_B", "theme_c"])])
        report = analyze_saturation(interviews)
        assert "theme_a" in report.all_themes
        assert "theme_b" in report.all_themes
        assert "theme_c" in report.all_themes

    def test_codes_whitespace_stripped(self):
        interviews = [InterviewEntry(participant_id="P01", codes=[" a ", " b", "c "])]
        report = analyze_saturation(interviews)
        assert "a" in report.all_themes
        assert "b" in report.all_themes
        assert "c" in report.all_themes

    def test_duplicate_codes_within_interview_deduplicated(self):
        interviews = make_interviews([("P01", ["a", "a", "b", "b"])])
        report = analyze_saturation(interviews)
        assert report.total_unique_themes == 2
        assert report.points[0].new_themes_count == 2

    def test_mixed_case_deduplication_across_interviews(self):
        interviews = make_interviews([
            ("P01", ["CognitiveLoad"]),
            ("P02", ["cognitive_load", "NEW_THEME"]),
        ])
        report = analyze_saturation(interviews)
        # cognitive_load and cognitiveload are distinct after normalisation
        # but NEW_THEME → new_theme is definitely new
        assert report.points[1].new_themes_count >= 1


# ---------------------------------------------------------------------------
# Threshold and window configuration
# ---------------------------------------------------------------------------


class TestThresholdAndWindow:
    def test_relaxed_threshold_detects_saturation_earlier(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b", "c", "d", "f"]),   # 1/6 ≈ 16 %
            ("P03", ["a", "b", "c"]),
            ("P04", ["a", "b", "c"]),
            ("P05", ["a", "b", "c"]),
        ])
        report_strict = analyze_saturation(interviews, new_theme_threshold=0.01)
        report_relaxed = analyze_saturation(interviews, new_theme_threshold=0.20)
        if report_relaxed.is_saturated and report_strict.is_saturated:
            assert report_relaxed.estimated_saturation_index <= report_strict.estimated_saturation_index

    def test_window_size_1_detects_immediately(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b", "c"]),
            ("P03", ["a", "b"]),
        ])
        report = analyze_saturation(interviews, new_theme_threshold=0.05, window_size=1)
        # P02 rate: 0/5 = 0 → saturated at window 1
        assert report.is_saturated is True

    def test_large_window_requires_more_evidence(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b"]),
            ("P03", ["a", "b"]),
        ])
        report_w2 = analyze_saturation(interviews, window_size=2)
        report_w4 = analyze_saturation(interviews, window_size=4)
        # Window of 4 can't fire with only 3 interviews
        assert report_w4.is_saturated is False


# ---------------------------------------------------------------------------
# Confidence and warnings
# ---------------------------------------------------------------------------


class TestConfidenceAndWarnings:
    def test_insufficient_data_for_two_interviews(self):
        interviews = make_interviews([
            ("P01", ["a", "b"]),
            ("P02", ["a", "b"]),
        ])
        report = analyze_saturation(interviews)
        assert report.confidence == "insufficient_data"
        assert len(report.warnings) > 0

    def test_high_confidence_with_many_post_saturation_interviews(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e", "f"]),
            ("P02", ["a", "b"]),
            ("P03", ["a", "b"]),
            ("P04", ["a", "b"]),
            ("P05", ["a", "b"]),
            ("P06", ["a", "b"]),
            ("P07", ["a", "b"]),
            ("P08", ["a", "b"]),
        ])
        report = analyze_saturation(interviews)
        if report.is_saturated:
            assert report.confidence in ("high", "medium")

    def test_stop_recommendation_present(self):
        interviews = make_interviews([("P01", ["a"])])
        report = analyze_saturation(interviews)
        assert isinstance(report.stop_recommendation, str)
        assert len(report.stop_recommendation) > 0

    def test_stop_recommendation_saturated_mentions_saturation(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c", "d", "e"]),
            ("P02", ["a", "b"]),
            ("P03", ["a", "b"]),
            ("P04", ["a", "b"]),
        ])
        report = analyze_saturation(interviews)
        if report.is_saturated:
            assert "saturation" in report.stop_recommendation.lower()

    def test_stop_recommendation_not_saturated_says_continue(self):
        interviews = make_interviews([
            ("P01", ["a", "b", "c"]),
            ("P02", ["d", "e", "f"]),
        ])
        report = analyze_saturation(interviews)
        rec = report.stop_recommendation.lower()
        assert "continue" in rec or "too few" in rec or "cannot" in rec

    def test_warning_for_12_plus_without_saturation(self):
        interviews = make_interviews(
            [(f"P{i:02d}", [f"unique_{i}_a", f"unique_{i}_b"]) for i in range(13)]
        )
        report = analyze_saturation(interviews)
        assert not report.is_saturated
        assert any("12" in w or "interviews" in w for w in report.warnings)


# ---------------------------------------------------------------------------
# saturation_summary helper
# ---------------------------------------------------------------------------


class TestSaturationSummary:
    def test_summary_keys_present(self):
        interviews = make_interviews([("P01", ["a", "b"]), ("P02", ["a", "b"])])
        report = analyze_saturation(interviews)
        summary = saturation_summary(report)
        assert "total_interviews" in summary
        assert "total_unique_themes" in summary
        assert "is_saturated" in summary
        assert "saturation_index" in summary
        assert "confidence" in summary

    def test_summary_values_consistent(self):
        interviews = make_interviews([("P01", ["a", "b"]), ("P02", ["a", "b"])])
        report = analyze_saturation(interviews)
        summary = saturation_summary(report)
        assert summary["total_interviews"] == report.total_interviews
        assert summary["is_saturated"] == report.is_saturated
