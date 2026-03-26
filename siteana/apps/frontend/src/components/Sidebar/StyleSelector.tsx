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
            <div className={`w-full h-12 rounded-lg mb-1 flex items-center justify-center ${
              style.id === 'minimal-dark' ? 'bg-slate-900' : 
              style.id === 'positron-light' ? 'bg-slate-200' : 'bg-blue-100'
            }`}>
               <Layers size={18} className={style.id === 'minimal-dark' ? 'text-slate-700' : 'text-slate-400'} />
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
