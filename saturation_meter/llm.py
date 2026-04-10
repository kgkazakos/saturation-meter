"""
LLM narrative enrichment for saturation-meter.

Supported backends (all optional — install only what you need):
  openai    — pip install openai        (model: gpt-4o-mini)
  anthropic — pip install anthropic     (model: claude-haiku-4-5-20251001)
  gemini    — pip install google-genai  (model: gemini-3.1-pro-preview)

Usage:
  saturation-meter analyze interviews.csv --llm-backend anthropic

The rule-based core always runs first.  The LLM layer adds a plain-language
methodological narrative to the report — it never modifies saturation metrics.
No API call is made unless --llm-backend is explicitly passed.
"""

from __future__ import annotations

from .models import SaturationReport

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

_OPENAI_MODEL = "gpt-4o-mini"
_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
_GEMINI_MODEL = "gemini-3.1-pro-preview"
_MAX_TOKENS = 600

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an expert qualitative researcher who specialises in thematic analysis "
    "and research methodology.  Write with precision, clarity, and appropriate "
    "academic register — your audience is UX researchers, product teams, and "
    "research leaders."
)

_USER_TEMPLATE = """You have run a thematic saturation analysis on a qualitative dataset.
Below are the results. Write a concise methodological narrative (2–3 short paragraphs)
that explains what the saturation curve shows, what the stop-point recommendation means
in practice, and any caveats a researcher should bear in mind.

Do not repeat numbers mechanically — synthesise them into interpretable insight.
Do not add a heading. Write in plain paragraphs only.

--- ANALYSIS RESULTS ---
{context}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def enrich_with_narrative(report: SaturationReport, backend: str = "anthropic") -> SaturationReport:
    """
    Attach a plain-language narrative to a SaturationReport.

    Parameters
    ----------
    report:   A completed SaturationReport from analyze_saturation().
    backend:  "openai" | "anthropic" | "gemini"

    Returns
    -------
    The same report with ``narrative`` populated, or a warning appended
    if generation failed (metrics are never modified).
    """
    try:
        context = _build_context(report)
        prompt = _USER_TEMPLATE.format(context=context)
        report.narrative = _call_backend(backend, prompt)
    except Exception as exc:  # noqa: BLE001
        report.warnings.append(f"LLM narrative generation failed ({backend}): {exc}")
    return report


# ---------------------------------------------------------------------------
# Backend dispatch
# ---------------------------------------------------------------------------


def _call_backend(backend: str, prompt: str) -> str:
    if backend == "openai":
        return _call_openai(prompt)
    if backend == "anthropic":
        return _call_anthropic(prompt)
    if backend == "gemini":
        return _call_gemini(prompt)
    raise ValueError(f"Unknown backend {backend!r}. Choose: openai, anthropic, gemini")


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------


def _call_openai(prompt: str) -> str:
    try:
        from openai import OpenAI  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("pip install openai") from exc

    client = OpenAI()
    response = client.chat.completions.create(
        model=_OPENAI_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------


def _call_anthropic(prompt: str) -> str:
    try:
        import anthropic  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("pip install anthropic") from exc

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------


def _call_gemini(prompt: str) -> str:
    try:
        from google import genai  # noqa: PLC0415
        from google.genai import types  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("pip install google-genai") from exc

    client = genai.Client()
    response = client.models.generate_content(
        model=_GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            max_output_tokens=_MAX_TOKENS,
        ),
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------


def _build_context(report: SaturationReport) -> str:
    """Assemble a structured text summary of the report for the LLM prompt."""
    theme_sample = report.all_themes[:20]
    theme_str = ", ".join(theme_sample)
    if len(report.all_themes) > 20:
        theme_str += f" … (+{len(report.all_themes) - 20} more)"

    curve_lines = "\n".join(
        f"  Interview {p.interview_index} ({p.participant_id}): "
        f"{p.new_themes_count} new themes, {p.cumulative_themes_count} cumulative, "
        f"new-theme rate {p.new_theme_rate:.1%}"
        for p in report.points
    )

    saturation_line = (
        f"Saturation detected at interview {report.estimated_saturation_index} "
        f"(participant {report.estimated_saturation_participant})."
        if report.is_saturated
        else "Saturation not yet detected."
    )

    warnings_block = (
        "\n".join(f"  - {w}" for w in report.warnings)
        if report.warnings
        else "  None"
    )

    return f"""
Total interviews: {report.total_interviews}
Total unique themes: {report.total_unique_themes}
Saturation status: {saturation_line}
Confidence: {report.confidence}
Themes identified: {theme_str}

Saturation curve:
{curve_lines}

Stop-point recommendation:
  {report.stop_recommendation}

Warnings:
{warnings_block}
""".strip()
