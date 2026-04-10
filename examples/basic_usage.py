"""Basic usage examples for saturation-meter."""

from saturation_meter import InterviewEntry, analyze_saturation, saturation_summary
from saturation_meter.io import load_csv, report_to_dict
from pathlib import Path

# ---------------------------------------------------------------------------
# Example 1: In-memory usage
# ---------------------------------------------------------------------------

print("=" * 60)
print("Example 1 — In-memory analysis")
print("=" * 60)

interviews = [
    InterviewEntry("P01", ["cognitive_load", "feature_overload", "navigation_confusion",
                            "trust_deficit", "onboarding_friction", "mental_model_mismatch"]),
    InterviewEntry("P02", ["cognitive_load", "feature_overload", "information_overload",
                            "navigation_confusion", "feedback_loop_absence"]),
    InterviewEntry("P03", ["trust_deficit", "data_privacy_concern", "cognitive_load",
                            "feature_overload"]),
    InterviewEntry("P04", ["navigation_confusion", "feature_overload", "cognitive_load",
                            "task_completion_anxiety"]),
    InterviewEntry("P05", ["cognitive_load", "feature_overload", "navigation_confusion",
                            "trust_deficit"]),
    InterviewEntry("P06", ["cognitive_load", "feature_overload", "navigation_confusion"]),
    InterviewEntry("P07", ["trust_deficit", "cognitive_load", "feature_overload", "navigation_confusion"]),
    InterviewEntry("P08", ["cognitive_load", "feature_overload", "navigation_confusion"]),
]

report = analyze_saturation(interviews, new_theme_threshold=0.05, window_size=3)

print(f"Interviews analysed: {report.total_interviews}")
print(f"Unique themes:       {report.total_unique_themes}")
print(f"Is saturated:        {report.is_saturated}")
print(f"Confidence:          {report.confidence}")
if report.is_saturated:
    print(f"Saturation at:       interview {report.estimated_saturation_index} "
          f"({report.estimated_saturation_participant})")
print()
print("Stop-point recommendation:")
print(f"  {report.stop_recommendation}")
print()

# Saturation curve
print("Saturation curve:")
print(f"  {'#':>3}  {'Participant':<14}  {'New':>5}  {'Cumul':>6}  {'Rate':>7}")
for p in report.points:
    print(f"  {p.interview_index:>3}  {p.participant_id:<14}  "
          f"{p.new_themes_count:>5}  {p.cumulative_themes_count:>6}  "
          f"{p.new_theme_rate * 100:>6.1f}%")

# ---------------------------------------------------------------------------
# Example 2: Load from CSV, get summary dict
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("Example 2 — Load from CSV, quick summary")
print("=" * 60)

fixture_path = Path(__file__).parent / "tests" / "fixtures" / "sample_coded.csv"
if fixture_path.exists():
    csv_interviews = load_csv(fixture_path)
    csv_report = analyze_saturation(csv_interviews)
    summary = saturation_summary(csv_report)
    print(summary)
else:
    print("(Fixture file not found — run from the project root)")
