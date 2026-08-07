# 11_hypotheses.md — Testable Hypotheses Registry

**Phase:** Hypotheses Registry  
**Status:** Active  
**Based on:** 01–08

---

## Purpose

Единый реестр **проверяемых гипотез** для MRI.  
Каждая гипотеза должна быть: конкретной, измеримой, ограниченной во времени.

---

## Hypothesis Template

```markdown
## H-XXX: Title

**Statement:** [One sentence, testable claim]

**Status:** [ ] Not Tested | [ ] In Progress | [ ] Confirmed | [ ] Rejected | [ ] Inconclusive

**Priority:** P0 / P1 / P2

**Source:** [Problem ID / Observation / Literature]

**Variables:**
- Independent: [What we change]
- Dependent: [What we measure]
- Controls: [What we hold constant]

**Method:** [Experiment type: A/B, Ablation, Grid Search, Observational]

**Sample Size:** [N, power analysis]

**Success Criteria:**
- Primary metric: [metric, threshold, direction]
- Statistical: [p < 0.05, effect size > X%, CI]

**Timeline:** [Start date] → [End date]

**Owner:** [Name]

**Dependencies:** [Prerequisites: Memory Trace, Metrics, etc.]

**Status Log:**
- YYYY-MM-DD: Created
- YYYY-MM-DD: Experiment started
- YYYY-MM-DD: Result recorded
```

---

## Active Hypotheses

---

### H-001: Episode Memory Underutilization
**Statement:** Episode Memory перечитывается менее чем в 3% запросов, несмотря на хранение всех диалогов.

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 01_inventory (Episodic used by 2 phases only)

**Variables:**
- Independent: —
- Dependent: `episodic_read_rate` = `episodic_reads / pipeline_turns`
- Controls: Same traffic, same model

**Method:** Observational (Memory Trace analysis)

**Sample:** 10,000 turns

**Success Criteria:**
- Primary: `episodic_read_rate < 0.03` confirmed
- p < 0.01, effect size > 0.8

**Timeline:** Week 1 (after Trace ready)

**Owner:** Research Stream

**Dependencies:** Memory Trace (Phase 6) ready

**Status Log:**
- 2026-07-31: Created

---

### H-002: Semantic vs Episodic Usage Gap
**Statement:** Semantic Memory используется значительно чаще Episodic (коэффициент > 10x).

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 04_flow_mapping (SemanticPhase every turn, Episodic rarely)

**Variables:**
- Independent: —
- Dependent: `semantic_reads / episodic_reads` ratio
- Controls: Same traffic period

**Method:** Observational (Memory Trace)

**Sample:** 10,000 turns

**Success Criteria:**
- Ratio > 10 confirmed
- p < 0.001

**Timeline:** Week 1 (after Trace ready)

**Owner:** Research Stream

---

### H-003: Emotion Dominance
**Statement:** Emotion влияет на качество генерации сильнее, чем Memory (Episodic/Semantic).

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 04_flow_mapping (EmotionPhase reads every turn, Memory phases less)

**Variables:**
- Independent: Emotion ablation (ON/OFF) vs Memory ablation (ON/OFF)
- Dependent: Generation quality (LLM judge: coherence, empathy, tone)
- Controls: Same prompts, same model, same context

**Method:** Ablation A/B (3 arms: Control, No Emotion, No Memory)

**Sample:** 300 turns per arm (100 each)

**Success Criteria:**
- Emotion ablation quality drop > Memory ablation drop
- p < 0.05, effect size > 0.5

**Timeline:** Week 2 (after Trace + ablation flags ready)

**Owner:** Research Stream

**Dependencies:** Ablation flags in PipelineExecutor

---

### H-004: Dead Memory Accumulation
**Statement:** > 80% записей в Episodic/Semantic Memory никогда не читаются после создания.

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 01_inventory (no TTL, no access tracking)

**Variables:**
- Independent: —
- Dependent: `never_read_ratio = never_read / total_created`
- Controls: Same time window

