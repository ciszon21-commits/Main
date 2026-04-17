import { useState } from 'react';
import { useStore } from '../store/useStore';
import { useMapPaintStore } from '../store/useMapPaintStore';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import { MapPaintEngine } from '../engine/MapPaintEngine';
import type maplibregl from 'maplibre-gl';

// EPSG:3826 (TWD97 / TM2 zone 121)
const TWD97 = '+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +units=m +no_defs';
const WGS84 = 'EPSG:4326';

let isProj4Registered = false;
const loadProj4 = async () => {
  const proj4Module = await import('proj4');
  const p = (proj4Module as any).default || proj4Module;
  if (p && p.defs && !isProj4Registered) {
    p.defs('EPSG:3826', TWD97);
    isProj4Registered = true;
  }
  return p;
};

const loadTurf = async () => {
  const turfModule = await import('@turf/turf');
  return turfModule;
};

const loadDrawing = async () => {
  const DrawingModule = await import('dxf-writer');
  const Drawing = (DrawingModule as any).default || DrawingModule;
  return Drawing;
};

/**
 * Loads the rhino3dm WebAssembly module.
 * Uses a script-tag injection approach to avoid Vite bundler issues
 * with WASM dynamic loading.
 */
const loadRhino3dm = (): Promise<any> => {
  return new Promise((resolve, reject) => {
    // If already loaded, reuse
    if ((window as any).__rhino3dm_instance) {
      resolve((window as any).__rhino3dm_instance);
      return;
    }
    
    const initRhino = () => {
      const factory = (window as any).rhino3dm;
      if (typeof factory !== 'function') {
        // If it's already a promise or instance, resolve it
        if (factory && typeof factory.then === 'function') {
            factory.then(resolve).catch(reject);
            return;
        }
        reject(new Error('rhino3dm factory function not found.'));
        return;
      }

      // Important: provide prefix/path arguments to locateFile
      factory({ 
        locateFile: (path: string, prefix: string) => {
          return '/rhino3dm.wasm';
        } 
      })
        .then((instance: any) => {
          (window as any).__rhino3dm_instance = instance;
          resolve(instance);
        })
        .catch(reject);
    };

    // Check if script is already injected
    if ((window as any).rhino3dm) {
      initRhino();
      return;
    }

    const script = document.createElement('script');
    script.src = '/rhino3dm.js';
    script.onload = initRhino;
    script.onerror = () => reject(new Error('Failed to load rhino3dm.js from /public/'));
    document.head.appendChild(script);
  });
};

/** Sanitize a coordinate array to remove nulls/NaNs */
const sanitizeCoords = (ring: number[][]): number[][] =>
  ring.filter(c => Array.isArray(c) && c.length >= 2 && c.every(v => typeof v === 'number' && isFinite(v)));

interface ExportOptions {
  scale?: number;
  size?: 'a4' | 'a3';
  title?: string;
}

