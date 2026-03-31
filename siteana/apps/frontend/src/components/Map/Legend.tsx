import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import { useMapPaintStore } from '../../store/useMapPaintStore';
import { ChevronDown, ChevronUp, Map as MapIcon, Layers, Compass } from 'lucide-react';
import NorthArrow from './NorthArrow';

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

  const { showLegendInExport, isExporting } = useStore();

  if (isExporting && !showLegendInExport) return null;

  return (
    <div 
      className={`transition-all duration-500 ease-in-out flex flex-col items-end gap-2`}
      data-html2canvas-ignore={!showLegendInExport ? "true" : "false"}
    >
      {/* Legend Content */}
      {/* Combined Container with relative button */}
      <div className="relative group">
        {/* Toggle Button - Now at TOP RIGHT of the whole widget area when collapsed, or TOP RIGHT of panel when expanded */}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={`absolute top-0 right-0 z-[30] w-8 h-8 glass-panel rounded-lg shadow-lg border border-white/50 flex flex-col items-center justify-center transition-all hover:bg-white text-brand-600 ${isCollapsed ? 'translate-y-0' : '-translate-y-2 translate-x-2'}`}
          title="圖例顯示控制"
          data-html2canvas-ignore="true"
        >
          {isCollapsed ? <Layers size={14} /> : <ChevronDown size={14} />}
        </button>

        {/* Legend Content */}
        <div 
          className={`glass-panel rounded-2xl shadow-2xl transition-all duration-300 overflow-hidden ${
            isCollapsed ? 'max-h-0 opacity-0 pointer-events-none' : 'max-h-[400px] w-48 p-4 opacity-100 mt-2'
          }`}
        >
          <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2 pr-6">
            <div className="flex items-center gap-2">
              <Layers size={12} className="text-brand-500" />
              <h4 className="text-[10px] font-black text-slate-800 uppercase tracking-widest mt-0.5">Map Legend</h4>
            </div>
            <div className="scale-75 origin-right">
              <NorthArrow />
            </div>
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
      </div>
    </div>
  );
};

export default Legend;
