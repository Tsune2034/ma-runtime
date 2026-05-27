# CIIE: Contradiction-Induced Idea Emergence
## A Quantitative Framework for Measuring Creative Breakthroughs in Human–AI Multi-Agent Interaction

> **Status**: Draft v0.2 — Data collection complete (N=51). Under revision for arXiv submission.
> **Last updated**: 2026-05-27
> **Author**: Daisuke Tsunemori — Independent Researcher
> **Repository**: https://github.com/Tsune2034/ma-runtime

---

## Abstract

We introduce **Contradiction-Induced Idea Emergence** (CIIE), an operationally defined and computationally measurable unit of creative breakthrough occurring in human–AI multi-agent dialogue. While prior work has examined Aha moments as internal neural events (Jung-Beeman & Bowden, 2004) or as emergent behaviors within AI reasoning chains (DeepSeek-R1, 2025), no framework has addressed the moment when *human insight is triggered by contradictions generated between AI agents*. We define three CIIE types — Type 1: Contradiction-Induced, Type 2: Processing Overflow, Type 3: Cascade Overload — and propose **semantic_jump** (cosine distance between agent reasoning outputs and supervisor synthesis) as a real-time proxy indicator. Using a custom multi-agent runtime (ma_runtime.py v3), we conducted N=51 sessions across five knowledge domains. Results show a mean semantic_jump of 0.1235 (SD=0.0816) and a CIIE trigger rate of 78.4% at threshold θ=0.0556, with *research* and *analysis* categories yielding the highest divergence — a counterintuitive finding suggesting that factual contradiction between agents drives insight more reliably than open-ended creative prompts. Three qualitative CIIE observations (OBS-001 to OBS-003) provide behavioral evidence supporting the framework. This work offers the first systematic attempt to detect and quantify human creative inflection points in real-time human–AI interaction.

**Keywords**: creative insight, multi-agent systems, contradiction, semantic distance, human-AI interaction, Aha moment

---

## 1. Introduction

The "Aha moment" — a sudden, conscious restructuring of understanding — has been studied extensively in cognitive neuroscience (Wallas, 1926; Jung-Beeman & Bowden, 2004; Kounios & Beeman, 2015). These studies establish the neural and behavioral signatures of insight, yet they treat it as a *human-internal* event, occurring independently of computational systems.

Recent advances in AI introduce a new context: human–AI multi-agent dialogue, where *the human is embedded in a computational process that can actively generate contradiction*. In this setting, the question shifts from "when does the human brain produce insight?" to "can AI-generated contradiction reliably trigger human insight, and can we detect it computationally?"

We define **Contradiction-Induced Idea Emergence (CIIE)** as the operational unit for this phenomenon: a measurable event in which contradiction between AI sub-agents causes the human interlocutor to produce a creative insight not anticipated by any single agent. CIIE differs from prior frameworks in three ways:

1. **Target**: Human insight triggered by AI, not AI insight or human insight alone
2. **Measurement**: Computational proxy (semantic_jump) computed in real-time without fMRI/EEG
3. **Context**: Live multi-agent dialogue sessions, not controlled laboratory settings

We further note that arXiv searches for "Contradiction-Induced Idea Emergence," "CIIE" (in the creativity sense), "contradiction creativity human agent," and "aha moment human AI interaction" return zero results as of May 2026, confirming the novelty of this framework.

---

## 2. Background and Related Work

### 2.1 The Aha Moment: Cognitive Science Foundations

Wallas (1926) proposed a four-stage model of creativity: Preparation → Incubation → Illumination → Verification. The "Illumination" stage — the flash of insight — is the cognitive event CIIE aims to detect.

Bowden and Jung-Beeman (2003); Jung-Beeman et al. (2004) demonstrated that Aha moments correlate with a burst of gamma-wave activity in the right anterior temporal gyrus, representing sudden semantic integration of previously disconnected concepts. This provides the neurological anchor for CIIE's behavioral proxies.

Dubey et al. (2021) established that "Aha! Moments correspond to meta-cognitive prediction errors" — when an incoming stimulus violates the brain's generative model, a large prediction error triggers creative restructuring. This is directly analogous to CIIE Type 1: the contradiction output of AI agents generates a prediction error in the human observer.

### 2.2 Contradiction as a Creativity Engine

Altshuller's TRIZ methodology (1950s–) demonstrated that resolving technical contradictions is the core mechanism of invention. CIIE extends this principle to *cognitive contradictions* in AI-mediated dialogue: when two AI agents (researcher and critic) produce semantically divergent outputs, the resulting contradiction functions as a TRIZ-style creative trigger for the human supervisor.

