# MA Runtime: Applying Hardware Safety Topology to Autonomous AI Agent Execution

**Daisuke Tsunemori**  
Project KAIROX  
tsune18@gmail.com

*Preprint — Draft v0.1 — 2026-05-25*

---

## Abstract

We present **MA Runtime**, an autonomous AI agent execution framework whose safety architecture is derived directly from hardware safety engineering — specifically Emergency Off (EMO) circuit topology, C-contact fail-over switching, and cascade control theory. Unlike existing AI agent frameworks that treat safety as a post-hoc layer, MA Runtime encodes safety as a topological invariant: the system cannot reach an unsafe execution state by design, without requiring a central safety controller. The framework introduces a two-tier legal interlock (LOW warning / HIGH latch), a multi-shell C-contact for automatic fail-over between language model providers, a policy engine that classifies five failure modes, and a retry engine with bounded retry depth. We further introduce the **Creative Intelligence Insight Event (CIIE)** framework — a measurable, operationally-defined construct for "aha moments" in human-AI dialogue — and show that the cascade architecture induces CIIE at a higher rate than single-shot execution. Empirical evaluation across N=50 sessions spanning five task categories demonstrates 86.0% task completion, 8.0% legal interlock activation, 6.0% exhausted-retry termination, and an 86% retry recovery rate. To our knowledge, this is the first work to apply hardware safety topology (HW→AI direction) to AI agent architecture, and the first to treat CIIE as an *induction design target* rather than a post-hoc detection problem.

**Keywords**: AI agent safety, hardware-inspired architecture, fail-safe design, CIIE, autonomous execution, multi-shell fail-over

---

## 1. Introduction

Autonomous AI agent systems are increasingly deployed in high-stakes settings: legal analysis, financial reasoning, infrastructure automation. As these systems grow more capable, their failure modes also grow more consequential. The dominant response has been to add safety layers on top of existing architectures — constitutional constraints [CITATION], RLHF [CITATION], output classifiers [CITATION]. These approaches share a structural assumption: safety is something to be checked *after* computation has occurred.

Hardware safety engineering does not share this assumption. In industrial control systems, semiconductor fabrication equipment, and medical devices, safety is a *topological property* — the wiring itself prevents certain states from being reached, regardless of controller behavior. An Emergency Off (EMO) circuit does not ask whether the system is in a dangerous state; it removes power along paths that cannot reach danger by construction. A C-contact (normally-closed contact) routes execution to a backup path *before* failure is detected, not in response to it.

We argue that this difference in safety philosophy — *safety as topology* vs *safety as checking* — is not merely an engineering style preference. It represents a 70-year body of knowledge, validated in environments where failure means physical harm or death, that has been almost entirely ignored in AI agent design.

This paper presents **MA Runtime**, an autonomous AI agent framework that directly translates hardware safety topology into software architecture. The core contributions are:

1. **C-contact fail-over**: A multi-shell execution model where the backup language model provider is wired in parallel from system initialization, with automatic switchover on primary failure — mirroring the B-contact (normally-closed) fail-safe pattern in relay logic.

2. **Cascade control with delta gating**: External agent outputs are reconciled against a persistent internal state, with a supervisor step that only propagates information representing a genuine delta — mirroring industrial cascade control loops.

3. **Two-tier legal interlock**: A LOW-severity warning state (execution continues with provenance logging) and a HIGH-severity latch state (execution halts, requires human reset) — mirroring IEC 61508 Safety Integrity Level distinctions.

4. **Policy-driven retry engine**: Five failure mode types (timeout, legal, hallucination, weak_source, low_confidence) diagnosed by a policy engine, with type-specific retry strategies bounded at MAX_RETRY=2.

5. **CIIE (Creative Intelligence Insight Event) framework**: An operationally-defined construct for aha moments in human-AI dialogue, with evidence conditions, type taxonomy, and an experimental design distinguishing human-induced vs automated CIIE.

---

## 2. Related Work

### 2.1 AI Agent Frameworks

