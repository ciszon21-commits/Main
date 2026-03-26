import React from 'react';

const Legend: React.FC = () => {
  const items = [
    { label: 'Commercial', color: '#ff7f7f' },
    { label: 'Residential', color: '#ffff7f' },
    { label: 'Park & Open Space', color: '#7fbf7f' },
    { label: 'Institutional', color: '#7f7fbf' },
  ];

  return (
    <div className="absolute bottom-24 right-6 w-48 bg-white/90 backdrop-blur-md rounded-2xl border border-slate-200/50 shadow-2xl p-4 pointer-events-none">
      <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Map Legend</h4>
      <div className="space-y-2.5">
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-3">
            <div 
              className="w-3.5 h-3.5 rounded-full border border-white/50 shadow-sm" 
              style={{ backgroundColor: item.color }} 
            />
            <span className="text-[11px] font-bold text-slate-700 tracking-tight">{item.label}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-3 border-t border-slate-100 flex justify-between items-center">
        <span className="text-[9px] font-medium text-slate-300">SOURCE: SITEANA GIS</span>
        <div className="flex gap-0.5">
          <div className="w-1 h-1 rounded-full bg-slate-200" />
          <div className="w-1 h-1 rounded-full bg-slate-200" />
          <div className="w-1 h-1 rounded-full bg-slate-200" />
        </div>
      </div>
    </div>
  );
};

export default Legend;
