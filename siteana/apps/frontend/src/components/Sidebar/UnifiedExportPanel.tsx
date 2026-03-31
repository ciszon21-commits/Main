import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import { useExport } from '../../hooks/useExport';
import { 
  Download, 
  FileText, 
  FileImage, 
  LayoutTemplate, 
  Monitor, 
  Printer, 
  Type, 
  User,
  CheckCircle2,
  Settings,
  ChevronRight,
  Circle
} from 'lucide-react';

const UnifiedExportPanel: React.FC = () => {
  const { 
    selectedTemplate, setSelectedTemplate,
    exportTitle, setExportTitle,
    exportAuthor, setExportAuthor,
    analysisResult,
    circularMask, setCircularMask
  } = useStore();
  
  const { exportToPNG, exportToPDF, isExporting } = useExport();
  const [format, setFormat] = useState<'png' | 'pdf'>('pdf');
  const [resLevel, setResLevel] = useState<'standard' | 'high'>('high');

  const handleExport = () => {
    const scale = resLevel === 'high' ? 2 : 1;
    if (format === 'png') {
      exportToPNG({ scale });
    } else {
      const size = selectedTemplate === 'presentation' ? 'a3' : 'a4';
      exportToPDF({ scale, size });
    }
  };

  const templates = [
    { id: 'presentation', name: '16:9 簡報', icon: Monitor, desc: '適合螢幕展示' },
    { id: 'report', name: 'A3/A4 圖紙', icon: Printer, desc: '精確打印排版' }
  ] as const;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="space-y-5 px-1 pb-2">
        
        {/* STEP 1: Paper & Layout */}
        <div className="space-y-3">
          <label className="text-[10px] text-slate-400 font-black uppercase tracking-widest flex items-center gap-2">
            <span className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] text-slate-500">1</span>
            版面規劃
          </label>
          <div className="grid grid-cols-2 gap-2">
            {templates.map((tpl) => (
              <button
                key={tpl.id}
                onClick={() => setSelectedTemplate(tpl.id)}
                className={`flex flex-col items-center gap-2 p-3 rounded-xl border text-center transition-all ${
                  selectedTemplate === tpl.id
                    ? 'bg-brand-50 border-brand-500 text-brand-700 shadow-sm'
                    : 'bg-white border-slate-100 text-slate-500 hover:bg-slate-50'
                }`}
              >
                <tpl.icon size={18} className={selectedTemplate === tpl.id ? 'text-brand-600' : 'text-slate-400'} />
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold">{tpl.name}</span>
                  <span className="text-[9px] opacity-70 uppercase">{tpl.desc}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* STEP 2: Format & Res */}
        <div className="space-y-3">
          <label className="text-[10px] text-slate-400 font-black uppercase tracking-widest flex items-center gap-2">
             <span className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] text-slate-500">2</span>
             技術規格
          </label>
          <div className="space-y-3 pl-1">
            <div className="flex gap-2">
              {[
                { id: 'pdf', label: 'PDF 格式', icon: FileText },
                { id: 'png', label: 'PNG 圖片', icon: FileImage },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFormat(f.id as any)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border text-[11px] font-medium transition-all ${
                    format === f.id
                      ? 'bg-slate-800 border-slate-800 text-white shadow-md'
                      : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                  }`}
                >
                  <f.icon size={13} /> {f.label}
                </button>
              ))}
            </div>
            
            <div className="flex bg-slate-100 p-1 rounded-lg">
              {[
                { id: 'standard', label: '清晰' },
                { id: 'high', label: '高清 (2x)' },
              ].map((r) => (
                <button
                  key={r.id}
                  onClick={() => setResLevel(r.id as any)}
                  className={`flex-1 py-1.5 rounded-md text-[10px] font-bold transition-all ${
                    resLevel === r.id
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>

            {/* Circular Mask Toggle */}
            <label className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-3 py-2.5 cursor-pointer hover:border-brand-200 transition-colors">
              <span className="flex items-center gap-2 text-[11px] font-bold text-slate-700">
                <Circle size={13} className="text-slate-400" />
                圓形遮罩輸出
                <span className="text-[9px] font-normal text-slate-400 ml-1">PNG transparent</span>
              </span>
              <div className={`relative w-8 h-4 rounded-full transition-colors ${circularMask ? 'bg-brand-500' : 'bg-slate-200'}`} onClick={() => setCircularMask(!circularMask)}>
                <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full shadow transition-transform ${circularMask ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </div>
            </label>
          </div>
        </div>

        {/* STEP 3: Documentation Meta */}
        <div className="space-y-3">
           <label className="text-[10px] text-slate-400 font-black uppercase tracking-widest flex items-center gap-2">
             <span className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] text-slate-500">3</span>
             圖紙資訊
           </label>
           <div className="space-y-3 pl-1">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-medium ml-0.5">
                  <Type size={11} /> 專案名稱 / 標題
                </div>
                <input 
                  type="text" 
                  value={exportTitle}
                  onChange={(e) => setExportTitle(e.target.value)}
                  className="w-full text-xs font-medium border-b border-slate-200 py-1.5 focus:border-brand-500 focus:outline-none bg-transparent transition-colors"
                  placeholder="輸入匯出標題..."
                />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-medium ml-0.5">
                  <User size={11} /> 製圖人 / 單位
                </div>
                <input 
                  type="text" 
                  value={exportAuthor}
                  onChange={(e) => setExportAuthor(e.target.value)}
                  className="w-full text-xs font-medium border-b border-slate-200 py-1.5 focus:border-brand-500 focus:outline-none bg-transparent transition-colors"
                  placeholder="輸入名稱..."
                />
              </div>
           </div>
        </div>

        {/* ACTION */}
        <div className="pt-2">
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="group w-full py-3.5 bg-brand-500 text-white rounded-2xl shadow-lg shadow-brand-200 hover:bg-brand-600 hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:translate-y-0 disabled:shadow-none flex items-center justify-center gap-3"
          >
            {isExporting ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
                <span className="text-sm font-bold tracking-widest uppercase">處理中...</span>
              </>
            ) : (
              <>
                <span className="text-sm font-bold tracking-widest uppercase italic">Create Document</span>
                <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
          
          <div className="mt-4 flex items-start gap-2 px-1">
             <CheckCircle2 size={12} className="text-emerald-500 mt-0.5" />
             <p className="text-[9px] text-slate-400 font-medium leading-relaxed">
                系統將捕捉目前地圖視角，並根據您選擇的模板自動生成高解析度報告文件。
             </p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default UnifiedExportPanel;
