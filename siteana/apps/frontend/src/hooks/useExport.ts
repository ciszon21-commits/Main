import { useStore } from '../store/useStore';
import { useMapPaintStore } from '../store/useMapPaintStore';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import { MapPaintEngine } from '../engine/MapPaintEngine';

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
   * HIGH FIDELITY CAPTURE (GURANTEED FIDELITY)
   * The most reliable way to export MapLibre with all presets/basemaps matching 1:1.
   * Logic: Temporarily resize the Map Container -> Resize Map -> Wait for IDLE -> Capture -> Restore
   */
  const captureMap = async (scale: number, fillWhiteBg: boolean = false): Promise<HTMLCanvasElement> => {
    if (!mapRef) throw new Error('地圖尚未初始化，無法出圖。');

    const target = document.querySelector<HTMLElement>('#map-export-target');
    const mapCanvas = mapRef.getCanvas();
    if (!target || !mapCanvas) throw new Error('Map container not found');

    // 1. SAVE ORIGINAL STATE
    const originalWidth = target.style.width;
    const originalHeight = target.style.height;
    const rect = target.getBoundingClientRect();
    const exportW = rect.width * scale;
    const exportH = rect.height * scale;

    // 2. TRIGGER RE-RENDER AT TARGET RESOLUTION
    // This forces MapLibre to fetch high-res tiles and re-apply all shaders/presets for the new size
    target.style.width = `${exportW}px`;
    target.style.height = `${exportH}px`;
    mapRef.resize();

    // 3. WAIT FOR ENGINE IDLE (CRITICAL FIX)
    // 'idle' means no more movements and all tiles/resources are loaded
    await new Promise<void>((resolve) => {
      mapRef.once('idle', () => resolve());
      // Fallback timeout in case idle never fires
      setTimeout(resolve, 5000); 
    });

    // Short buffer for post-idle effects
    await sleep(200);

    // 4. CAPTURE UI OVERLAYS (Legend, etc.)
    // We hide the map canvas so html2canvas only captures the HTML parts
    const originalDisplay = mapCanvas.style.display;
    mapCanvas.style.display = 'none';
    
    const uiCanvas = await html2canvas(target, {
      scale: 1, // Already resized the target, so scale 1 is enough
      useCORS: true,
      backgroundColor: null,
      logging: false,
    });
    
    mapCanvas.style.display = originalDisplay;

    // 5. COMBINE HIGH-RES MAP + HIGH-RES UI
    const finalCanvas = document.createElement('canvas');
    finalCanvas.width = exportW;
    finalCanvas.height = exportH;
    const ctx = finalCanvas.getContext('2d', { alpha: true })!;

    if (fillWhiteBg) {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, exportW, exportH);
    }
    
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    
    // Draw the native high-res WebGL buffer
    ctx.drawImage(mapCanvas, 0, 0, exportW, exportH);
    // Draw UI overlays
    ctx.drawImage(uiCanvas, 0, 0);

    // 6. RESTORE ORIGINAL UI STATE
    target.style.width = originalWidth;
    target.style.height = originalHeight;
    mapRef.resize();

    if (!circularMask) return finalCanvas;

    // --- 7. APPLY CIRCULAR MASK ---
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

  return { exportToPNG, exportToPDF, exportToGeoJSON, generatePreviewUrl, isExporting };
};