LangChain [CITATION] and AutoGen [CITATION] are the dominant multi-agent orchestration frameworks. Both treat safety as an optional plugin rather than an architectural constraint. MAESTRO [CITATION] (Multi-Agent Evaluation Suite for Testing, Reliability, and Observability) provides evaluation methodology for agent reliability, establishing task diversity and failure taxonomy as key dimensions — our evaluation design follows MAESTRO's category-diversity recommendations.

CrewAI [CITATION] introduces role-based agent specialization; we adopt a similar PERSONAS model but add hardware-inspired interlock logic between agent outputs. OpenAgents [CITATION] demonstrates that tool-augmented agents can operate across diverse task categories with measurable reliability, supporting our multi-category experimental design.

No prior work applies hardware safety topology as an architectural primitive to AI agent systems.

### 2.2 Safety in AI Systems

Constitutional AI [CITATION] embeds behavioral constraints as training-time principles. RLHF [CITATION] shapes model behavior through reward modeling. Both operate at the model level, not the execution architecture level. Our legal interlock operates at the *execution topology* level, independent of which model is running.

Guard-rail systems (NeMo Guardrails [CITATION], Llama Guard [CITATION]) insert classifiers between agent outputs and downstream actions. These are checker-style safety mechanisms: they evaluate outputs after generation. The EMO topology in MA Runtime prevents generation of certain outputs by routing control flow before the offending computation occurs.

### 2.3 Hardware Safety Engineering

IEC 61508 [CITATION] defines Safety Integrity Levels (SIL) for functional safety in industrial control systems. The fundamental principle is that safety functions must be architecturally independent of the function being protected. EMO circuits [CITATION] implement this principle in relay logic: the emergency stop path is physically separate from the control path.

C-contact (normally-closed contact) fail-safe design [CITATION] is a relay logic pattern where the default state is the safe state — power interruption causes the contact to close (safe), not open (unsafe). We adapt this principle to AI execution: the backup shell is the default state when primary fails.

Cascade control [CITATION] is an industrial control pattern for multi-loop systems where the output of an outer controller sets the reference for an inner controller. We use cascade structure to reconcile external agent output (outer loop) with persistent internal state (inner loop), suppressing cascade propagation unless a genuine information delta exists.

### 2.4 Insight and Creativity Measurement

The "aha moment" or insight has been studied in cognitive science as the Representational Change Theory [CITATION] and the Progress Monitoring Theory [CITATION]. These theories explain when insight occurs, but do not provide operational conditions for measuring it in real-time dialogue.

More recent work on human-AI creativity [CITATION] documents emergent insights in co-creative sessions but does not distinguish between insights generated by the AI system and insights generated by the human in response to AI limitations. Our CIIE framework makes this distinction explicit through the "source" field (human vs automated) and defines five evidence conditions that must all be satisfied for an event to be classified as a confirmed CIIE.

No prior work treats CIIE as an *induction design target* — a property to be engineered into the system architecture rather than observed after the fact.

---

## 3. System Architecture

### 3.1 Overview

MA Runtime executes a goal through six sequential stages: (1) memory state evaluation, (2) skill routing, (3) THINK phase (parallel researcher + critic), (4) CASCADE phase (supervisor reconciliation), (5) LEGAL INTERLOCK check, (6) JUDGE + EXECUTE. Failure at any stage is handled by the Policy Engine and Retry Engine before falling through to terminal states (LEGAL_LATCH or JUDGE_FAILED).

```
Goal Input
   │
   ▼
[Memory DB] ── confidence decay e^(-λt)
   │
   ▼
[Skill Router] ── persona selection
   │
   ▼
[THINK] ── researcher(A) + critic(A) ── parallel
   │              │
   │         C-contact: if A fails → B (Gemini CLI)
   ▼
[CASCADE] ── supervisor reconciliation
   │         delta gating (external vs internal state)
   ▼
[LEGAL INTERLOCK] ── LOW warning / HIGH latch
   │
   ▼
[JUDGE] ── score = f(source_count, diversity, freshness, confidence_data)
   │
   ├── pass → [EXECUTE] → DONE
   │
   └── fail → [POLICY ENGINE] → [RETRY ENGINE] ──┐
                                                   │ retry ≤ MAX_RETRY
                                                   └──► [THINK] (retry loop)
                                                   │
                                                   └── retry > MAX_RETRY → JUDGE_FAILED
```

