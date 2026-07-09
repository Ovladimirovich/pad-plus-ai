import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../components/ui/Select';
import { apiFetch } from '../services/api';
import KnowledgeGraphCanvas from '../components/graph/KnowledgeGraphCanvas';

const TYPE_COLORS = {
  concept: { bg: 'bg-blue-900/30', border: 'border-blue-800', text: 'text-blue-300' },
  fact: { bg: 'bg-green-900/30', border: 'border-green-800', text: 'text-green-300' },
  skill: { bg: 'bg-purple-900/30', border: 'border-purple-800', text: 'text-purple-300' },
  question: { bg: 'bg-yellow-900/30', border: 'border-yellow-800', text: 'text-yellow-300' },
  entity: { bg: 'bg-cyan-900/30', border: 'border-cyan-800', text: 'text-cyan-300' },
};
const DEFAULT_COLOR = { bg: 'bg-gray-700/50', border: 'border-gray-600', text: 'text-gray-300' };

function getTypeColor(type) {
  return TYPE_COLORS[type?.toLowerCase()] || DEFAULT_COLOR;
}

const RELATION_TYPES = [
  'related', 'is_a', 'uses', 'contains', 'part_of', 'similar_to',
  'depends_on', 'causes', 'precedes', 'contradicts', 'extends'
];

