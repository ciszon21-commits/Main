import React, { useState } from 'react';
import { createPortal } from 'react-dom';
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
  Circle,
  Layers
} from 'lucide-react';

const UnifiedExportPanel: React.FC = () => {
  const { 
    selectedTemplate, setSelectedTemplate,
    exportTitle, setExportTitle,
    exportAuthor, setExportAuthor,
    analysisResult,
    circularMask, setCircularMask,
    showLegendInExport, setShowLegendInExport
  } = useStore();
  
  const { exportToPNG, exportToPDF, generatePreviewUrl, isExporting } = useExport();
  const [format, setFormat] = useState<'png' | 'pdf'>('png');
  const [resLevel, setResLevel] = useState<'standard' | 'high' | '4k' | '8k'>('high');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);

  const getScale = () => {
    switch(resLevel) {
      case 'standard': return 1;
      case 'high': return 2;
      case '4k': return 4;
      case '8k': return 8; // Max quality for large print
      default: return 2;
    }
  }

  const handleExport = () => {
    const scale = getScale();
    if (format === 'png') {
      exportToPNG({ scale });
    } else {
      const size = selectedTemplate === 'presentation' ? 'a3' : 'a4';
      exportToPDF({ scale, size });
    }
  };

  const handlePreview = async () => {
    setIsPreviewing(true);
    try {
      const url = await generatePreviewUrl();
      setPreviewUrl(url);
    } catch {
      alert('預覽產生失敗');
    } finally {
      setIsPreviewing(false);
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
            
            <div className="grid grid-cols-4 gap-1 bg-slate-100 p-1 rounded-lg">
              {[
                { id: 'standard', label: '1080p' },
                { id: 'high', label: '2K' },
                { id: '4k', label: '4K' },
                { id: '8k', label: '8K' }
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

            {/* Export options */}
            <div className="space-y-2">
              <label className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-3 py-2.5 cursor-pointer hover:border-brand-200 transition-colors">
                <span className="flex items-center gap-2 text-[11px] font-bold text-slate-700">
                  <Circle size={13} className="text-slate-400" />
                  圓形遮罩輸出
                </span>
                <div className={`relative w-8 h-4 rounded-full transition-colors ${circularMask ? 'bg-brand-500' : 'bg-slate-200'}`} onClick={() => setCircularMask(!circularMask)}>
                  <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full shadow transition-transform ${circularMask ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
              </label>

              <label className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-3 py-2.5 cursor-pointer hover:border-brand-200 transition-colors">
                <span className="flex items-center gap-2 text-[11px] font-bold text-slate-700">
                  <Layers size={13} className="text-slate-400" />
                  包含地圖圖例
                </span>
                <div className={`relative w-8 h-4 rounded-full transition-colors ${showLegendInExport ? 'bg-brand-500' : 'bg-slate-200'}`} onClick={() => setShowLegendInExport(!showLegendInExport)}>
                  <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full shadow transition-transform ${showLegendInExport ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
              </label>
            </div>
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
        <div className="pt-2 flex flex-col gap-2">
          {/* Preview Button */}
          <button
            onClick={handlePreview}
            disabled={isExporting || isPreviewing}
            className="w-full py-2.5 bg-brand-50 text-brand-700 border border-brand-200 rounded-xl hover:bg-brand-100 transition-colors disabled:opacity-50 text-xs font-bold tracking-wider flex items-center justify-center gap-2"
          >
            {isPreviewing ? (
              <span className="animate-spin w-3 h-3 border-2 border-brand-500 border-t-transparent rounded-full" />
            ) : <Monitor size={14} />}
            出圖預覽 (PREVIEW)
          </button>

          <button
            onClick={handleExport}
            disabled={isExporting || isPreviewing}
            className="group w-full py-3.5 bg-brand-500 text-white rounded-2xl shadow-lg shadow-brand-200 hover:bg-brand-600 hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:translate-y-0 disabled:shadow-none flex items-center justify-center gap-3"
          >
            {isExporting && !isPreviewing ? (
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
          
          <div className="mt-2 flex items-start gap-2 px-1">
             <CheckCircle2 size={12} className="text-emerald-500 mt-0.5" />
             <p className="text-[9px] text-slate-400 font-medium leading-relaxed">
                預覽以 1x 倍率呈現；正式出圖將根據您的設定以最高至 8K 倍率重新渲染高解析度圖紙。
             </p>
          </div>
        </div>

      </div>

      {previewUrl && createPortal(
        <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in zoom-in duration-200" onClick={() => setPreviewUrl(null)}>
          <div className="relative max-w-5xl w-full h-full flex flex-col items-center justify-center pointer-events-none">
            <div className="bg-white p-2 rounded-xl shadow-2xl relative pointer-events-auto">
              <button 
                className="absolute -top-4 -right-4 w-8 h-8 bg-white text-slate-900 rounded-full shadow-lg flex items-center justify-center hover:scale-110 hover:text-red-500 transition-all font-bold"
                onClick={() => setPreviewUrl(null)}
              >
                ×
              </button>
              <img src={previewUrl} className="max-w-full max-h-[85vh] rounded-lg object-contain shadow-inner border border-slate-100" alt="Export Preview" />
            </div>
            <div className="mt-6 pointer-events-auto">
              <button
                onClick={(e) => { e.stopPropagation(); setPreviewUrl(null); handleExport(); }}
                className="px-8 py-3 bg-brand-500 text-white font-bold tracking-wider rounded-xl shadow-lg shadow-brand-500/30 hover:-translate-y-1 transition-transform flex items-center gap-2"
              >
                <Download size={18} /> 確認，執行輸出
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

    </div>
  );
};

export default UnifiedExportPanel;
