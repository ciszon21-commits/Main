import { useState } from 'react';
import ProjectList, { SiteList } from './components/Sidebar/ProjectList';
import SiteDetails from './components/Sidebar/SiteDetails';
import Map from './components/Map/Map';
import MapStyleStudio from './components/Sidebar/MapStyleStudio';
import UnifiedExportPanel from './components/Sidebar/UnifiedExportPanel';
import AnalysisPanel from './components/Sidebar/AnalysisPanel';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';

const SectionHeader: React.FC<{ en: string, cn: string }> = ({ en, cn }) => (
  <div className="flex flex-col mb-4 px-1">
    <span className="text-[10px] font-black text-brand-600/60 uppercase tracking-[0.3em] leading-none mb-1">{en}</span>
    <h3 className="text-sm font-bold text-slate-800 tracking-tight">{cn}</h3>
  </div>
);

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 transition-colors duration-300">

      {/* Sidebar */}
      <aside
        className={`h-full border-r bg-white shadow-sm z-10 flex flex-col${sidebarOpen ? ' w-80' : ' sidebar-collapsed'}`}
      >
        {/* Logo Header */}
        <header className="p-5 border-b flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white font-bold text-lg shadow-sm transition-colors duration-300">S</div>
            <div>
              <h1 className="text-base font-bold tracking-tight leading-tight">SiteANA</h1>
              <p className="text-[10px] text-slate-400 font-medium leading-none">Design-oriented Web GIS</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="收合側邊欄"
          >
            <PanelLeftClose size={16} />
          </button>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-3 py-4 custom-scrollbar space-y-8">

          {/* PROJECT & SITE */}
          <div className="sidebar-section px-1 animate-slide-up">
            <ProjectList />
            <SiteList />
          </div>

          {/* VISUAL ENGINE (Priority Move) */}
          <div className="sidebar-section px-1 animate-slide-up" style={{ animationDelay: '50ms' }}>
            <SectionHeader en="VISUAL ENGINE" cn="視覺風格工作坊" />
            <MapStyleStudio />
          </div>

          {/* SPATIAL ANALYSIS */}
          <div className="sidebar-section px-1 animate-slide-up" style={{ animationDelay: '100ms' }}>
            <SectionHeader en="SPATIAL ANALYTICS" cn="空間分析引擎" />
            <AnalysisPanel />
          </div>

          {/* EXPORT STUDIO */}
          <div className="sidebar-section px-1 animate-slide-up" style={{ animationDelay: '150ms' }}>
            <SectionHeader en="EXPORT STUDIO" cn="分析報表中心" />
            <UnifiedExportPanel />
          </div>

          {/* SITE DETAILS */}
          <div className="sidebar-section px-1 animate-slide-up" style={{ animationDelay: '200ms' }}>
            <SectionHeader en="SITE METADATA" cn="基地數據細覽" />
            <SiteDetails />
          </div>
        </div>

        {/* Footer */}
        <footer className="px-4 py-3 border-t bg-slate-50 shrink-0">
          <div className="text-[9px] text-slate-400 font-mono flex justify-between">
            <span>v0.9.0-alpha · Phase 9</span>
            <span>SiteANA Studio</span>
          </div>
        </footer>
      </aside>

      {/* Sidebar Toggle Button (when collapsed) */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="absolute left-3 top-4 z-30 p-2 glass-panel rounded-lg text-slate-600 hover:text-brand-600 transition-colors shadow-md"
          title="展開側邊欄"
        >
          <PanelLeftOpen size={18} />
        </button>
      )}

      {/* Main Map */}
      <main className="flex-1 relative">
        <Map />
      </main>
    </div>
  );
}

export default App;