function NodeDetailModal({ node, graph, onClose, onDelete, onMerge, onEditRelation }) {
  if (!node) return null;

  const related = graph.edges?.filter(e => e.source === node.id || e.target === node.id) || [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[85vh] overflow-y-auto shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">{node.name}</h3>
            <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none">&times;</button>
          </div>

          <div className="space-y-4 text-sm">
            <div className="flex flex-wrap gap-2">
              <span className={`px-2 py-0.5 rounded-full text-xs ${getTypeColor(node.type || node.concept_type).bg} ${getTypeColor(node.type || node.concept_type).border} ${getTypeColor(node.type || node.concept_type).text}`}>
                {node.type || node.concept_type || 'concept'}
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800 border border-gray-700 text-gray-300">
                {((node.confidence || 0.5) * 100).toFixed(0)}%
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800 border border-gray-700 text-gray-300">
                {node.source || '—'}
              </span>
            </div>

            {node.metadata?.definition && (
              <div className="pt-2 border-t border-gray-700">
                <span className="text-gray-400 block mb-1">Определение</span>
                <span className="text-gray-300 text-xs">{node.metadata.definition}</span>
              </div>
            )}

            {related.length > 0 && (
              <div className="pt-2 border-t border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Связи ({related.length})</span>
                  <Button size="sm" variant="ghost" onClick={() => onEditRelation(null, node.id)}>+ Добавить</Button>
                </div>
                <div className="space-y-1 max-h-60 overflow-y-auto">
                  {related.map((e, i) => {
                    const isSource = e.source === node.id;
                    const otherId = isSource ? e.target : e.source;
                    const otherNode = graph.nodes?.find(n => n.id === otherId);
                    const otherName = otherNode?.name || otherId;
                    const direction = isSource ? '→' : '←';
                    return (
                      <motion.div
                        key={e.id || i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.02 }}
                        className="flex items-center gap-2 p-2 bg-gray-800/50 rounded-lg"
                      >
                        <span className={`px-2 py-0.5 rounded text-xs ${getTypeColor(otherNode?.type).bg} ${getTypeColor(otherNode?.type).text}`}>
                          {otherName}
                        </span>
                        <span className="text-gray-500 px-2">{direction}</span>
                        <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300">{e.type || 'related'}</span>
                        <Button size="xs" variant="ghost" className="text-red-400 hover:text-red-300 ml-auto" onClick={(ev) => { ev.stopPropagation(); onEditRelation(e.id, node.id, 'delete'); }}>
                          🗑️
                        </Button>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-4 border-t border-gray-700">
              <Button variant="outline" size="sm" onClick={() => onMerge(node.id)} className="flex-1">🔗 Объединить</Button>
              <Button variant="outline" size="sm" className="text-red-400 border-red-500 hover:bg-red-500/10" onClick={() => onDelete(node.id)}>🗑️ Удалить</Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function MergeModal({ sourceNode, allNodes, onClose, onConfirm }) {
  if (!sourceNode) return null;

  const targets = allNodes.filter(n => n.id !== sourceNode.id);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <h3 className="text-lg font-semibold mb-4">Объединить «{sourceNode.name}» в…</h3>
          <p className="text-sm text-gray-400 mb-4">Выберите целевую концепцию. Все связи перенесутся, дубликат удалится.</p>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {targets.map(n => (
              <button
                key={n.id}
                onClick={() => onConfirm(n.id)}
                className="w-full text-left px-3 py-2 rounded-lg border border-gray-700 hover:border-blue-500 hover:bg-gray-800 transition-colors"
              >
                <span className="font-medium">{n.name}</span>
                <span className="text-xs text-gray-500 ml-2">({n.type || 'concept'})</span>
              </button>
            ))}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="mt-4 w-full">Отмена</Button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function EditRelationModal({ relation, graph, onClose, onSave, isNew }) {
  if (!relation) return null;

  const [form, setForm] = useState({
    source_id: relation.source_id || '',
    target_id: relation.target_id || '',
    relation_type: relation.type || 'related',
    weight: relation.weight || 1.0,
    confidence: relation.confidence || 0.5,
  });

  const allNodes = graph.nodes || [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <h3 className="text-lg font-semibold mb-4">{isNew ? 'Создать связь' : 'Редактировать связь'}</h3>

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Источник</label>
              <Select value={form.source_id} onValueChange={v => setForm({...form, source_id: v})}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Выберите источник" /></SelectTrigger>
                <SelectContent>
                  {allNodes.map(n => <SelectItem key={n.id} value={n.id}>{n.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Цель</label>
              <Select value={form.target_id} onValueChange={v => setForm({...form, target_id: v})}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Выберите цель" /></SelectTrigger>
                <SelectContent>
                  {allNodes.map(n => <SelectItem key={n.id} value={n.id}>{n.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Тип связи</label>
              <Select value={form.relation_type} onValueChange={v => setForm({...form, relation_type: v})}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Тип" /></SelectTrigger>
                <SelectContent>
                  {RELATION_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Вес ({form.weight})</label>
                <input type="range" min="0" max="5" step="0.1" value={form.weight}
                  onChange={e => setForm({...form, weight: parseFloat(e.target.value)})} className="w-full" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Уверенность ({form.confidence})</label>
                <input type="range" min="0" max="1" step="0.05" value={form.confidence}
                  onChange={e => setForm({...form, confidence: parseFloat(e.target.value)})} className="w-full" />
              </div>
            </div>
          </div>

          <div className="flex gap-2 mt-6">
            <Button variant="outline" size="sm" className="flex-1" onClick={onClose}>Отмена</Button>
            <Button size="sm" className="flex-1" onClick={() => onSave(form)}>{isNew ? 'Создать' : 'Сохранить'}</Button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function AddConceptModal({ onClose, onSave }) {
  const [form, setForm] = useState({ name: '', type: 'concept', confidence: 0.5, source: 'user' });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      await onSave(form);
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <h3 className="text-lg font-semibold mb-4">Добавить концепцию</h3>
          <div className="space-y-3">
            <Input
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              placeholder="Название концепции"
              autoFocus
            />
            <Select value={form.type} onValueChange={v => setForm({...form, type: v})}>
              <SelectTrigger className="w-full"><SelectValue placeholder="Тип" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="concept">Концепция</SelectItem>
                <SelectItem value="fact">Факт</SelectItem>
                <SelectItem value="skill">Навык</SelectItem>
                <SelectItem value="question">Вопрос</SelectItem>
                <SelectItem value="entity">Сущность</SelectItem>
              </SelectContent>
            </Select>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Уверенность ({form.confidence})</label>
                <input type="range" min="0" max="1" step="0.05" value={form.confidence}
                  onChange={e => setForm({...form, confidence: parseFloat(e.target.value)})} className="w-full" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Источник</label>
                <Input value={form.source} onChange={e => setForm({...form, source: e.target.value})} placeholder="user" />
              </div>
            </div>
          </div>
          <div className="flex gap-2 mt-6">
            <Button variant="outline" size="sm" className="flex-1" onClick={onClose}>Отмена</Button>
            <Button size="sm" className="flex-1" loading={saving} onClick={handleSave}>Добавить</Button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        <div className="space-y-6 animate-pulse">
          <h1 className="text-2xl font-semibold mb-6">🔗 Граф знаний</h1>
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map(i => <div key={i} className="h-24 bg-gray-800/50 rounded-2xl" />)}
          </div>
          <div className="h-12 bg-gray-800/50 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="bg-gray-900/50 border-gray-700 mt-6">
      <CardContent className="p-8 text-center">
        <div className="text-4xl mb-4">🕸️</div>
        <h3 className="text-lg font-medium text-gray-300 mb-2">Граф знаний ещё не сформирован</h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          Данные появятся после диалогов с AI. Система автоматически извлекает концепции
          и создаёт связи между ними в процессе обучения.
        </p>
      </CardContent>
    </Card>
  );
}

// version 2.1 — force new hash
export default function KnowledgePage() {
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [graph, setGraph] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('graph');
  const [extractText, setExtractText] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState(null);

  const [editMode, setEditMode] = useState(false);
  const [mergeSource, setMergeSource] = useState(null);
  const [editRelation, setEditRelation] = useState(null);
  const [addConceptOpen, setAddConceptOpen] = useState(false);

  const handleRecomputeEmbeddings = async () => {
    if (!confirm('Перегенерировать эмбеддинги для всех концепций? Это может занять время.')) return;
    try {
      const res = await apiFetch('/api/v1/knowledge/recompute-embeddings?limit=100', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Готово: обновлено ${data.updated}, ошибок ${data.failed}`);
        await refreshGraph();
      } else {
        const err = await res.text();
        alert('Ошибка: ' + err);
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  };

  const handleExtract = async () => {
    if (!extractText.trim()) return;
    setExtracting(true);
    setExtractResult(null);
    try {
      const res = await apiFetch('/api/v1/knowledge/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: extractText }),
      });
      if (res.ok) {
        const data = await res.json();
        setExtractResult(data);
        const gr = await apiFetch('/api/v1/knowledge/graph?limit=30');
        if (gr.ok) setGraph(await gr.json());
        const st = await apiFetch('/api/v1/knowledge/stats');
        if (st.ok) setStats(await st.json());
      } else {
        const err = await res.text();
        setExtractResult({ error: err });
      }
    } catch (e) {
      setExtractResult({ error: e.message });
    } finally {
      setExtractText('');
      setExtracting(false);
    }
  };

  const refreshGraph = useCallback(async () => {
    try {
      const [gr, st] = await Promise.all([
        apiFetch('/api/v1/knowledge/graph?limit=200'),
        apiFetch('/api/v1/knowledge/stats'),
      ]);
      if (gr.ok) setGraph(await gr.json());
      if (st.ok) setStats(await st.json());
    } catch (e) {
      console.error('Refresh graph error:', e);
    }
  }, []);

  useEffect(() => {
    refreshGraph().finally(() => setLoading(false));
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await apiFetch(`/api/v1/knowledge/search?q=${encodeURIComponent(searchQuery)}&limit=20`);
      if (res.ok) setResults((await res.json()).concepts || []);
    } catch (e) {
      console.error('Knowledge search error:', e);
    } finally {
      setSearching(false);
    }
  };

  const handleAddConcept = async (form) => {
    // prevent invalid payload (backend returns 400 without name)
    const name = (form?.name || '').trim();
    if (!name) {
      alert('Введите название концепции');
      return;
    }

    try {
      const payload = {
        ...form,
        name,
      };

      console.log('Sending concept:', JSON.stringify(payload));
      const res = await apiFetch('/api/v1/knowledge/concepts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const text = await res.text();
      console.log('Response status:', res.status, 'body:', text);
      if (res.ok) {
        await refreshGraph();
        setAddConceptOpen(false);
      } else {
        alert('Ошибка (' + res.status + '): ' + text);
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  };

  const handleDeleteConcept = async (conceptId) => {
    if (!confirm('Удалить концепцию и все её связи?')) return;
    try {
      const res = await apiFetch(`/api/v1/knowledge/concepts/${conceptId}`, { method: 'DELETE' });
      if (res.ok) {
        await refreshGraph();
        setSelectedNode(null);
      } else {
        alert('Ошибка: ' + await res.text());
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  };

  const handleMergeConfirm = async (targetId) => {
    if (!mergeSource) return;
    try {
      const res = await apiFetch(`/api/v1/knowledge/concepts/${mergeSource}/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_id: targetId }),
      });
      if (res.ok) {
        await refreshGraph();
        setSelectedNode(null);
        setMergeSource(null);
      } else {
        alert('Ошибка: ' + await res.text());
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  };

  const handleSaveRelation = async (form) => {
    try {
      const res = await apiFetch('/api/v1/knowledge/relations', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        await refreshGraph();
        setEditRelation(null);
      } else {
        alert('Ошибка: ' + await res.text());
      }
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  };

  const handleEditRelation = (relationId, sourceNodeId, action) => {
    if (action === 'delete') {
      if (!confirm('Удалить эту связь?')) return;
      return;
    }
    const relation = relationId
      ? graph.edges?.find(e => e.id === relationId)
      : null;
    setEditRelation({
      relation: relation || { source_id: sourceNodeId, target_id: '', type: 'related', weight: 1, confidence: 0.5 },
      isNew: !relationId,
    });
  };

  const isEmpty = stats && stats.nodes === 0;

  if (loading) return <LoadingSkeleton />;

  const fullscreen = graph?.nodes?.length > 0 && viewMode === 'graph';

  return (
    <div className={`${fullscreen ? 'h-screen overflow-hidden' : 'min-h-screen'} bg-gray-950 text-white flex flex-col`}>
      <div className="shrink-0 border-b border-gray-800 px-4 lg:px-6 py-3">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <h1 className="text-xl font-semibold">🔗 Граф знаний</h1>

          {stats && (
            <div className="flex items-center gap-4 text-sm">
              <span className="text-blue-400">{stats.nodes ?? 0} концепций</span>
              <span className="text-purple-400">{stats.edges ?? 0} связей</span>
              <span className="text-green-400">{stats.density != null ? (stats.density * 100).toFixed(1) : 0}%</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Поиск..."
              className="w-32 lg:w-48 px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white"
            />
            <Button onClick={handleSearch} loading={searching} size="sm">🔍</Button>

            <button
              onClick={() => { setExtractResult(null); document.getElementById('extract-panel')?.classList.toggle('hidden'); }}
              className="px-2.5 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-gray-300 transition-colors"
              title="Извлечь знания из текста"
            >🧠 Извлечь</button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleRecomputeEmbeddings}
              className="ml-2"
            >🔄 Эмбеддинги</Button>

            <Button
              variant={editMode ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setEditMode(!editMode)}
            >
              {editMode ? '✏️ Редактировать' : '✏️ Режим редактирования'}
            </Button>

            {graph?.nodes?.length > 0 && (
              <div className="flex gap-1 bg-gray-800 rounded-lg p-0.5">
                <button onClick={() => setViewMode('graph')} className={`px-2.5 py-1 text-xs rounded-md transition-colors ${viewMode === 'graph' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}>Граф</button>
                <button onClick={() => setViewMode('list')} className={`px-2.5 py-1 text-xs rounded-md transition-colors ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}>Список</button>
              </div>
            )}
          </div>
        </div>

        {editMode && (
          <div className="flex items-center gap-3 mt-3 pt-3 border-t border-gray-800">
            <span className="text-xs text-gray-400">Режим редактирования:</span>
            <Button size="sm" onClick={() => setAddConceptOpen(true)}>➕ Концепцию</Button>
            <span className="text-xs text-gray-500 ml-auto">Кликните на узел для действий</span>
          </div>
        )}

        {results.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-800">
            {results.map((c, i) => (
              <motion.button
                key={c.id || i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02 }}
                onClick={() => setSelectedNode(c)}
                className={`px-2.5 py-1 rounded-full text-xs border cursor-pointer transition-colors hover:brightness-125 ${getTypeColor(c.type || c.concept_type).bg} ${getTypeColor(c.type || c.concept_type).border} ${getTypeColor(c.type || c.concept_type).text}`}
              >
                {c.name}
              </motion.button>
            ))}
          </div>
        )}
      </div>

      <div id="extract-panel" className="hidden shrink-0 border-b border-gray-800 px-4 lg:px-6 py-3 bg-gray-900/50">
        <div className="max-w-3xl">
          <p className="text-xs text-gray-400 mb-2">Вставьте текст для извлечения концепций и связей:</p>
          <textarea
            value={extractText}
            onChange={e => setExtractText(e.target.value)}
            placeholder="Например: Нейронные сети используют градиентный спуск для оптимизации. Трансформеры основаны на механизме внимания."
            className="w-full h-20 px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white resize-none"
          />
          <div className="flex items-center gap-3 mt-2">
            <Button onClick={handleExtract} loading={extracting} size="sm">🧠 Извлечь</Button>
            {extractResult && !extractResult.error && (
              <span className="text-xs text-green-400">
                +{extractResult.concepts_added ?? 0} концепций, +{extractResult.relations_added ?? 0} связей
              </span>
            )}
            {extractResult?.error && (
              <span className="text-xs text-red-400">Ошибка: {extractResult.error}</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        {isEmpty && !searchQuery && (
          <div className="h-full flex items-center justify-center p-6">
            <EmptyState />
          </div>
        )}

        {!isEmpty && graph?.nodes?.length > 0 && viewMode === 'list' && (
          <div className="p-4 lg:p-6 max-w-6xl mx-auto">
            <div className="flex flex-wrap gap-2">
              {graph.nodes.map((n, i) => {
                const colors = getTypeColor(n.type || n.concept_type);
                const connCount = graph.edges?.filter(e => e.source === n.id || e.target === n.id).length || 0;
                return (
                  <motion.button
                    key={n.id || i}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSelectedNode(n)}
                    className={`px-3 py-1.5 ${colors.bg} ${colors.border} rounded-full text-xs ${colors.text} border cursor-pointer transition-colors hover:brightness-125`}
                  >
                    {n.name}{connCount > 0 && <span className="ml-1.5 opacity-60">({connCount})</span>}
                  </motion.button>
                );
              })}
            </div>
          </div>
        )}

        {!isEmpty && graph?.nodes?.length > 0 && viewMode === 'graph' && (
          <KnowledgeGraphCanvas
            nodes={graph.nodes}
            edges={graph.edges}
            onNodeClick={setSelectedNode}
          />
        )}
      </div>

      <NodeDetailModal
        node={selectedNode}
        graph={graph}
        onClose={() => setSelectedNode(null)}
        onDelete={handleDeleteConcept}
        onMerge={id => setMergeSource(id)}
        onEditRelation={handleEditRelation}
      />

      <MergeModal
        sourceNode={mergeSource ? graph.nodes?.find(n => n.id === mergeSource) : null}
        allNodes={graph.nodes || []}
        onClose={() => setMergeSource(null)}
        onConfirm={handleMergeConfirm}
      />

      <EditRelationModal
        relation={editRelation?.relation}
        graph={graph}
        onClose={() => setEditRelation(null)}
        onSave={handleSaveRelation}
        isNew={editRelation?.isNew}
      />

      {addConceptOpen && (
        <AddConceptModal
          onClose={() => setAddConceptOpen(false)}
          onSave={handleAddConcept}
        />
      )}
    </div>
  );
}