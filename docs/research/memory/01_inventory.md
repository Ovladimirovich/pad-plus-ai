# 01_inventory.md — Memory Inventory (Auto-Generated)

**Generated:** 2026-07-31T02:50:00.887089
**Scanner version:** 1.0
**Components found:** 50

---

## AuthManager

**File:** `core\auth_manager.py`
**Class:** `AuthManager`

### Owner
AuthManager

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## CacheManager

**File:** `core\cache_manager.py`
**Class:** `CacheManager`

### Owner
CacheManager

### Storage
Redis

### TTL / Eviction
Has TTL/eviction logic

**Session Scoped:** NO
**Session Isolation:** NO


---

## CognitiveStateManager

**File:** `core\xray\cognitive_state.py`
**Class:** `CognitiveStateManager`

### Owner
CognitiveStateManager

### Writers
- complete_state

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## ConfigManager

**File:** `core\config_manager.py`
**Class:** `ConfigManager`

### Owner
ConfigManager

### Readers
- _load_from_file

### Storage
SQLite, JSON file, PostgreSQL/pgvector

### Consolidation
Participates in consolidation

**Session Scoped:** NO
**Session Isolation:** NO


---

## ConnectionManager

**File:** `main_stable.py`
**Class:** `ConnectionManager`

### Owner
ConnectionManager

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## CrossMemorySync

**File:** `core\pipeline\cross_memory_sync.py`
**Class:** `CrossMemorySync`

### Owner
CrossMemorySync

### Readers
- sync_rag_to_semantic

### Storage
RAM

**Session Scoped:** YES
**Session Isolation:** NO


---

## DataCollector

**File:** `learning\collector.py`
**Class:** `DataCollector`

### Owner
DataCollector

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## DataManager

**File:** `core\data_manager.py`
**Class:** `DataManager`

### Owner
DataManager

### Readers
- _export_persona
- _export_emotion
- _export_roots
- _export_health
- _export_cache

### Storage
SQLite

**Session Scoped:** NO
**Session Isolation:** NO


---

## DecisionStore

**File:** `core\decisions\store.py`
**Class:** `DecisionStore`

### Owner
DecisionStore

### Storage
SQLite

**Session Scoped:** YES
**Session Isolation:** NO


---

## EpisodicMemory

**File:** `memory\episodic_postgres.py`
**Class:** `EpisodicMemory`

### Owner
EpisodicMemory

### Writers
- add_episode

### Storage
PostgreSQL/pgvector

**Session Scoped:** YES
**Session Isolation:** NO


---

## ExperiencePostgresStore

**File:** `core\experience\postgres_store.py`
**Class:** `ExperiencePostgresStore`

### Owner
ExperiencePostgresStore

### Storage
JSON file, PostgreSQL/pgvector

**Session Scoped:** NO
**Session Isolation:** NO


---

## ExperienceSQLiteStore

**File:** `core\experience\sqlite_store.py`
**Class:** `ExperienceSQLiteStore`

### Owner
ExperienceSQLiteStore

### Storage
SQLite, JSON file

**Session Scoped:** YES
**Session Isolation:** NO


---

## ExperienceStore

**File:** `core\experience\store.py`
**Class:** `ExperienceStore`

### Owner
ExperienceStore

### Readers
- get_stats

### Writers
- save

### Storage
SQLite

**Session Scoped:** YES
**Session Isolation:** NO


---

## GuardMemory

**File:** `core\guard\self_healing.py`
**Class:** `GuardMemory`

### Owner
GuardMemory

### Writers
- update

### Storage
SQLite, JSON file

**Session Scoped:** NO
**Session Isolation:** NO


---

## HealingChangesStore

**File:** `healing\changes_store.py`
**Class:** `HealingChangesStore`

### Owner
HealingChangesStore

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## ImpulseCore

**File:** `core\impulse\core.py`
**Class:** `ImpulseCore`

### Owner
ImpulseCore

