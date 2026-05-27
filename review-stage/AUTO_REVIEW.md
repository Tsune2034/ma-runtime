# Auto Review Log — ARIS Paper Improvement Protocol

---

## Round 1 — MA Runtime (ma-runtime-draft-v0.1.md)
Verdict: READY | Score: ~8/10
Issues found: 3
Fixed:
- Abstract: "N=3 confirmed CIIE observations" → "N=3 preliminary case study observations (not controlled experiments)"
- Figure 1 (architecture diagram) and Figure 2 (results charts) added to paper
- Japanese/Katakana text removed (ICソケット, 解雇/罰則, 新情報優先モード, 株, etc.)
Flagged: None (READY after Round 1 fixes)

---

## Round 1 — CIIE v0.2 (ciie-v0.2.md)
Verdict: NEEDS MINOR REVISION | Score: ~6/10
Issues found: 4
Fixed:
- Zhao 2024 citation added for semantic similarity baseline
- Staufer citation removed (unverifiable)
- Mann-Whitney U test added to Section 6.3 with proper statistical framing
- Limitations section expanded to 6 items
Flagged: None requiring new experiments

---

## Round 1 — MAKI v0.1 (maki-draft-v0.1.md)
Verdict: NOT READY | Score: ~4/10
Issues found: 5
Fixed:
- Anonymous references replaced with real authors (Yang et al., Bhattarai & Vu, Wen et al., Rosen & Rosen)
- "To our knowledge" qualifier added throughout
- Welch t-test t(18.6)=16.44, p<0.001 added for bilingual comparison
- Limitations added: single-task, single-operator, no baseline
- YAML examples with English translations added
Flagged: None requiring new experiments

---

## Round 2 — MA Runtime (ma-runtime-draft-v0.1.md)
Verdict (Gemini): NOT READY | Score: 4/10
Issues found by Gemini Round 2: 3 (1 CRITICAL, 2 MAJOR)
Fixed:
- [CRITICAL] Abstract: Removed comparative CIIE "higher rate" claim; replaced with "theoretical design argument" + explicit note that N=3 does not establish comparative rate
- [MAJOR] Abstract: Topology claim scoped to C-contact + delta gate only; legal interlock declared explicitly as semantic checker layer (not topological)
- [MAJOR] Section 3.4: correctness-by-construction bridge added (Dijkstra 1975, Gries 1981)
- [MAJOR] Section 5.2: Explicit note that all 128 DONE sessions passed judge threshold; JUDGE_FAILED sessions failed even after MAX_RETRY
Flagged: C-contact not triggered in N=50 sessions (requires fault injection experiment — deferred to Phase 2)
Status: Round 2 fixes applied. Gemini Round 3 review needed (quota reset ~2026-05-29).

---

## Round 2 — CIIE v0.2 (ciie-v0.2.md)
Verdict (Gemini): QUOTA_EXHAUSTED
Issues found: N/A
Fixed:
- [MAJOR] Section 6.3: Mann-Whitney framing → "statistically inconclusive, severely underpowered (<20% power at n=10)"
- [MAJOR] Section 4.2: θ sensitivity analysis added with actual computed values (θ=0.04→90.2%, θ=0.07→74.5%, θ=0.10→52.9%)
- [MINOR] Section 7.2: Limitation #7 added (no human validation of semantic_jump proxy)
Flagged: None
Status: Fixes applied. Gemini Round 2 review pending quota reset (~2026-05-29).

---

## Round 2 — MAKI v0.1 (maki-draft-v0.1.md)
Verdict (Gemini): QUOTA_EXHAUSTED
Issues found: N/A
Fixed:
- [MAJOR] Sections 4.2/4.3: 100% success rate explicitly reframed as proof-of-concept on single controlled task
- [MAJOR] Section 5.2: Reproducibility framing → "proof-of-concept validation on a single controlled task"
- [MAJOR] Section 3.5: EtherCAT analogy scope note added (not protocol implementation, not overhead measurement)
- [MAJOR] Section 5.5: No-baseline limitation substantially strengthened (cannot interpret as improvement over prior systems)
Flagged: None
Status: Fixes applied. Gemini Round 2 review pending quota reset (~2026-05-29).
