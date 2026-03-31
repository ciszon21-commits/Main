import React from 'react';
import { useStore } from '../../store/useStore';
import { Palette, Layers } from 'lucide-react';

const StyleSelector: React.FC = () => {
  const { stylePresets, selectedStyle, setSelectedStyle } = useStore();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Style Presets</h2>
        <Palette size={16} className="text-slate-300" />
      </div>

      <div className="grid grid-cols-2 gap-2 px-1">
        {stylePresets.map((style) => (
          <button
            key={style.id}
            onClick={() => setSelectedStyle(style)}
            className={`flex flex-col gap-2 p-3 rounded-xl border text-left transition-all group ${
              selectedStyle?.id === style.id
                ? 'bg-white border-brand-500 shadow-md ring-2 ring-brand-50'
                : 'bg-slate-50 border-slate-100 hover:bg-white hover:border-slate-200 hover:shadow-sm'
            }`}
          >
            <div className={`w-full h-16 rounded-lg mb-1 flex items-center justify-center overflow-hidden border ${
              style.id === 'osm-raster' ? 'border-amber-200' : 'border-slate-200'
            }`}>
               {/* 模擬地圖縮圖預覽 */}
               {style.id === 'ofm-liberty' && (
                 <div className="w-full h-full bg-[#f8f4f0] relative flex items-center justify-center">
                    <div className="absolute w-full h-[2px] bg-white rotate-12"></div>
                    <div className="absolute w-[2px] h-full bg-white -rotate-12"></div>
                    <Layers size={20} className="text-slate-400 z-10" />
                 </div>
               )}
               {style.id === 'ofm-bright' && (
                 <div className="w-full h-full bg-[#eceadd] relative flex items-center justify-center">
                    <div className="absolute w-full h-[3px] bg-white -rotate-6"></div>
                    <Layers size={20} className="text-stone-500 z-10" />
                 </div>
               )}
               {style.id === 'osm-raster' && (
                 <div className="w-full h-full bg-[#f2efe9] relative flex items-center justify-center overflow-hidden">
                    <div className="absolute w-full h-full opacity-30 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-green-100 via-transparent to-transparent"></div>
                    <Layers size={20} className="text-emerald-600 z-10" />
                 </div>
               )}
            </div>
            <div className="flex flex-col">
              <span className={`text-[11px] font-bold ${selectedStyle?.id === style.id ? 'text-brand-600' : 'text-slate-700'}`}>
                {style.name}
              </span>
              <span className="text-[9px] text-slate-400 uppercase tracking-tight">{style.type}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default StyleSelector;