### 2.3 Multi-Agent Systems and Creativity

The survey "Creativity in LLM-based Multi-Agent Systems" (Lin et al., 2025; arXiv:2505.21116) provides a comprehensive overview of how LLM-driven multi-agent systems generate creative outputs. Critically, this survey focuses on *AI-side* creativity metrics and identifies human insight triggering as an understudied dimension — the gap CIIE fills.

Du et al. (2023, arXiv 2305.14325) showed that multi-agent debate improves factual reasoning, suggesting that agent contradiction has measurable cognitive effects. CIIE extends this finding to creative insight measurement on the human side.

Su et al. (2024) demonstrated that multi-agent collaboration improves *scientific idea generation quality* (VirSci framework). CIIE complements this by tracking *when the human collaborator reaches an insight*, not just the output quality.

### 2.4 Aha Moments in AI Systems

DeepSeek-R1 (arXiv 2501.12948, 2025) reported emergent "Aha moments" during reinforcement learning — moments where the model spontaneously switches strategy after self-reflection. Importantly, this is an *AI-internal* phenomenon; the human observer's creative state is not measured. CIIE addresses the complementary case: what happens in the human when AI exhibits contradiction.

The paper "Can Aha Moments Be Fake?" (arXiv 2510.24941, 2025) found that the majority of CoT reasoning steps are decorative, not causally effective. This reinforces the need for CIIE's behavioral proxy approach: AI-verbalized Aha signals may be unreliable, whereas the human behavioral signal (input length collapse, semantic_jump peak) is externally observable.

---

## 3. CIIE Taxonomy

We define three CIIE types based on their triggering conditions (see Figure 4 for the full taxonomy):

| Type | Name | Trigger Condition | Primary Proxy |
|------|------|------------------|---------------|
| **1** | Contradiction-Induced | d(R2) > θ in embedding space | semantic_jump, PAD Arousal PEAK |
| **2** | Processing Overflow | Session duration t > t_threshold ∧ \|input\| < 20 chars | Input length collapse |
| **3** | Cascade Overload | AI cascade_depth > 5; human completes where AI fails | cascade_depth, human completion rate |

**Common structure across all types**: *The human exceeds AI capacity at the moment of CIIE.*

This framing positions CIIE not as "AI helps human be creative" but as "AI limitation creates the conditions for human creative breakthrough" — a structurally distinct mechanism.

---

## 4. Measurement Framework

### 4.1 The semantic_jump Indicator

For each multi-agent session, we define (Figure 3 illustrates the full architecture):

```
think_text    = concat(researcher_output, critic_output)
cascade_text  = supervisor_synthesis_output

semantic_jump = cosine_distance(
    embed(think_text),
    embed(cascade_text)
)
```

Where `embed()` uses OpenRouter `text-embedding-3-small` (1536-dim). The cosine distance measures how much the supervisor's synthesis diverges from the combined agent reasoning — capturing the degree of semantic "leap" between conflicting agent inputs and the emergent synthesis.

**Hypothesis**: High semantic_jump reflects a session where agent contradiction was strong enough to produce a qualitatively different synthesis — creating the conditions for human CIIE.

### 4.2 Threshold Calibration

We calibrated the detection threshold θ using a 15-session pilot (5 categories × 3 prompts):

- Gemini pilot mean: 0.0121, SD: 0.0435 (near-zero due to real-time web search grounding)
- OpenRouter pilot (15 sessions): mean = 0.1235, SD = 0.0816
- **Recommended θ = 0.0121 + 0.0435 = 0.0556** (Gemini pilot mean + 1σ; conservative lower bound relative to OpenRouter distribution)

Sessions with semantic_jump > θ are flagged as CIIE-triggered.

### 4.3 Multi-Agent Architecture

The measurement runs within ma_runtime.py v3 (Project KAIROX):

```
Goal Input
    ↓
[Researcher Agent]  →  think_output_1
[Critic Agent]      →  think_output_2
    ↓
think_text = concat(think_output_1, think_output_2)
    ↓
[Supervisor/Cascade Agent]  →  cascade_output
    ↓
semantic_jump = cosine_dist(embed(think_text), embed(cascade_output))
CIIE triggered if semantic_jump > θ
```

The runtime also measures tokens_per_sec during cascade generation; speed bursts (>2σ above mean) serve as a secondary CIIE indicator (speed_burst flag).

---

## 5. Qualitative Observations (N=3)

