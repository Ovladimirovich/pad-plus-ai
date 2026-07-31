#!/usr/bin/env python3
"""
Ownership Analyzer v2 — работает
"""
import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List

backend_root = Path(r"C:\Projects\pad-ai\backend")

class OwnershipAnalyzer:
    def __init__(self, backend_root: Path):
        self.backend_root = backend_root
        self.readers = defaultdict(set)  # state -> set(readers)
        self.writers = defaultdict(set)  # state -> set(writers)
        
    def scan(self):
        """Сканирует весь backend"""
        py_files = list(self.backend_root.rglob("*.py"))
        print(f"Scanning {len(py_files)} Python files...")
        
        for file_path in self.backend_root.rglob("*.py"):
            if file_path.name.startswith("test_") or "__pycache__" in str(file_path):
                continue
            try:
                self.scan_file(file_path)
            except Exception as e:
                pass
        
        self.resolve_conflicts()
        self.generate_report()
    
    def scan_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding='utf-8')
        except:
            return
            
        try:
            tree = ast.parse(content)
        except:
            return
            
        rel_path = file_path.relative_to(Path("C:/Projects/pad-ai"))
        
        # Find all classes and their methods
        for node in ast.walk(ast.parse(content)):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                class_file = str(file_path.relative_to(Path("C:/Projects/pad-ai")))
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method = item.name
                        source = ast.get_source_segment(content, item) or ""
                        
                        # Detect reads
                        if any(p in source for p in ['get_', 'find_', 'search', 'load', 'read', '.get(']):
                            self.readers[class_name].add(f"{rel_path}:{class_name}.{method}")
                        
                        # Detect writes
                        if any(p in source for p in ['add_', 'save', 'write', 'update', 'delete', 'delete_', 'remove', 'create_', 'insert', 'upsert', 'push', 'pop', 'set_', 'apply_']):
                            self.writers[class_name].add(f"{rel_path}:{class_name}.{method}")
    
    def resolve_conflicts(self):
        """Резолвит конфликты множественных писателей"""
        # Priority for choosing owner
        priority = {
            'EpisodicMemory': 100, 'SemanticMemory': 100, 'UserPersonaManager': 100,
            'SessionEmotionStore': 100, 'SessionImpulseStore': 100, 'SessionManager': 100,
            'RAGMemory': 80, 'SemanticMemory': 80, 'ImpulseCore': 70,
            'PersonaMemory': 70, 'RootsMemory': 70, 'RAGMemory': 60, 'Consolidation': 50,
        }
        
        for state, writers in list(self.writers.items()):
            if len(writers) > 1:
                # Choose highest priority writer
                best = max(writers, key=lambda w: priority.get(w.split(':')[0].split('.')[-1], 0))
                self.writers[state] = {best}
                print(f"  Resolved conflict for {state}: {best} wins")

    def generate_report(self):
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
        
        all_states = set(self.readers.keys()) | set(self.writers.keys())
        
        for state in sorted(self.writers.keys()):
            readers = self.readers.get(state, set())
            writers = self.writers.get(state, set())
            
            # Determine single owner
            owner = "NONE"
            if len(self.writers.get(state, [])) == 1:
                owner = list(self.writers[state])[0].split(':')[-1]  # just method
                owner = owner.split('.')[0]  # just class
            elif self.writers.get(state):
                owner = f"CONFLICT: {', '.join(w.split(':')[-1].split('.')[0] for w in self.writers[state])}"
            
            readers_str = ', '.join(sorted(r.split(':')[-1] for r in self.readers.get(state, []))) or '—'
            writers_str = ', '.join(sorted(w.split(':')[-1] for w in self.writers.get(state, []))) or '—'
            
            print(f"| {state} | {owner} | {readers_str} | {writers_str} |")
        
        # Conflicts
        conflicts = {s: w for s, w in self.writers.items() if len(w) > 1}
        if any(len(w) > 1 for w in self.writers.values()):
            print("\n## Conflicts")
            for state, writers in self.writers.items():
                if len(writers) > 1:
                    print(f"  {state}: {writers}")

if __name__ == "__main__":
    backend = Path(r"C:\Projects\pad-ai\backend")
    analyzer = OwnershipAnalyzer(backend)
    analyzer.scan()
    print("\nDone!")