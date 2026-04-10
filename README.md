# saturation-meter

**Thematic saturation estimation from coded transcript data — with stop-point guidance.**

Part of the [CPR Orbital](https://github.com/kgkazakos) 40-tool open-source series for AI-native product research infrastructure.

---

## The problem

You are running a qualitative study. You have 6 interviews coded. Or 10. Or 14.
And someone — a stakeholder, a PM, your own instinct — is asking the same question:

*"Are we done? Can we stop?"*

The honest answer is: saturation is an empirical question, not a gut call.
Thematic saturation occurs when new interviews stop contributing new themes or
codes to your corpus. But tracking it by hand, interview by interview, is
tedious — and most teams don't do it at all.

`saturation-meter` does it for you.

---

## What it does

- Calculates **per-interview new-theme rates** as you add coded data
- Plots a **saturation curve** — cumulative themes and marginal discovery over time
- Applies a **configurable detection algorithm** (rolling window + threshold)
- Returns a **stop-point recommendation** with confidence rating
- Emits **structured JSON** for CI integration or downstream analysis
- Optionally generates a **plain-language narrative** via DSPy (community scaffolding)

---

## Installation

```bash
pip install saturation-meter
```

With optional LLM enrichment:

```bash
pip install "saturation-meter[llm]"
```

---

## Usage

### CLI — full report

```bash
saturation-meter analyze interviews.csv
```

```
╭─────────────────── saturation-meter ────────────────────╮
│  SATURATED  ·  confidence: high                          │
╰──────────────────────────────────────────────────────────╯

  Interviews analysed : 10
  Unique themes found : 10
  Saturation from     : interview 5  (participant P05)

   #   Participant     New themes  Cumulative  Rate   Signal
   1   P01                      6           6  100.0%  ○ active
   2   P02                      2           8   25.0%  ○ active
   3   P03                      2          10   20.0%  ○ slowing
   4   P04                      0          10    0.0%  –
   5   P05                      0          10    0.0%  ● saturated
   ...
```

### CLI — JSON output (for CI)

```bash
saturation-meter analyze interviews.csv --json-output
```

```json
{
  "total_interviews": 10,
  "total_unique_themes": 10,
  "is_saturated": true,
  "estimated_saturation_index": 5,
  "estimated_saturation_participant": "P05",
  "confidence": "high",
  "stop_recommendation": "Saturation detected from interview 5 ...",
  "saturation_curve": [...]
}
```

### CLI — saturation curve only

```bash
saturation-meter curve interviews.csv
```

Returns a JSON array of per-interview metrics — pipe into your plotting tool of choice.

### CLI — tuning parameters

```bash
# Use a 10 % threshold (default 5 %) and a window of 2 (default 3)
saturation-meter analyze interviews.csv --threshold 0.10 --window 2
```

### Python API

```python
from saturation_meter import InterviewEntry, analyze_saturation

interviews = [
    InterviewEntry("P01", ["cognitive_load", "feature_overload", "trust_deficit"]),
    InterviewEntry("P02", ["cognitive_load", "feature_overload", "onboarding_friction"]),
    # ...
]

report = analyze_saturation(interviews)
print(report.is_saturated)         # True / False
print(report.confidence)           # "high" | "medium" | "low" | "insufficient_data"
print(report.stop_recommendation)  # plain-language guidance
```

---

## Input format

### CSV

```
participant_id,codes
P01,"cognitive_load,feature_overload,navigation_confusion"
P02,"cognitive_load,trust_deficit,onboarding_friction"
```

### JSON

```json
[
  {"participant_id": "P01", "codes": ["cognitive_load", "feature_overload"]},
  {"participant_id": "P02", "codes": "cognitive_load,trust_deficit"}
]
```

Codes are **case-insensitive** and **whitespace-normalised** on load.

---

## How saturation detection works

For each interview (in sequence):

1. Count themes not seen in any prior interview → `new_theme_rate = new / cumulative`
2. Apply a **rolling window** of `n` consecutive interviews
3. If all rates in the window are ≤ threshold → saturation is flagged
4. The index of the **first interview in that window** is the saturation point

**Default parameters** (adjustable):
- `--threshold 0.05` — 5 % new-theme rate
- `--window 3` — 3 consecutive sub-threshold interviews

**Confidence** is based on how many interviews occurred after saturation:
- `high` — ≥ 2× window size
- `medium` — ≥ window size
- `low` — marginal evidence
- `insufficient_data` — fewer than 3 interviews

---

## LLM enrichment (community scaffolding)

The `--llm-backend` flag triggers narrative generation via DSPy.
This layer is **intentionally incomplete** — it ships as a contribution scaffold.

```bash
saturation-meter analyze interviews.csv --llm-backend anthropic
```

To implement: see `saturation_meter/llm.py` and `CONTRIBUTING.md`.
No LLM call is ever made when the flag is absent.

---

## Part of the CPR Ecosystem

`saturation-meter` is Tool 8 in the **CPR Orbital** series — 40 open-source tools
for AI-native product research infrastructure, shipping every Friday from March to
December 2026.

Related tools:
- [`transcript-cleaner`](https://github.com/kgkazakos/transcript-cleaner) — fix diarization errors before coding
- [`qual-sniffer`](https://github.com/kgkazakos/qual-sniffer) — detect methodological weaknesses in discussion guides
- [`guide-scorer`](https://github.com/kgkazakos/guide-scorer) — score discussion guides across 8 quality dimensions
- [`research-rubric`](https://github.com/kgkazakos/research-rubric) — evaluate qualitative research quality

**Computational Product Research** — [github.com/kgkazakos](https://github.com/kgkazakos)

---

## Development

```bash
git clone https://github.com/kgkazakos/saturation-meter
cd saturation-meter
pip install -e ".[dev]"
pytest tests/ -v
ruff check saturation_meter/
```

---

## License

MIT © Kostas Kazakos
