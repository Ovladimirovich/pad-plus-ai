import { useState, useEffect, useRef } from 'react';
import RunsTab from './research/RunsTab';
import CompareTab from './research/CompareTab';
import TracesTab from './research/TracesTab';
import XRayDashboardTab from './research/XRayDashboardTab';
import MetricsTab from './research/MetricsTab';
import EvalTab from './research/EvalTab';
import RegistryTab from './research/RegistryTab';
import DecisionsTab from './research/DecisionsTab';
import MicroscopeTab from './research/MicroscopeTab';
import ProvidersCompareTab from './research/ProvidersCompareTab';
import ResearchHeader from './research/ResearchHeader';

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-lg text-sm transition-colors ${
        active
          ? 'bg-primary text-white'
          : 'text-text-secondary hover:text-text-primary hover:bg-gray-800'
      }`}
    >
      {children}
    </button>
  );
}

const TABS = [
  { id: 'microscope', label: '🔬 Microscope' },
  { id: 'runs', label: '▶ Experiments' },
  { id: 'compare', label: '⇄ Comparisons' },
  { id: 'providers', label: '🏢 Providers' },
  { id: 'decisions', label: '🔍 Decisions' },
  { id: 'xray', label: '🔬 Live' },
  { id: 'metrics', label: '📈 System' },
  { id: 'eval', label: '🏆 Scores' },
  { id: 'pipeline', label: '⚙ Registry' },
];

export default function ResearchPage({ navParams = {} }) {
  const [tab, setTab] = useState(
    navParams.microscope ? 'microscope' : (navParams.component ? 'decisions' : 'microscope')
  );

  // При изменении navParams (hash-навигация) переключаемся на нужную вкладку
  useEffect(() => {
    if (navParams.microscope) setTab('microscope');
    else if (navParams.component) setTab('decisions');
  }, [navParams]);

  return (
    <div className="p-4 max-w-7xl mx-auto h-[calc(100vh-120px)] flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-xl font-bold text-text-primary">Research Platform</h2>
        <span className="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary">v2.0</span>
      </div>

      <ResearchHeader />

      <div className="flex gap-1 mb-3 border-b border-border pb-2 overflow-x-auto">
        {TABS.map((t) => (
          <TabButton key={t.id} active={tab === t.id} onClick={() => setTab(t.id)}>
            {t.label}
          </TabButton>
        ))}
      </div>

      <div className="flex-1 overflow-hidden">
        {tab === 'microscope' && <MicroscopeTab navParams={navParams} />}
        {tab === 'runs' && <RunsTab />}
        {tab === 'compare' && <CompareTab />}
        {tab === 'providers' && <ProvidersCompareTab />}
        {tab === 'decisions' && <DecisionsTab initialComponent={navParams.component || ''} since={navParams.since || ''} />}
        {tab === 'xray' && <XRayDashboardTab />}
        {tab === 'metrics' && <MetricsTab />}
        {tab === 'eval' && <EvalTab />}
        {tab === 'pipeline' && <RegistryTab />}
      </div>
    </div>
  );
}
