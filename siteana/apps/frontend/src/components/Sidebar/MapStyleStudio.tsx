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
    roadColors: { highway: '#9ca3af', primary: '#d1d5db', secondary: '#e5e7eb', residential: '#f3f4f6', path: '#f9fafb' },
    buildingColor: '#333333', buildingOpacity: 1.0, building3D: true, buildingVisibility: true,
    landUseColors: { residential: '#e5e7eb', commercial: '#e5e7eb', park: '#d1d5db', water: '#cbd5e1', industrial: '#e5e7eb' },
    backgroundColor: '#f3f4f6', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '量體感：強調建築與街廓的虛實關係'
  },
  ecological_texture: {
    roadColors: { highway: '#e5e7eb', primary: '#f3f4f6', secondary: '#f9fafb', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#d6d3d1', buildingOpacity: 0.4, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#fafaf9', commercial: '#fafaf9', park: '#166534', water: '#1e3a8a', industrial: '#fafaf9' },
    backgroundColor: '#fdfbf7', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '生命力：將藍綠帶色彩極大化'
  },
  traffic_hierarchy: {
    roadColors: { highway: '#ff5500', primary: '#f97316', secondary: '#cbd5e1', residential: '#e2e8f0', path: '#f1f5f9' },
    buildingColor: '#e2e8f0', buildingOpacity: 0.4, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#f8fafc', water: '#f1f5f9', industrial: '#ffffff' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '流動性：利用色彩區分路網層級'
  },
  blueprint_tech: {
    roadColors: { highway: '#e0f2fe', primary: '#bae6fd', secondary: '#7dd3fc', residential: '#38bdf8', path: '#e0f2fe' },
    buildingColor: '#ffffff', buildingOpacity: 0.8, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#003366', commercial: '#003366', park: '#004080', water: '#002244', industrial: '#003366' },
    backgroundColor: '#003366', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '製圖感：經典青曬圖 (Cyanotype) 視覺'
  },
  soft_site: {
    roadColors: { highway: '#e5e7eb', primary: '#f3f4f6', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#ffffff', buildingOpacity: 0.9, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#fdf8f5', commercial: '#fdf8f5', park: '#dcfce7', water: '#bae6fd', industrial: '#fdf8f5' },
    backgroundColor: '#fdf8f5', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '空氣感：低飽和度、高亮度的底圖'
  },
  architectural_grey: {
    roadColors: { highway: '#444444', primary: '#555555', secondary: '#666666', residential: '#888888', path: '#aaaaaa' },
    buildingColor: '#ffffff', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#cccccc', commercial: '#cccccc', park: '#a3b18a', water: '#778da9', industrial: '#cccccc' },
    backgroundColor: '#eeeeee', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '標準化：類似專業 CAD 導出的配置圖'
  },
  architectural_line: {
    roadColors: { highway: '#d3d3d3', primary: '#e0e0e0', secondary: '#ebebeb', residential: '#f5f5f5', path: '#fafafa' },
    buildingColor: '#ffffff', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#ffffff', water: '#ffffff', industrial: '#ffffff' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '抽象化：無色彩，僅靠線條傳達空間'
  },
  figure_ground: {
    roadColors: { highway: '#ffffff', primary: '#ffffff', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#000000', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#ffffff', water: '#ffffff', industrial: '#ffffff' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '對比度：極端黑白，用於空間型態分析'
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
                  <span className="text-[11px] text-slate-600 font-medium">顯示建築圖層</span>
                  <input 
                    type="checkbox" 
                    checked={paintStore.buildingVisibility}
                    onChange={(e) => paintStore.setBuildingStyles({ buildingVisibility: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
               </div>
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
