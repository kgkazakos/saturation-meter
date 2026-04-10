"""
Saturation analysis engine.

All logic is rule-based and runs without any API calls.
LLM narrative enrichment is an optional community layer (see llm.py).
"""

from typing import Optional

from .models import InterviewEntry, SaturationPoint, SaturationReport

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _all_below(values: list[float], threshold: float) -> bool:
    return len(values) > 0 and all(v <= threshold for v in values)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_saturation(
    interviews: list[InterviewEntry],
    new_theme_threshold: float = 0.05,
    window_size: int = 3,
) -> SaturationReport:
    """
    Estimate thematic saturation from a sequence of coded interviews.

    Parameters
    ----------
    interviews:
        Ordered list of InterviewEntry objects (order matters — it reflects
        your data-collection sequence).
    new_theme_threshold:
        New-theme rate (0–1) below which an interview is considered
        non-contributory.  Default 0.05 = 5 %.
    window_size:
        Number of consecutive sub-threshold interviews required to signal
        saturation.  Default 3.

    Returns
    -------
    SaturationReport with per-interview metrics, saturation index, confidence
    rating, and a plain-language stop-point recommendation.
    """
    warnings: list[str] = []

    if len(interviews) < 3:
        warnings.append(
            "Fewer than 3 interviews — saturation analysis is not meaningful "
            "at this scale.  Collect more data before interpreting results."
        )

    seen_themes: set[str] = set()
    first_new_count: int = 0
    points: list[SaturationPoint] = []

    for idx, interview in enumerate(interviews):
        codes_set = set(interview.codes)
        new_themes = codes_set - seen_themes
        seen_themes |= codes_set

        new_count = len(new_themes)
        cumulative_count = len(seen_themes)

        if idx == 0:
            first_new_count = max(new_count, 1)  # guard against divide-by-zero

        new_theme_rate = new_count / cumulative_count if cumulative_count else 0.0
        marginal_rate = new_count / first_new_count

        points.append(
            SaturationPoint(
                interview_index=idx + 1,
                participant_id=interview.participant_id,
                new_themes_count=new_count,
                cumulative_themes_count=cumulative_count,
                new_theme_rate=round(new_theme_rate, 4),
                marginal_discovery_rate=round(marginal_rate, 4),
            )
        )

    # ------------------------------------------------------------------
    # Saturation detection: first window of `window_size` interviews
    # whose new-theme rates are ALL <= threshold
    # ------------------------------------------------------------------
    rates = [p.new_theme_rate for p in points]
    estimated_saturation_index: Optional[int] = None
    estimated_saturation_participant: Optional[str] = None

    if len(points) >= window_size:
        for i in range(window_size - 1, len(points)):
            window = rates[i - window_size + 1 : i + 1]
            if _all_below(window, new_theme_threshold):
                start_idx = i - window_size + 1
                estimated_saturation_index = points[start_idx].interview_index
                estimated_saturation_participant = points[start_idx].participant_id
                break

    is_saturated = estimated_saturation_index is not None

    # ------------------------------------------------------------------
    # Confidence rating
    # ------------------------------------------------------------------
    n = len(interviews)

    if n < 3:
        confidence = "insufficient_data"
    elif is_saturated:
        interviews_after = n - (estimated_saturation_index - 1)
        if interviews_after >= window_size * 2:
            confidence = "high"
        elif interviews_after >= window_size:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        if n >= 12:
            confidence = "low"
            warnings.append(
                f"{n} interviews completed without a saturation signal.  "
                "Consider reviewing coding consistency or expanding participant diversity."
            )
        else:
            confidence = "insufficient_data"

    # ------------------------------------------------------------------
    # Stop-point recommendation
    # ------------------------------------------------------------------
    if is_saturated:
        stop_recommendation = (
            f"Saturation detected from interview {estimated_saturation_index} "
            f"(participant {estimated_saturation_participant}).  "
            f"No new themes emerged across the following {window_size}-interview window.  "
            f"You may stop data collection with {confidence} confidence."
        )
    elif n < 5:
        stop_recommendation = (
            f"Continue collecting — only {n} interview(s) available.  "
            "Saturation cannot be assessed reliably below 5 interviews."
        )
    elif n < 8:
        stop_recommendation = (
            f"Continue collecting — {n} interviews completed, "
            "saturation signal not yet reached."
        )
    else:
        stop_recommendation = (
            f"Continue collecting — {n} interviews completed without a saturation signal.  "
            "Review your codebook and consider whether participant diversity is sufficient."
        )

    # Catch-all warning for very small datasets
    if n < 5 and not any("Fewer than" in w for w in warnings):
        warnings.append(
            "Fewer than 5 interviews.  Saturation estimates are unreliable at this scale."
        )

    return SaturationReport(
        total_interviews=n,
        total_unique_themes=len(seen_themes),
        all_themes=sorted(seen_themes),
        points=points,
        estimated_saturation_index=estimated_saturation_index,
        estimated_saturation_participant=estimated_saturation_participant,
        is_saturated=is_saturated,
        confidence=confidence,
        stop_recommendation=stop_recommendation,
        warnings=warnings,
    )


def saturation_summary(report: SaturationReport) -> dict:
    """Return a compact dict summary of key saturation metrics."""
    return {
        "total_interviews": report.total_interviews,
        "total_unique_themes": report.total_unique_themes,
        "is_saturated": report.is_saturated,
        "saturation_index": report.estimated_saturation_index,
        "confidence": report.confidence,
    }