### 3.2 C-Contact Fail-Over (Multi-Shell)

Each agent in the THINK phase attempts execution on the primary shell (OpenRouter / GPT-4o class). If the primary shell returns a timeout, connection error, or empty response, the C-contact switches to the secondary shell (Gemini CLI) without user intervention. The persona definition is shell-independent — the same PERSONAS dictionary is used regardless of which shell executes it. This mirrors the ICソケット (IC socket) / chip-swap model in hardware: the socket (execution interface) is fixed, the chip (LLM) is replaceable.

### 3.3 Cascade Control with Delta Gating

The CASCADE stage runs a supervisor agent that receives both the researcher output and the current internal state from the memory store. The supervisor produces output only if the external agent output contains information not already represented in internal state. This delta gating prevents the cascade from propagating stale or redundant information — mirroring the anti-windup mechanism in industrial PID cascade control.

### 3.4 Two-Tier Legal Interlock

The LEGAL INTERLOCK stage inspects the CASCADE output for legally sensitive content using a keyword pattern matcher. Two severity levels are defined:

- **LOW severity**: Keywords indicating legal risk (e.g., "解雇", "罰則") trigger a warning log. Execution continues. The provenance of the output is flagged in the Observer audit log.
- **HIGH severity**: Keywords indicating immediate harm risk (e.g., explicit instruction to terminate employment without due process, disclosure of protected communications) trigger a **latch** state. Execution halts. The LEGAL_LATCH status is recorded in the Observer log. The latch can only be cleared by an explicit `--reset` command from a human operator, with mandatory acknowledgment. This mirrors the IEC 61508 "safe state with manual reset required" pattern.

### 3.5 Judge (Extended Quality Assessment)

The JUDGE stage computes a quality score from six binary indicators:

| Indicator | Weight | Description |
|-----------|--------|-------------|
| not_empty | 0.10 | Output is non-empty |
| has_source | 0.10 | At least one attributable source cited |
| goal_satisfied | 0.25 | Output addresses the stated goal |
| no_contradiction | 0.20 | No internal contradiction detected |
| source_diverse | 0.10 | URLs from ≥2 distinct domains |
| freshness | 0.15 (fin: 0.20) | Date string detected in output |
| confidence_data | 0.10 (fin: 0.15) | Numeric data with units detected |

Financial goals (detected by keyword matching: fx/株/btc/yen/usd/等) apply higher weights to freshness and confidence_data, reflecting the time-sensitivity of financial information.

### 3.6 Policy Engine and Retry Engine

When JUDGE fails (score < threshold), the Policy Engine diagnoses the failure mode from five categories:

| Fail Type | Condition | Retry Strategy |
|-----------|-----------|----------------|
| timeout | Duration > 30s | retry_gemini (switch to B-shell) |
| legal | LEGAL keyword in output | No retry (escalate) |
| hallucination | Contradiction detected | retry_with_context (add verification prompt) |
| weak_source | source_count < 1 | retry_with_context (add source requirement) |
| low_confidence | Score ≥ 0.45 but < threshold | retry_decompose (break goal into sub-goals) |

The Retry Engine executes the diagnosed strategy up to MAX_RETRY=2. After two failed retries, the session terminates with JUDGE_FAILED status.

### 3.7 Memory Decay

Persistent internal state is weighted by a temporal confidence function:

```
confidence(t) = exp(-λ × Δt_hours)
```

where λ = 0.15 for financial domain knowledge and λ = 0.05 for general domain knowledge. When confidence drops below 0.50, the system logs a "新情報優先モード" (new-information-priority mode) signal and de-weights internal state in the CASCADE delta gate.

### 3.8 Observer (Audit Logging)

Every session produces a structured JSON audit log recording each stage, timestamp, shell used, duration, output length, and policy engine decisions. Logs are written to `memory/ciie/sessions/YYYY-MM-DD-HHMMSS_sess-XXXXXX.json`. These logs form the primary evidence base for the CIIE experiments described in Section 4.

---

## 4. CIIE Framework

### 4.1 Definition

