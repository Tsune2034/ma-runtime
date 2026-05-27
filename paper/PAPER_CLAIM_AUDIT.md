# Paper Claim Audit Report — MA Runtime v0.1

**Date**: 2026-05-27  
**Auditors**: ARARA (Claude Sonnet 4.6) + Gemini 2.5 Pro (B-contact) + Codex GPT-5.5 (A-contact, zero-context, executed Python against raw files)  
**Paper**: MA Runtime: Applying Hardware Safety Topology to Autonomous AI Agent Execution  
**Raw data**: `/memory/ciie/sessions/2026-05-25-*.json` (N=151 files)

## Overall Verdict: PASS (after corrections)

## Corrections Applied During Audit

### FIXED: Abstract retry recovery rate
- **Was**: "86% retry recovery rate"
- **Now**: "81% retry recovery rate (78 of 96 retried sessions recovered)"
- **Evidence**: 78/96 = 81.25% → 81%

### FIXED: Table 2 Judge Score Distribution
- **Was**: Incorrect data (3+15+7+13+7+1=46 sessions, mean=0.726)
- **Now**: Correct data (78+11+12+19+2+6=128 sessions, mean=0.569)
- **Evidence**: Computed from 128 DONE session JSON files (judge step score field)

### FIXED: Author/contact info
- Removed `tsune18[at]gmail.com` from header
- Removed "Project KAIROX" branding → "MA Runtime v3"
- Added "Experimenter: Tsune2034"

## All Claims Verified

| # | Location | Claim | Evidence | Status |
|---|---------|-------|---------|--------|
| 1 | Abstract/Table 1 | N=151 sessions | 151 files in 2026-05-25 session dir | exact_match |
| 2 | Abstract/Table 1 | DONE=84.8% | 128/151=84.77% | rounding_ok |
| 3 | Abstract/Table 1 | LEGAL_LATCH=3.3% | 5/151=3.31% | rounding_ok |
| 4 | Abstract/Table 1 | JUDGE_FAILED=11.9% | 18/151=11.92% | rounding_ok |
| 5 | Table 3 | 0-retry=55 (DONE:50, LATCH:5) | Counter confirmed | exact_match |
| 6 | Table 3 | 1-retry=96 (DONE:78, FAILED:18) | 50+5+78+18=151 ✓ | exact_match |
| 7 | Table 3 | Recovery=81% | 78/96=81.25% | rounding_ok |
| 8 | Table 4 | Mean=26.4s | mean=26.361s | rounding_ok |
| 9 | Table 4 | Min=12.1s, Max=44.1s | exact | exact_match |
| 10 | Table 2 | Judge score distribution (corrected) | computed from session files | exact_match |

## Known Limitations (not errors)

- `[CITATION]` placeholders remain for LangChain, AutoGen, MAESTRO, CrewAI, OpenAgents, etc. — these are well-known frameworks whose existence is not disputed; full BibTeX will be added before peer submission.
- LEGAL_LATCH is implemented as a keyword pattern matcher, not a formal topological safety proof. This is an acknowledged limitation.
- N=151 from a single experimenter (Tsune2034); no inter-rater reliability.
