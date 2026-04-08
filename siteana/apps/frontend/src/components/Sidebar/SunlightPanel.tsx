import React from 'react';
import { Sun, X } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { useMapPaintStore } from '../../store/useMapPaintStore';

const SunlightPanel: React.FC = () => {
  const {
    sunlightEnabled, setSunlightEnabled,
    sunlightDate, setSunlightDate,
    sunlightTime, setSunlightTime,
    sunlightShadowOpacity, setSunlightShadowOpacity,
    stylePresets, setSelectedStyle, selectedStyle
  } = useStore();

  const handleSunlightToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const isEnabled = e.target.checked;
    setSunlightEnabled(isEnabled);
    
    if (isEnabled) {
      // Auto-switch to vector map if on raster
      if (selectedStyle?.category === 'Raster (像素底圖)' || selectedStyle?.id === 'osm-raster') {
         const liberty = stylePresets.find(p => p.id === 'ofm-liberty');
         if (liberty) setSelectedStyle(liberty);
      }

      // Auto-apply neutral preset to make shadows pop
      useMapPaintStore.getState().applyPreset('architectural_plan', {
         backgroundColor: '#f8fafc',
         building3D: true, 
         buildingVisibility: true,
         buildingColor: '#e2e8f0',
         buildingOutlineColor: '#cbd5e1',
         buildingOpacity: 0.95
      });
    }
  };

  const formatSunTime = (decimalHours: number) => {
     const h = Math.floor(decimalHours);
     const m = Math.floor((decimalHours - h) * 60).toString().padStart(2, '0');
     return `${h.toString().padStart(2, '0')}:${m}`;
  };

  return (
    <div className="space-y-3 animate-fade-in py-2">
      <label className="flex items-center justify-between cursor-pointer border border-slate-200 p-3 rounded-xl bg-white hover:border-brand-200 hover:bg-brand-50 transition-colors shadow-sm">
         <span className="text-xs font-bold text-slate-700 flex items-center gap-2">
           <Sun size={15} className={sunlightEnabled ? 'text-amber-500' : 'text-slate-400'} />
           啟用建築日照陰影
         </span>
         <input type="checkbox" checked={sunlightEnabled} onChange={handleSunlightToggle} className="w-4 h-4 text-brand-600 rounded accent-brand-500" />
      </label>

      {sunlightEnabled && (
        <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-6">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-500">分析日期 (YYYY-MM-DD)</label>
            <input type="date" value={sunlightDate} onChange={e => setSunlightDate(e.target.value)}
              className="w-full px-2 py-2 text-xs font-medium rounded-lg border border-slate-200 focus:outline-none focus:border-brand-400" />
          </div>
          <div className="space-y-1.5">
            <label className="flex items-center justify-between text-[10px] font-bold text-slate-500">
              <span>時刻設定</span>
              <span className="text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded font-mono text-xs">{formatSunTime(sunlightTime)}</span>
            </label>
            <input type="range" min="0" max="24" step="0.25" value={sunlightTime} onChange={e => setSunlightTime(Number(e.target.value))}
              className="w-full accent-amber-500 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer" />
            <div className="flex justify-between text-[9px] text-slate-400 mt-1 px-1">
              <span>00:00</span>
              <span>12:00</span>
              <span>24:00</span>
            </div>
          </div>
          <div className="space-y-1.5 pt-2 border-t border-slate-200/60">
            <label className="flex items-center justify-between text-[10px] font-bold text-slate-500">
              <span>陰影深淺 (不透明度)</span>
              <span className="text-slate-500">{(sunlightShadowOpacity * 100).toFixed(0)}%</span>
            </label>
            <input type="range" min="0.1" max="1.0" step="0.05" value={sunlightShadowOpacity} onChange={e => setSunlightShadowOpacity(Number(e.target.value))}
              className="w-full accent-slate-600 h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer" />
          </div>
          
          <div className="bg-amber-50 p-2.5 rounded-lg border border-amber-100 flex gap-2">
            <Sun size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-amber-700 leading-relaxed">
              系統已自動為您切換至 <b>工程線稿模式 (Architectural)</b> 與 <b>向量底圖</b>，以利清晰觀察所有的建築投影。
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SunlightPanel;