### Writers
- pop

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## ImpulseManager

**File:** `core\impulse\manager.py`
**Class:** `ImpulseManager`

### Owner
ImpulseManager

### Readers
- start
- load

### Writers
- start

### Storage
JSON file

**Session Scoped:** NO
**Session Isolation:** NO


---

## InsightsEngine

**File:** `core\xray\insights.py`
**Class:** `InsightsEngine`

### Owner
InsightsEngine

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## MemoryConsolidator

**File:** `memory\consolidation.py`
**Class:** `MemoryConsolidator`

### Owner
MemoryConsolidator

### Readers
- consolidate_rag_to_semantic
- consolidate_semantic_to_roots

### Storage
RAM

### Consolidation
Participates in consolidation

**Session Scoped:** YES
**Session Isolation:** NO


---

## MemoryFusion

**File:** `memory\fusion.py`
**Class:** `MemoryFusion`

### Owner
MemoryFusion

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## MemoryHookManager

**File:** `core\pipeline\memory_hooks.py`
**Class:** `MemoryHookManager`

### Owner
MemoryHookManager

### Storage
RAM

### Consolidation
Participates in consolidation

**Session Scoped:** NO
**Session Isolation:** NO


---

## MemoryItem

**File:** `memory\hygiene.py`
**Class:** `MemoryItem`

### Owner
MemoryItem

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## MemoryMaintenancePhase

**File:** `core\pipeline\phases\memory_maintenance.py`
**Class:** `MemoryMaintenancePhase`

### Owner
MemoryMaintenancePhase

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## MemoryRecord

**File:** `memory\base.py`
**Class:** `MemoryRecord`

### Owner
MemoryRecord

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## MemoryStorageException

**File:** `core\exceptions.py`
**Class:** `MemoryStorageException`

### Owner
MemoryStorageException

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## MetricsCollector

**File:** `core\metrics_collector.py`
**Class:** `MetricsCollector`

### Owner
MetricsCollector

### Storage
RAM

**Session Scoped:** YES
**Session Isolation:** NO


---

## ModelRouter

**File:** `core\agi\model_router.py`
**Class:** `ModelRouter`

### Owner
ModelRouter

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## PADModel

**File:** `emotion\pad_model.py`
**Class:** `PADModel`

### Owner
PADModel

### Readers
- _load_or_create

### Storage
JSON file

### TTL / Eviction
Has TTL/eviction logic

**Session Scoped:** NO
**Session Isolation:** NO


---

## PersonaMemory

**File:** `memory\persona.py`
**Class:** `PersonaMemory`

### Owner
PersonaMemory

### Readers
- _load_or_init

### Writers
- evolve_from_dialog

### Storage
JSON file

**Session Scoped:** NO
**Session Isolation:** NO


---

## PipelineExecutor

**File:** `core\pipeline\executor.py`
**Class:** `PipelineExecutor`

### Owner
PipelineExecutor

### Writers
- _check_anti_loop

### Storage
RAM

### Consolidation
Participates in consolidation

**Session Scoped:** YES
**Session Isolation:** NO


---

## ProviderManager

**File:** `runtime\provider_manager.py`
**Class:** `ProviderManager`

### Owner
ProviderManager

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## RAGMemory

**File:** `memory\rag_postgres.py`
**Class:** `RAGMemory`

### Owner
RAGMemory

### Storage
PostgreSQL/pgvector

**Session Scoped:** YES
**Session Isolation:** NO


---

## ReflectionEngine

**File:** `core\evolution\reflection.py`
**Class:** `ReflectionEngine`

### Owner
ReflectionEngine

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## RemediationEngine

**File:** `healing\remediation.py`
**Class:** `RemediationEngine`

### Owner
RemediationEngine

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## RootsMemory

**File:** `memory\roots.py`
**Class:** `RootsMemory`

### Owner
RootsMemory

### Readers
- _load

### Storage
JSON file

**Session Scoped:** NO
**Session Isolation:** NO


