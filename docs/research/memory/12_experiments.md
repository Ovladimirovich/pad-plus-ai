# 12_experiments.md — Memory Research Experiments

**Phase:** 12 — Experiments  
**Status:** Draft  
**Based on:** 11_hypotheses.md

---

## Purpose

Журнал экспериментов для валидации гипотез (11_hypotheses.md).

> **Правило:** Никакое изменение архитектуры не вливается в main без подтверждающего эксперимента.

---

## Experiment Template

```markdown
## Experiment XXX: Short Title

### Hypothesis Tested
H-XXX

### Objective
What we're trying to learn.

### Design
- **Type:** Ablation / A/B / Grid Search / Correlation / Load Test
- **Duration:** X days / N turns
- **Sample Size:** N users / N sessions / N turns
- **Control Group:** Description
- **Treatment Group:** Description

### Metrics
- Primary: ...
- Secondary: ...

### Implementation
- Code changes needed
- Config changes
- Rollback plan

### Results
- Raw data summary
- Statistical significance
- Effect size

### Conclusion
[ ] Confirmed  [ ] Rejected  [ ] Inconclusive

### Next Steps
What to do based on result.
```

---

## Experiment Catalog

### Exp-001: Memory Usage Profile
**Hypotheses Tested:** H-001, H-002, H-004, H-009, H-010, H-011, H-012  
**Type:** Observational / Profiling  
**Duration:** 7 days production traffic (or 10k synthetic turns)  
**Status:** [ ] Not Started

**Design:**
- Enable full Memory Trace for 100% of turns
- Collect all MemoryEvents for 7 days
- Analyze: read/write ratios, dead memory, churn, re-read rates

**Metrics to Collect:**
- Per-component: reads, writes, deletes, latency
- Per-object: read count after write, time to first read, lifetime
- Cross-component: read/write ratios, dead object ratio

**Deliverables:**
- `exp001_memory_profile_report.md`
- `exp001_raw_data.parquet`
- Updated hypotheses status (H-001, H-002, H-004, H-009, H-010, H-011, H-012)

---

### Exp-002: Session State vs Working Memory
**Hypothesis Tested:** H-005 (Session Memory replaces Working Memory)  
**Type:** Ablation Study  
**Duration:** 3 days / 500 turns  
**Status:** [ ] Not Started

**Design:**
- **Control:** Full Pipeline (Working Memory + Session State)
- **Treatment:** Pipeline с отключенным Working Memory (PipelineContext), только Session State (Emotion, Impulse, UserPersona)
- **Sample:** 250 turns control / 250 turns treatment

**Metrics:**
- Generation quality (LLM judge / human eval)
- Latency
- Context relevance (manual annotation)
- Prompt size (tokens)

**Implementation:**
```python
# Pipeline flag: --no-working-memory
# In PipelineExecutor: skip context population, use only session stores
```

**Success Criteria:** Quality delta < 5%, latency improvement > 10%.

---

### Exp-003: Emotion Ablation
**Hypothesis Tested:** H-003 (Emotion dominance)  
**Type:** Ablation Study  
**Duration:** 3 days / 300 turns  
**Status:** [ ] Not Started

**Design:**
- **Control:** Full Pipeline
- **Treatment A:** EmotionPhase disabled (no emotion_style in prompt)
- **Treatment B:** EmotionUpdatePhase disabled (no emotion learning)
- **Sample:** 100 turns each

**Metrics:**
- Generation quality (LLM judge: coherence, empathy, tone)
- User satisfaction (if real users) / Self-eval
- Emotion appropriateness (manual annotation)

**Implementation:**
```python
# Pipeline flags: --no-emotion-phase, --no-emotion-update
```

**Success Criteria:** Emotion ablation quality drop > Memory ablation drop (p < 0.05).

---

### Exp-004: Consolidation Impact
**Hypothesis Tested:** H-006 (Consolidation irrelevance)  
**Type:** A/B Test  
**Duration:** 7 days / 2000 turns  
**Status:** [ ] Not Started