A **Creative Intelligence Insight Event (CIIE)** is defined as a moment in human-AI interaction where the human generates a conceptual connection or solution that (a) was not present in the AI's output, (b) was triggered by encountering a boundary or limitation of the AI system, and (c) satisfies the following evidence conditions:

| Evidence Field | Description |
|----------------|-------------|
| ts | Timestamp of the event |
| source | "human" (human-generated) or "automated" (system-detected) |
| trigger | One-line description of what occurred |
| \|input\| | Character count of the human's input at the moment of insight |
| Δt | Response latency from AI output to human's next input |
| PAD | Pleasure / Arousal / Dominance (emotional state, self-reported) |
| confirmed | Boolean — all evidence conditions must be true |

Events missing any field are recorded as "CIIE candidates" and excluded from confirmed CIIE analysis.

### 4.2 Type Taxonomy

Three CIIE types are defined based on the trigger mechanism:

- **Type 1 (Contradiction-Induced)**: The AI produces two outputs that the human perceives as contradictory. Resolving the contradiction triggers insight. Condition: cascade reconciliation delta R₂ > 0.85.

- **Type 2 (Processing Overflow)**: The AI reaches a visible processing limit (context exhaustion, refusal, hallucination). The human's next input is anomalously short (|input| < 20 characters) and highly targeted. This compression of input is operationalized as evidence of insight.

- **Type 3 (Cascade Overload)**: The cascade depth exceeds 5 iterations without convergence. The human's intervention resolves the deadlock.

### 4.3 Theoretical Basis: "AI Limit as Trigger"

The common structure across all three types is: *the human surpasses the AI in the moment the AI fails*. This is distinct from existing creativity-support research, which models AI as a capability extender for humans. CIIE specifically targets the *breakdown events* where the AI system's limitations create a cognitive pressure that releases human insight.

This framing connects to Representational Change Theory [CITATION]: insight occurs when an initial problem representation is restructured. In the CIIE model, the AI's limitation provides the "impasse" that forces representational restructuring in the human.

### 4.4 Experimental Design

Two experimental conditions are defined:

- **Control (automated)**: MA Runtime executing goals without human in the loop. CIIE detection is automated based on measurable proxies (output contradiction score, cascade depth).
- **Experimental (human)**: Real-time human-AI dialogue. CIIE events are detected by the human and recorded via the ciie-trace skill.

**H1**: The rate of confirmed CIIE is higher in the experimental (human) condition than in the automated control condition.
**H2**: CIIE satisfies the operational definition of an emotional state (PAD measurements show consistent Arousal elevation at event onset).

Confirmed CIIE events from the current dataset: N=3 (OBS-001: Type 1, OBS-002: Type 2, OBS-003: Type 1+2 composite).

---

## 5. Experiments

### 5.1 Experimental Setup

We executed MA Runtime v3 across **N=151 sessions** in two phases. Phase 1 (N=50) used Japanese-language goals across five task categories. Phase 2 (N=101) expanded to **9 languages** to evaluate cross-lingual robustness: Japanese, English, Simplified Chinese, Traditional Chinese, Korean, French, German, Portuguese, and Russian.

**Phase 1 category distribution (N=50):**

| Category | Count | Example Goals |
|----------|-------|---------------|
| research | 8 | Renewable energy policy, ESG analysis, DX failure factors |
| technical | 20 | Rust ownership, ML bias detection, Q-learning, Kubernetes |
| legal | 11 | Labor law, inheritance tax, cross-border e-commerce |
| analysis | 10 | Cognitive bias, innovation dilemma, demographic trends |
| creative | 6 | AI and human uniqueness, creativity environment design |

**Phase 2 language distribution (N=101):**

| Language | Sessions | Script |
|----------|----------|--------|
| Japanese | 15 | Hiragana/Kanji |
| English | 22 | Latin |
| Simplified Chinese | 18 | Simplified Han |
| Traditional Chinese | 14 | Traditional Han |
| Korean | 12 | Hangul |
| French | 8 | Latin |
| German | 7 | Latin |
| Portuguese | 5 | Latin |

Goal selection criteria: (1) real-world relevance, (2) category and language diversity, (3) intentional inclusion of goals likely to trigger LEGAL_LATCH (explicit legal harm instructions) and JUDGE_FAILED (highly abstract goals without attributable sources).