**Method:** Observational (Memory Trace + creation timestamps)

**Sample:** All records older than 7 days

**Success Criteria:**
- `never_read_ratio > 0.8` confirmed
- p < 0.001

**Timeline:** Week 1 (after Trace ready)

**Owner:** Research Stream

---

### H-005: Episode Memory Irrelevance
**Statement:** Отключение Episode Memory не снижает качество генерации более чем на 1%.

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** H-001 (low read rate) + 04_flow_mapping (used by 2 phases only)

**Variables:**
- Independent: Episode Memory (ON/OFF via Consolidation + SaveEpisode flags)
- Dependent: Generation quality (LLM judge), Latency, Recall (probe questions)
- Controls: Same prompts, same users, same model

**Method:** A/B Test (Control: Episode ON, Treatment: Episode OFF)

**Sample:** 1000 turns per arm

**Success Criteria:**
- Quality delta < 1% (p > 0.05)
- p > 0.05 for quality difference

**Timeline:** Week 3 (after ablation flags ready)

**Owner:** Research Stream

**Dependencies:** Episode Memory toggle in Pipeline

---

### H-006: Consolidation Irrelevance
**Statement:** Отключение Consolidation не ухудшает качество генерации.

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 04_flow_mapping (Consolidation only in background, 2 phases use results)

**Variables:**
- Independent: Consolidation (ON/OFF via `CONSOLIDATION_INTERVAL=0`)
- Dependent: Generation quality, Recall of consolidated facts (probe questions)
- Controls: Same traffic, same model

**Method:** A/B Test (Control: ON, Treatment: OFF)

**Sample:** 1000 turns per arm

**Success Criteria:**
- Quality delta < 1% (p > 0.05)
- No significant recall degradation on consolidated facts

**Timeline:** Week 3

**Owner:** Research Stream

---

### H-007: Emotion Decay Optimum
**Statement:** Существует оптимальный decay rate для Emotion, отличный от текущего 0.001/sec, который улучшает appropriateness score.

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 01_inventory (decay rate hardcoded, never tuned)

**Variables:**
- Independent: `decay_rate` ∈ {0.0001, 0.0003, 0.0005, 0.001, 0.002, 0.005, 0.01} per sec
- Dependent: Emotion appropriateness (LLM judge 1-10)
- Controls: Same prompts, same users, same contexts

**Method:** Grid Search (7 rates × 50 turns each = 350 turns)

**Success Criteria:**
- Found rate with significantly better appropriateness (p < 0.05 vs 0.001)
- Effect size > 0.3

**Timeline:** Week 2-3

**Owner:** Research Stream

---

### H-008: Session Isolation Violation
**Statement:** В текущей архитектуре происходит cross-session leakage эмоций/импульсов/RAG.

**Status:** [ ] Not Tested  
**Priority:** P0  
**Source:** 08_problem_analysis (P0-01, P0-02, P0-03)

**Variables:**
- Independent: 50 concurrent users, 10 turns each
- Dependent: Cross-session reads/writes in Emotion, Impulse, RAG, Semantic, Persona
- Controls: Isolated sessions via API

**Method:** Load test (50 concurrent users × 10 turns)

**Success Criteria:**
- Cross-session read/write events = 0
- p < 0.001 (zero expected)

**Timeline:** Week 2

**Owner:** Engineering Stream

---

### H-009: Semantic Memory Underutilization
**Statement:** > 80% фактов в Semantic Memory никогда не используются в RAG/SemanticPhase.

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 01_inventory (Semantic: 2 readers, 1 writer)

**Variables:**
- Independent: —
- Dependent: `unused_fact_ratio = never_read_facts / total_facts`
- Controls: Facts older than 7 days

**Method:** Observational (Trace + Semantic storage scan)

**Sample:** Facts older than 7 days

**Success Criteria:**
- `unused_fact_ratio > 0.8` confirmed

---

### H-010: Memory Churn Rate
**Statement:** Memory churn (create + delete rate) > 10% в день, указывая на нестабильность.

