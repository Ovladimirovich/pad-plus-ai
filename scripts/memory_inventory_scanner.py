#!/usr/bin/env python3
"""
Memory Inventory Auto-Scanner
Парсит backend/ и извлекает информацию о компонентах памяти для 01_inventory.md
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MemoryComponent:
    name: str
    file_path: str
    class_name: str = ""
    purpose: str = ""
    owner: str = ""
    readers: List[str] = field(default_factory=list)
    writers: List[str] = field(default_factory=list)
    storage: str = ""
    lifetime: str = ""
    session_scoped: bool = False
    operations: List[str] = field(default_factory=list)
    storage_schema: str = ""
    ttl_eviction: str = ""
    consolidation: str = ""
    session_isolation: bool = False
    purpose: str = ""
    problems: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    readers_detail: List[str] = field(default_factory=list)
    writers_detail: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

class InventoryScanner:
    def __init__(self, backend_root: Path):
        self.backend_root = Path(backend_root)
        self.components: Dict[str, MemoryComponent] = {}
        self.known_components = {
            'EpisodicMemory': 'memory/episodic.py',
            'SemanticMemory': 'memory/semantic.py', 
            'RAGMemory': 'memory/rag.py',
            'RAGMemoryPostgres': 'memory/rag_postgres.py',
            'RootsMemory': 'memory/roots.py',
            'PersonaMemory': 'memory/persona.py',
            'UserPersona': 'memory/user_persona.py',
            'UserPersonaManager': 'memory/user_persona.py',
            'SessionEmotionStore': 'emotion/session_store.py',
            'PADModel': 'emotion/pad_model.py',
            'ImpulseCore': 'core/impulse/core.py',
            'ImpulseManager': 'core/impulse/manager.py',
            'SessionImpulseStore': 'core/impulse/session_store.py',
            'SessionManager': 'core/session_manager.py',
            'MemoryConsolidator': 'memory/consolidation.py',
            'TraceCollector': 'core/xray/trace_collector.py',
            'PipelineExecutor': 'core/pipeline/executor.py',
            'PipelineContext': 'core/pipeline/context.py',
            'MemoryConsolidator': 'memory/consolidation.py',
        }
        
        # Patterns for detecting readers/writers
        self.read_patterns = [
            r'\.get_recent\(',
            r'\.get_all\(',
            '\.get_all_facts\(',
            '\.find_applicable_procedure\(',
            '\.search\(',
            '\.get_state\(',
            '\.get_persona_context',
            '\.get_roots_context',
            '\.get_rag_context',
            '\.get_episodic_context',
            '\.get_persona_context',
            '\.get_topic_stats',
            '\.get_stats\(',
            '\.get_all\(',
            '\.load\(',
        ]
        self.write_patterns = [
            r'\.add_episode\(',
            '\.add_fact\(',
            '\.add_procedure\(',
            '\.add_root\(',
            '\.apply_event\(',
            '\.apply_deltas\(',
            '\.record_fusion\(',
            '\.save\(',
            '\.save_persona\(',
            '\.adjust_style\(',
            '\.adjust_trait\(',
            '\.evolve_from_dialog',
            '\.record_interaction',
            '\.push\(',
            '\.pop\(',
            '\.create_session\(',
            '\.end_session\(',
        ]
        self.session_patterns = [
            r'session_id',
            r'user_id',
        ]

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Сканирует один Python файл и извлекает информацию о компонентах памяти"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return {'error': str(e)}
        
        result = {
            'classes': [],
            'imports': [],
            'reads': [],
            'writes': [],
            'session_refs': [],
            'methods': [],
        }
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return result
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        result['imports'].append(f"{node.module}.{alias.name}")
            
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'methods': [],
                    'bases': [base.id for base in node.bases if isinstance(base, ast.Name)],
                    'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                }
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = item.name
                        class_info['methods'].append(method_name)
                        
                        # Check for read/write patterns in method body
                        method_source = ast.get_source_segment(content, item)
                        if method_source:
                            for pattern in self.read_patterns:
                                if re.search(pattern, method_source):
                                    result['reads'].append(f"{node.name}.{method_name}")
                            for pattern in self.write_patterns:
                                if re.search(pattern, method_source):
                                    result['writes'].append(f"{node.name}.{method_name}")
                            for pattern in self.session_patterns:
                                if re.search(pattern, method_source):
                                    result['session_refs'].append(f"{node.name}.{method_name}")
                        
                        result['classes'].append(class_info)
                
                if isinstance(node, ast.FunctionDef) and not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(node) if isinstance(parent, ast.ClassDef)):
                    result['methods'].append(node.name)
        
        return result

    def scan_backend(self) -> Dict[str, Dict]:
        """Сканирует весь backend и собирает информацию о компонентах памяти"""
        results = {}
        
        for root, dirs, files in os.walk(self.backend_root):
            # Skip __pycache__ and test files
            dirs[:] = [d for d in dirs if not d.startswith('__') and d != 'tests']
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and not file.startswith('_'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.backend_root)
                    result = self.scan_file(file_path)
                    if result.get('classes') or result.get('methods'):
                        results[str(rel_path)] = result
        
        return results

    def build_components(self, scan_results: Dict[str, Dict]) -> Dict[str, MemoryComponent]:
        """Строит объекты MemoryComponent из результатов сканирования"""
        components = {}
        
        # Map file paths to known components
        file_to_component = {
            'memory/episodic.py': 'EpisodicMemory',
            'memory/semantic.py': 'SemanticMemory',
            'memory/rag.py': 'RAGMemory',
            'memory/rag_postgres.py': 'RAGMemoryPostgres',
            'memory/roots.py': 'RootsMemory',
            'memory/persona.py': 'PersonaMemory',
            'memory/user_persona.py': 'UserPersona',
            'memory/user_persona_postgres.py': 'UserPersonaPostgres',
            'emotion/session_store.py': 'SessionEmotionStore',
            'emotion/pad_model.py': 'PADModel',
            'core/impulse/core.py': 'ImpulseCore',
            'core/impulse/manager.py': 'ImpulseManager',
            'core/impulse/session_store.py': 'SessionImpulseStore',
            'core/session_manager.py': 'SessionManager',
            'memory/consolidation.py': 'MemoryConsolidator',
            'core/xray/trace_collector.py': 'TraceCollector',
            'core/pipeline/executor.py': 'PipelineExecutor',
            'core/pipeline/context.py': 'PipelineContext',
            'memory/user_persona.py': 'UserPersona',
            'memory/user_persona_postgres.py': 'UserPersonaPostgres',
            'emotion/pad_model.py': 'PADModel',
        }
        
        for file_path, scan_data in scan_results.items():
            component_name = file_to_component.get(file_path)
            if not component_name:
                # Try to infer from class names
                for class_info in scan_data.get('classes', []):
                    class_name = class_info['name']
                    if any(keyword in class_name for keyword in ['Memory', 'Store', 'Manager', 'Core', 'Engine', 'Model', 'Consolidator', 'Collector', 'Executor', 'Context', 'Manager']):
                        component_name = class_name
                        break
            
            if not component_name:
                continue
                
            if component_name not in self.components:
                self.components[component_name] = MemoryComponent(
                    name=component_name,
                    file_path=file_path
                )
            
            comp = self.components[component_name]
            comp.class_name = component_name
            comp.file_path = file_path
            comp.imports = list(set(scan_data.get('imports', [])))
            
            # Extract readers/writers from method names
            for read in scan_data.get('reads', []):
                if component_name in read:
                    method = read.replace(f"{component_name}.", "")
                    if method not in comp.readers:
                        comp.readers.append(method)
            for write in scan_data.get('writes', []):
                if component_name in write:
                    method = write.replace(f"{component_name}.", "")
                    if method not in comp.writers:
                        comp.writers.append(method)
            
            # Detect session references
            has_session = len(scan_data.get('session_refs', [])) > 0
            comp.session_scoped = has_session
            
            # Detect storage type from imports
            storage_types = []
            for imp in comp.imports:
                if 'psycopg2' in imp or 'pgvector' in imp or 'asyncpg' in imp:
                    storage_types.append('PostgreSQL/pgvector')
                elif 'sqlite' in imp:
                    storage_types.append('SQLite')
                elif 'redis' in imp:
                    storage_types.append('Redis')
                elif 'json' in imp and ('dump' in str(scan_data) or 'load' in str(scan_data)):
                    storage_types.append('JSON file')
            comp.storage = ', '.join(set(storage_types)) if storage_types else 'RAM'
            
            # Detect TTL/eviction patterns
            content = ''
            try:
                content = Path(self.backend_root / file_path).read_text(encoding='utf-8')
            except:
                pass
            
            ttl_patterns = [
                r'TTL.*=.*\d+',
                r'MAX_AGE.*=.*\d+',
                r'MAX_SESSIONS.*=.*\d+',
                r'CLEANUP_INTERVAL.*=.*\d+',
                r'_evict_',
                r'_maybe_cleanup',
                r'DECAY_RATE',
                r'_evict_expired',
                r'_evict_lru',
            ]
            for pattern in ttl_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    comp.ttl_eviction = 'Has TTL/eviction logic'
                    break
            
            # Detect consolidation patterns
            if 'consolidat' in content.lower():
                comp.consolidation = 'Participates in consolidation'
            
            # Detect session isolation
            if 'session_id' in content and ('get_or_create' in content or 'session_id' in str(comp.writers)):
                comp.session_isolation = True
            
        return self.components

    def generate_inventory_md(self) -> str:
        """Генерирует markdown для 01_inventory.md"""
        lines = [
            "# 01_inventory.md — Memory Inventory (Auto-Generated)",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Scanner version:** 1.0",
            f"**Components found:** {len(self.components)}",
            "",
            "---",
            "",
        ]
        
        for name, comp in sorted(self.components.items()):
            lines.extend(self._format_component(comp))
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Add summary table
        lines.extend([
            "## Summary Table",
            "",
            "| Component | Owner | Session | TTL | Storage | Isolation |",
            "|-----------|-------|---------|-----|---------|-----------|",
        ])
        
        for name, comp in sorted(self.components.items()):
            owner = comp.owner or comp.class_name
            session = "YES" if comp.session_scoped else "NO"
            ttl = "YES" if comp.ttl_eviction else "NO"
            storage = comp.storage or "RAM"
            isolation = "YES" if comp.session_isolation else "NO"
            lines.append(f"| {comp.name} | {owner} | {session} | {ttl} | {storage} | {isolation} |")
        
        return "\n".join(lines)
    
    def _format_component(self, comp: MemoryComponent) -> List[str]:
        lines = [
            f"## {comp.name}",
            "",
            f"**File:** `{comp.file_path}`",
            f"**Class:** `{comp.class_name}`",
            "",
        ]
        
        if comp.purpose:
            lines.extend([
                "### Purpose",
                comp.purpose,
                "",
            ])
        
        lines.extend([
            "### Owner",
            comp.owner or comp.class_name,
            "",
        ])
        
        if comp.readers:
            lines.extend([
                "### Readers",
                *[f"- {r}" for r in comp.readers],
                "",
            ])
        
        if comp.writers:
            lines.extend([
                "### Writers",
                *[f"- {w}" for w in comp.writers],
                "",
            ])
        
        if comp.storage:
            lines.extend([
                "### Storage",
                comp.storage,
                "",
            ])
        
        if comp.ttl_eviction:
            lines.extend([
                "### TTL / Eviction",
                comp.ttl_eviction,
                "",
            ])
        
        if comp.consolidation:
            lines.extend([
                "### Consolidation",
                comp.consolidation,
                "",
            ])
        
        lines.extend([
            f"**Session Scoped:** {'YES' if comp.session_scoped else 'NO'}",
            f"**Session Isolation:** {'YES' if comp.session_isolation else 'NO'}",
            "",
        ])
        
        if comp.problems:
            lines.extend([
                "### Problems",
                *[f"- {p}" for p in comp.problems],
                "",
            ])
        
        if comp.open_questions:
            lines.extend([
                "### Open Questions",
                *[f"- {q}" for q in comp.open_questions],
                "",
            ])
        
        return lines

def main():
    backend_root = Path("C:/Projects/pad-ai/backend")
    scanner = InventoryScanner(backend_root)
    
    print("Scanning backend...")
    scan_results = scanner.scan_backend()
    print(f"Scanned {len(scan_results)} files")
    
    print("Building components...")
    components = scanner.build_components(scan_results)
    print(f"Found {len(components)} components")
    
    print("Generating markdown...")
    markdown = scanner.generate_inventory_md()
    
    output_path = Path("C:/Projects/pad-ai/docs/research/memory/01_inventory.md")
    output_path.write_text(markdown, encoding='utf-8')
    print(f"Written to {output_path}")

if __name__ == "__main__":
    main()