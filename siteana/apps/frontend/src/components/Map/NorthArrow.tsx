import React from 'react';
import { Compass } from 'lucide-react';

const NorthArrow: React.FC = () => {
  return (
    <div className="flex flex-col items-center gap-1 group pointer-events-none">
      <div className="w-9 h-9 rounded-full bg-white/80 backdrop-blur-sm border border-slate-200/50 shadow-lg flex items-center justify-center text-slate-900 transition-transform group-hover:scale-110">
        <Compass size={20} strokeWidth={2} className="text-brand-600" />
      </div>
      <span className="text-[9px] font-black text-slate-900 tracking-tighter bg-white/80 backdrop-blur-sm px-1.5 rounded border border-slate-200/20 shadow-sm">N</span>
    </div>
  );
};

export default NorthArrow;
