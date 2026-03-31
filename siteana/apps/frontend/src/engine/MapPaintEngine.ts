import maplibregl from 'maplibre-gl';
import { MapPaintState } from '../store/useMapPaintStore';

export class MapPaintEngine {
  /**
   * 套用所有儲存的視覺設定到地圖實例
   */
  static applyAll(map: maplibregl.Map, state: MapPaintState) {
    if (!map.isStyleLoaded()) return;

    console.log('[MapPaintEngine] Applying all visual overrides...');
    this.applyRoads(map, state);
    this.applyBuildings(map, state);
    this.applyLandUse(map, state);
    this.applyLabels(map, state);
    this.applyEnvironment(map, state);
  }

  /**
   * 道路顏色控制 - 針對 OpenFreeMap Liberty 圖層優化
   */
  static applyRoads(map: maplibregl.Map, state: MapPaintState) {
    const { roadColors } = state;
    
    // 對應 Store 中的 key 與地圖 ID 中的關鍵字
    const mappings: Record<string, string[]> = {
      highway: ['motorway', 'trunk', 'highway', 'road_motorway', 'road_trunk'],
      primary: ['primary', 'major_road', 'road_primary'],
      secondary: ['secondary', 'medium_road', 'road_secondary'],
      residential: ['residential', 'tertiary', 'minor_road', 'street', 'road_tertiary', 'road_major_residential', 'road_minor'],
      path: ['path', 'pedestrian', 'footway', 'cycleway', 'track', 'service', 'road_service', 'road_path'],
    };

    const layers = map.getStyle()?.layers || [];

    Object.entries(mappings).forEach(([type, keywords]) => {
      const color = (roadColors as any)[type];
      if (!color) return;
      
      const targetLayerIds = layers.filter(l => 
        (l.type === 'line') && 
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetLayerIds.forEach(id => {
        try {
          map.setPaintProperty(id, 'line-color', color);
        } catch (e) {}
      });
    });
  }

  /**
   * 建築物與 3D 視覺
   */
  static applyBuildings(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    const buildingLayers = layers.filter(l => 
      l.id.toLowerCase().includes('building') && 
      (l.type === 'fill' || l.type === 'fill-extrusion')
    ).map(l => l.id);

    // 依據樓層設定漸層色 (低層: 淺灰, 中層: 橘色, 高層: 深紅)
    const gradientExpression = [
      'interpolate', ['linear'], ['get', 'render_height'],
      0, '#e2e8f0',   // 平房/低矮 (0m)
      15, '#fcd34d',  // 低層 (5樓左右, ~15m)
      36, '#f97316',  // 中層 (12樓左右, ~36m)
      80, '#b91c1c'   // 高層 (25樓以上, 80m+)
    ];

    const isGradient = state.activePresetId === 'urban_density';

    buildingLayers.forEach(id => {
      try {
        const layer = map.getLayer(id);
        if (!layer) return;

        // --- Visibility ---
        map.setLayoutProperty(id, 'visibility', state.buildingVisibility ? 'visible' : 'none');
        if (!state.buildingVisibility) return;

        const colorProp = isGradient ? gradientExpression : state.buildingColor;

        if (layer.type === 'fill') {
          map.setPaintProperty(id, 'fill-color', colorProp);
          map.setPaintProperty(id, 'fill-opacity', state.buildingOpacity);
        } else if (layer.type === 'fill-extrusion') {
          // If in 2D mode, hide extrusion layers IF there's likely a fill layer (usually true in OpenFreeMap)
          // Or just flatten them properly. For SiteANA, we want 2D to be REALLY flat.
          if (!state.building3D) {
             map.setPaintProperty(id, 'fill-extrusion-height', 0);
             map.setPaintProperty(id, 'fill-extrusion-base', 0);
             map.setPaintProperty(id, 'fill-extrusion-opacity', 0); // Hide extrusion layer in 2D
          } else {
             map.setPaintProperty(id, 'fill-extrusion-color', colorProp);
             map.setPaintProperty(id, 'fill-extrusion-opacity', state.buildingOpacity);
             map.setPaintProperty(id, 'fill-extrusion-height', ['get', 'render_height']);
             map.setPaintProperty(id, 'fill-extrusion-base', ['get', 'render_min_height']);
          }
        }
      } catch (e) {}
    });
  }

  /**
   * 土地利用分區
   */
  static applyLandUse(map: maplibregl.Map, state: MapPaintState) {
    const { landUseColors } = state;
    const layers = map.getStyle()?.layers || [];

    const apply = (keywords: string[], color: string) => {
      const targetLayers = layers.filter(l => 
        (l.type === 'fill') &&
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetLayers.forEach(id => {
        try {
          map.setPaintProperty(id, 'fill-color', color);
        } catch (e) {}
      });
    };

    apply(['park', 'garden', 'recreation', 'leisure', 'green', 'grass', 'forest', 'wood', 'landuse_park', 'landuse_grass'], landUseColors.park);
    apply(['water', 'river', 'lake', 'stream', 'ocean', 'sea'], landUseColors.water);
    apply(['residential', 'neighborhood', 'urban', 'landuse_residential'], landUseColors.residential);
    apply(['commercial', 'retail', 'business', 'office', 'landuse_commercial'], landUseColors.commercial);
    apply(['industrial', 'quarry', 'factory', 'landuse_industrial'], landUseColors.industrial);
  }

  /**
   * 標籤文字 (Categorized toggle)
   */
  static applyLabels(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    
    // Categorize keywords to match layer IDs to the 4 categories
    const labelMapping = {
      road: ['road-label', 'highway-name', 'street', 'shield'],
      park: ['park', 'garden', 'recreation', 'square', 'memorial'],
      water: ['water', 'stream', 'ocean', 'sea', 'lake'],
      poi: ['poi', 'place', 'railway', 'airport', 'hospital', 'school', 'station', 'transit', 'label', 'name'] // fallback for all other symbols
    };

    const targetLayers = layers.filter(l => l.type === 'symbol');
    
    targetLayers.forEach(layer => {
      const id = layer.id.toLowerCase();
      
      // Determine which category this layer belongs to
      let category: keyof typeof state.labelVisibility = 'poi'; // default to poi if unmatched
      if (labelMapping.road.some(k => id.includes(k))) category = 'road';
      else if (labelMapping.park.some(k => id.includes(k))) category = 'park';
      else if (labelMapping.water.some(k => id.includes(k))) category = 'water';
      
      const isVisible = state.labelVisibility[category];

      try {
        map.setLayoutProperty(layer.id, 'visibility', isVisible ? 'visible' : 'none');
      } catch (e) {}
    });
  }

  /**
   * 全局環境 (背景色)
   */
  static applyEnvironment(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    
    // 尋找背景圖層
    const bgLayers = layers.filter(l => l.type === 'background' || l.id === 'background').map(l => l.id);
    bgLayers.forEach(id => {
      try {
        map.setPaintProperty(id, 'background-color', state.backgroundColor);
      } catch (e) {}
    });
  }
}
