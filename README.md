# MA Runtime — Hardware Safety Topology for AI Agent Execution

**Daisuke Tsunemori** · One Hour Value Inc. · Japan

> *"Safety is not a layer you add on top. It is a topological property of the execution graph."*

---

## Overview

**MA Runtime** is an autonomous AI agent execution framework whose safety architecture is derived directly from hardware safety engineering — specifically:

- **C-contact (normally-closed) fail-over**: Automatic switchover to a backup LLM shell on primary failure
- **Cascade control with delta gating**: External agent outputs are reconciled against persistent internal state; only genuine information deltas propagate
- **Two-tier legal interlock**: LOW warning (execution continues, flagged) / HIGH latch (execution halts, human reset required) — modeled on IEC 61508 Safety Integrity Levels
- **Policy engine + retry engine**: Five failure mode types diagnosed automatically, with type-specific retry strategies bounded at MAX_RETRY=2
- **Observer audit logging**: Every session produces a structured JSON trace for reproducibility

The framework also introduces **CIIE (Creative Intelligence Insight Event)** — the first operationally-defined, induction-design-targeted construct for "aha moments" in human-AI dialogue.

---

## Key Results (N=50)

| Metric | Value |
|--------|-------|
| Task completion (DONE) | 86.0% |
| Legal interlock activation | 8.0% |
| Retry recovery rate | 86% (19/22) |
| Mean execution time | 25.8 s |
| Judge score (mean) | 0.726 |

---

## Repository Structure

```
ma-runtime/
├── ma_runtime.py          # Core implementation (v3)
├── paper/
│   └── ma-runtime-draft-v0.1.md   # Paper draft
├── experiments/
│   └── sessions/          # N=50 Observer audit logs (JSON)
└── README.md
```

---

## Requirements

```bash
pip install requests python-dotenv
```

Set environment variables:
```bash
export OPENROUTER_API_KEY=your_key_here
# Gemini CLI (B-shell / C-contact fallback)
# Install: https://github.com/google-gemini/gemini-cli
```

## Usage

```bash
python3 ma_runtime.py "Your goal here"
```

Output: structured JSON result + Observer log in `experiments/sessions/`

---

## Paper

**"MA Runtime: Applying Hardware Safety Topology to Autonomous AI Agent Execution"**

Draft v0.1 — 2026-05-25  
Target: arXiv cs.AI / cs.HC

Key novelty claims:
1. First application of hardware safety topology (HW→AI direction) to AI agent architecture
2. First treatment of CIIE as an *induction design target* rather than a post-hoc detection problem

---

## Background

The author has 25 years of experience as a field/equipment engineer, including 10 years as a semiconductor FSE (ASM Japan · CVD/ALD process equipment), specializing in systems where failure means physical harm. The safety design patterns in this framework — EMO topology, C-contact fail-safe, cascade control — were validated in that context before being applied to AI execution.

---

## License

MIT License — © 2026 Daisuke Tsunemori
