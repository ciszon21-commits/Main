import React, { useState } from 'react';
import { useStore, DEFAULT_STYLES } from '../../store/useStore';
import { useMapPaintStore, MapPaintState } from '../../store/useMapPaintStore';
import { 
  Layers, 
  Palette, 
  Settings2, 
  CloudSun, 
  Type, 
  Droplet, 
  Trees, 
  Zap,
  Check,
  ChevronRight,
  Plus,
  Navigation,
  Car,
  Home,
  Tags
} from 'lucide-react';

const PRESETS: Record<string, Partial<MapPaintState> & { description: string }> = {
  urban_density: {
    roadColors: { highway: '#334155', primary: '#475569', secondary: '#64748b', residential: '#94a3b8', path: '#cbd5e1' },
    buildingColor: '#f97316', buildingOpacity: 0.9, building3D: true,
    landUseColors: { residential: '#f1f5f9', commercial: '#f1f5f9', park: '#f8fafc', water: '#e2e8f0', industrial: '#f1f5f9' },
    backgroundColor: '#cbd5e1', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Analysis: Urban Density & Built Environment'
  },
  ecological_texture: {
    roadColors: { highway: '#cbd5e1', primary: '#e2e8f0', secondary: '#f1f5f9', residential: '#f8fafc', path: '#f8fafc' },
    buildingColor: '#ffffff', buildingOpacity: 0.3, building3D: false,
    landUseColors: { residential: '#f8fafc', commercial: '#f8fafc', park: '#22c55e', water: '#3b82f6', industrial: '#f8fafc' },
    backgroundColor: '#f1f5f9', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Analysis: Ecological Network & Green-Blue Infrastructure'
  },
  traffic_hierarchy: {
    roadColors: { highway: '#ef4444', primary: '#fb923c', secondary: '#facc15', residential: '#94a3b8', path: '#cbd5e1' },
    buildingColor: '#e2e8f0', buildingOpacity: 1.0, building3D: false,
    landUseColors: { residential: '#f8fafc', commercial: '#f8fafc', park: '#f1f5f9', water: '#f1f5f9', industrial: '#f8fafc' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Analysis: Transportation Network & Accessibility'
  },
  blueprint_tech: {
    roadColors: { highway: '#ffffff', primary: '#ffffff', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#60a5fa', buildingOpacity: 0.6, building3D: true,
    landUseColors: { residential: '#1e3a8a', commercial: '#1e3a8a', park: '#1e3a8a', water: '#1e3a8a', industrial: '#1e3a8a' },
    backgroundColor: '#1e3a8a', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Technical: Scientific Blueprint & Engineering'
  },
  soft_site: {
    roadColors: { highway: '#d4a373', primary: '#e9edc9', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#ffedd5', buildingOpacity: 0.8, building3D: true,
    landUseColors: { residential: '#fefae0', commercial: '#fefae0', park: '#dcfce7', water: '#e0f2fe', industrial: '#fefae0' },
    backgroundColor: '#fff7ed', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Tone: Warm & Soft Preliminary Sketch'
  },
  architectural_grey: {
    roadColors: { highway: '#8d99ae', primary: '#adb5bd', secondary: '#ced4da', residential: '#e9ecef', path: '#f8f9fa' },
    buildingColor: '#6c757d', buildingOpacity: 0.6, building3D: false,
    landUseColors: { residential: '#dee2e6', commercial: '#e9ecef', park: '#ced4da', water: '#adb5bd', industrial: '#dee2e6' },
    backgroundColor: '#f1f3f5', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Tone: Professional Architectural Grey'
  },
  night_render: {
    roadColors: { highway: '#fca311', primary: '#e5e5e5', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#14213d', buildingOpacity: 0.9, building3D: true,
    landUseColors: { residential: '#000000', commercial: '#14213d', park: '#0a1d08', water: '#001219', industrial: '#1b1b1b' },
    backgroundColor: '#000000', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Visual: High-Contrast Night Presentation'
  },
  clean_analysis: {
    roadColors: { highway: '#ffffff', primary: '#ffffff', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#e2e8f0', buildingOpacity: 0.6, building3D: true,
    landUseColors: { residential: '#f8fafc', commercial: '#f8fafc', park: '#dcfce7', water: '#e0f2fe', industrial: '#f8fafc' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: 'Base: Completely Clean Map without Labels'
  }
};

const MapStyleStudio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'basemap' | 'layers' | 'presets'>('basemap');
  const { stylePresets, selectedStyle, setSelectedStyle } = useStore();
  const paintStore = useMapPaintStore();

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Tabs Header */}
      <div className="flex bg-slate-100 p-1 rounded-xl">
        {(['basemap', 'layers', 'presets'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all ${
              activeTab === tab 
                ? 'bg-white text-brand-600 shadow-sm' 
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab === 'basemap' && <Layers size={12} />}
            {tab === 'layers' && <Settings2 size={12} />}
            {tab === 'presets' && <Palette size={12} />}
            {tab}
          </button>
        ))}
      </div>

      {/* Tab 1: Basemaps */}
      {activeTab === 'basemap' && (
        <div className="grid grid-cols-2 gap-2">
          {stylePresets.map((style) => (
            <button
              key={style.id}
              onClick={() => setSelectedStyle(style)}
              className={`group flex flex-col gap-2 p-2.5 rounded-xl border transition-all ${
                selectedStyle?.id === style.id
                  ? 'bg-white border-brand-500 shadow-md ring-2 ring-brand-50'
                  : 'bg-slate-50 border-slate-100 hover:bg-white hover:border-slate-200'
              }`}
            >
               <div className="aspect-video bg-slate-200 rounded-lg overflow-hidden relative">
                  {/* Pseudo preview colors */}
                  <div className={`absolute inset-0 opacity-40`} style={{ backgroundColor: style.id === 'minimal-dark' ? '#1a1a1a' : '#f8f4f0' }} />
                  <div className="absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-40 transition-opacity">
                    <Layers size={24} />
                  </div>
                  {selectedStyle?.id === style.id && (
                    <div className="absolute top-1 right-1 bg-brand-500 text-white rounded-full p-0.5 shadow-sm">
                      <Check size={10} />
                    </div>
                  )}
               </div>
               <div className="flex flex-col text-left">
                  <span className={`text-[11px] font-bold truncate ${selectedStyle?.id === style.id ? 'text-brand-600' : 'text-slate-700'}`}>
                    {style.name}
                  </span>
                  <span className="text-[9px] text-slate-400 uppercase">{style.type}</span>
               </div>
            </button>
          ))}
        </div>
      )}

      {/* Tab 2: Layers */}
      {activeTab === 'layers' && (
        <div className="space-y-5 px-1 py-1 custom-scrollbar max-h-[400px] overflow-y-auto">
          {/* Section: Roads */}
          <div className="space-y-3">
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <ChevronRight size={10} /> 道路系統
            </h4>
            <div className="grid grid-cols-1 gap-2.5 pl-2">
               {[
                 { key: 'highway', icon: Navigation, label: '高速公路' },
                 { key: 'primary', icon: Car, label: '主要幹道' },
                 { key: 'residential', icon: Home, label: '生活街道' }
               ].map(({ key, icon: Icon, label }) => (
                 <div key={key} className="flex items-center justify-between gap-4">
                    <span className="flex items-center gap-2 text-[11px] text-slate-600 font-medium">
                       <Icon size={12} className="text-slate-400" />
                       {label}
                    </span>
                    <input 
                      type="color" 
                      value={(paintStore.roadColors as any)[key]} 
                      onChange={(e) => paintStore.setRoadColor(key as any, e.target.value)}
                      className="w-8 h-6 rounded border border-slate-200 cursor-pointer overflow-hidden p-0"
                    />
                 </div>
               ))}
            </div>
          </div>

          {/* Section: Buildings */}
          <div className="space-y-3">
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <ChevronRight size={10} /> 建築物
            </h4>
            <div className="space-y-3 pl-2">
               <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-600 font-medium">填色</span>
                  <input 
                    type="color" 
                    value={paintStore.buildingColor} 
                    onChange={(e) => paintStore.setBuildingStyles({ buildingColor: e.target.value })}
                    className="w-8 h-6 rounded border border-slate-200"
                  />
               </div>
               <div className="space-y-1">
                  <div className="flex justify-between text-[11px] text-slate-600">
                    <span>透明度</span>
                    <span>{Math.round(paintStore.buildingOpacity * 100)}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="1" step="0.1" 
                    value={paintStore.buildingOpacity}
                    onChange={(e) => paintStore.setBuildingStyles({ buildingOpacity: parseFloat(e.target.value) })}
                    className="w-full accent-brand-500 h-1 bg-slate-200 rounded-lg cursor-pointer"
                  />
               </div>
               <label className="flex items-center gap-3 cursor-pointer group">
                  <input 
                    type="checkbox" 
                    checked={paintStore.building3D}
                    onChange={(e) => paintStore.setBuildingStyles({ building3D: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span className="text-[11px] text-slate-600 group-hover:text-slate-900 transition-colors">啟用 3D 立體陰影</span>
               </label>
            </div>
          </div>

          {/* Section: Land Use */}
          <div className="space-y-3">
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <ChevronRight size={10} /> 街廓與綠地
            </h4>
            <div className="grid grid-cols-1 gap-2.5 pl-2">
               {Object.entries({ park: '公園綠地', water: '水體系統', residential: '住宅街廓', commercial: '商業中心' }).map(([key, label]) => (
                 <div key={key} className="flex items-center justify-between gap-4">
                    <span className="text-[11px] text-slate-600 font-medium">{label}</span>
                    <input 
                      type="color" 
                      value={(paintStore.landUseColors as any)[key]} 
                      onChange={(e) => paintStore.setLandUseColor(key as any, e.target.value)}
                      className="w-8 h-6 rounded border border-slate-200 pointer-events-auto"
                    />
                 </div>
               ))}
            </div>
          </div>

          {/* Section: Labels */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <ChevronRight size={10} /> 地圖標籤顯示控制
              </h4>
              <button 
                onClick={() => {
                  const currentAnyOn = Object.values(paintStore.labelVisibility).some(v => v);
                  const nextState = !currentAnyOn;
                  paintStore.setLabelStyles({
                    labelVisibility: {
                      road: nextState, park: nextState, water: nextState, poi: nextState
                    }
                  });
                }}
                className="text-[9px] font-bold text-brand-500 hover:text-brand-600 flex items-center gap-1"
              >
                <Tags size={10} /> 全開/全關
              </button>
            </div>
            <div className="grid grid-cols-2 gap-y-2 gap-x-4 pl-2">
               {Object.entries({
                 road: '道路街道',
                 park: '公園綠地',
                 water: '水系水體',
                 poi: '設施地標'
               }).map(([key, label]) => (
                 <label key={key} className="flex items-center justify-between cursor-pointer group">
                    <span className="text-[11px] text-slate-600 group-hover:text-slate-900 transition-colors">{label}</span>
                    <input 
                      type="checkbox" 
                      checked={(paintStore.labelVisibility as any)[key]}
                      onChange={(e) => paintStore.setLabelStyles({ 
                        labelVisibility: { ...paintStore.labelVisibility, [key]: e.target.checked } 
                      })}
                      className="w-3.5 h-3.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                 </label>
               ))}
            </div>
          </div>

          {/* Section: Global */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
             <button 
               onClick={paintStore.resetToDefault}
               className="w-full py-2 border border-slate-200 rounded-lg text-slate-500 text-[10px] font-bold uppercase hover:bg-slate-50 transition-colors"
             >
               重設為原廠建議
             </button>
          </div>
        </div>
      )}

      {/* Tab 3: Presets */}
      {activeTab === 'presets' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-2.5">
            {Object.entries(PRESETS).map(([id, preset]) => (
              <button
                key={id}
                onClick={() => paintStore.applyPreset(id, preset)}
                className="group w-full flex items-center gap-4 p-3 bg-white border border-slate-100 rounded-xl hover:border-brand-300 hover:shadow-md transition-all text-left"
              >
                <div 
                  className="w-12 h-12 rounded-lg shrink-0 border border-slate-100 flex items-center justify-center p-1"
                  style={{ backgroundColor: preset.backgroundColor || '#fff' }}
                >
                  <div className="w-full h-full flex flex-col gap-0.5 opacity-60">
                    <div className="h-2 w-full rounded-sm" style={{ backgroundColor: preset.roadColors?.primary || '#ddd' }} />
                    <div className="h-4 w-4 rounded-sm mx-auto" style={{ backgroundColor: preset.buildingColor || '#ccc' }} />
                    <div className="h-1.5 w-full mt-auto rounded-sm" style={{ backgroundColor: preset.landUseColors?.park || '#eee', opacity: 0.5 }} />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] font-bold text-slate-800 uppercase tracking-tight">{id.replace('_', ' ')}</div>
                  <div className="text-[9px] text-slate-400 truncate">{preset.description}</div>
                </div>
                <ChevronRight size={14} className="text-slate-300 group-hover:text-brand-500 transform group-hover:translate-x-0.5 transition-all" />
              </button>
            ))}
          </div>

          <div className="pt-4 px-1">
            <button className="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed border-slate-200 rounded-xl text-slate-400 text-[10px] font-bold uppercase hover:border-brand-200 hover:text-brand-400 transition-all">
              <Plus size={14} /> 儲存目前樣式為自訂預設
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapStyleStudio;