**Design:**
- **Control:** Consolidation ON (default)
- **Treatment:** Consolidation OFF (disable ControlTick consolidation)
- **Sample:** 1000 turns each

**Metrics:**
- Generation quality (primary)
- Recall of consolidated facts (probe questions)
- Latency (consolidation overhead)

**Implementation:**
```python
# Config: CONSOLIDATION_INTERVAL=0 (disable)
# Or: MemoryConsolidator.enabled = False
```

**Success Criteria:** Quality delta < 1% (statistically insignificant).

---

### Exp-005: Emotion Decay Grid Search
**Hypothesis Tested:** H-007 (Emotion decay optimal rate)  
**Type:** Grid Search / Bayesian Optimization  
**Duration:** 5 days / 500 turns per config  
**Status:** [ ] Not Started

**Design:**
- Test decay rates: [0.0001, 0.0003, 0.0005, 0.001, 0.002, 0.005, 0.01] per sec
- 50 turns per rate (randomized order)
- Metric: Emotion appropriateness score (LLM judge)

**Parameters:**
```python
DECAY_RATES = [0.0001, 0.0003, 0.0005, 0.001, 0.002, 0.005, 0.01]  # per second
TURNS_PER_RATE = 50
JUDGE_PROMPT = "Rate emotion appropriateness 1-10"
```

**Success Criteria:** Found rate with significantly better appropriateness (p < 0.05 vs default 0.001).

---

### Exp-005: Emotion Decay Grid Search
**Hypothesis Tested:** H-007 (Emotion decay optimal rate)  
**Type:** Grid Search / Bayesian Optimization  
**Duration:** 5 days / 50 turns per config  
**Status:** [ ] Not Started

**Design:**
- Test decay rates: [0.0001, 0.0003, 0.0005, 0.001, 0.002, 0.005, 0.01] per sec
- 50 turns per rate (randomized order)
- Metric: Emotion appropriateness score (LLM judge)

**Parameters:**
```python
DECAY_RATES = [0.0001, 0.0003, 0.0005, 0.001, 0.002, 0.005, 0.01]  # per second
TURNS_PER_RATE = 50
JUDGE_PROMPT = "Rate emotion appropriateness 1-10"
```

**Success Criteria:** Found rate with significantly better quality (p < 0.05 vs default 0.001).

---

### Exp-006: Session Isolation Stress Test
**Hypothesis Tested:** H-008 (Session isolation violation)  
**Type:** Load Test / Chaos Engineering  
**Duration:** 1 day / 50 concurrent users  
**Status:** [ ] Not Started

**Design:**
- Simulate 50 concurrent users via API
- Each user: 10 sequential turns
- Monitor: Cross-session reads/writes in Emotion, Impulse, RAG, Semantic, Persona

**Metrics:**
- Cross-session read events (should be 0)
- Cross-session write events (should be 0)
- Latency under load
- Error rate

**Implementation:**
```python
# Locust script or custom asyncio load generator
# 50 concurrent async sessions
# Each: 10 turns with 1s delay
# Monitor: core.monitoring.get_monitoring_system().metrics_history
```

**Success Criteria:** Zero cross-session leakage events.

---

### Exp-007: Semantic Deduplication Impact
**Hypothesis:** Semantic deduplication reduces storage by >20% without quality loss  
**Type:** A/B Test  
**Duration:** 5 days  
**Status:** [ ] Not Started

**Design:**
- **Control:** Current SemanticMemory (no dedup)
- **Treatment:** Enable dedup on add_fact (cosine similarity > 0.95)
- **Sample:** 5000 facts each

**Metrics:**
- Storage reduction (%)
- Fact retrieval quality (precision/recall)
- Generation quality delta

**Implementation:**
```python
# In SemanticMemory.add_fact()
if config.dedup_enabled:
    similar = self.search(query=fact.content, top_k=1, threshold=0.95)
    if similar:
        # Merge or skip
        return similar[0].id
```

