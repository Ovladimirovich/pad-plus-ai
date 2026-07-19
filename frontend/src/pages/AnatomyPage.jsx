// Living Anatomy — интерактивная визуализация когнитивной архитектуры PAD+ AI.
// Дерево модулей Brain → Memory/Reasoning/Identity/... на ReactFlow.

import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { apiFetch } from '../services/api';

const MODULE_COLORS = {
  brain:     { bg: '#1e1b4b', border: '#818cf8', text: '#c7d2fe' },
  memory:    { bg: '#083344', border: '#06b6d4', text: '#67e8f9' },
  reasoning: { bg: '#3b0764', border: '#a855f7', text: '#c084fc' },
  identity:  { bg: '#422006', border: '#eab308', text: '#fde047' },
  emotion:   { bg: '#4a044e', border: '#ec4899', text: '#f9a8d4' },
  reflection:{ bg: '#052e16', border: '#22c55e', text: '#86efac' },
  dreams:    { bg: '#1e3a8a', border: '#3b82f6', text: '#93c5fd' },
  truth:     { bg: '#1c1917', border: '#a8a29e', text: '#d6d3d1' },
  safety:    { bg: '#450a0a', border: '#ef4444', text: '#fca5a5' },
  healer:    { bg: '#3f2d0a', border: '#f59e0b', text: '#fcd34d' },
  research:  { bg: '#064e3b', border: '#10b981', text: '#6ee7b7' },
  xray:      { bg: '#1f2937', border: '#9ca3af', text: '#e5e7eb' },
};
const DEFAULT_COLOR = { bg: '#1f2937', border: '#6b7280', text: '#d1d5db' };

function moduleColor(key) {
  return MODULE_COLORS[key?.toLowerCase()] || DEFAULT_COLOR;
}

const STATUS_COLOR = {
  active: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
  unknown: '#6b7280',
};

