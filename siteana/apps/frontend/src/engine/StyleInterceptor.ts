/**
 * StyleInterceptor
 * 
 * 負責在 MapLibre 正式載入底圖前，透過網路攔截 Style JSON，
 * 並且對其內部結構進行暴力清理。
 * 這能確保「草地紋理」、「三叉草符號」這類在初始化階段因非同步問題
 * 而無法根除的圖層，在 MapLibre 解析前就被物理刪除，確保一次到位。
 */

export class StyleInterceptor {
  static async fetchAndCleanStyle(styleUrlOrObj: string | any): Promise<any> {
    try {
      let styleObj: any;

      if (typeof styleUrlOrObj === 'string' && styleUrlOrObj.startsWith('http')) {
        const res = await fetch(styleUrlOrObj);
        styleObj = await res.json();
      } else {
        // Deep clone if it's already an object
        styleObj = JSON.parse(JSON.stringify(styleUrlOrObj));
      }

      if (!styleObj || !styleObj.layers) return styleUrlOrObj;

      // 1. 強力過濾所有擾人的自然環境圖示 (Symbol Layers)
      styleObj.layers = styleObj.layers.filter((l: any) => {
        if (l.type === 'symbol') {
          const id = l.id.toLowerCase();
          const isDistracting = [
            'grass', 'forest', 'wood', 'scrub', 'nature', 'park-symbol', 
            'landuse-icon', 'plant', 'tree', 'vegetation', 'landcover', 
            'landuse', 'wetland', 'pitch', 'leisure', 'garden', 'recreation',
            'orchard', 'vineyard', 'fell', 'tundra', 'glacier'
          ].some(k => id.includes(k));
          
          if (isDistracting) return false; 
        }
        return true;
      });

      // 2. 拔除所有 fill 類型圖層的 fill-pattern
      // 並對自然圖層補上安全底色，避免回退為黑色
      const NATURE_KEYWORDS = ['grass', 'wood', 'forest', 'park', 'garden', 'scrub',
                               'wetland', 'landcover', 'natural', 'leisure', 'vegetation',
                               'allotment', 'orchard', 'vineyard', 'fell', 'sand', 'beach',
                               'pitch', 'recreation', 'golf', 'meadow', 'cemetery', 'green'];
      const WATER_KEYWORDS  = ['water', 'river', 'lake', 'stream', 'ocean', 'sea', 'canal', 'basin'];
      const URBAN_KEYWORDS  = ['pedestrian', 'plaza', 'square', 'bridge', 'parking', 'aeroway', 'runway', 'taxiway', 'apron', 'pier', 'highway', 'transportation'];

      styleObj.layers.forEach((l: any) => {
        if (l.type === 'fill' && l.paint) {
          // 清除 pattern 讓底色能正常顯示
          if (l.paint['fill-pattern'] !== undefined) {
            delete l.paint['fill-pattern'];

            // 若刪除 fill-pattern 後沒有 fill-color，補上中性基底色，後續由 MapPaintEngine 依據 Preset 動態覆蓋
            if (!l.paint['fill-color']) {
              if (WATER_KEYWORDS.some(k => (l.id || '').toLowerCase().includes(k))) {
                l.paint['fill-color'] = '#aad3df'; // 水體藍
              } else {
                l.paint['fill-color'] = '#f8fafc'; // 全域中性保底色
              }
            }
          }
        }
      });

      console.log('[StyleInterceptor] Style cleaning complete. Layers count:', styleObj.layers.length);
      return styleObj;
      
    } catch (err) {
      console.error('[StyleInterceptor] Critical error, falling back to URL string:', err);
      // 如果任何地方出錯，絕對不要回傳半成品的 styleObj，回傳 URL 字串讓 MapLibre 自己抓
      return typeof styleUrlOrObj === 'string' ? styleUrlOrObj : styleUrlOrObj;
    }
  }
}
