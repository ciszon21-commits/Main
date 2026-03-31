import React, { useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { useStore } from '../../store/useStore';
import { PenLine, Trash2, CheckCircle, Upload, Download } from 'lucide-react';
import * as turf from '@turf/turf';

interface DrawToolProps {
  mapRef: React.RefObject<maplibregl.Map | null>;
}

const DrawTool: React.FC<DrawToolProps> = ({ mapRef }) => {
  const { setDrawnGeometry, drawnGeometry, setAnalysisResult } = useStore();
  const [isDrawing, setIsDrawing] = useState(false);
  const [points, setPoints] = useState<[number, number][]>([]);
  const clickHandlerRef = useRef<((e: maplibregl.MapMouseEvent) => void) | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateMapPolygon = (map: maplibregl.Map, geojson: any) => {
    if (map.getSource('drawn-polygon')) {
      (map.getSource('drawn-polygon') as maplibregl.GeoJSONSource).setData(geojson);
    } else {
      map.addSource('drawn-polygon', { type: 'geojson', data: geojson });
      map.addLayer({ id: 'drawn-polygon-fill', type: 'fill', source: 'drawn-polygon', paint: { 'fill-color': '#0ea5e9', 'fill-opacity': 0.15 } });
      map.addLayer({ id: 'drawn-polygon-line', type: 'line', source: 'drawn-polygon', paint: { 'line-color': '#0ea5e9', 'line-width': 2 } });
    }
  };

  const startDrawing = () => {
    const map = mapRef.current;
    if (!map) return;
    setIsDrawing(true);
    setPoints([]);
    map.getCanvas().style.cursor = 'crosshair';

    const handler = (e: maplibregl.MapMouseEvent) => {
      const { lng, lat } = e.lngLat;
      setPoints(prev => [...prev, [lng, lat]]);
      new maplibregl.Marker({ color: '#0ea5e9', scale: 0.6 }).setLngLat([lng, lat]).addTo(map);
    };
    map.on('click', handler);
    clickHandlerRef.current = handler;
  };

  const finishDrawing = () => {
    const map = mapRef.current;
    if (!map || points.length < 3) return;
    const closedPoints = [...points, points[0]];
    const geojson = { type: 'Feature' as const, properties: {}, geometry: { type: 'Polygon' as const, coordinates: [closedPoints] } };
    setDrawnGeometry(geojson);
    cleanupDrawing();
    updateMapPolygon(map, geojson);
  };

  const clearDrawing = () => {
    const map = mapRef.current;
    if (!map) return;
    cleanupDrawing();
    setDrawnGeometry(null);
    setAnalysisResult(null);
    if (map.getLayer('drawn-polygon-fill')) map.removeLayer('drawn-polygon-fill');
    if (map.getLayer('drawn-polygon-line')) map.removeLayer('drawn-polygon-line');
    if (map.getSource('drawn-polygon')) map.removeSource('drawn-polygon');
    Array.from(document.querySelectorAll('.maplibregl-marker')).forEach(el => el.remove());
  };

  const cleanupDrawing = () => {
    const map = mapRef.current;
    if (map && clickHandlerRef.current) { map.off('click', clickHandlerRef.current); clickHandlerRef.current = null; }
    map?.getCanvas && (map.getCanvas().style.cursor = '');
    setIsDrawing(false);
  };

  // ── GeoJSON Export ──────────────────────────────────────────
  const exportGeoJSON = () => {
    if (!drawnGeometry) return;
    const content = JSON.stringify(drawnGeometry, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SiteANA_基地_${new Date().toISOString().slice(0, 10)}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── GeoJSON Import ──────────────────────────────────────────
  const importGeoJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target?.result as string);
        const map = mapRef.current;
        if (!map) return;

        // Accept FeatureCollection or single Feature
        let feature = parsed;
        if (parsed.type === 'FeatureCollection' && parsed.features?.length > 0) {
          feature = parsed.features[0];
        }
        if (!feature.type) {
          // Raw geometry
          feature = { type: 'Feature', properties: {}, geometry: parsed };
        }

        setDrawnGeometry(feature);
        setAnalysisResult(null);

        // Wait for style to load if needed
        const applyToMap = () => {
          updateMapPolygon(map, feature);
          // FlyTo bounds
          try {
            const bbox = turf.bbox(feature);
            map.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], { padding: 60, duration: 1000 });
          } catch { /* bbox error */ }
        };

        if (map.isStyleLoaded()) applyToMap();
        else map.once('load', applyToMap);
      } catch {
        alert('檔案格式無效，請匯入有效的 GeoJSON 檔案。');
      }
    };
    reader.readAsText(file);
    // Reset file input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-2.5">
      {/* Draw Controls */}
      <div className="flex gap-2">
        {!isDrawing ? (
          <button onClick={startDrawing} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-500 text-white text-xs font-medium hover:bg-brand-600 transition-colors flex-1">
            <PenLine size={13} /> 開始繪製基地
          </button>
        ) : (
          <button onClick={finishDrawing} disabled={points.length < 3} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500 text-white text-xs font-medium hover:bg-emerald-600 transition-colors flex-1 disabled:opacity-40">
            <CheckCircle size={13} /> 完成繪製 ({points.length} 點)
          </button>
        )}
        <button onClick={clearDrawing} className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-colors" title="清除全部">
          <Trash2 size={13} />
        </button>
      </div>

      {isDrawing && (
        <p className="text-[10px] text-slate-400 px-0.5">點擊地圖以設定節點，至少需要 3 個點。</p>
      )}

      {/* GeoJSON Import / Export */}
      <div className="flex gap-1.5 pt-1 border-t border-slate-100">
        <label className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-[11px] font-medium cursor-pointer hover:bg-brand-50 hover:border-brand-200 hover:text-brand-700 transition-colors flex-1 justify-center">
          <Upload size={11} /> 匯入 GeoJSON
          <input ref={fileInputRef} type="file" accept=".geojson,.json" className="hidden" onChange={importGeoJSON} />
        </label>
        <button
          onClick={exportGeoJSON}
          disabled={!drawnGeometry}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-[11px] font-medium hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 transition-colors flex-1 justify-center disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Download size={11} /> 匯出 GeoJSON
        </button>
      </div>
    </div>
  );
};

export default DrawTool;