function ModuleNode({ data }) {
  const colors = moduleColor(data.moduleKey);
  const statusColor = STATUS_COLOR[data.status] || STATUS_COLOR.unknown;
  const metrics = data.metrics || {};
  const metricEntries = Object.entries(metrics).slice(0, 4);

  return (
    <div
      className="px-4 py-3 rounded-xl border-2 shadow-lg backdrop-blur-sm min-w-[150px] max-w-[220px] cursor-pointer transition-transform hover:scale-105"
      style={{ backgroundColor: colors.bg, borderColor: colors.border }}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-500" />
      <div className="flex items-center gap-2">
        <span
          className="w-2.5 h-2.5 rounded-full shrink-0"
          style={{ backgroundColor: statusColor, boxShadow: `0 0 6px ${statusColor}` }}
        />
        <div className="text-sm font-semibold truncate" style={{ color: colors.text }}>
          {data.label}
        </div>
      </div>

      {metricEntries.length > 0 && (
        <div className="mt-2 space-y-0.5">
          {metricEntries.map(([k, v]) => (
            <div key={k} className="flex justify-between text-[10px] leading-tight" style={{ color: colors.text }}>
              <span className="opacity-60 truncate max-w-[90px]">{k}</span>
              <span className="font-mono opacity-90 truncate max-w-[90px] text-right">
                {typeof v === 'boolean' ? (v ? 'on' : 'off') : String(v)}
              </span>
            </div>
          ))}
        </div>
      )}

      {data.childrenCount > 0 && (
        <div className="text-[10px] mt-1 opacity-50" style={{ color: colors.text }}>
          ↳ {data.childrenCount} подмодулей
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-gray-500" />
    </div>
  );
}

const nodeTypes = { moduleNode: ModuleNode };

function layoutTree(brain, width, height) {
  const nodes = [];
  const edges = [];
  const center = { x: width / 2, y: 80 };

  const rootId = 'brain';
  nodes.push({
    id: rootId,
    type: 'moduleNode',
    position: center,
    data: {
      label: brain.label,
      moduleKey: 'brain',
      status: brain.status,
      metrics: brain.metrics || {},
      childrenCount: Object.keys(brain.children || {}).length,
    },
  });

  const children = brain.children || {};
  const childKeys = Object.keys(children);
  const radius = Math.min(width, height) * 0.38;
  const angleStep = (2 * Math.PI) / Math.max(childKeys.length, 1);

  childKeys.forEach((key, i) => {
    const child = children[key];
    const angle = -Math.PI / 2 + i * angleStep;
    const pos = {
      x: center.x + Math.cos(angle) * radius - 75,
      y: center.y + Math.abs(Math.sin(angle)) * radius * 1.4 + 60,
    };
    nodes.push({
      id: key,
      type: 'moduleNode',
      position: pos,
      data: {
        label: child.label,
        moduleKey: key,
        status: child.status,
        metrics: child.metrics || {},
        childrenCount: Object.keys(child.children || {}).length,
      },
    });
    edges.push({
      id: `e-${rootId}-${key}`,
      source: rootId,
      target: key,
      type: 'smoothstep',
      animated: true,
      style: { stroke: moduleColor(key).border, strokeWidth: 1.5, opacity: 0.6 },
      markerEnd: { type: MarkerType.ArrowClosed, color: moduleColor(key).border },
    });

    // Вложенные подмодули (например, Memory → Episodic/Semantic/...)
    const sub = child.children || {};
    const subKeys = Object.keys(sub);
    const subRadius = radius * 0.42;
    subKeys.forEach((sk, si) => {
      const subChild = sub[sk];
      const subAngle = angle + (si - (subKeys.length - 1) / 2) * 0.32;
      const subPos = {
        x: pos.x + Math.cos(subAngle) * subRadius,
        y: pos.y + Math.sin(subAngle) * subRadius + 40,
      };
      nodes.push({
        id: `${key}.${sk}`,
        type: 'moduleNode',
        position: subPos,
        data: {
          label: subChild.label,
          moduleKey: sk,
          status: subChild.status,
          metrics: subChild.metrics || {},
          childrenCount: 0,
        },
      });
      edges.push({
        id: `e-${key}-${key}.${sk}`,
        source: key,
        target: `${key}.${sk}`,
        type: 'smoothstep',
        animated: false,
        style: { stroke: moduleColor(key).border, strokeWidth: 1, opacity: 0.35 },
        markerEnd: { type: MarkerType.ArrowClosed, color: moduleColor(key).border },
      });
    });
  });

  return { nodes, edges };
}

function ModuleDetailModal({ module, onClose }) {
  if (!module) return null;
  const colors = moduleColor(module.moduleKey);
  const statusColor = STATUS_COLOR[module.status] || STATUS_COLOR.unknown;
  const metrics = module.metrics || {};

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
          className="bg-gray-900 border border-gray-700 rounded-2xl p-6 max-w-lg w-full mx-4 max-h-[85vh] overflow-y-auto shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: statusColor, boxShadow: `0 0 8px ${statusColor}` }} />
              <h3 className="text-lg font-semibold text-white">{module.label}</h3>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none">&times;</button>
          </div>

          <div className="mb-3">
            <span className="px-2 py-0.5 rounded-full text-xs" style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }}>
              {module.status}
            </span>
          </div>

          <div className="space-y-2 text-sm">
            {Object.entries(metrics).map(([k, v]) => (
              <div key={k} className="flex justify-between items-center p-2 bg-gray-800/50 rounded-lg">
                <span className="text-gray-400 capitalize">{k.replace(/_/g, ' ')}</span>
                <span className="font-mono text-gray-200">
                  {typeof v === 'boolean' ? (v ? '✅ on' : '⭕ off') : Array.isArray(v) ? v.join(', ') : String(v)}
                </span>
              </div>
            ))}
            {Object.keys(metrics).length === 0 && (
              <div className="text-gray-500 text-center py-4">Нет метрик</div>
            )}
          </div>

          {module.component && (
            <div className="mt-4 pt-3 border-t border-gray-700 flex items-center gap-2">
              <button
                onClick={() => {
                  window.location.hash = `research?component=${encodeURIComponent(module.component)}`;
                  onClose();
                }}
                className="flex-1 px-3 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                Решения модуля ({module.decision_count ?? 0})
              </button>
              <button
                onClick={() => {
                  window.location.hash = `research?microscope=1&component=${encodeURIComponent(module.component || '')}`;
                  onClose();
                }}
                className="flex-1 px-3 py-2 text-sm rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition-colors"
              >
                Под микроскопом
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function AnatomyPage({ navParams = {} }) {
  const [anatomy, setAnatomy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [snapshotSlice, setSnapshotSlice] = useState(null);

  // Cross-integration: Snapshot → Anatomy slice
  useEffect(() => {
    if (navParams.snapshot) {
      const sid = navParams.snapshot;
      apiFetch(`/api/v1/experiments/snapshots/${sid}`)
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => { if (d) setSnapshotSlice(d.snapshot); })
        .catch(() => setSnapshotSlice(null));
    } else {
      setSnapshotSlice(null);
    }
  }, [navParams]);

  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [initialized, setInitialized] = useState(false);

  const fetchAnatomy = useCallback(async () => {
    try {
      const res = await apiFetch('/api/v1/anatomy');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAnatomy(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnatomy();
  }, [fetchAnatomy]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchAnatomy, 5000);
    return () => clearInterval(id);
  }, [autoRefresh, fetchAnatomy]);

  const layout = useMemo(() => {
    if (!anatomy?.brain) return { nodes: [], edges: [] };
    const w = typeof window !== 'undefined' ? window.innerWidth : 1000;
    const h = typeof window !== 'undefined' ? window.innerHeight : 700;
    return layoutTree(anatomy.brain, w, h);
  }, [anatomy]);

  useEffect(() => {
    if (!initialized && layout.nodes.length > 0) {
      setRfNodes(layout.nodes);
      setRfEdges(layout.edges);
      setInitialized(true);
      return;
    }
    if (!initialized) return;

    // Live-обновление: обновляем данные узлов, сохраняя позиции,
    // которые пользователь мог перетащить вручную.
    setRfNodes((prev) => {
      const posById = new Map(prev.map((n) => [n.id, n.position]));
      return layout.nodes.map((n) => ({
        ...n,
        position: posById.get(n.id) || n.position,
      }));
    });
    setRfEdges(layout.edges);
  }, [layout, initialized, setRfNodes, setRfEdges]);

  const onNodeClick = useCallback(async (_, node) => {
    const key = node.data.moduleKey;
    // Базовые данные из узла (мгновенно)
    const base = {
      label: node.data.label,
      moduleKey: key,
      status: node.data.status,
      metrics: node.data.metrics || {},
    };
    setSelected(base);
    // Подтягиваем деталь (component + decision_count) из backend
    try {
      const res = await apiFetch(`/api/v1/anatomy/${key}`);
      if (res.ok) {
        const detail = await res.json();
        setSelected({
          ...base,
          component: detail.component,
          decision_count: detail.decision_count,
          metrics: detail.metrics || base.metrics,
        });
      }
    } catch (e) {
      console.warn('anatomy detail error:', e);
    }
  }, []);

  const activeCount = anatomy?.brain?.children
    ? Object.values(anatomy.brain.children).filter(c => c.status === 'active').length
    : 0;
  const totalCount = anatomy?.brain?.children ? Object.keys(anatomy.brain.children).length : 0;

  if (loading && !anatomy) {
    return (
      <div className="h-[calc(100vh-4rem)] flex items-center justify-center bg-gray-950 text-gray-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          Загрузка анатомии…
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gray-950 text-white">
      <div className="shrink-0 border-b border-gray-800 px-4 lg:px-6 py-3">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-semibold">🧬 Живая анатомия</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Когнитивная архитектура PAD+ AI в реальном времени
            </p>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <span className="text-green-400">{activeCount}/{totalCount} активны</span>
            {anatomy?.timestamp && (
              <span className="text-gray-500 text-xs">
                {new Date(anatomy.timestamp).toLocaleTimeString()}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                autoRefresh
                  ? 'bg-indigo-900/40 border-indigo-700 text-indigo-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {autoRefresh ? '🔄 Live: on' : '⏸ Live: off'}
            </button>
            <Button size="sm" variant="outline" onClick={fetchAnatomy}>Обновить</Button>
          </div>
        </div>

        {error && (
          <div className="mt-2 text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-1.5">
            ⚠ Ошибка: {error}
          </div>
        )}

        {snapshotSlice && (
          <div className="mt-2 flex items-center gap-3 text-xs bg-purple-500/10 border border-purple-500/30 rounded-lg px-3 py-1.5">
            <span className="text-purple-300">🧬 Срез из снэпшота: <b>{snapshotSlice.label}</b></span>
            {snapshotSlice.pad && snapshotSlice.pad.pleasure !== undefined && (
              <span className="text-gray-300 font-mono">
                PAD {snapshotSlice.pad.pleasure.toFixed(2)}/{snapshotSlice.pad.arousal.toFixed(2)}/{snapshotSlice.pad.dominance.toFixed(2)}
              </span>
            )}
            {snapshotSlice.meta_learner_stats && Object.keys(snapshotSlice.meta_learner_stats).length > 0 && (
              <span className="text-gray-300">стратегий: {Object.keys(snapshotSlice.meta_learner_stats).length}</span>
            )}
            <button
              onClick={() => { setSnapshotSlice(null); window.location.hash = 'anatomy'; }}
              className="ml-auto text-purple-300 hover:text-white"
            >
              ✕ Live
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-hidden relative">
        {layout.nodes.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            Нет данных анатомии
          </div>
        ) : (
           <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            onInit={(inst) => inst.fitView({ padding: 0.15 })}
            minZoom={0.2}
            maxZoom={2}
            attributionPosition="bottom-left"
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#374151" gap={22} />
            <Controls className="!bg-gray-900 !border-gray-700 [&_button]:!text-gray-400 [&_button]:!border-gray-700 [&_button:hover]:!bg-gray-800" />
            <MiniMap
              nodeColor={(n) => moduleColor(n.data?.moduleKey).border}
              maskColor="rgba(0,0,0,0.75)"
              className="!bg-gray-900 !border-gray-700"
            />
          </ReactFlow>
        )}
      </div>

      <ModuleDetailModal module={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
