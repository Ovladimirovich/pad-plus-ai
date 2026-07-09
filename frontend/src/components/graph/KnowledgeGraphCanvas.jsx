import { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import ConceptNode from './ConceptNode';

const nodeTypes = { conceptNode: ConceptNode };

function layoutNodes(nodes, edges, width, height) {
  if (nodes.length === 0) return nodes;

  // Copy nodes with positions
  const positioned = nodes.map(n => ({ ...n }));

  if (nodes.length === 1) {
    positioned[0].position = { x: width / 2 - 60, y: height / 2 - 20 };
    return positioned;
  }

  // Count connections per node for weighted layout
  const connCount = {};
  for (const n of nodes) {
    connCount[n.id] = 0;
  }
  for (const e of edges) {
    if (connCount[e.source] !== undefined) connCount[e.source]++;
    if (connCount[e.target] !== undefined) connCount[e.target]++;
  }

  // Sort by connection count (most connected = center)
  const sorted = [...nodes].sort((a, b) => (connCount[b.id] || 0) - (connCount[a.id] || 0));
  const centerId = sorted[0]?.id;

  // Group by type for visual clustering
  const byType = {};
  for (const n of nodes) {
    const t = n.data?.type || 'concept';
    if (!byType[t]) byType[t] = [];
    byType[t].push(n.id);
  }

  const typeKeys = Object.keys(byType);
  const typeAngleStep = (2 * Math.PI) / typeKeys.length;

  const placed = new Set();

  // Center node
  if (centerId) {
    const node = positioned.find(n => n.id === centerId);
    if (node) {
      node.position = { x: width / 2 - 60, y: height / 2 - 20 };
      placed.add(centerId);
    }
  }

  // Place other nodes in type-based rings
  const ringRadius = Math.min(width, height) * 0.35;
  let nodeIdx = 0;

  for (let ti = 0; ti < typeKeys.length; ti++) {
    const type = typeKeys[ti];
    const typeNodes = byType[type].filter(id => id !== centerId);
    const angleBase = ti * typeAngleStep;
    const nodeAngleStep = (typeAngleStep * 0.7) / Math.max(typeNodes.length, 1);

    typeNodes.forEach((id, ni) => {
      const node = positioned.find(n => n.id === id);
      if (!node || placed.has(id)) return;
      const angle = angleBase + ni * nodeAngleStep;
      const r = ringRadius + (connCount[id] || 0) * 8;
      node.position = {
        x: width / 2 + Math.cos(angle) * r - 60,
        y: height / 2 + Math.sin(angle) * r - 20,
      };
      placed.add(id);
    });
    nodeIdx++;
  }

  // Place any remaining nodes
  let fallbackIdx = 0;
  for (const n of positioned) {
    if (!placed.has(n.id)) {
      const angle = fallbackIdx * 0.5;
      n.position = {
        x: width / 2 + Math.cos(angle) * (ringRadius + 100) - 60,
        y: height / 2 + Math.sin(angle) * (ringRadius + 100) - 20,
      };
      placed.add(n.id);
      fallbackIdx++;
    }
  }

  return positioned;
}

export default function KnowledgeGraphCanvas({ nodes, edges, onNodeClick }) {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [initialized, setInitialized] = useState(false);

  const { rfNodesInitial, rfEdgesInitial } = useMemo(() => {
    if (!nodes || nodes.length === 0) return { rfNodesInitial: [], rfEdgesInitial: [] };

    const connCount = {};
    for (const n of nodes) connCount[n.id] = 0;
    for (const e of edges || []) {
      if (connCount[e.source] !== undefined) connCount[e.source]++;
      if (connCount[e.target] !== undefined) connCount[e.target]++;
    }

    const rfNodesInit = nodes.map(n => ({
      id: n.id,
      type: 'conceptNode',
      data: {
        label: n.name,
        type: n.type || n.concept_type,
        connectionCount: connCount[n.id] || 0,
        raw: n,
      },
      position: { x: 0, y: 0 },
    }));

    const rfEdgesInit = (edges || []).map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#6b7280', strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#6b7280' },
      label: e.type || '',
      labelStyle: { fill: '#9ca3af', fontSize: 10 },
    }));

    return { rfNodesInitial: rfNodesInit, rfEdgesInitial: rfEdgesInit };
  }, [nodes, edges]);

  const onInit = useCallback(
    (reactFlowInstance) => {
      if (initialized || rfNodesInitial.length === 0) return;
      const { width, height } = reactFlowInstance.getViewport();
      const viewportW = document.querySelector('.react-flow')?.clientWidth || 600;
      const viewportH = document.querySelector('.react-flow')?.clientHeight || 400;
      const positioned = layoutNodes(rfNodesInitial, rfEdgesInitial, viewportW, viewportH);
      setRfNodes(positioned);
      setRfEdges(rfEdgesInitial);
      setInitialized(true);
      setTimeout(() => reactFlowInstance.fitView({ padding: 0.2 }), 50);
    },
    [rfNodesInitial, rfEdgesInitial, initialized, setRfNodes, setRfEdges]
  );

  const onNodeClickHandler = useCallback(
    (_, node) => {
      onNodeClick?.(node.data?.raw || node.data);
    },
    [onNodeClick]
  );

  if (!nodes || nodes.length === 0) return null;

  return (
    <div className="w-full h-full bg-gray-950 overflow-hidden">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onInit={onInit}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2.5}
        attributionPosition="bottom-left"
      >
        <Background color="#374151" gap={20} />
        <Controls className="!bg-gray-900 !border-gray-700 [&_button]:!text-gray-400 [&_button]:!border-gray-700 [&_button:hover]:!bg-gray-800" />
        <MiniMap
          nodeColor={(n) => {
            const colors = {
              concept: '#3b82f6', fact: '#22c55e', skill: '#a855f7',
              question: '#eab308', entity: '#06b6d4',
            };
            return colors[n.data?.type?.toLowerCase()] || '#6b7280';
          }}
          maskColor="rgba(0,0,0,0.7)"
          className="!bg-gray-900 !border-gray-700"
        />
      </ReactFlow>
    </div>
  );
}