---

## SemanticMemory

**File:** `memory\semantic_postgres.py`
**Class:** `SemanticMemory`

### Owner
SemanticMemory

### Storage
JSON file, PostgreSQL/pgvector

**Session Scoped:** NO
**Session Isolation:** NO


---

## SessionContext

**File:** `core\session_manager.py`
**Class:** `SessionContext`

### Owner
SessionContext

### Writers
- add_topic
- add_emotion

### Storage
JSON file

### TTL / Eviction
Has TTL/eviction logic

**Session Scoped:** YES
**Session Isolation:** YES


---

## SessionEmotionStore

**File:** `emotion\session_store.py`
**Class:** `SessionEmotionStore`

### Owner
SessionEmotionStore

### Readers
- get_all_states
- get_aggregate

### Writers
- save
- save_all
- remove
- _evict_expired
- _evict_lru

### Storage
RAM

### TTL / Eviction
Has TTL/eviction logic

**Session Scoped:** YES
**Session Isolation:** YES


---

## SessionImpulseStore

**File:** `core\impulse\session_store.py`
**Class:** `SessionImpulseStore`

### Owner
SessionImpulseStore

### Writers
- save
- save_all
- remove

### Storage
RAM

### TTL / Eviction
Has TTL/eviction logic

**Session Scoped:** YES
**Session Isolation:** YES


---

## SessionProviderManager

**File:** `runtime\session_provider_manager.py`
**Class:** `SessionProviderManager`

### Owner
SessionProviderManager

### Storage
RAM

**Session Scoped:** YES
**Session Isolation:** NO


---

## SpanContext

**File:** `core\xray\trace_context.py`
**Class:** `SpanContext`

### Owner
SpanContext

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## StyleManager

**File:** `core\style_manager.py`
**Class:** `StyleManager`

### Owner
StyleManager

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## SystemStateManager

**File:** `core\xray\system_state.py`
**Class:** `SystemStateManager`

### Owner
SystemStateManager

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## ToneEngine

**File:** `core\guard\tone_engine.py`
**Class:** `ToneEngine`

### Owner
ToneEngine

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## TraceCollector

**File:** `core\trace_collector.py`
**Class:** `TraceCollector`

### Owner
TraceCollector

### Storage
RAM

**Session Scoped:** YES
**Session Isolation:** NO


---

## TraceCollectorProtocol

**File:** `core\pipeline\base.py`
**Class:** `TraceCollectorProtocol`

### Owner
TraceCollectorProtocol

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## UserPersonaManager

**File:** `memory\user_persona.py`
**Class:** `UserPersonaManager`

### Owner
UserPersonaManager

### Readers
- _load

### Storage
JSON file

**Session Scoped:** YES
**Session Isolation:** NO


---

## UserPersonaPostgresManager

**File:** `memory\user_persona_postgres.py`
**Class:** `UserPersonaPostgresManager`

### Owner
UserPersonaPostgresManager

### Storage
RAM

**Session Scoped:** YES
**Session Isolation:** NO


---

## WebSocketManager

**File:** `core\websocket_manager.py`
**Class:** `WebSocketManager`

### Owner
WebSocketManager

### Storage
RAM

**Session Scoped:** NO
**Session Isolation:** NO


---

## XRayTraceCollector

**File:** `core\xray\trace_collector.py`
**Class:** `XRayTraceCollector`

### Owner
XRayTraceCollector

### Storage
RAM

### TTL / Eviction
Has TTL/eviction logic

**Session Scoped:** NO
**Session Isolation:** NO


---

## Summary Table