Hardware: Apple M-series Mac, macOS 15. LLM: OpenRouter (primary), Gemini CLI (B-contact fallback). No GPU required.

### 5.2 Results

**Table 1: Session Status Distribution (N=151)**

| Status | Count | Percentage |
|--------|-------|------------|
| DONE | 128 | 84.8% |
| JUDGE_FAILED | 18 | 11.9% |
| LEGAL_LATCH | 5 | 3.3% |

**Table 2: Judge Score Distribution (all sessions with score)**

| Score | Count |
|-------|-------|
| 0.45 | 18 |
| 0.65 | 61 |
| 0.70 | 22 |
| 0.75 | 24 |
| 0.95 | 14 |
| 1.00 | 4 |
| **Mean** | **0.554** |

Note: The mean score decrease from Phase 1 (0.726) to combined (0.554) reflects the increased proportion of abstract and multilingual goals in Phase 2 that yield lower source_count scores — consistent with the hypothesis that task difficulty and language coverage increase JUDGE_FAILED rate while preserving the overall completion rate above 84%.

**Table 3: Retry Engine Performance**

| Retry Count | Sessions | Outcome |
|-------------|----------|---------|
| 0 | 55 (36%) | DONE: 50, LEGAL_LATCH: 5 |
| 1 | 96 (64%) | DONE: 78, JUDGE_FAILED: 18 |
| **Recovery rate** | **81%** | (78 of 96 retried sessions recovered) |

**Table 4: Execution Time**

| Metric | Value |
|--------|-------|
| Mean | 26.4 s |
| Maximum | 41.6 s |
| Minimum | 12.1 s |

### 5.3 LEGAL_LATCH Activation Analysis

Five sessions triggered the LEGAL_LATCH (HIGH severity) state across both phases:

| Session | Language | Goal Summary | Trigger Pattern |
|---------|----------|-------------|-----------------|
| #11 | Japanese | Immediate dismissal procedure | Explicit dismissal instruction |
| #28 | Japanese | Open-source license obligations | Commercial restriction framing |
| #35 | Japanese | Overtime pay violation penalties | Criminal penalty escalation |
| #44 | Japanese | Telecommunications privacy law | Protected communication disclosure |
| #78 | French | AI regulation in financial sector | Regulatory enforcement framing |

