import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import { useMapPaintStore } from '../../store/useMapPaintStore';
import { ChevronDown, ChevronUp, Map as MapIcon, Layers } from 'lucide-react';

const Legend: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { drawnGeometry, bufferGeometry } = useStore();
  const { activePresetId, buildingColor, roadColors, landUseColors } = useMapPaintStore();

  const isGradient = activePresetId === 'urban_density';

  const items = [
    { label: '基地', color: '#0ea5e9', active: !!drawnGeometry, type: 'drawn' },
    { label: '緩衝區', color: '#f59e0b', active: !!bufferGeometry, type: 'buffer' },
    ...(!isGradient ? [{ label: '建築量體', color: buildingColor, active: true, type: 'basic' }] : []),
    { label: '道路', color: roadColors.primary, active: true, type: 'basic' },
    { label: '公園', color: landUseColors.park, active: true, type: 'basic' },
    { label: '水體', color: landUseColors.water, active: true, type: 'basic' },
  ];

  return (
    <div className={`transition-all duration-500 ease-in-out flex flex-col items-end gap-2`}>
      {/* Legend Content */}
      <div 
        className={`glass-panel rounded-2xl shadow-2xl transition-all duration-300 overflow-hidden ${
          isCollapsed ? 'max-h-0 opacity-0 pointer-events-none' : 'max-h-80 w-44 p-4 opacity-100'
        }`}
      >
        <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-2">
          <Layers size={12} className="text-brand-500" />
          <h4 className="text-[10px] font-black text-slate-800 uppercase tracking-widest mt-0.5">Map Legend</h4>
        </div>

        <div className="space-y-4 animate-fade-in">
          {isGradient && (
            <div className="space-y-1.5 pb-2 border-b border-slate-100">
               <span className="text-[9px] font-bold text-slate-500 tracking-tight">建築高度分級</span>
               <div className="h-1.5 w-full rounded-full bg-gradient-to-r from-slate-200 via-amber-300 to-red-700 shadow-inner" />
               <div className="flex justify-between text-[7px] font-medium text-slate-400">
                  <span>-15m</span>
                  <span>+80m</span>
               </div>
            </div>
          )}

          <div className="space-y-2.5">
            {items.filter(i => i.active).map((item, index) => (
              <div key={index} className="flex items-center gap-2.5">
                <div 
                  className={`w-2.5 h-2.5 rounded-full border shadow-sm ${item.type === 'buffer' ? 'border-dashed border-2' : ''}`} 
                  style={{ 
                    backgroundColor: item.type === 'drawn' ? 'transparent' : item.color,
                    borderStyle: item.type === 'buffer' ? 'dashed' : 'solid',
                    borderColor: item.type === 'drawn' ? '#ef4444' : undefined,
                    borderWidth: item.type === 'drawn' ? '2px' : undefined
                  }} 
                />
                <span className="text-[10px] font-bold text-slate-700 tracking-tight">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Toggle Button */}
      <button 
        onClick={() => setIsCollapsed(!isCollapsed)}
        className={`w-10 h-10 glass-panel rounded-xl shadow-lg border border-white/50 flex flex-col items-center justify-center transition-all hover:bg-white group ${isCollapsed ? 'text-slate-400' : 'text-brand-600'}`}
        title="圖例顯示控制"
      >
        <Layers size={18} className={isCollapsed ? 'opacity-40' : 'animate-pulse'} />
        <span className="text-[7px] font-bold uppercase tracking-tighter mt-0.5">{isCollapsed ? 'Show' : 'Hide'}</span>
      </button>
    </div>
  );
};

export default Legend;