---

### Exp-008: Unified Forgetting Framework
**Hypothesis:** Unified TTL + Importance scoring reduces memory size by 50% without quality loss  
**Type:** A/B Test  
**Duration:** 7 days  
**Status:** [ ] Not Started

**Design:**
- **Control:** Current (no forgetting except Emotion)
- **Treatment:** Unified forgetting framework enabled for all components
- **Sample:** Full production traffic

**Metrics:**
- Memory size reduction
- Generation quality
- Latency
- Eviction rate

---

### Exp-009: Importance Scoring Calibration
**Hypothesis:** Learned importance scoring outperforms fixed importance  
**Type:** A/B / Bandit  
**Duration:** 14 days  
**Status:** [ ] Not Started

**Design:**
- **Control:** Fixed importance (1.0 for all new items)
- **Treatment:** Learned importance (based on access frequency, recency, user feedback)
- **Sample:** 50/50 split

**Metrics:**
- Dead memory ratio reduction
- Hit rate improvement
- Storage savings

---

## Experiment Tracking

| Exp | Hypotheses | Type | Status | Start | End | Result |
|-----|------------|------|--------|-------|-----|--------|
| Exp-001 | H-001,002,004,009,010,011,012 | Profiling | [ ] Not Started | | | |
| Exp-002 | H-005 | Ablation | [ ] Not Started | | | |
| Exp-003 | H-003 | Ablation | [ ] Not Started | | | |
| Exp-004 | H-006 | A/B | [ ] Not Started | | | |
| Exp-005 | H-007 | Grid Search | [ ] Not Started | | | |
| Exp-006 | H-008 | Load Test | [ ] Not Started | | | |
| Exp-007 | P2-02 | A/B | [ ] Not Started | | | |
| Exp-008 | P1-01 | A/B | [ ] Not Started | | | |
| Exp-009 | P2-01 | Bandit | [ ] Not Started | | | |

---

## Experiment Governance

| Role | Responsibility |
|------|----------------|
| **Experiment Owner** | Design, execution, analysis |
| **Data Engineer** | Data collection, pipeline |
| **Statistician** | Significance testing, power analysis |
| **Engineering Lead** | Implementation, rollback |
| **Product Owner** | Priority, acceptance criteria |

### Review Gates

| Gate | Criteria |
|------|----------|
| **Design Review** | Hypothesis clear, metrics defined, sample size calculated |
| **Pre-Launch** | Code reviewed, rollback tested, monitoring active |
| **Mid-Course** | No safety issues, data quality OK |
| **Post-Experiment** | Statistical significance, effect size, CI reported |
| **Decision** | Ship / Iterate / Kill |

---

## Data Management

| Artifact | Location | Retention |
|----------|----------|-----------|
| Raw MemoryEvents | `s3://padplus-research/memory_events/` | 90 days |
| Experiment Data | `s3://padplus-research/experiments/exp-XXX/` | 1 year |
| Reports | `docs/research/memory/experiments/` | Permanent |
| Analysis Notebooks | `notebooks/experiments/` | Permanent |

---

## Reporting Template

```markdown
# Experiment XXX Report

## Summary
- Hypothesis: H-XXX
- Result: [Confirmed / Rejected / Inconclusive]
- Effect Size: X%
- P-value: Y
- Confidence: Z%

## Methodology
- Design: ...
- Sample: N = ...
- Duration: ...

## Results
- Primary Metric: ...
- Secondary Metrics: ...

## Statistical Analysis
- Test used: ...
- P-value: ...
- Confidence Interval: ...

## Interpretation
What this means for architecture.

## Recommendations
- [ ] Ship
- [ ] Iterate
- [ ] Kill

## Artifacts
- Raw data: s3://...
- Notebook: notebooks/experiments/exp-XXX.ipynb
- Dashboard: grafana/memory-exp-XXX
```

---

*Experiments are the engine of MRI. Each experiment teaches us what memory actually does.*