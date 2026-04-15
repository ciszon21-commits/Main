import { useState } from 'react';
import ProjectList from './components/Sidebar/ProjectList';
import Map from './components/Map/Map';
import MapStyleStudio from './components/Sidebar/MapStyleStudio';
import UnifiedExportPanel from './components/Sidebar/UnifiedExportPanel';
import AnalysisPanel from './components/Sidebar/AnalysisPanel';
import SunlightPanel from './components/Sidebar/SunlightPanel';
import { PanelLeftClose, PanelLeftOpen, Sun, Activity, TreePine, Box, ChevronRight, Sparkles } from 'lucide-react';
import LoadingScreen from './components/UI/LoadingScreen';
import { useStore } from './store/useStore';
import { useMapPaintStore } from './store/useMapPaintStore';
import { MapPaintEngine } from './engine/MapPaintEngine';
import { useEffect } from 'react';

const SectionHeader: React.FC<{ en: string, cn: string, color?: string }> = ({ en, cn, color = 'brand' }) => {
  const colorMap: Record<string, string> = {
    brand: 'text-brand-600/60 bg-brand-50/50',
    blue: 'text-blue-600/60 bg-blue-50/50',
    emerald: 'text-emerald-600/60 bg-emerald-50/50',
    amber: 'text-amber-600/60 bg-amber-50/50',
    slate: 'text-slate-600/60 bg-slate-50/50',
  };
  
  const dotColorMap: Record<string, string> = {
    brand: 'bg-brand-500',
    blue: 'bg-blue-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    slate: 'bg-slate-500',
  };

  return (
    <div className="flex flex-col mb-4 px-1 group">
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className={`w-1 h-3 rounded-full ${dotColorMap[color] || dotColorMap.brand} transition-all group-hover:h-5`} />
        <span className={`text-[10px] font-black uppercase tracking-[0.3em] leading-none px-2 py-0.5 rounded-md ${colorMap[color] || colorMap.brand}`}>
          {en}
        </span>
      </div>
      <h3 className="text-sm font-bold text-slate-800 tracking-tight pl-0.5">{cn}</h3>
    </div>
  );
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeModule, setActiveModule] = useState<'sunlight' | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [showLoader, setShowLoader] = useState(true);
  const { hasHydrated: hasPaintHydrated, activePresetId } = useMapPaintStore();
  const { hasHydrated: hasStoreHydrated, selectedStyle } = useStore();

  // [PRECISION FIX] Ensure presets are applied when both map and storage are ready
  // Also reacts to preset changes (activePresetId) to immediately apply paint
  useEffect(() => {
    if (!isMapReady) return;
    const map = (window as any).map;
    if (!map) return;

    console.log('[App] Paint sync triggered. Preset:', activePresetId);
    MapPaintEngine.applyAll(map, useMapPaintStore.getState());

    // [BRUTE FORCE] Re-inject after a short delay to catch layers that finish loading after the initial call
    const timer = setTimeout(() => {
       MapPaintEngine.applyAll(map, useMapPaintStore.getState());
    }, 800);

    return () => clearTimeout(timer);
  }, [isMapReady, hasPaintHydrated, hasStoreHydrated, selectedStyle, activePresetId]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 transition-colors duration-300">
      {showLoader && (
        <LoadingScreen 
          isMapReady={isMapReady} 
          isPaintHydrated={hasPaintHydrated && hasStoreHydrated}
          onLoadingComplete={() => setShowLoader(false)} 
        />
      )}

      {/* Sidebar */}
      <aside
        className={`h-full border-r bg-white shadow-sm z-10 flex flex-col transition-all duration-300 ${sidebarOpen ? 'w-80' : 'w-0 border-none'}`}
      >
        {/* Logo Header */}
        <header className="p-5 border-b flex items-center justify-between shrink-0 bg-white/80 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white font-bold text-lg shadow-sm">S</div>
            <div>
              <h1 className="text-base font-bold tracking-tight leading-tight">SiteANA</h1>
              <p className="text-[10px] text-slate-400 font-medium leading-none">Design-oriented Web GIS</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
            title="收合側邊欄"
          >
            <PanelLeftClose size={16} />
          </button>
        </header>

        {/* Scrollable Content */}
        <div className={`flex-1 overflow-y-auto px-4 py-6 custom-scrollbar space-y-10 transition-opacity duration-200 ${sidebarOpen ? 'opacity-100' : 'opacity-0'}`}>

          {/* 1. VISUAL ENGINE */}
          <div className="sidebar-section px-1 animate-slide-up pb-8 border-b border-slate-50">
            <SectionHeader en="VISUAL ENGINE" cn="視覺風格工作坊" color="blue" />
            <MapStyleStudio />
          </div>

          {/* 2. SPATIAL ANALYSIS */}
          <div className="sidebar-section px-1 animate-slide-up pb-8 border-b border-slate-50" style={{ animationDelay: '50ms' }}>
            <SectionHeader en="SPATIAL ANALYTICS" cn="空間分析引擎" color="emerald" />
            <AnalysisPanel />
          </div>

          {/* 3. PROJECTS */}
          <div className="sidebar-section px-1 animate-slide-up pb-8 border-b border-slate-50" style={{ animationDelay: '100ms' }}>
            <ProjectList />
          </div>

          {/* 4. ADVANCED MODULES */}
          <div className="sidebar-section px-1 animate-slide-up pb-8 border-b border-slate-50" style={{ animationDelay: '150ms' }}>
            <SectionHeader en="ADVANCED MODULES" cn="進階分析模組" color="amber" />
            
            <div className="grid grid-cols-2 gap-2 mb-4">
              <button 
                onClick={() => setActiveModule(activeModule === 'sunlight' ? null : 'sunlight')}
                className={`group relative flex flex-col items-center gap-2 p-3 rounded-xl border transition-all ${
                  activeModule === 'sunlight' 
                  ? 'border-orange-200 bg-orange-50 ring-2 ring-orange-100' 
                  : 'border-slate-200 bg-white hover:border-orange-200 hover:bg-orange-50/50'
                } text-center shadow-sm`}
              >
                <div className={`p-2 rounded-lg ${activeModule === 'sunlight' ? 'bg-orange-500 text-white' : 'bg-orange-50 text-orange-500'}`}>
                  <Sun size={18} />
                </div>
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-slate-700">日照微氣候</span>
                  <span className="text-[9px] opacity-70 uppercase text-slate-400">Solar Analysis</span>
                </div>
                {activeModule === 'sunlight' && (
                  <div className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                )}
              </button>
              
              <button disabled className="group relative flex flex-col items-center gap-2 p-3 rounded-xl border border-slate-200 bg-slate-50/50 text-center cursor-not-allowed opacity-40">
                <Activity size={18} className="text-blue-500" />
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-slate-600">都市可及性</span>
                  <span className="text-[9px] opacity-70 uppercase text-slate-400">Isochrone</span>
                </div>
              </button>

              <button disabled className="group relative flex flex-col items-center gap-2 p-3 rounded-xl border border-slate-200 bg-slate-50/50 text-center cursor-not-allowed opacity-40">
                <TreePine size={18} className="text-emerald-500" />
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-slate-600">綠化指數</span>
                  <span className="text-[9px] opacity-70 uppercase text-slate-400">NDVI / Green</span>
                </div>
              </button>

              <button disabled className="group relative flex flex-col items-center gap-2 p-3 rounded-xl border border-slate-200 bg-slate-50/50 text-center cursor-not-allowed opacity-40">
                <Box size={18} className="text-sky-400" />
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-slate-600">參數化量體</span>
                  <span className="text-[9px] opacity-70 uppercase text-slate-400">Massing</span>
                </div>
              </button>
            </div>

            {/* Active Module Panel */}
            {activeModule === 'sunlight' && (
              <div className="px-1 py-1 bg-slate-50/50 rounded-2xl border border-slate-100">
                <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Sparkles size={12} className="text-orange-500" />
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Analysis</span>
                  </div>
                </div>
                <div className="p-1">
                  <SunlightPanel />
                </div>
              </div>
            )}
          </div>

          {/* 5. EXPORT STUDIO */}
          <div className="sidebar-section px-1 animate-slide-up pb-12" style={{ animationDelay: '200ms' }}>
            <SectionHeader en="EXPORT STUDIO" cn="分析報表中心" color="slate" />
            <UnifiedExportPanel />
          </div>

        </div>

        <footer className="px-5 py-4 border-t bg-slate-50 shrink-0">
          <div className="text-[9px] text-slate-400 font-mono flex justify-between">
            <span>v0.14.0-preview · P13+</span>
            <span>SiteANA Studio</span>
          </div>
        </footer>
      </aside>

      {/* Sidebar Toggle Button (when collapsed) */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="absolute left-6 top-6 z-30 w-10 h-10 flex items-center justify-center glass-panel rounded-xl text-slate-600 hover:text-brand-600 transition-all shadow-xl border border-white/50"
          title="展開側邊欄"
        >
          <PanelLeftOpen size={20} />
        </button>
      )}

      {/* Main Map */}
      <main className="flex-1 relative">
        <Map onReady={() => setIsMapReady(true)} startIntro={!showLoader} />
      </main>
    </div>
  );
}

export default App;