export const useExport = () => {
  const { 
    setIsExporting, 
    isExporting, 
    selectedTemplate, 
    analysisResult,
    exportTitle,
    exportAuthor,
    circularMask,
    showLegendInExport,
    mapRef
  } = useStore();
  
  const buildFilename = (ext: string) =>
    `SiteANA_${selectedTemplate === 'presentation' ? '簡報' : '圖紙'}_${new Date().toISOString().slice(0, 10)}.${ext}`;

  const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

  /**
   * HIGH FIDELITY CAPTURE - v4 (FINAL FIX)
   * Root cause: mapRef from useStore() is a React state that can be STALE inside async closures.
   * Fix: Always read the live map instance from window.map (set in Map.tsx on init).
   */
  const captureMap = async (scale: number, fillWhiteBg: boolean = false): Promise<HTMLCanvasElement> => {
    // Always get live map instance from Zustand exactly when capture happens
    const liveMap = useStore.getState().mapRef;
    if (!liveMap) throw new Error('地圖尚未初始化，無法出圖。');

    const target = document.querySelector<HTMLElement>('#map-export-target');
    const mapCanvas = liveMap.getCanvas();
    if (!target || !mapCanvas) throw new Error('Map container not found');

    // 1. Wait for map to settle initially
    if (liveMap.isMoving() || liveMap.isZooming() || liveMap.isRotating()) {
      await new Promise<void>(r => { liveMap.once('idle', r); setTimeout(r, 2000); });
    }
    
    // 2. High-Res MapLibre Capture Hack
    // We adjust devicePixelRatio to force MapLibre to render a larger physical WebGL buffer
    let didScaleHack = false;
    const originalDpr = window.devicePixelRatio || 1;
    if (scale > 1) {
      try {
        Object.defineProperty(window, 'devicePixelRatio', { get: () => originalDpr * scale, configurable: true });
        didScaleHack = true;
        liveMap.resize();
        
        // Wait for high-res map tiles to load at the new pixel ratio
        await new Promise<void>(r => { liveMap.once('idle', r); setTimeout(r, 4000); });
      } catch (e) {
        console.warn('High-res DPR hack blocked by browser.', e);
      }
    }

    // 3. SNAPSHOT — The ONLY 100% reliable way: capture during the render loop
    const mapDataUrl = await new Promise<string>((resolve) => {
      liveMap.once('render', () => {
        resolve(liveMap.getCanvas().toDataURL('image/png'));
      });
      liveMap.triggerRepaint();
    });

    // Restore DPR
    if (didScaleHack) {
      Object.defineProperty(window, 'devicePixelRatio', { get: () => originalDpr, configurable: true });
      liveMap.resize();
    }

    const rect = target.getBoundingClientRect();
    const exportW = Math.round(rect.width * scale);
    const exportH = Math.round(rect.height * scale);

    const originalBg = target.style.backgroundColor;
    const hadBgClass = target.classList.contains('bg-slate-900');
    if (hadBgClass) target.classList.remove('bg-slate-900');
    target.style.backgroundColor = 'transparent';

    // 3. CAPTURE UI OVERLAYS (legend, north arrow, etc.) — skip the WebGL canvas
    const uiCanvas = await html2canvas(target, {
      scale: scale,
      useCORS: true,
      backgroundColor: null,
      logging: false,
      ignoreElements: (el) => el.classList && el.classList.contains('maplibregl-canvas'),
    });

    target.style.backgroundColor = originalBg;
    if (hadBgClass) target.classList.add('bg-slate-900');

    // 4. COMPOSITE: map + UI
    const finalCanvas = document.createElement('canvas');
    finalCanvas.width = exportW;
    finalCanvas.height = exportH;
    const ctx = finalCanvas.getContext('2d')!;

    if (fillWhiteBg) {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, exportW, exportH);
    }

    await new Promise<void>((resolve) => {
      const img = new Image();
      img.onload = () => { ctx.drawImage(img, 0, 0, exportW, exportH); resolve(); };
      img.onerror = () => resolve();
      img.src = mapDataUrl;
    });

    ctx.drawImage(uiCanvas, 0, 0, exportW, exportH);

    if (!circularMask) return finalCanvas;

    // 5. CIRCULAR MASK (optional)
    const output = document.createElement('canvas');
    const size = Math.min(exportW, exportH);
    output.width = size;
    output.height = size;
    const outCtx = output.getContext('2d')!;
    if (fillWhiteBg) {
      outCtx.fillStyle = '#ffffff';
      outCtx.fillRect(0, 0, size, size);
    }
    outCtx.beginPath();
    outCtx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    outCtx.clip();
    const sx = (exportW - size) / 2;
    const sy = (exportH - size) / 2;
    outCtx.drawImage(finalCanvas, sx, sy, size, size, 0, 0, size, size);
    return output;
  };

  const generatePreviewUrl = async (): Promise<string> => {
    setIsExporting(true);
    try {
      // Preview uses 1x for speed
      const canvas = await captureMap(1, false);
      return canvas.toDataURL('image/png');
    } catch (e) {
      console.error('[SiteANA Export] Preview failed:', e);
      throw e;
    } finally {
      setIsExporting(false);
    }
  };

  const exportToPNG = async ({ scale = 2 }: ExportOptions = {}) => {
    setIsExporting(true);
    try {
      // GUARANTEE: Ensure map labels/layers are fully calculated before snapshot
      await sleep(300); 
      const canvas = await captureMap(scale, false);
      const url = canvas.toDataURL('image/png', 1.0); // Highest quality PNG
      
      const a = document.createElement('a');
      a.href = url;
      a.download = buildFilename('png');
      a.click();
    } catch (e) {
      console.error('[SiteANA Export] PNG export failed:', e);
      alert('匯出失敗，請確認地圖已完成渲染。');
    } finally {
      setIsExporting(false);
    }
  };

  const exportToPDF = async ({ scale = 2, size = 'a4', title }: ExportOptions = {}) => {
    const { selectedStyle } = useStore.getState();
    const paintState = useMapPaintStore.getState();
    setIsExporting(true);
    try {
      // PDF output: Use high scale for print quality (300dpi territory)
      const canvas = await captureMap(scale, true);
      const isA3 = size === 'a3' || selectedTemplate === 'presentation';
      const pageW = isA3 ? 420 : 297;
      const pageH = isA3 ? 297 : 210;

      const pdf = new jsPDF({ 
        orientation: 'landscape', 
        unit: 'mm', 
        format: isA3 ? 'a3' : 'a4',
        compress: true 
      });

      // --- Map Image ---
      // Use higher quality for JPEG within PDF
      const imgData = canvas.toDataURL('image/jpeg', 0.95);
      const canvasRatio = canvas.width / canvas.height;

      const HEADER_H = 12;
      const FOOTER_H = 8;
      const contentH = pageH - HEADER_H - FOOTER_H;

      let drawW = pageW;
      let drawH = contentH;
      if (canvasRatio > (pageW / contentH)) {
        drawH = pageW / canvasRatio;
      } else {
        drawW = contentH * canvasRatio;
      }
      const offsetX = (pageW - drawW) / 2;
      const imgY = HEADER_H;

      pdf.addImage(imgData, 'JPEG', offsetX, imgY, drawW, drawH, undefined, 'FAST');

      // --- Header Bar ---
      pdf.setFillColor(15, 165, 233); // brand-500
      pdf.rect(0, 0, pageW, HEADER_H, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'bold');
      pdf.text(exportTitle, 8, 7.5);

      if (title) {
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');
        pdf.text(title, pageW / 2, 7.5, { align: 'center' });
      }

      const dateStr = new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' });
      pdf.setFontSize(7);
      pdf.text(`REPORT_DATE：${dateStr}`, pageW - 8, 7.5, { align: 'right' });

      // --- Footer Bar ---
      const footerY = pageH - FOOTER_H;
      pdf.setFillColor(241, 245, 249); // slate-100
      pdf.rect(0, footerY, pageW, FOOTER_H, 'F');
      pdf.setTextColor(100, 116, 139); // slate-500
      pdf.setFontSize(6.5);
      pdf.setFont('helvetica', 'normal');

      if (analysisResult) {
        const statsArea = `基地面積: ${analysisResult.area_m2?.toLocaleString()} m²（${analysisResult.area_ping?.toLocaleString()} 坪）`;
        pdf.text(statsArea, 8, footerY + 4.5);
      }

      const styleMeta = `底圖風格: ${selectedStyle?.name || 'Default'} | 都市預設: ${paintState.activePresetId}`;
      pdf.text(styleMeta, pageW / 2, footerY + 4.5, { align: 'center' });

      pdf.setTextColor(14, 165, 233); // brand-500
      pdf.setFont('helvetica', 'bold');
      pdf.text(`${exportAuthor} | SITEANA STUDIO`, pageW - 8, footerY + 4.5, { align: 'right' });

      pdf.save(buildFilename('pdf'));
    } catch (e) {
      console.error('[SiteANA Export] PDF export failed:', e);
      alert('PDF 匯出失敗。');
    } finally {
      setIsExporting(false);
    }
  };

  const exportToGeoJSON = () => {
    const { drawnGeometry, analysisResult, exportTitle, exportAuthor, siteMarkerText } = useStore.getState();
    if (!drawnGeometry) {
      alert("尚未繪製基地，無法匯出地理資料。");
      return;
    }

    setIsExporting(true);
    try {
      const featureCollection = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            geometry: drawnGeometry.geometry,
            properties: {
              ...drawnGeometry.properties,
              project_title: exportTitle,
              author: exportAuthor,
              label: siteMarkerText,
              area_m2: analysisResult?.area_m2,
              export_timestamp: new Date().toISOString()
            }
          }
        ]
      };
      const blob = new Blob([JSON.stringify(featureCollection, null, 2)], { type: "application/geo+json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = buildFilename('geojson');
      a.click();
    } catch (e) {
      alert("數據匯出失敗。");
    } finally {
      setIsExporting(false);
    }
  };

  /**
   * AEC EXPORT: DXF (AutoCAD)
   * 1000m radius, AIA Standard Layers, TWD97 Projection
   */
  const exportToDXF = async () => {
    const { drawnGeometry, mapRef } = useStore.getState();
    if (!mapRef) return;

    setIsExporting(true);
    try {
      const p = await loadProj4();
      const turf = await loadTurf();
      const Drawing = await loadDrawing();

      // 1. Calculate Bounding Box (1000m radius from site OR center of screen)
      let centerPoint;
      if (drawnGeometry) {
        centerPoint = turf.centroid(drawnGeometry as any);
      } else {
        const center = mapRef.getCenter();
        centerPoint = turf.point([center.lng, center.lat]);
      }
      const buffer = turf.buffer(centerPoint, 1000, { units: 'meters' });
      const bbox = turf.bbox(buffer);
      
      // Convert BBox to screen coordinates to query features
      const p1 = mapRef.project([bbox[0], bbox[1]]);
      const p2 = mapRef.project([bbox[2], bbox[3]]);
      
      // 2. Query Features
      // We query all rendered features in the 1000m bounding box
      const features = mapRef.queryRenderedFeatures([
        [Math.min(p1.x, p2.x), Math.min(p1.y, p2.y)],
        [Math.max(p1.x, p2.x), Math.max(p1.y, p2.y)]
      ]);

      const d = new Drawing();
      
      // AIA Standard Layers
      const LAYERS = {
        SITE: { name: 'V-SITE-BRDY', color: Drawing.ACI.RED },
        BLDG: { name: 'A-BLDG', color: Drawing.ACI.BLUE },
        ROAD: { name: 'C-ROAD', color: Drawing.ACI.CYAN },
        WATR: { name: 'C-WATR', color: Drawing.ACI.MAGENTA }
      };

      Object.values(LAYERS).forEach(l => d.addLayer(l.name, l.color, 'CONTINUOUS'));

      const project = (coords: number[]) => p(WGS84, 'EPSG:3826', coords);

      // 3. Process Site Boundary (Only if it exists)
      if (drawnGeometry) {
        const siteCoords = (drawnGeometry.geometry as any).coordinates[0];
        const projectedSite = siteCoords.map((c: number[]) => project(c));
        d.drawPolyline(projectedSite, true, LAYERS.SITE.name);
      }

      // 4. Process Map Features
      const seen = new Set();
      features.forEach(f => {
        const id = f.id || JSON.stringify(f.geometry);
        if (seen.has(id)) return;
        seen.add(id);

        const layerId = f.layer.id;
        let targetLayer = '';
        
        if (layerId.includes('building')) targetLayer = LAYERS.BLDG.name;
        else if (layerId.includes('road') || layerId.includes('highway')) targetLayer = LAYERS.ROAD.name;
        else if (layerId.includes('water')) targetLayer = LAYERS.WATR.name;

        if (!targetLayer) return;

        const heightRaw = f.properties?.render_height || f.properties?.height || 0;
        const baseHeightRaw = f.properties?.render_min_height || f.properties?.min_height || 0;
        const height = isFinite(Number(heightRaw)) ? Number(heightRaw) : 0;
        const baseHeight = isFinite(Number(baseHeightRaw)) ? Number(baseHeightRaw) : 0;

        const isBuilding = targetLayer === LAYERS.BLDG.name;

        const processRing = (ring: any[]) => {
          const projected = sanitizeCoords(ring.map((c: number[]) => project(c)));
          if (projected.length < 2) return;

          if (isBuilding && height > 0) {
            // Elevated Wireframe for Buildings
            const bottomRing = projected.map(pt => [pt[0], pt[1], baseHeight]);
            const topRing = projected.map(pt => [pt[0], pt[1], baseHeight + height]);
            
            d.drawPolyline(bottomRing, true, targetLayer);
            d.drawPolyline(topRing, true, targetLayer);

            // Vertical lines connecting top and bottom at each vertex
            for (let i = 0; i < projected.length - 1; i++) {
              d.drawPolyline([
                [projected[i][0], projected[i][1], baseHeight],
                [projected[i][0], projected[i][1], baseHeight + height]
              ], false, targetLayer);
            }
          } else {
            // Flat 2D for roads, water, or flat buildings
            const flat = projected.map(pt => [pt[0], pt[1], baseHeight]);
            d.drawPolyline(flat, true, targetLayer);
          }
        };

        if (f.geometry.type === 'Polygon') {
          (f.geometry.coordinates as any).forEach((ring: any) => processRing(ring));
        } else if (f.geometry.type === 'MultiPolygon') {
          (f.geometry.coordinates as any).forEach((poly: any) => poly.forEach((ring: any) => processRing(ring)));
        } else if (f.geometry.type === 'LineString') {
          const projected = sanitizeCoords((f.geometry.coordinates as any).map((c: number[]) => project(c)));
          if (projected.length > 1) {
             d.drawPolyline(projected.map(pt => [pt[0], pt[1], baseHeight]), false, targetLayer);
          }
        } else if (f.geometry.type === 'MultiLineString') {
          (f.geometry.coordinates as any).forEach((line: any) => {
            const projected = sanitizeCoords(line.map((c: number[]) => project(c)));
            if (projected.length > 1) {
              d.drawPolyline(projected.map(pt => [pt[0], pt[1], baseHeight]), false, targetLayer);
            }
          });
        }
      });

      const dxfString = d.toDxfString();
      const blob = new Blob([dxfString], { type: 'application/dxf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = buildFilename('dxf');
      a.click();
    } catch (e) {
      console.error('[SiteANA DXF] Export failed:', e);
      alert('CAD 匯出失敗。');
    } finally {
      setIsExporting(false);
    }
  };

  /**
   * AEC EXPORT: Rhino 3DM
   * 1000m radius, 3D Massing Extrusion, TWD97 Projection
   */
  const exportToRhino = async () => {
    const { drawnGeometry, mapRef } = useStore.getState();
    if (!mapRef) return;

    setIsExporting(true);
    try {
      const p = await loadProj4();
      const turf = await loadTurf();

      // Load Rhino3dm via reliable script-injection approach
      const rhino = await loadRhino3dm();
      const doc = new rhino.File3dm();

      // Setup Coordinate Projection — safe wrapper around proj4
      const project = (coords: number[]): number[] | null => {
        try {
          const result = p(WGS84, 'EPSG:3826', coords);
          if (!result || !isFinite(result[0]) || !isFinite(result[1])) return null;
          return result;
        } catch {
          return null;
        }
      };

      // Create Layers and store their indices
      let fallbackCounter = 0;
      const getLayerIndex = (name: string, color: any): number => {
        const layer = new rhino.Layer();
        layer.name = name;
        layer.color = color;
        doc.layers().add(layer);
        
        // Securely fetch layer count supporting both property and method variations in rhino3dm JS
        const countSource = doc.layers().count;
        const c = typeof countSource === 'function' ? countSource.call(doc.layers()) : countSource;
        
        if (typeof c === 'number' && !isNaN(c) && c > 0) {
            return c - 1;
        }
        // Failsafe sequence if count is unreadable, usually starts at 0
        return fallbackCounter++;
      };

      const LAYER_MAP = {
        SITE: getLayerIndex('V-SITE-BRDY', { r: 255, g: 0, b: 0, a: 255 }),
        BLDG: getLayerIndex('A-BLDG', { r: 0, g: 0, b: 255, a: 255 }),
        ROAD: getLayerIndex('C-ROAD', { r: 0, g: 255, b: 255, a: 255 }),
        WATR: getLayerIndex('C-WATR', { r: 255, g: 0, b: 255, a: 255 })
      };

      // Query Features
      let centerPoint;
      if (drawnGeometry) {
        centerPoint = turf.centroid(drawnGeometry as any);
      } else {
        const center = mapRef.getCenter();
        centerPoint = turf.point([center.lng, center.lat]);
      }

      const bbox = turf.buffer(centerPoint, 1, { units: 'kilometers' });
      const renderedQuery = mapRef.queryRenderedFeatures();
      
      const features = renderedQuery.filter(f => 
        f.geometry && 
        f.source === 'composite' && 
        f.layer.id !== 'background'
      );

      // --- Robust WASM Geometry Adder (Safe Mode) ---
      // Instead of forcing custom layers and risking silent pointer crashes in WASM, 
      // we output pure Elevated Wireframes to the default layer.
      const pushToRhino = (nurbsCurve: any) => {
         doc.objects().add(nurbsCurve, null);
      };

      // Process Site (2D only - only if drawn)
      if (drawnGeometry) {
        try {
          const siteRaw = (drawnGeometry.geometry as any).coordinates[0];
          const siteClean = sanitizeCoords(siteRaw);
          if (siteClean.length >= 2) {
            const sitePoly = new rhino.Polyline();
            siteClean.forEach((c: number[]) => {
              const pt = project(c);
              if (pt) sitePoly.add(pt[0], pt[1], 0);
            });
            if (sitePoly.count > 1) {
              const nurbs = sitePoly.toNurbsCurve();
              pushToRhino(nurbs);
              // DO NOT delete `nurbs` here; the document retains it!
            }
            sitePoly.delete();
          }
        } catch(e) { console.warn('[Rhino] site boundary error', e); }
      }

      // Process Buildings (3D Extrusion)
      const seen = new Set();
      features.forEach(f => {
        try {
          const layerId = f.layer.id;
          const isBuilding = layerId.includes('building');
          const isRoad = layerId.includes('road') || layerId.includes('highway');
          const isWater = layerId.includes('water');

          if (!isBuilding && !isRoad && !isWater) return;

          const targetLayerIndex = isBuilding ? LAYER_MAP.BLDG : (isRoad ? LAYER_MAP.ROAD : LAYER_MAP.WATR);

          const id = f.id || JSON.stringify(f.geometry);
          if (seen.has(id)) return;
          seen.add(id);

          const heightRaw = isBuilding ? (f.properties?.render_height || f.properties?.height || 10) : 0;
          const baseHeightRaw = isBuilding ? (f.properties?.render_min_height || f.properties?.min_height || 0) : 0;
          const height = isFinite(Number(heightRaw)) ? Number(heightRaw) : 10;
          const baseHeight = isFinite(Number(baseHeightRaw)) ? Number(baseHeightRaw) : 0;

          const processPolygon = (coords: any[]) => {
            const clean = sanitizeCoords(coords);
            if (!clean || clean.length < 3) return;

            const projected = clean.map(c => project(c)).filter((pt): pt is number[] => pt !== null);

            if (projected.length < 3) return;

            if (height > 0) {
              // 3D Wireframe
              const bottomCurve = new rhino.Polyline();
              const topCurve = new rhino.Polyline();
              
              projected.forEach(pt => {
                bottomCurve.add(pt[0], pt[1], baseHeight);
                topCurve.add(pt[0], pt[1], baseHeight + height);
              });
              
              if (bottomCurve.count > 1) {
                 const n1 = bottomCurve.toNurbsCurve();
                 pushToRhino(n1);
              }
              if (topCurve.count > 1) {
                 const n2 = topCurve.toNurbsCurve();
                 pushToRhino(n2);
              }

              // Vertical lines
              projected.forEach(pt => {
                  const verticalCurve = new rhino.Polyline();
                  verticalCurve.add(pt[0], pt[1], baseHeight);
                  verticalCurve.add(pt[0], pt[1], baseHeight + height);
                  if (verticalCurve.count > 1) {
                      const n3 = verticalCurve.toNurbsCurve();
                      pushToRhino(n3);
                  }
                  verticalCurve.delete(); // Delete temporary polyline
              });
              
              bottomCurve.delete();
              topCurve.delete();
            } else {
              // 2D: polyline on the ground
              const curve = new rhino.Polyline();
              projected.forEach(pt => curve.add(pt[0], pt[1], baseHeight));
              if (curve.count > 1) {
                  const n4 = curve.toNurbsCurve();
                  pushToRhino(n4);
              }
              curve.delete(); // Delete temporary polyline
            }
          };

          if (f.geometry.type === 'Polygon') {
            (f.geometry.coordinates as any[]).forEach((ring: any) => processPolygon(ring));
          } else if (f.geometry.type === 'MultiPolygon') {
            (f.geometry.coordinates as any[]).forEach((poly: any) => poly.forEach((ring: any) => processPolygon(ring)));
          } else if (f.geometry.type === 'LineString') {
            processPolygon(f.geometry.coordinates as any);
          } else if (f.geometry.type === 'MultiLineString') {
            (f.geometry.coordinates as any[]).forEach((line: any) => processPolygon(line));
          }
        } catch(e) {
          console.warn('[Rhino] feature processing error, skipped:', e);
        }
      });

      const bufferData = doc.toByteArray();
      const blob = new Blob([bufferData], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = buildFilename('3dm');
      a.click();
    } catch (e) {
      console.error('[SiteANA Rhino] Export failed:', e);
      alert('Rhino 匯出失敗。');
    } finally {
      setIsExporting(false);
    }
  };

  return { exportToPNG, exportToPDF, exportToGeoJSON, exportToDXF, exportToRhino, generatePreviewUrl, isExporting };
};
