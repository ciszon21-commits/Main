import React from 'react';
import { useStore } from '../../store/useStore';
import { LayoutTemplate, FileText } from 'lucide-react';

const TemplateSelector: React.FC = () => {
  const { selectedTemplate, setSelectedTemplate } = useStore();

  const templates = [
    { id: 'presentation', name: '簡報預覽 (16:9)', icon: LayoutTemplate, desc: '適合螢幕展示與簡報' },
    { id: 'report', name: '圖紙預覽 (A3/A4)', icon: FileText, desc: '精確的列印排版比例' }
  ] as const;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Analysis Templates</h2>
      </div>

      <div className="flex flex-col gap-2 px-1">
        {templates.map((tpl) => (
          <button
            key={tpl.id}
            onClick={() => setSelectedTemplate(tpl.id)}
            className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
              selectedTemplate === tpl.id
                ? 'bg-brand-50 border-brand-200 ring-1 ring-brand-500'
                : 'bg-white border-slate-200 hover:bg-slate-50'
            }`}
          >
            <div className={`p-2 rounded-md ${selectedTemplate === tpl.id ? 'bg-brand-100 text-brand-600' : 'bg-slate-100 text-slate-500'}`}>
              <tpl.icon size={16} />
            </div>
            <div>
              <div className={`text-sm font-medium ${selectedTemplate === tpl.id ? 'text-brand-900' : 'text-slate-700'}`}>
                {tpl.name}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">{tpl.desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default TemplateSelector;
