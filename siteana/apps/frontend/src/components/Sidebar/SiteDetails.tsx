import React from 'react';
import { useStore } from '../../store/useStore';
import { MapPin, Info, Ruler } from 'lucide-react';

const SiteDetails: React.FC = () => {
  const { analysisResult, drawnGeometry } = useStore();

  if (!drawnGeometry) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
        <MapPin size={32} className="text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 font-medium whitespace-pre-wrap">請先在地圖上繪製基地輪廓<br/>(Draw a polygon to begin)</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-brand-100 flex items-center justify-center text-brand-600">
          <MapPin size={22} />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900 leading-tight">基地基礎資料</h3>
          <p className="text-[10px] text-slate-400 font-medium mt-0.5 uppercase tracking-wider">Site Measurements</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Ruler size={14} className="text-brand-500" /> Area</span>
            <p className="text-xl font-black text-slate-800 tracking-tight">
              {analysisResult?.area_m2.toLocaleString()} <span className="text-xs font-semibold text-slate-400 tracking-normal">m²</span>
            </p>
          </div>
          <div className="flex flex-col gap-1 text-right">
             <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Taiwan Ping</span>
             <p className="text-sm font-bold text-slate-600">{analysisResult?.area_ping.toLocaleString()} <span className="text-[10px] text-slate-400">坪</span></p>
          </div>
        </div>

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <Info size={16} className="text-brand-500" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Perimeter</span>
          </div>
          <p className="text-xl font-black text-slate-800 tracking-tight">
            {analysisResult?.perimeter_m.toLocaleString()} <span className="text-xs font-semibold text-slate-400 tracking-normal">m (周長)</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SiteDetails;
