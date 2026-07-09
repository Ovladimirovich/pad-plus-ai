"""Seed knowledge graph with test data for visualization demo"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from knowledge.graph import get_knowledge_graph
graph = get_knowledge_graph()

# Concepts
concepts = [
    ("Нейронная сеть", "concept", 0.95, "system"),
    ("Машинное обучение", "concept", 0.92, "system"),
    ("Глубокое обучение", "concept", 0.90, "system"),
    ("Трансформер", "concept", 0.88, "system"),
    ("Внимание (Attention)", "concept", 0.85, "system"),
    ("RNN", "concept", 0.80, "system"),
    ("CNN", "concept", 0.82, "system"),
    ("Обучение с учителем", "concept", 0.87, "system"),
    ("Обучение без учителя", "concept", 0.86, "system"),
    ("Обучение с подкреплением", "concept", 0.84, "system"),
    ("Градиентный спуск", "fact", 0.93, "system"),
    ("Функция потерь", "fact", 0.91, "system"),
    ("Обратное распространение", "fact", 0.89, "system"),
    ("Переобучение", "fact", 0.78, "system"),
    ("Регуляризация", "fact", 0.83, "system"),
    ("PyTorch", "skill", 0.94, "system"),
    ("TensorFlow", "skill", 0.90, "system"),
    ("Scikit-learn", "skill", 0.85, "system"),
    ("Python", "skill", 0.96, "system"),
    ("Jupyter", "skill", 0.82, "system"),
    ("Что такое энтропия в ML?", "question", 0.70, "user"),
    ("Как работает dropout?", "question", 0.72, "user"),
    ("Зачем нужен batch normalization?", "question", 0.68, "user"),
    ("PAD+ AI", "entity", 0.98, "system"),
    ("OpenAI", "entity", 0.88, "system"),
]

ids = {}
for name, ctype, conf, source in concepts:
    c = graph.add_concept(name, concept_type=ctype, confidence=conf, source=source)
    ids[name] = c.id

# Relations
relations = [
    ("Нейронная сеть", "Машинное обучение", "is_subfield_of"),
    ("Глубокое обучение", "Машинное обучение", "is_subfield_of"),
    ("Глубокое обучение", "Нейронная сеть", "uses"),
    ("Трансформер", "Глубокое обучение", "is_technique_of"),
    ("Внимание (Attention)", "Трансформер", "is_part_of"),
    ("RNN", "Нейронная сеть", "is_type_of"),
    ("CNN", "Нейронная сеть", "is_type_of"),
    ("Обучение с учителем", "Машинное обучение", "is_paradigm_of"),
    ("Обучение без учителя", "Машинное обучение", "is_paradigm_of"),
    ("Обучение с подкреплением", "Машинное обучение", "is_paradigm_of"),
    ("Градиентный спуск", "Машинное обучение", "is_algorithm_of"),
    ("Функция потерь", "Градиентный спуск", "is_part_of"),
    ("Обратное распространение", "Градиентный спуск", "is_part_of"),
    ("Переобучение", "Нейронная сеть", "is_problem_of"),
    ("Регуляризация", "Переобучение", "solves"),
    ("PyTorch", "Нейронная сеть", "implements"),
    ("TensorFlow", "Нейронная сеть", "implements"),
    ("Scikit-learn", "Машинное обучение", "implements"),
    ("Python", "PyTorch", "is_language_for"),
    ("Python", "TensorFlow", "is_language_for"),
    ("Python", "Scikit-learn", "is_language_for"),
    ("Jupyter", "Python", "is_environment_for"),
    ("PAD+ AI", "Нейронная сеть", "uses"),
    ("PAD+ AI", "Глубокое обучение", "uses"),
    ("PAD+ AI", "PyTorch", "uses"),
    ("OpenAI", "Трансформер", "developed"),
    ("Внимание (Attention)", "RNN", "is_alternative_to"),
]

for src_name, tgt_name, rel_type in relations:
    if src_name in ids and tgt_name in ids:
        graph.add_relation(ids[src_name], ids[tgt_name], relation_type=rel_type)

stats = graph.get_stats()
print(f"Ok: {stats['nodes']} concepts, {stats['edges']} relations")
print(f"Density: {stats['density']*100:.1f}%")
print("Restart backend and refresh page to see the graph!")
