#!/usr/bin/env python3
"""
Memory Ownership Analyzer
Определяет единственных владельцев для каждого куска состояния памяти
"""
import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class OwnershipAnalyzer:
    def __init__(self, backend_root: Path):
        self.backend_root = Path(backend_root)
        self.state_owners: Dict[str, Dict] = {}
        self.readers: Dict[str, Set[str]] = defaultdict(set)
        self.writers: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze(self):
        """Полный анализ владения состоянием"""
        for root, dirs, files in os.walk(self.backend_root):
            dirs[:] = [d for d in dirs if not d.startswith('__') and d != 'tests']
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and not file.startswith('_'):
                    file_path = Path(root) / file
                    self._analyze_file(file_path)
        
        self._resolve_conflicts()
        return self._generate_report()
    
    def _analyze_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except Exception:
            return
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                if self._is_memory_component(class_name):
                    self._analyze_class(node, class_name, file_path)
    
    def _is_memory_component(self, class_name: str) -> bool:
        keywords = ['Memory', 'Store', 'Session', 'Cache', 'Context', 'Persona', 'Emotion', 'Impulse', 'Episode', 'Semantic', 'RAG', 'Roots', 'Consolidation', 'Manager']
        return any(kw.lower() in class_name.lower() for kw in keywords)
    
    def _analyze_class(self, node: ast.ClassDef, class_name: str, file_path: Path):
        writes = set()
        reads = set()
        
        for item in node.body:
            if isinstance(node, ast.FunctionDef):
                # Анализируем тело метода
                method_source = ast.get_source_segment(ast.unparse(node), item)
                if not method_source:
                    continue
                    
                # Паттерны записи
                write_patterns = [
                    r'\.add_', r'\.create_', r'\.save\(', r'\.update\(',
                    r'\.delete\(', r'\.remove_', r'\.delete_',
                    r'\.apply_', r'\.push\(', r'\.pop\(', r'\.set_',
                    r'\.create_session', r'\.end_session', r'\.record_',
                    r'\.add_', r'\.insert_', r'\.upsert_', r'\.write\(',
                    r'\.apply_event', r'\.apply_deltas', r'\.save\(', r'\.persist',
                ]
                
                read_patterns = [
                    r'\.get_', r'\.find_', r'\.search_', r'\.query_',
                    r'\.load\(', r'\.read\(', r'\.fetch_', r'\.retrieve_',
                    r'\.get_all', r'\.get_recent', r'\.get_stats',
                    r'\.list_', r'\.scan_', r'\.query_',
                ]
                
                for pattern in write_patterns:
                    if re.search(pattern, method_source):
                        # Определяем что пишется из имени метода или аргументов
                        state = self._extract_state_from_method(class_name, item.name)
                        if state:
                            self.writers[state].add(class_name)
                
                for pattern in read_patterns:
                    if re.search(pattern, method_source):
                        state = self._extract_state_from_method(class_name, item.name)
                        if state:
                            self.readers[state].add(class_name)
    
    def _extract_state_from_method(self, class_name: str, method_name: str) -> str:
        """Извлекает название состояния из имени класса и метода"""
        mapping = {
            ('EpisodicMemory', 'add_episode'): 'Episodes',
            ('EpisodicMemory', 'get_recent'): 'Episodes',
            ('EpisodicMemory', 'get_all'): 'Episodes',
            ('SemanticMemory', 'add_fact'): 'Semantic Facts',
            ('SemanticMemory', 'add_procedure'): 'Semantic Procedures',
            ('SemanticMemory', 'find_applicable_procedure'): 'Semantic Procedures',
            ('SemanticMemory', 'find_facts'): 'Semantic Facts',
            ('RAGMemory', 'add_dialog'): 'RAG Dialogs',
            ('RAGMemory', 'search'): 'RAG Dialogs',
            ('RootsMemory', 'get_roots_context'): 'Roots',
            ('PersonaMemory', 'adjust_trait'): 'Persona Traits',
            ('PersonaMemory', 'add_reflection'): 'Persona Reflections',
            ('UserPersonaManager', 'adjust_style'): 'User Persona',
            ('UserPersonaManager', 'get_persona'): 'User Persona',
            ('RootsMemory', 'add_root'): 'Roots',
            ('ImpulseCore', 'set_from_labels'): 'Impulse State',
            ('ImpulseCore', 'push'): 'Impulse Stack',
            ('ImpulseCore', 'pop'): 'Impulse Stack',
            ('PADModel', 'apply_event'): 'Emotion State',
            ('SessionEmotionStore', 'save'): 'Emotion State',
            ('SessionEmotionStore', 'get_or_create'): 'Emotion State',
            ('SessionImpulseStore', 'save'): 'Impulse State',
            ('SessionImpulseStore', 'get_or_create'): 'Impulse State',
            ('SessionManager', 'create_session'): 'Session',
            ('SessionManager', 'end_session'): 'Session',
            ('MemoryConsolidator', 'consolidate_all'): 'Episodic→Semantic',
            ('MemoryConsolidator', 'run_scheduled_consolidation'): 'Consolidation',
        }
        
        key = (class_name, method_name)
        if key in mapping:
            return mapping[key]
        return ""
    
    def _resolve_conflicts(self):
        """Резолвит конфликты владения"""
        conflicts = {}
        for state, writers in self.writers.items():
            if len(writers) > 1:
                conflicts[state] = writers
        
        # Авто-резолюция по приоритетам
        priority = {
            'EpisodicMemory': 10,
            'SemanticMemory': 10,
            'UserPersonaManager': 10,
            'SessionEmotionStore': 10,
            'SessionImpulseStore': 10,
            'SessionManager': 10,
            'RAGMemory': 8,
            'SemanticMemory': 8,
            'ImpulseCore': 7,
            'PersonaMemory': 7,
            'RootsMemory': 7,
            'RAGMemory': 6,
            'Consolidation': 5,
            'EmotionEngine': 5,
            'ImpulseManager': 5,
        }
        
        for state, writers in conflicts.items():
            best = max(writers, key=lambda w: priority.get(w, 0))
            for w in writers:
                if w != best:
                    self.writers[state].remove(w)
    
    def _generate_report(self) -> str:
        """Генерирует отчет по владению"""
        lines = [
            "# 02_ownership.md — Memory Ownership",
            "",
            "**Phase:** 1 — Ownership",
            "**Status:** Auto-generated",
            "",
            "## Ownership Matrix",
            "",
            "| State | Single Owner | Readers | Writers |",
            "|-------|--------------|---------|---------|",
        ]
        
        # Собираем все состояния
        all_states = set(self.readers.keys()) | set(self.writers.keys())
        
        for state in sorted(all_states):
            readers = self.readers.get(state, set())
            writers = self.writers.get(state, set())
            
            # Определяем единственного владельца
            owner = "NONE"
            if len(self.writers.get(state, [])) == 1:
                owner = list(self.writers[state])[0]
            elif self.writers.get(state):
                # Multiple writers - conflict
                owner = f"CONFLICT: {', '.join(self.writers[state])}"
            
            lines.append(f"| {state} | {owner} | {', '.join(sorted(readers)) or '—'} | {', '.join(sorted(writers)) or '—'} |")
        
        # Conflicts section
        conflicts = {s: w for s, w in self.writers.items() if len(w) > 1}
        if conflicts:
            lines.extend([
                "",
                "## ⚠️ Ownership Conflicts",
                "",
                "| State | Writers | Resolution |",
                "|-------|---------|------------|",
            ])
            priority = {
                'EpisodicMemory': 10, 'SemanticMemory': 10, 'UserPersonaManager': 10,
                'SessionEmotionStore': 10, 'SessionImpulseStore': 10, 'SessionManager': 10,
            }
            for state, writers in conflicts.items():
                best = max(writers, key=lambda w: priority.get(w, 0))
                others = [w for w in writers if w != best]
                lines.append(f"| {state} | {', '.join(writers)} | **Owner: {best}**, demote: {', '.join(others)} |")
        
        # Single owner verification
        lines.extend([
            "",
            "## ✅ Ownership Verification",
            "",
            "| Check | Status |",
            "|-------|--------|",
        ])
        
        single_owner = sum(1 for s, w in self.writers.items() if len(w) == 1)
        multi_owner = sum(1 for s, w in self.writers.items() if len(w) > 1)
        no_writer = sum(1 for s in set(self.readers.keys()) if not self.writers.get(s))
        
        lines.append(f"| Single Writer per State | {single_owner} / {len(self.writers)} |")
        lines.append(f"| Conflicts Resolved | {multi_owner} resolved |")
        lines.append(f"| States without Writer | {no_writer} |")
        
        return "\n".join(lines)


def main():
    backend_root = Path(r"C:\Projects\pad-ai\backend")
    analyzer = OwnershipAnalyzer(backend_root)
    analyzer.analyze()
    report = analyzer._generate_report()
    
    output_path = Path(r"C:\Projects\pad-ai\docs\research\memory\02_ownership.md")
    output_path.write_text(report, encoding='utf-8')
    print(f"Written to {output_path}")

if __name__ == "__main__":
    main()