| Component | Owner | Session | TTL | Storage | Isolation |
|-----------|-------|---------|-----|---------|-----------|
| AuthManager | AuthManager | NO | NO | RAM | NO |
| CacheManager | CacheManager | NO | YES | Redis | NO |
| CognitiveStateManager | CognitiveStateManager | NO | NO | RAM | NO |
| ConfigManager | ConfigManager | NO | NO | SQLite, JSON file, PostgreSQL/pgvector | NO |
| ConnectionManager | ConnectionManager | NO | NO | RAM | NO |
| CrossMemorySync | CrossMemorySync | YES | NO | RAM | NO |
| DataCollector | DataCollector | NO | NO | RAM | NO |
| DataManager | DataManager | NO | NO | SQLite | NO |
| DecisionStore | DecisionStore | YES | NO | SQLite | NO |
| EpisodicMemory | EpisodicMemory | YES | NO | PostgreSQL/pgvector | NO |
| ExperiencePostgresStore | ExperiencePostgresStore | NO | NO | JSON file, PostgreSQL/pgvector | NO |
| ExperienceSQLiteStore | ExperienceSQLiteStore | YES | NO | SQLite, JSON file | NO |
| ExperienceStore | ExperienceStore | YES | NO | SQLite | NO |
| GuardMemory | GuardMemory | NO | NO | SQLite, JSON file | NO |
| HealingChangesStore | HealingChangesStore | NO | NO | RAM | NO |
| ImpulseCore | ImpulseCore | NO | NO | RAM | NO |
| ImpulseManager | ImpulseManager | NO | NO | JSON file | NO |
| InsightsEngine | InsightsEngine | NO | NO | RAM | NO |
| MemoryConsolidator | MemoryConsolidator | YES | NO | RAM | NO |
| MemoryFusion | MemoryFusion | NO | NO | RAM | NO |
| MemoryHookManager | MemoryHookManager | NO | NO | RAM | NO |
| MemoryItem | MemoryItem | NO | NO | RAM | NO |
| MemoryMaintenancePhase | MemoryMaintenancePhase | NO | NO | RAM | NO |
| MemoryRecord | MemoryRecord | NO | NO | RAM | NO |
| MemoryStorageException | MemoryStorageException | NO | NO | RAM | NO |
| MetricsCollector | MetricsCollector | YES | NO | RAM | NO |
| ModelRouter | ModelRouter | NO | NO | RAM | NO |
| PADModel | PADModel | NO | YES | JSON file | NO |
| PersonaMemory | PersonaMemory | NO | NO | JSON file | NO |
| PipelineExecutor | PipelineExecutor | YES | NO | RAM | NO |
| ProviderManager | ProviderManager | NO | NO | RAM | NO |
| RAGMemory | RAGMemory | YES | NO | PostgreSQL/pgvector | NO |
| ReflectionEngine | ReflectionEngine | NO | NO | RAM | NO |
| RemediationEngine | RemediationEngine | NO | NO | RAM | NO |
| RootsMemory | RootsMemory | NO | NO | JSON file | NO |
| SemanticMemory | SemanticMemory | NO | NO | JSON file, PostgreSQL/pgvector | NO |
| SessionContext | SessionContext | YES | YES | JSON file | YES |
| SessionEmotionStore | SessionEmotionStore | YES | YES | RAM | YES |
| SessionImpulseStore | SessionImpulseStore | YES | YES | RAM | YES |
| SessionProviderManager | SessionProviderManager | YES | NO | RAM | NO |
| SpanContext | SpanContext | NO | NO | RAM | NO |
| StyleManager | StyleManager | NO | NO | RAM | NO |
| SystemStateManager | SystemStateManager | NO | NO | RAM | NO |
| ToneEngine | ToneEngine | NO | NO | RAM | NO |
| TraceCollector | TraceCollector | YES | NO | RAM | NO |
| TraceCollectorProtocol | TraceCollectorProtocol | NO | NO | RAM | NO |
| UserPersonaManager | UserPersonaManager | YES | NO | JSON file | NO |
| UserPersonaPostgresManager | UserPersonaPostgresManager | YES | NO | RAM | NO |
| WebSocketManager | WebSocketManager | NO | NO | RAM | NO |
| XRayTraceCollector | XRayTraceCollector | NO | YES | RAM | NO |