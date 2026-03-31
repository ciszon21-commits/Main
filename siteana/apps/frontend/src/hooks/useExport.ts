import { useStore } from '../store/useStore';
import { useMapPaintStore } from '../store/useMapPaintStore';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

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
    siteMarkerText
  } = useStore();
  
  const buildFilename = (ext: string) =>
    `SiteANA_${selectedTemplate === 'presentation' ? '簡報' : '圖紙'}_${new Date().toISOString().slice(0, 10)}.${ext}`;

  const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

  const captureMap = async (scale: number, fillWhiteBg: boolean = false): Promise<HTMLCanvasElement> => {
    const target = document.querySelector<HTMLElement>('#map-export-target');
    const mapCanvas = document.querySelector('.maplibregl-canvas') as HTMLCanvasElement;
    if (!target || !mapCanvas) throw new Error('Map container not found');

    // Wait 1 frame so UI state is propagated (e.g., hiding legend)
    await sleep(100); 

    // --- HIGH RES MAP FIX ---
    // Make DOM backgrounds transparent temporarily so uiCanvas is just the UI elements
    const originalTargetClasses = target.className;
    target.classList.remove('bg-slate-900');
    
    const mapDiv = mapCanvas.parentElement;
    const originalMapDivClasses = mapDiv?.className || '';
    if (mapDiv) {
      mapDiv.classList.remove('bg-slate-900');
      mapDiv.style.backgroundColor = 'transparent';
    }

    // Capture ONLY the UI overlays (Legend, Scale, etc.), ignoring Maplibre canvas
    const uiCanvas = await html2canvas(target, {
      scale,
      useCORS: true,
      backgroundColor: null,
      logging: false,
      ignoreElements: (element) => element.classList && element.classList.contains('maplibregl-canvas'),
    });

    // Restore DOM
    target.className = originalTargetClasses;
    if (mapDiv) {
      mapDiv.className = originalMapDivClasses;
      mapDiv.style.backgroundColor = '';
    }

    const rawCanvas = document.createElement('canvas');
    rawCanvas.width = uiCanvas.width;
    rawCanvas.height = uiCanvas.height;
    const ctx = rawCanvas.getContext('2d', { alpha: true })!;

    // Draw Maplibre WebGL directly
    if (!circularMask && fillWhiteBg) {
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, rawCanvas.width, rawCanvas.height);
    }
    
    // Smooth drawing for the map
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(mapCanvas, 0, 0, rawCanvas.width, rawCanvas.height);
    
    // Overlay the UI
    ctx.drawImage(uiCanvas, 0, 0);

    if (!circularMask) return rawCanvas;

    // Apply circular mask — crop to circle
    const output = document.createElement('canvas');
    const size = Math.min(rawCanvas.width, rawCanvas.height);
    output.width = size;
    output.height = size;
    const outCtx = output.getContext('2d')!;
    
    // Fill white background for PDF, else keep transparent for PNG
    if (fillWhiteBg) {
      outCtx.fillStyle = '#fff';
      outCtx.fillRect(0, 0, size, size);
    } else {
      outCtx.clearRect(0, 0, size, size);
    }

    outCtx.beginPath();
    outCtx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    outCtx.clip();

    const sx = (rawCanvas.width - size) / 2;
    const sy = (rawCanvas.height - size) / 2;
    outCtx.drawImage(rawCanvas, sx, sy, size, size, 0, 0, size, size);
    
    return output;
  };

  const generatePreviewUrl = async (): Promise<string> => {
    setIsExporting(true);
    try {
      const canvas = await captureMap(1, false); // Fast render at 1x
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
      const canvas = await captureMap(scale, false);
      const url = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = url;
      a.download = buildFilename('png');
      a.click();
    } catch (e) {
      console.error('[SiteANA Export] PNG export failed:', e);
      alert('匯出失敗，請確認地圖已載入。');
    } finally {
      setIsExporting(false);
    }
  };

  const exportToPDF = async ({ scale = 2, size = 'a4', title }: ExportOptions = {}) => {
    const { selectedStyle } = useStore.getState();
    const paintState = useMapPaintStore.getState();
    setIsExporting(true);
    try {
      // PDF needs white background to prevent transparent parts becoming black in JPEG
      const canvas = await captureMap(scale, true);
      const isA3 = size === 'a3' || selectedTemplate === 'presentation';
      const pageW = isA3 ? 420 : 297;
      const pageH = isA3 ? 297 : 210;

      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: isA3 ? 'a3' : 'a4' });

      // ── Map Image ─────────────────────────────────────────────────
      const imgData = canvas.toDataURL('image/jpeg', 0.93);
      const canvasRatio = canvas.width / canvas.height;

      // Reserve room for header and footer
      const HEADER_H = 12;
      const FOOTER_H = 8;
      const contentH = pageH - HEADER_H - FOOTER_H;

      let drawW = pageW;
      let drawH = contentH;
      if ((canvas.width / canvas.height) > (pageW / contentH)) {
        drawH = pageW / canvasRatio;
      } else {
        drawW = contentH * canvasRatio;
      }
      const offsetX = (pageW - drawW) / 2;
      const imgY = HEADER_H;

      pdf.addImage(imgData, 'JPEG', offsetX, imgY, drawW, drawH);

      // ── Header Bar ────────────────────────────────────────────────
      pdf.setFillColor(15, 165, 233);           // brand-500
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

      pdf.setFontSize(7);
      const dateStr = new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' });
      pdf.text(`出圖日期：${dateStr}`, pageW - 8, 7.5, { align: 'right' });

      // ── Footer Bar ────────────────────────────────────────────────
      const footerY = pageH - FOOTER_H;
      pdf.setFillColor(241, 245, 249);          // slate-100
      pdf.rect(0, footerY, pageW, FOOTER_H, 'F');
      pdf.setTextColor(100, 116, 139);          // slate-500
      pdf.setFontSize(6.5);
      pdf.setFont('helvetica', 'normal');

      // Left: analysis stats if available
      if (analysisResult) {
        const statsArea = `面積: ${analysisResult.area_m2?.toLocaleString()} m²（${analysisResult.area_ping?.toLocaleString()} 坪）`;
        pdf.text(statsArea, 8, footerY + 4.5);
      }

      // Middle: style info
      const styleMeta = `底圖: ${selectedStyle?.name || 'Default'} | 建築顏色: ${paintState.buildingColor}`;
      pdf.text(styleMeta, pageW / 2, footerY + 4.5, { align: 'center' });

      // Right: branding & author
      pdf.setTextColor(14, 165, 233);           // brand-500
      pdf.setFont('helvetica', 'bold');
      pdf.text(`${exportAuthor}  |  SiteANA studio`, pageW - 8, footerY + 4.5, { align: 'right' });

      pdf.save(buildFilename('pdf'));
    } catch (e) {
      console.error('[SiteANA Export] PDF export failed:', e);
      alert('匯出失敗，請確認地圖已載入。');
    } finally {
      setIsExporting(false);
    }
  };

  return { exportToPNG, exportToPDF, generatePreviewUrl, isExporting };
};
