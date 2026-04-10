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
  // 1. 量體感 — 建築與街廓虛實
  urban_density: {
    roadColors: { highway: '#94a3b8', expressway: '#b0bec5', primary: '#cfd8dc', secondary: '#dde3e8', residential: '#ecf0f1', path: '#f5f5f5' },
    buildingColor: '#2d3748', buildingOutlineColor: '#4a5568', buildingOpacity: 0.95, building3D: true, buildingVisibility: true,
    landUseColors: { residential: '#f7fafc', commercial: '#f7fafc', park: '#e2e8f0', water: '#cbd5e1', industrial: '#f7fafc' },
    backgroundColor: '#f7fafc', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '量體感：強調建築與街廓的虛實關係'
  },
  // 2. 生態紋理 — 藍綠帶極大化
  ecological_texture: {
    roadColors: { highway: '#e8f5e9', expressway: '#f1f8e9', primary: '#f9fbe7', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#f1f5f2', buildingOutlineColor: '#c8e6c9', buildingOpacity: 0.5, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#86efac', water: '#60a5fa', industrial: '#ffffff', pedestrian: '#d1fae5' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '生命力：將藍綠帶色彩極大化'
  },
  // 3. 大眾運輸路網
  transit_network: {
    roadColors: { highway: '#e8eaf6', expressway: '#ede7f6', primary: '#f3e5f5', secondary: '#fce4ec', residential: '#f8fafc', path: '#f8fafc', transit_rail: '#374151', transit_mrt: '#008659' },
    buildingColor: '#f8fafc', buildingOutlineColor: '#e2e8f0', buildingOpacity: 0.35, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#f8fafc', commercial: '#f8fafc', park: '#f0fdf4', water: '#eff6ff', industrial: '#f8fafc' },
    backgroundColor: '#f8fafc', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '大眾運輸路網：台鐵深灰、高鐵橘色、捷運路線色'
  },
  // 4. 道路層級分析 (Google Maps 色系)
  road_hierarchy: {
    roadColors: {
      highway:     '#e63946', // 高速公路 — 鮮紅
      expressway:  '#f4a261', // 快速道路 — 橘橙
      primary:     '#f9c74f', // 省道/連外 — 橘黃
      secondary:   '#dee2e6', // 主要幹道 — 淺灰白
      residential: '#adb5bd', // 市區道路 — 中灰
      path:        '#ced4da', // 步道     — 淡灰
    },
    buildingColor: '#f8fafc', buildingOutlineColor: '#dee2e6', buildingOpacity: 0.35, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#f8fafc', commercial: '#f8fafc', park: '#f0fdf4', water: '#eff6ff', industrial: '#f8fafc' },
    backgroundColor: '#ffffff', labelVisibility: { road: true, park: false, water: false, poi: false },
    description: '道路層級：高速紅→快速橘→省道黃→幹道灰，Google Maps 風格'
  },
  // 5. 人流動線分析
  pedestrian_flow: {
    roadColors: {
      highway: '#f1f5f9', expressway: '#f1f5f9', primary: '#f1f5f9', secondary: '#f1f5f9', residential: '#f1f5f9',
      path:     '#f97316', // 人行道 — 橘黃
      overpass: '#a855f7', // 天橋/地下道/地下街 — 紫色
      crossing: '#facc15', // 斑馬線 — 亮黃
    },
    buildingColor: '#ffffff', buildingOutlineColor: '#cbd5e1', buildingOpacity: 0.8, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#f8fafc', commercial: '#f8fafc', park: '#bbf7d0', water: '#bfdbfe', industrial: '#f8fafc', parking: '#fef9c3', pedestrian: '#fed7aa' },
    backgroundColor: '#f8fafc', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '人流分析：人行道橘黃 / 天橋地下道紫 / 斑馬線黃'
  },
  // 6. 藍曬圖
  blueprint_tech: {
    roadColors: { highway: '#ffffff', expressway: '#e0f2fe', primary: '#bae6fd', secondary: '#7dd3fc', residential: '#38bdf8', path: '#0ea5e9' },
    buildingColor: '#012a4a', buildingOutlineColor: '#ffffff', buildingOpacity: 0.85, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#012a4a', commercial: '#012a4a', park: '#013a63', water: '#01497c', industrial: '#012a4a' },
    backgroundColor: '#012a4a', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '製圖感：經典青曬圖 (Cyanotype) 視覺'
  },
  // 7. 空氣感
  soft_site: {
    roadColors: { highway: '#cbd5e1', expressway: '#d4dce8', primary: '#e2e8f0', secondary: '#f1f5f9', residential: '#f8fafc', path: '#f8fafc' },
    buildingColor: '#faf8f5', buildingOutlineColor: '#cbd5e1', buildingOpacity: 0.3, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#faf8f5', commercial: '#faf8f5', park: '#ccfbf1', water: '#bae6fd', industrial: '#faf8f5' },
    backgroundColor: '#faf8f5', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '空氣感：低飽和度、高亮度的底圖'
  },
  // 8. 建築灰階
  architectural_grey: {
    roadColors: { highway: '#374151', expressway: '#4b5563', primary: '#6b7280', secondary: '#9ca3af', residential: '#d1d5db', path: '#e5e7eb' },
    buildingColor: '#ffffff', buildingOutlineColor: '#111827', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#e5e7eb', commercial: '#e5e7eb', park: '#d1d5db', water: '#9ca3af', industrial: '#e5e7eb' },
    backgroundColor: '#f3f4f6', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '標準化：類似專業 CAD 導出的配置圖'
  },
  // 9. 建築線稿
  architectural_line: {
    roadColors: { highway: '#9ca3af', expressway: '#d1d5db', primary: '#e5e7eb', secondary: '#f3f4f6', residential: '#f9fafb', path: '#f9fafb' },
    buildingColor: '#ffffff', buildingOutlineColor: '#111827', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#ffffff', water: '#f0f9ff', industrial: '#ffffff' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '抽象化：無色彩，僅靠線條傳達空間'
  },
  // 10. 圖底分析
  figure_ground: {
    roadColors: { highway: '#ffffff', expressway: '#ffffff', primary: '#ffffff', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
    buildingColor: '#111827', buildingOutlineColor: '#111827', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
    landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#ffffff', water: '#f0f9ff', industrial: '#ffffff' },
    backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
    description: '對比度：極端黑白，用於空間型態分析'
  }
};

const MapStyleStudio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'basemap' | 'layers' | 'presets'>('basemap');
  const { selectedStyle, setSelectedStyle } = useStore();
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
        <div className="space-y-5">
          {['Vector (向量可調)', 'Raster (像素底圖)', 'Historic (歷史圖繪)'].map(category => {
            const stylesInCategory = DEFAULT_STYLES.filter(s => s.category === category);
            if (stylesInCategory.length === 0) return null;
            return (
              <div key={category} className="space-y-2">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">{category}</h4>
                <div className="grid grid-cols-2 gap-2">
                  {stylesInCategory.map((style) => (
                    <button
                      key={style.id}
                      onClick={() => setSelectedStyle(style)}
                      className={`group flex flex-col gap-2 p-2.5 rounded-xl border transition-all ${
                        selectedStyle?.id === style.id
                          ? 'bg-white border-brand-500 shadow-md ring-2 ring-brand-50'
                          : 'bg-slate-50 border-slate-100 hover:bg-white hover:border-slate-200'
                      }`}
                    >
                      <div className="aspect-video bg-slate-200 rounded-lg overflow-hidden relative border border-slate-200/50">
                          {/* Pseudo preview pattern based on basemap classification */}
                          <div className={`absolute inset-0`} style={{ 
                             backgroundColor: 
                               style.id.includes('dark') ? '#1a202c' : 
                               style.id.includes('satellite') ? '#2f855a' : 
                               style.id.includes('historic') ? '#e6dfd1' : 
                               style.id.includes('bright') ? '#f0f9ff' :
                               style.id.includes('liberty') ? '#e2e8f0' : '#f8fafc' 
                          }} />
                          
                          {style.id.includes('dark') && <div className="absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-400 via-transparent to-transparent" />}
                          {style.id.includes('satellite') && <div className="absolute inset-x-0 bottom-0 h-1/2 bg-slate-900/40 backdrop-blur-[1px]" />}
                          {style.id.includes('historic') && <div className="absolute inset-0 opacity-10 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4IiBoZWlnaHQ9IjgiPgo8cmVjdCB3aWR0aD0iOCIgaGVpZ2h0PSI4IiBmaWxsPSIjZmZmIj48L3JlY3Q+CjxwYXRoIGQ9Ik0wIDBMODg4Wk04IDBMMCA4WiIgc3Ryb2tlPSIjMDAwIiBzdHJva2Utd2lkdGg9IjEuNSI+PC9wYXRoPgo8L3N2Zz4=')]"/>}
                          
                          {/* Abstract Map Line */}
                          <div className={`absolute top-0 bottom-0 left-[35%] w-1.5 transform -rotate-12 ${style.id.includes('satellite') ? 'bg-white/30' : style.id.includes('dark') ? 'bg-indigo-500/50' : style.id.includes('historic') ? 'bg-amber-900/20' : 'bg-slate-300'}`} />
                          <div className={`absolute top-[40%] right-0 left-[35%] h-1 transform rotate-6 ${style.id.includes('satellite') ? 'bg-white/20' : style.id.includes('dark') ? 'bg-indigo-400/30' : style.id.includes('historic') ? 'bg-amber-900/10' : 'bg-slate-200'}`} />
                          
                          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-white/20 backdrop-blur-[1.5px]">
                            <Layers size={20} className={style.id.includes('dark') || style.id.includes('satellite') ? 'text-white drop-shadow-md' : 'text-slate-700 drop-shadow-sm'} />
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
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
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
          {!selectedStyle?.supportsPresets ? (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex flex-col gap-2 items-center text-center text-amber-700 animate-fade-in">
               <span className="text-xl">⚠️</span>
               <span className="text-[11px] font-bold">目前底圖不支援樣式覆寫</span>
               <span className="text-[10px] opacity-80">由於像素底圖與歷史圖層的限制，無法更改個別建築或道路顏色。<br/><br/>請切換至「向量可調 (Vector)」分類的底圖，即可啟用進階渲染腳本。</span>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
            {Object.entries(PRESETS).map(([id, preset]) => {
              const isActive = paintStore.activePresetId === id;
              return (
              <button
                key={id}
                onClick={() => paintStore.applyPreset(id, preset)}
                className={`group flex flex-col p-2 bg-white rounded-xl transition-all text-left relative overflow-hidden ${
                  isActive 
                    ? 'border border-brand-400 bg-brand-50/50 shadow-md ring-1 ring-brand-500/20' 
                    : 'border border-slate-100 hover:border-brand-300 hover:shadow-md'
                }`}
              >
                {isActive && (
                  <div className="absolute top-1.5 right-1.5 z-10 bg-brand-500 text-white rounded-full p-1 shadow-sm">
                     <Check size={10} strokeWidth={3} />
                  </div>
                )}
                <div 
                  className="aspect-video w-full rounded-lg shrink-0 border border-slate-100 relative overflow-hidden mb-1.5"
                  style={{ backgroundColor: preset.backgroundColor || '#fff' }}
                >
                   <div className="absolute inset-0">
                     {/* Landuse Areas */}
                     <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full blur-[4px] opacity-80" style={{ backgroundColor: preset.landUseColors?.park }} />
                     <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[50%] rounded-full blur-[3px] opacity-70" style={{ backgroundColor: preset.landUseColors?.water }} />
                     
                     {/* Road Primary */}
                     <div className="absolute top-0 bottom-0 left-[30%] w-2 transform shadow-sm" style={{ backgroundColor: preset.roadColors?.primary || '#ddd' }} />
                     {/* Road Secondary */}
                     <div className="absolute top-[50%] right-0 left-[30%] h-1" style={{ backgroundColor: preset.roadColors?.secondary || '#eee' }} />
                     
                     {/* Buildings */}
                     <div className="absolute top-[20%] right-[15%] w-[35%] h-[20%] rounded-sm shadow-sm" style={{ backgroundColor: preset.buildingColor, borderColor: preset.buildingOutlineColor, borderWidth: preset.buildingOutlineColor ? '1.5px' : '0' }} />
                     <div className="absolute bottom-[10%] left-[10%] w-[15%] h-[35%] rounded-sm shadow-sm" style={{ backgroundColor: preset.buildingColor, borderColor: preset.buildingOutlineColor, borderWidth: preset.buildingOutlineColor ? '1.5px' : '0' }} />
                     <div className="absolute bottom-[15%] right-[25%] w-[20%] h-[20%] rounded-[1px] shadow-sm" style={{ backgroundColor: preset.buildingColor, borderColor: preset.buildingOutlineColor, borderWidth: preset.buildingOutlineColor ? '1.5px' : '0' }} />
                   </div>
                   <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors" />
                </div>
                <div className="flex flex-col w-full px-0.5 pb-0.5">
                  <div className="text-[10px] font-bold text-slate-800 uppercase tracking-tight truncate w-full">{id.replace('_', ' ')}</div>
                  <div className="text-[8px] text-slate-400 mt-0.5 leading-[1.3] opacity-80">{preset.description}</div>
                </div>
              </button>
            )})}
            </div>
          )}

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