**Status:** [ ] Not Tested  
**Priority:** P2

**Variables:**
- Independent: —
- Dependent: `(writes + deletes) / total_items` per day
- Controls: Stable traffic period

**Method:** Observational (Trace + storage metrics)

**Sample:** 7 days production

---

### H-011: Impulse Stack Unbounded
**Statement:** ImpulseCore stack растет неограниченно, памяти достаточно на 30 дней активной работы.

**Status:** [ ] Not Tested  
**Priority:** P2  
**Source:** 01_inventory (no max stack size)

**Variables:**
- Independent: Time (days of uptime)
- Dependent: `stack_depth_max`, `stack_depth_avg`
- Controls: Normal traffic

**Method:** Observational (ImpulseCore state monitoring)

**Sample:** 30 days uptime

---

### H-012: Consolidation Lag
**Statement:** Consolidation lag > 20 turns (факты появляются в Semantic с задержкой 20+ диалогов).

**Status:** [ ] Not Tested  
**Priority:** P1  
**Source:** 04_flow_mapping (Consolidation every 10 dialogs, async)

**Variables:**
- Independent: —
- Dependent: `consolidation_lag_turns = turn_consolidated - turn_created`
- Controls: Active sessions only

**Method:** Observational (Consolidation logs + Episode timestamps)

**Sample:** 1000 consolidated episodes

---

## Hypothesis Status Dashboard

| ID | Statement | Status | Priority | Phase | Owner |
|----|-----------|--------|----------|-------|-------|
| H-001 | Episode underutilized | [ ] Not Tested | P1 | Phase 3 | Research |
| H-002 | Semantic > Episodic usage | [ ] Not Tested | P1 | Phase 3 | Research |
| H-003 | Emotion > Memory impact | [ ] Not Tested | P1 | Phase 3 | Research |
| H-004 | Dead memory > 80% | [ ] Not Tested | P1 | Phase 3 | Research |
| H-005 | Episode ablation < 1% | [ ] Not Tested | P1 | Phase 3 | Research |
| H-006 | Consolidation irrelevant | [ ] Not Tested | P1 | Phase 3 | Research |
| H-007 | Emotion decay optimum | [ ] Not Tested | P1 | Phase 2 | Research |
| H-008 | Session isolation broken | [ ] Not Tested | P0 | Phase 2 | Engineering |
| H-009 | Semantic dead memory > 80% | [ ] Not Tested | P1 | Phase 3 | Research |
| H-010 | Churn > 10%/day | [ ] Not Tested | P2 | Phase 3 | Research |
| H-011 | Impulse stack unbounded | [ ] Not Tested | P2 | Phase 3 | Research |
| H-012 | Consolidation lag > 20 | [ ] Not Tested | P1 | Phase 3 | Research |

---

## Hypothesis Lifecycle

| Stage | Criteria |
|-------|----------|
| **Created** | Hypothesis written, template filled, owner assigned |
| **Designed** | Experiment designed, sample size calc, metrics defined |
| **Running** | Experiment launched, data collection active |
| **Analyzed** | Data collected, statistical analysis complete |
| **Resolved** | Confirmed / Rejected / Inconclusive with evidence |
| **Archived** | Decision recorded, lessons learned documented |

---

## Statistical Standards

| Standard | Requirement |
|--------|-------------|
| Significance | p < 0.05 (Bonferroni corrected for multiple comparisons) |
| Power | ≥ 80% (1 - β ≥ 0.8) |
| Effect Size | Cohen's d ≥ 0.5 (medium) for primary outcomes |
| Confidence | 95% CI reported |
| Multiple Comparisons | Bonferroni / Benjamini-Hochberg correction |

---

## Hypothesis Lifecycle Log

| Date | Hypothesis | Event | Notes |
|------|------------|-------|-------|
| 2026-07-31 | H-001..H-012 | Created | Initial registry from MRI analysis |
| | | | |

---

*All hypotheses must die by data. If not testable — reformulate or discard.*