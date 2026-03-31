import React, { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { Type, PaintBucket } from 'lucide-react';

// Explicitly defined color palettes for direct injection (bypasses CSS specificity issues)
const PALETTES = {
  brand: {
    50: '#f0f9ff', 100: '#e0f2fe', 200: '#bae6fd', 300: '#7dd3fc',
    400: '#38bdf8', 500: '#0ea5e9', 600: '#0284c7', 700: '#0369a1',
    800: '#075985', 900: '#0c4a6e',
  },
  slate: {
    50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 300: '#cbd5e1',
    400: '#94a3b8', 500: '#64748b', 600: '#475569', 700: '#334155',
    800: '#1e293b', 900: '#0f172a',
  },
  emerald: {
    50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7',
    400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857',
    800: '#065f46', 900: '#064e3b',
  },
};

const FONTS: Record<string, string> = {
  sans: 'Inter, system-ui, Helvetica, Arial, sans-serif',
  serif: 'Georgia, "Times New Roman", serif',
  mono: '"Courier New", "Fira Code", monospace',
};

const ThemeSelector: React.FC = () => {
  const { themeColor, setThemeColor, fontFamily, setFontFamily } = useStore();

  // Apply color palette directly as inline CSS variable via style.setProperty
  useEffect(() => {
    const root = document.documentElement;
    const palette = PALETTES[themeColor];
    if (palette) {
      Object.entries(palette).forEach(([shade, color]) => {
        root.style.setProperty(`--color-primary-${shade}`, color);
      });
    }
  }, [themeColor]);

  // Apply font directly as inline style (bypasses `:root { font-family: ... }` specificity)
  useEffect(() => {
    document.documentElement.style.fontFamily = FONTS[fontFamily] || FONTS.sans;
  }, [fontFamily]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Appearance</h2>
      </div>

      <div className="px-1 space-y-4">
        {/* Color Palette */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
            <PaintBucket size={14} /> 主題色系
          </div>
          <div className="flex gap-2">
            {[
              { id: 'brand', bg: '#0ea5e9', label: 'Blue' },
              { id: 'slate', bg: '#475569', label: 'Slate' },
              { id: 'emerald', bg: '#059669', label: 'Green' },
            ].map((c) => (
              <button
                key={c.id}
                title={c.label}
                onClick={() => setThemeColor(c.id as any)}
                className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all ${
                  themeColor === c.id
                    ? 'border-slate-400 shadow-md ring-2 ring-slate-100 scale-110'
                    : 'border-transparent hover:scale-105'
                }`}
              >
                <div className="w-6 h-6 rounded-full" style={{ backgroundColor: c.bg }} />
              </button>
            ))}
          </div>
        </div>

        {/* Font Family */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
            <Type size={14} /> 系統字體
          </div>
          <div className="flex gap-2">
            {[
              { id: 'sans', label: 'Sans', preview: 'Aa' },
              { id: 'serif', label: 'Serif', preview: 'Aa' },
              { id: 'mono', label: 'Mono', preview: '<>' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFontFamily(f.id as any)}
                className={`flex-1 py-2 text-[10px] rounded border transition-colors ${
                  fontFamily === f.id
                    ? 'bg-slate-100 border-slate-400 text-slate-900 font-bold'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <div
                  style={{ fontFamily: FONTS[f.id] }}
                  className="text-base leading-none mb-0.5"
                >
                  {f.preview}
                </div>
                <div className="text-[9px] uppercase tracking-widest">{f.label}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeSelector;