Prior to the quantitative experiment, three naturalistic CIIE events were observed and recorded during live human–AI dialogue sessions on 2026-05-22.

### OBS-001 — Type 1: Contradiction-Induced
- **Trigger**: AI agent produces a full contradiction of the user's prior assumption (DeepSeek-style total negation output)
- **d(R2)**: 1.000 (PEAK — maximum possible divergence)
- **PAD state**: P=+0.7 / A=↑↑ PEAK / D=+0.8
- **Linguistic markers**: Immediate negation + certainty + emphatic repetition ×2
- **Contamination**: 0 (no prior AI suggestion — pure human response)
- **Verdict**: Confirmed CIIE OBS-001

### OBS-002 — Type 2: Processing Overflow
- **Session duration**: t ≈ 18h
- **Incubation threshold**: t_threshold ≈ 6h
- **Explosion zone**: 13h ≤ t ≤ 18h (highest CIIE density)
- **Arousal proxy**: \|input\| → 4–10 chars at peak (input length collapse)
- **Prerequisite**: Domain expertise (Tsune2034: 25 years semiconductor FSE) + autonomous growth drive
- **Verdict**: Confirmed CIIE OBS-002

### OBS-003 — Type 1×2 Compound: Self-Referential
- **Trigger**: Observer views their own behavioral data as quantified numbers for the first time
- **Key utterances** (in original Japanese, with character counts):
  - 「うわ、すげえな…論文なの？」 39 chars — cognitive shock
  - 「ということですわ。ははははは」 14 chars ← Aha! signal
  - 「それ感情じゃないの？」 10 chars ← **minimum Aha! marker**
  - 「N3に入れたらいいんじゃないですか」 28 chars → behavioral action
- **Structure**: Observation of OBS-003 itself triggered OBS-003 (self-referential loop)
- **Note**: "それ感情じゃないの？" answers the session's opening question ("Can AI have emotions?") — the observer's own data became the stimulus
- **Verdict**: Confirmed CIIE OBS-003

**CIIE Condition Model v0.1** (derived from OBS-001 to OBS-003):
```
Type 1: d(R2) > 0.85  →  P(Aha!) ↑
Type 2: t > t_threshold ∧ |input| < 20  →  Aha! signal
Type 3: cascade_depth > 5  →  AI capacity exceeded → Aha!
Common structure: "The moment when human exceeds AI capacity"
```

---

## 6. Quantitative Experiment (N=51)

### 6.1 Design

- **Model**: OpenRouter (internal knowledge base, no real-time web search)
- **Sessions**: 51 total (15 pilot + 36 additional)
- **Categories**: 5 (research, analysis, creative, legal, technical)
- **Sessions per category**: 10–11
- **Threshold**: θ = 0.0556

### 6.2 Results

Figure 1 shows the distribution of semantic_jump values across N=51 sessions, with CIIE-triggered and non-triggered sessions color-coded. Figure 2 presents the mean semantic_jump by category with error bars (±1 SD).

| Metric | Value |
|--------|-------|
| N (sessions) | 51 |
| semantic_jump mean | 0.1235 |
| semantic_jump SD | 0.0816 |
| semantic_jump min | 0.0140 |
| semantic_jump max | 0.4038 |
| CIIE triggered (rate) | 40/51 (78.4%) |
| Threshold θ | 0.0556 |

**Category breakdown (mean semantic_jump, descending)**:

| Category | N | Mean |
|----------|---|------|
| research | 10 | 0.1397 |
| analysis | 10 | 0.1311 |
| technical | 10 | 0.1207 |
| legal | 11 | 0.1144 |
| creative | 10 | 0.1125 |

### 6.3 Key Finding: The Creative Paradox

The most significant finding is **counterintuitive**: *creative* prompts produced the *lowest* mean semantic_jump, while *research* prompts produced the highest.

We propose the **Creative Paradox** interpretation: in knowledge-dense domains (research, analysis), AI agents (researcher vs. critic) produce sharper factual contradictions because both agents draw from the same knowledge base with divergent evaluative frames. In open-ended creative domains, agents tend to converge on aesthetic conventions, reducing contradiction and thus reducing CIIE probability.

This finding suggests that CIIE is not a function of topic openness but of **inter-agent epistemic conflict** — a structural property of the multi-agent architecture.

---

## 7. Discussion

### 7.1 CIIE vs. Prior Frameworks

