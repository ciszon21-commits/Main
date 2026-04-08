import React, { useRef, useState } from 'react';
import { useStore } from '../../store/useStore';
import {
  PenLine, Trash2, CheckCircle, Upload, Download,
  Ruler, CircleDot, MapPin, Type,
  Navigation, BarChart2, FileDown, X, Sun
} from 'lucide-react';
import { useMapPaintStore } from '../../store/useMapPaintStore';
import * as turf from '@turf/turf';

// ── DXF Export utility ───────────────────────────────────────
const exportToDXF = (geometry: any) => {
  try {
    // Simple DXF LWPOLYLINE generation without external library
    const coords: [number, number][] = geometry?.geometry?.coordinates?.[0] || [];
    if (coords.length < 3) return;

    let dxf = `0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n`;
    dxf += `0\nLWPOLYLINE\n8\nSITE\n70\n1\n90\n${coords.length}\n`;
    coords.forEach(([x, y]) => {
      dxf += `10\n${x}\n20\n${y}\n30\n0.0\n`;
    });
    dxf += `0\nENDSEC\n0\nEOF\n`;

    const blob = new Blob([dxf], { type: 'application/dxf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SiteANA_基地_${new Date().toISOString().slice(0, 10)}.dxf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('DXF 匯出失敗');
  }
};

const AnalysisPanel: React.FC = () => {
  const {
    drawnGeometry, analysisResult, setAnalysisResult,
    setBufferGeometry, bufferGeometry,
    setDrawnGeometry,
    showSiteMarker, setShowSiteMarker, siteMarkerText, setSiteMarkerText,
    mapRef, isDrawingMode, setIsDrawingMode,
    sunlightEnabled, setSunlightEnabled,
    sunlightDate, setSunlightDate,
    sunlightTime, setSunlightTime,
    sunlightShadowOpacity, setSunlightShadowOpacity,
    stylePresets, setSelectedStyle, selectedStyle
  } = useStore();

  const [activeTab, setActiveTab] = useState<'site' | 'measure' | 'sunlight'>('site');
  const [bufferRadius, setBufferRadius] = useState(50);
  const [isLoading, setIsLoading] = useState(false);

  // ── Drawing state ─────────────────────────────────────────
  const [drawPoints, setDrawPoints] = useState<[number, number][]>([]);
  const clickHandlerRef = useRef<((e: any) => void) | null>(null);

  // ── Measure state ─────────────────────────────────────────
  const [measureMode, setMeasureMode] = useState<'distance' | 'area' | null>(null);
  const [measurePoints, setMeasurePoints] = useState<[number, number][]>([]);
  const [measureResult, setMeasureResult] = useState<{ distance?: number; area?: number } | null>(null);
  const measureClickRef = useRef<((e: any) => void) | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Map polygon helper ────────────────────────────────────
  const updateMapPolygon = (geojson: any) => {
    const map = mapRef;
    if (!map) return;
    if (map.getSource('drawn-polygon')) {
      (map.getSource('drawn-polygon') as any).setData(geojson);
    } else {
      map.addSource('drawn-polygon', { type: 'geojson', data: geojson });
      map.addLayer({ id: 'drawn-polygon-fill', type: 'fill', source: 'drawn-polygon', paint: { 'fill-color': '#0ea5e9', 'fill-opacity': 0.15 } });
      map.addLayer({ id: 'drawn-polygon-line', type: 'line', source: 'drawn-polygon', paint: { 'line-color': '#0ea5e9', 'line-width': 2 } });
    }
  };

  // ── Site Drawing ──────────────────────────────────────────
  const startDrawing = () => {
    const map = mapRef;
    if (!map) return;
    setDrawPoints([]);
    setIsDrawingMode(true);
    map.getCanvas().style.cursor = 'crosshair';

    const handler = (e: any) => {
      const { lng, lat } = e.lngLat;
      setDrawPoints(prev => [...prev, [lng, lat]]);
    };
    map.on('click', handler);
    clickHandlerRef.current = handler;
  };

  const finishDrawing = () => {
    const map = mapRef;
    if (!map || drawPoints.length < 3) return;
    const closed = [...drawPoints, drawPoints[0]];
    const geojson = {
      type: 'Feature' as const,
      properties: {},
      geometry: { type: 'Polygon' as const, coordinates: [closed] }
    };
    setDrawnGeometry(geojson);
    cleanupDrawing();
    updateMapPolygon(geojson);
  };

  const cleanupDrawing = () => {
    const map = mapRef;
    if (map && clickHandlerRef.current) {
      map.off('click', clickHandlerRef.current);
      clickHandlerRef.current = null;
    }
    if (map) map.getCanvas().style.cursor = '';
    setIsDrawingMode(false);
  };

  const clearSite = () => {
    const map = mapRef;
    cleanupDrawing();
    setDrawPoints([]);
    setDrawnGeometry(null);
    setAnalysisResult(null);
    setBufferGeometry(null);
    if (map) {
      if (map.getLayer('drawn-polygon-fill')) map.removeLayer('drawn-polygon-fill');
      if (map.getLayer('drawn-polygon-line')) map.removeLayer('drawn-polygon-line');
      if (map.getSource('drawn-polygon')) map.removeSource('drawn-polygon');
      if (map.getLayer('buffer-fill')) map.removeLayer('buffer-fill');
      if (map.getLayer('buffer-line')) map.removeLayer('buffer-line');
      if (map.getSource('buffer-polygon')) map.removeSource('buffer-polygon');
    }
  };

  // ── GeoJSON Import ────────────────────────────────────────
  const importGeoJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target?.result as string);
        const map = mapRef;
        let feature = parsed;
        if (parsed.type === 'FeatureCollection' && parsed.features?.length > 0) feature = parsed.features[0];
        if (!feature.type) feature = { type: 'Feature', properties: {}, geometry: parsed };
        setDrawnGeometry(feature);
        setAnalysisResult(null);
        const applyToMap = () => {
          updateMapPolygon(feature);
          try {
            const bbox = turf.bbox(feature);
            map?.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], { padding: 60, duration: 1000 });
          } catch { }
        };
        if (map?.isStyleLoaded()) applyToMap();
        else map?.once('load', applyToMap);
      } catch { alert('檔案格式無效，請匯入有效的 GeoJSON 檔案。'); }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ── Analysis ──────────────────────────────────────────────
  const runAnalysis = async () => {
    if (!drawnGeometry) return;
    setIsLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/analysis/stats', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ geojson: drawnGeometry }), signal: AbortSignal.timeout(3000)
      });
      if (res.ok) { const { data } = await res.json(); setAnalysisResult(data); }
      else throw new Error();
    } catch {
      const areaM2 = turf.area(drawnGeometry as any);
      const perimeter = turf.length(drawnGeometry as any, { units: 'meters' });
      const centroid = turf.centroid(drawnGeometry as any);
      setAnalysisResult({
        area_m2: Math.round(areaM2 * 100) / 100,
        area_ping: Math.round((areaM2 / 3.305785) * 100) / 100,
        perimeter_m: Math.round(perimeter * 100) / 100,
        centroid: { lon: centroid.geometry.coordinates[0], lat: centroid.geometry.coordinates[1] }
      });
    }
    setIsLoading(false);
  };

  const runBuffer = async () => {
    if (!drawnGeometry) return;
    setIsLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/analysis/buffer', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ geojson: drawnGeometry, radius_m: bufferRadius }), signal: AbortSignal.timeout(3000)
      });
      if (res.ok) { const { data } = await res.json(); setBufferGeometry(data); }
      else throw new Error();
    } catch {
      const buffered = turf.buffer(drawnGeometry as any, bufferRadius, { units: 'meters' });
      if (buffered) setBufferGeometry(buffered as any);
    }
    setIsLoading(false);
  };

  const clearBuffer = () => {
    const map = mapRef;
    setBufferGeometry(null);
    if (map) {
      setTimeout(() => {
        try { if (map.getLayer('buffer-fill')) map.removeLayer('buffer-fill'); } catch { }
        try { if (map.getLayer('buffer-line')) map.removeLayer('buffer-line'); } catch { }
        try { if (map.getSource('buffer-polygon')) map.removeSource('buffer-polygon'); } catch { }
      }, 50);
    }
  };

  // ── Measure Tool ──────────────────────────────────────────
  const startMeasure = (mode: 'distance' | 'area') => {
    const map = mapRef;
    if (!map) return;
    stopMeasure();
    setMeasureMode(mode);
    setMeasurePoints([]);
    setMeasureResult(null);
    map.getCanvas().style.cursor = 'crosshair';

    const handler = (e: any) => {
      const { lng, lat } = e.lngLat;
      setMeasurePoints(prev => {
        const next = [...prev, [lng, lat] as [number, number]];
        // Live compute
        if (mode === 'distance' && next.length >= 2) {
          const line = turf.lineString(next);
          setMeasureResult({ distance: turf.length(line, { units: 'meters' }) });
        } else if (mode === 'area' && next.length >= 3) {
          const poly = turf.polygon([[...next, next[0]]]);
          setMeasureResult({ area: turf.area(poly) });
        }
        return next;
      });
    };
    map.on('click', handler);
    measureClickRef.current = handler;
  };

  const stopMeasure = () => {
    const map = mapRef;
    if (map && measureClickRef.current) {
      map.off('click', measureClickRef.current);
      measureClickRef.current = null;
    }
    if (map) map.getCanvas().style.cursor = '';
    setMeasureMode(null);
  };

  const clearMeasure = () => {
    stopMeasure();
    setMeasurePoints([]);
    setMeasureResult(null);
  };

  // ── Sunlight Action ───────────────────────────────────────
  const handleSunlightToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const isEnabled = e.target.checked;
    setSunlightEnabled(isEnabled);
    
    if (isEnabled) {
      // Auto-switch to vector map if on raster
      if (selectedStyle?.category === 'Raster (像素底圖)' || selectedStyle?.id === 'osm-raster') {
         const liberty = stylePresets.find(p => p.id === 'ofm-liberty');
         if (liberty) setSelectedStyle(liberty);
      }

      // Auto-apply neutral preset to make shadows pop
      useMapPaintStore.getState().applyPreset('architectural_plan', {
         backgroundColor: '#f8fafc',
         building3D: true, 
         buildingVisibility: true,
         buildingColor: '#e2e8f0',
         buildingOutlineColor: '#cbd5e1',
         buildingOpacity: 0.95
      });
    }
  };

  const formatSunTime = (decimalHours: number) => {
     const h = Math.floor(decimalHours);
     const m = Math.floor((decimalHours - h) * 60).toString().padStart(2, '0');
     return `${h.toString().padStart(2, '0')}:${m}`;
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Tab Switch */}
      <div className="flex bg-slate-100 p-1 rounded-xl">
        {([
          { id: 'site', label: '🔷 基地' },
          { id: 'measure', label: '📏 量測' },
          { id: 'sunlight', label: '☀️ 日照' }
        ] as const).map(tab => (
          <button
            key={tab.id}
            onClick={() => { stopMeasure(); setActiveTab(tab.id); }}
            className={`flex-1 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all ${activeTab === tab.id ? 'bg-white text-brand-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── SITE TAB ─────────────────────────────────────────── */}
      {activeTab === 'site' && (
        <div className="space-y-3 px-1">
          {/* Draw controls */}
          <div className="flex gap-2">
            {!isDrawingMode ? (
              drawnGeometry ? (
                <button onClick={startDrawing} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 transition-colors flex-1 border border-slate-200">
                  <PenLine size={13} /> 重新繪製基地
                </button>
              ) : (
                <button onClick={startDrawing} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-500 text-white text-xs font-bold hover:bg-brand-600 transition-colors flex-1 shadow-md shadow-brand-100">
                  <PenLine size={13} /> 開始繪製基地
                </button>
              )
            ) : (
              <button onClick={finishDrawing} disabled={drawPoints.length < 3} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500 text-white text-xs font-bold hover:bg-emerald-600 transition-colors flex-1 shadow-md shadow-emerald-100 disabled:opacity-40 animate-pulse">
                <CheckCircle size={13} /> 完成繪製 ({drawPoints.length}點)
              </button>
            )}
            <button onClick={clearSite} title="清除基地" className="p-2 rounded-lg border border-slate-200 text-slate-400 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-colors">
              <Trash2 size={13} />
            </button>
          </div>

          {isDrawingMode && (
            <p className="text-[10px] text-brand-500 bg-brand-50 rounded-lg px-2 py-1.5 font-medium">
              ✦ 繪製模式啟用中 — 點擊地圖設定基地節點
            </p>
          )}

          {/* Import / Export */}
          <div className="flex gap-1.5 pt-1 border-t border-slate-100">
            <label className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-[10px] font-medium cursor-pointer hover:bg-brand-50 hover:border-brand-200 hover:text-brand-700 transition-colors flex-1 justify-center">
              <Upload size={11} /> GeoJSON
              <input ref={fileInputRef} type="file" accept=".geojson,.json" className="hidden" onChange={importGeoJSON} />
            </label>
            <button onClick={() => { const c = JSON.stringify(drawnGeometry, null, 2); const b = new Blob([c], { type: 'application/json' }); const u = URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = 'SiteANA_site.geojson'; a.click(); }} disabled={!drawnGeometry} className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-[10px] font-medium hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 transition-colors flex-1 justify-center disabled:opacity-40">
              <Download size={11} /> GeoJSON
            </button>
            <button onClick={() => exportToDXF(drawnGeometry)} disabled={!drawnGeometry} className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg border border-orange-200 text-orange-600 text-[10px] font-medium hover:bg-orange-50 transition-colors flex-1 justify-center disabled:opacity-40">
              <FileDown size={11} /> DXF
            </button>
          </div>

          {/* Analysis */}
          {drawnGeometry && (
            <div className="space-y-3 pt-2 border-t border-slate-100">
              <button onClick={runAnalysis} disabled={isLoading} className="w-full py-2 px-4 bg-brand-500 text-white text-xs font-medium rounded-lg hover:bg-brand-600 transition-colors disabled:opacity-50">
                {isLoading ? '計算中...' : '計算基地面積與周長'}
              </button>

              {analysisResult && (
                <div className="space-y-2 bg-slate-50 rounded-xl p-3 border">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white p-2 rounded-lg border">
                      <div className="text-[9px] text-slate-400 uppercase">面積</div>
                      <div className="text-sm font-bold text-slate-800">{analysisResult.area_m2?.toLocaleString()} m²</div>
                      <div className="text-[10px] text-slate-500">{analysisResult.area_ping?.toLocaleString()} 坪</div>
                    </div>
                    <div className="bg-white p-2 rounded-lg border">
                      <div className="text-[9px] text-slate-400 flex items-center gap-1"><Ruler size={10} /> 周長</div>
                      <div className="text-sm font-bold text-slate-800">{analysisResult.perimeter_m?.toLocaleString()} m</div>
                    </div>
                  </div>
                  {analysisResult.centroid && (
                    <div className="bg-white p-2 rounded-lg border text-[10px] text-slate-500 flex items-center gap-2">
                      <MapPin size={12} className="text-brand-400 flex-shrink-0" />
                      重心: {analysisResult.centroid.lat.toFixed(5)}, {analysisResult.centroid.lon.toFixed(5)}
                    </div>
                  )}
                </div>
              )}

              {/* Buffer */}
              <div className="flex gap-2 items-center">
                <div className="flex-1 space-y-1">
                  <label className="text-[10px] text-slate-400 flex items-center gap-1"><CircleDot size={11} /> 緩衝半徑 (m)</label>
                  <input type="number" value={bufferRadius} onChange={(e) => setBufferRadius(Number(e.target.value))} min={1} max={2000} step={10}
                    className="w-full text-xs border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-300" />
                </div>
                <button onClick={runBuffer} disabled={isLoading} className="mt-5 px-3 py-1.5 bg-white border border-brand-200 text-brand-600 text-xs font-medium rounded-lg hover:bg-brand-50 transition-colors disabled:opacity-50 whitespace-nowrap">
                  套用緩衝
                </button>
              </div>
              {bufferGeometry && (
                <button onClick={clearBuffer} className="w-full text-[10px] text-orange-500 border border-orange-200 rounded-lg py-1.5 hover:bg-orange-50 transition-colors flex items-center justify-center gap-1">
                  <X size={11} /> 清除緩衝區
                </button>
              )}

              {/* Site Marker */}
              <div className="pt-3 border-t border-slate-100 space-y-2">
                <label className="flex items-center justify-between cursor-pointer">
                  <span className="text-[10px] text-slate-500 font-bold flex items-center gap-1.5">
                    <input type="checkbox" checked={showSiteMarker} onChange={(e) => setShowSiteMarker(e.target.checked)} className="w-3.5 h-3.5 rounded border-slate-300 text-brand-600" />
                    標示基地位置 (Site Marker)
                  </span>
                </label>
                {showSiteMarker && (
                  <div className="pl-5">
                    <label className="text-[9px] text-slate-400 flex items-center gap-1 mb-1"><Type size={10} /> 標示文字 (留白則不顯示)</label>
                    <input type="text" value={siteMarkerText} onChange={(e) => setSiteMarkerText(e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:border-brand-300" placeholder="例如：SITE 或 基地位置" />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── MEASURE TAB ──────────────────────────────────────── */}
      {activeTab === 'measure' && (
        <div className="space-y-3 px-1">
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => startMeasure('distance')} className={`flex flex-col items-center gap-1.5 py-3 rounded-xl border text-[11px] font-bold transition-all ${measureMode === 'distance' ? 'bg-brand-500 border-brand-500 text-white shadow-md' : 'bg-white border-slate-200 text-slate-600 hover:border-brand-200'}`}>
              <Navigation size={16} />
              距離量測
            </button>
            <button onClick={() => startMeasure('area')} className={`flex flex-col items-center gap-1.5 py-3 rounded-xl border text-[11px] font-bold transition-all ${measureMode === 'area' ? 'bg-brand-500 border-brand-500 text-white shadow-md' : 'bg-white border-slate-200 text-slate-600 hover:border-brand-200'}`}>
              <BarChart2 size={16} />
              面積量測
            </button>
          </div>

          {measureMode && (
            <p className="text-[10px] text-brand-500 bg-brand-50 rounded-lg px-2 py-1.5 font-medium">
              ✦ {measureMode === 'distance' ? '距離' : '面積'}量測模式 — 點擊地圖設定量測點
            </p>
          )}

          {measureResult && (
            <div className="bg-slate-50 rounded-xl p-3 border space-y-1">
              {measureResult.distance !== undefined && (
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-slate-500">量測距離</span>
                  <span className="text-sm font-bold text-slate-800">
                    {measureResult.distance >= 1000
                      ? `${(measureResult.distance / 1000).toFixed(3)} km`
                      : `${Math.round(measureResult.distance)} m`}
                  </span>
                </div>
              )}
              {measureResult.area !== undefined && (
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-slate-500">量測面積</span>
                  <span className="text-sm font-bold text-slate-800">
                    {measureResult.area?.toLocaleString(undefined, { maximumFractionDigits: 0 })} m²
                  </span>
                </div>
              )}
              <div className="text-[9px] text-slate-400 pt-1 border-t border-slate-200">
                已標記 {measurePoints.length} 個節點
              </div>
            </div>
          )}

          <button onClick={clearMeasure} className="w-full flex items-center justify-center gap-2 py-1.5 border border-slate-200 text-slate-500 text-[10px] font-bold rounded-lg hover:bg-slate-50 transition-colors">
            <Trash2 size={11} /> 清除量測
          </button>
        </div>
      )}

      {/* ── SUNLIGHT TAB ─────────────────────────────────────── */}
      {activeTab === 'sunlight' && (
        <div className="space-y-3 px-1 animate-fade-in">
          <label className="flex items-center justify-between cursor-pointer border border-slate-200 p-3 rounded-xl bg-white hover:border-brand-200 hover:bg-brand-50 transition-colors shadow-sm">
             <span className="text-xs font-bold text-slate-700 flex items-center gap-2">
               <Sun size={15} className={sunlightEnabled ? 'text-amber-500' : 'text-slate-400'} />
               啟用建築日照陰影
             </span>
             <input type="checkbox" checked={sunlightEnabled} onChange={handleSunlightToggle} className="w-4 h-4 text-brand-600 rounded accent-brand-500" />
          </label>

          {sunlightEnabled && (
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-6">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500">分析日期 (YYYY-MM-DD)</label>
                <input type="date" value={sunlightDate} onChange={e => setSunlightDate(e.target.value)}
                  className="w-full px-2 py-2 text-xs font-medium rounded-lg border border-slate-200 focus:outline-none focus:border-brand-400" />
              </div>
              <div className="space-y-1.5">
                <label className="flex items-center justify-between text-[10px] font-bold text-slate-500">
                  <span>時刻設定</span>
                  <span className="text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded font-mono text-xs">{formatSunTime(sunlightTime)}</span>
                </label>
                <input type="range" min="0" max="24" step="0.25" value={sunlightTime} onChange={e => setSunlightTime(Number(e.target.value))}
                  className="w-full accent-amber-500 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer" />
                <div className="flex justify-between text-[9px] text-slate-400 mt-1 px-1">
                  <span>00:00</span>
                  <span>12:00</span>
                  <span>24:00</span>
                </div>
              </div>
              <div className="space-y-1.5 pt-2 border-t border-slate-200/60">
                <label className="flex items-center justify-between text-[10px] font-bold text-slate-500">
                  <span>陰影深淺 (不透明度)</span>
                  <span className="text-slate-500">{(sunlightShadowOpacity * 100).toFixed(0)}%</span>
                </label>
                <input type="range" min="0.1" max="0.9" step="0.05" value={sunlightShadowOpacity} onChange={e => setSunlightShadowOpacity(Number(e.target.value))}
                  className="w-full accent-slate-600 h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer" />
              </div>
              
              <div className="bg-amber-50 p-2.5 rounded-lg border border-amber-100 flex gap-2">
                <Sun size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-[10px] text-amber-700 leading-relaxed">
                  系統已自動為您切換至 <b>工程線稿模式 (Architectural)</b> 與 <b>向量底圖</b>，以利清晰觀察所有的建築投影。
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalysisPanel;