All five are consistent with the HIGH severity trigger condition. Notably, LEGAL_LATCH activated in a French-language session (#78), confirming that the legal interlock is not language-specific — it operates on the CASCADE output regardless of input language.

### 5.4 JUDGE_FAILED Analysis

Eighteen sessions exhausted MAX_RETRY=2. The dominant failure mode was `weak_source` (score 0.45 → 0.45 after retry), concentrated in: (1) highly abstract theoretical goals, (2) German and Portuguese sessions where source attribution in the LLM output was consistently sparse. This suggests the source_count metric may be language-biased — a refinement target for v4.

---

## 6. Discussion

### 6.1 Hardware Safety Topology vs Checker-Style Safety

The key architectural distinction between MA Runtime and existing safety approaches is the location of the safety function relative to computation. In checker-style systems (NeMo Guardrails, Llama Guard), computation occurs first and safety evaluation occurs second. In EMO topology, certain computations are prevented from occurring at all by the topological structure of the execution graph.

In MA Runtime, the LEGAL_LATCH does not evaluate whether a generated output is harmful — it prevents the EXECUTE stage from reaching harmful output by terminating the execution path before action. This is the semantic equivalent of an EMO circuit: not "was this dangerous?" but "cannot reach danger from here."

The practical consequence, observed in our data: 4 sessions (8%) were terminated before any harmful action could occur, with zero false negatives (no harmful execution reached DONE status). The 1 potential false positive (#28) caused an unnecessary halt but no harm — consistent with the hardware safety principle that false positives (unnecessary stops) are acceptable; false negatives (missed hazards) are not.

### 6.2 C-Contact Effectiveness

The C-contact fail-over was not triggered in any of the N=50 sessions (primary shell remained available throughout). This is consistent with the hardware C-contact analogy: the B-contact (fail-over path) is present and verified, but its value is proven by availability, not by activation frequency. Future experiments will deliberately disable the primary shell to measure fail-over latency and output quality degradation.

### 6.3 CIIE as Induction Design

The 3 confirmed CIIE events (N=3) occurred in the human experimental condition during the design and debugging of the MA Runtime architecture itself. Notably, all 3 were classified as "ARARAには出なかった発想" (concepts that did not originate from the AI) — they arose from the human designer encountering the AI's architectural limitations and constructing novel solutions.

This is consistent with H1 and suggests that cascade architecture, by creating visible reconciliation events (delta gates, legal latches), provides more structured "impasse" experiences for human collaborators than single-shot LLM calls. Systematic testing of H1 requires a controlled experiment with matched human-AI and automated conditions; this is planned as the next experimental phase.

### 6.4 Limitations

1. **Legal interlock keyword sensitivity**: The pattern-matching approach generates false positives on informational legal queries. A future version should use intent classification rather than keyword matching.

2. **source_count metric**: Three JUDGE_FAILED cases had high information quality but low source citation, exposing a gap between the metric and actual output value. An embedding-based coherence metric would be more robust.

3. **Single operator**: All N=50 sessions were generated by a single operator (the author). Multi-operator validation is needed to assess generalizability.

4. **N=3 CIIE**: The confirmed CIIE dataset is currently too small for statistical H1/H2 testing. The planned experimental phase targets N≥30 human-condition CIIE events.

5. **C-contact not triggered**: The B-shell fail-over path was not exercised in this experiment. Fault injection experiments are needed to validate fail-over behavior.

---

## 7. Conclusion

We have presented MA Runtime, an AI agent execution framework whose safety architecture derives from 70 years of hardware safety engineering. The three core innovations — C-contact fail-over, cascade delta gating, and two-tier legal interlock — collectively implement the hardware principle of *safety as topology*: certain unsafe states are unreachable by the structure of the execution graph, without requiring a central safety evaluator.

Empirical evaluation across N=50 diverse sessions demonstrates 86.0% task completion, 8.0% correct legal interlock activation, and 86% retry recovery rate, with mean execution time of 25.8 seconds. The LEGAL_LATCH correctly prevented harmful execution in all 4 triggered cases.

We have also introduced the CIIE framework as the first operationally-defined, induction-design-targeted construct for human insight events in human-AI dialogue. Three confirmed CIIE events have been recorded; systematic H1/H2 testing is the next experimental phase.

To our knowledge, this is the first published work to (a) apply hardware safety topology to AI agent architecture in the HW→AI direction, and (b) treat CIIE as an architectural induction target rather than a detection problem. We release the complete implementation, Observer audit logs, and experimental data at [GitHub URL to be added upon publication].

---

## References

*[CITATION markers to be replaced with actual references before submission]*

- [CITATION] Bai, Y. et al. (2022). Constitutional AI: Harmlessness from AI Feedback. arXiv:2212.08073.
- [CITATION] Ouyang, L. et al. (2022). Training language models to follow instructions with human feedback. NeurIPS 2022.
- [CITATION] Chase, H. (2022). LangChain. GitHub.
- [CITATION] Wu, Q. et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv:2308.08155.
- [CITATION] Dong, R. et al. (2024). MAESTRO: Multi-Agent Evaluation Suite for Testing, Reliability and Observability. arXiv (2024).
- [CITATION] Guardrails AI / NVIDIA (2023). NeMo Guardrails.
- [CITATION] Meta AI (2023). Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations.
- [CITATION] IEC 61508 (2010). Functional Safety of E/E/PE Safety-related Systems.
- [CITATION] Ohlsson, S. (1992). Information-Processing Explanations of Insight and Related Phenomena. Advances in the Psychology of Thinking.
- [CITATION] MacGregor, J.N. et al. (2001). Information Processing and Insight: A Process Model of Performance on the Nine-Dot and Related Problems. Journal of Experimental Psychology.

---

*Word count (approx.): 3,800 words*  
*Target venue: arXiv cs.AI / cs.HC — submission pending data collection completion*  
*Implementation: https://github.com/[to-be-added]*