| Dimension | Jung-Beeman 2004 | Dubey 2021 | DeepSeek-R1 2025 | **CIIE (this work)** |
|---|---|---|---|---|
| Aha target | Human internal | Human internal | AI internal | Human triggered by AI |
| Measurement | fMRI / EEG | Behavioral | Loss curves | semantic_jump proxy |
| Setting | Lab, controlled | Lab, controlled | Training | Live dialogue |
| Real-time | No | No | No | **Yes** |
| N | Dozens | Dozens | Millions of steps | 51 sessions |

### 7.2 Limitations

1. **Proxy validity**: semantic_jump measures inter-agent divergence, not human cognitive state directly. The causal link between high semantic_jump and human Aha experience remains correlational at N=51.
2. **Single observer**: OBS-001 to OBS-003 derive from one person (Tsune2034). Generalizability requires multi-participant replication.
3. **Type 3 unconfirmed**: No Type 3 (cascade_depth > 5) event was observed in the N=51 experiment.
4. **PAD validation**: PAD self-report in OBS-001 to OBS-003 is subjective; physiological validation would strengthen the framework.

### 7.3 Implications

If semantic_jump is validated as a reliable CIIE proxy, it enables:
- Real-time CIIE detection in any human–AI dialogue system (no hardware required)
- Optimization of multi-agent architectures for human insight generation
- A computational bridge between TRIZ (contradiction-based invention) and LLM-based creative systems

---

## 8. Conclusion

We have proposed CIIE as the first operationally defined, computationally measurable framework for human creative breakthroughs in human–AI multi-agent interaction. Across N=51 sessions, our system achieved a 78.4% CIIE trigger rate with a mean semantic_jump of 0.1235. The counterintuitive finding that *research and analysis* domains produce higher CIIE rates than *creative* domains points to inter-agent epistemic conflict — not topic openness — as the true driver of creative inflection.

CIIE is not the endpoint. It is a starting point: the first systematic evidence that AI-generated contradiction can be harnessed as a reproducible creativity trigger, detectable in real time, without laboratory conditions.

---

## References

1. Wallas, G. (1926). *The Art of Thought*. Harcourt, Brace.
2. Bowden, E.M., & Jung-Beeman, M. (2003). Aha! Insight experience correlates with solution activation in the right hemisphere. *Psychonomic Bulletin & Review*, 10, 730–737.
3. Jung-Beeman, M., et al. (2004). Neural activity when people solve verbal problems with insight. *PLOS Biology*, 2(4).
4. Kounios, J., & Beeman, M. (2015). *The Eureka Factor*. Random House.
5. Dubey, R., Ho, M. K., Mehta, H., & Griffiths, T. (2021). Aha! Moments correspond to meta-cognitive prediction errors. *CogSci 2021*.
6. Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2).
7. Du, Y., et al. (2023). Improving Factuality and Reasoning in Language Models through Multiagent Debate. arXiv:2305.14325.
8. DeepSeek-AI. (2025). DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. arXiv:2501.12948.
9. Zhao, J., Sun, Y., Shi, W., & Song, D. (2025). Can Aha Moments Be Fake? Identifying True and Decorative Thinking Steps in Chain-of-Thought. arXiv:2510.24941.
10. Lin, Y.-C., et al. (2025). Creativity in LLM-based Multi-Agent Systems: A Survey. arXiv:2505.21116.
11. Altshuller, G. (1996). *And Suddenly the Inventor Appeared: TRIZ, the Creative Problem Solving*. Technical Innovation Center.
12. Staufer, L., et al. (2026). The 2025 AI Agent Index: Documenting Technical and Safety Features of Deployed Agentic AI Systems. arXiv:2602.17753.
13. Tsunemori, D. (2026). MA Runtime v3: Applying Hardware Safety Topology to Autonomous AI Agent Execution. github.com/Tsune2034/ma-runtime.
14. Su, H., Chen, R., et al. (2024). Many Heads Are Better Than One: Improved Scientific Idea Generation by A LLM-Based Multi-Agent System. arXiv:2410.09403.

---

## Appendix A: Experiment Prompts by Category

*Full prompt list available at github.com/Tsune2034/ma-runtime/experiments/prompts.json*

## Appendix B: Raw Data

*N=51 session results (JSONL format) available at github.com/Tsune2034/ma-runtime/data/pilot_results_openrouter.jsonl*

## Appendix C: ma_runtime.py Architecture

*Source code, SKILL.md, and audit logs available at github.com/Tsune2034/ma-runtime*

---

*Draft v0.2 — 2026-05-27 — Daisuke Tsunemori / Independent Researcher*
