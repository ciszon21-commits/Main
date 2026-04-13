import maplibregl from 'maplibre-gl';
import { MapPaintState } from '../store/useMapPaintStore';
import { SunlightEngine } from './SunlightEngine';

export interface SunlightState {
  enabled: boolean;
  date: string;
  time: number;
  opacity: number;
}

export class MapPaintEngine {
  /**
   * Helper to safely set properties only if the layer exists (for Map Instance)
   */
  private static safeSetPaint(map: maplibregl.Map, id: string, prop: string, value: any) {
    if (map.getLayer(id)) {
      try { map.setPaintProperty(id, prop, value); } catch (e) {}
    }
  }

  private static safeSetLayout(map: maplibregl.Map, id: string, prop: string, value: any) {
    if (map.getLayer(id)) {
      try { map.setLayoutProperty(id, prop, value); } catch (e) {}
    }
  }

  /**
   * 道路分類映射 table
   */
  private static readonly ROAD_MAPPINGS: Record<string, string[]> = {
    highway:    ['motorway', 'road_motorway', 'highway_motorway'],
    expressway: ['trunk', 'expressway', 'freeway', 'road_trunk'],
    primary:    ['primary', 'major_road', 'road_primary'],
    secondary:  ['secondary', 'tertiary', 'medium_road', 'road_secondary', 'road_tertiary'],
    residential:['residential', 'minor_road', 'street', 'road_minor', 'road_street', 'road_residential'],
    path:       ['footway', 'cycleway', 'track', 'service', 'road_service', 'road_path', 'road_pedestrian', 'path', 'pedestrian'],
    overpass:   ['bridge_foot', 'pedestrian_bridge', 'steps', 'escalator', 'tunnel_foot'],
    crossing:   ['crossing', 'zebra'],
    transit_rail: ['rail', 'railway', 'major_rail'],
    transit_mrt:  ['subway', 'tram', 'transit', 'bus']
  };

  /**
   * ==========================================
   * 1. 靜態預注入模式 (應用於 Style JSON)
   * ==========================================
   */
  static applyToStyleJSON(style: any, state: MapPaintState) {
    if (!style || !style.layers) return style;
    const { roadColors, landUseColors, activePresetId } = state;
    const preset = activePresetId || '';

    style.layers.forEach((l: any) => {
      const id = (l.id || '').toLowerCase();

      // --- ROADS ---
      if (l.type === 'line') {
        Object.entries(this.ROAD_MAPPINGS).forEach(([type, keywords]) => {
          if (keywords.some(k => id.includes(k))) {
            const color = (roadColors as any)[type];
            if (type === 'transit_rail' || type === 'transit_mrt') {
              l.layout = l.layout || {};
              l.layout.visibility = (preset === 'transit_network') ? 'visible' : 'none';
              if (preset === 'transit_network' && color) {
                l.paint = l.paint || {};
                l.paint['line-color'] = color;
              }
            } else if (color) {
              l.layout = l.layout || {};
              l.layout.visibility = 'visible';
              l.paint = l.paint || {};
              l.paint['line-color'] = color;
              l.paint['line-opacity'] = 1.0;
            }
          }
        });
      }

      // --- BUILDINGS ---
      if ((id.includes('building') || id.includes('structure')) && (l.type === 'fill' || l.type === 'fill-extrusion')) {
        l.layout = l.layout || {};
        l.layout.visibility = state.buildingVisibility ? 'visible' : 'none';
        if (state.buildingVisibility) {
           l.paint = l.paint || {};
           if (l.type === 'fill') {
             l.paint['fill-color'] = state.buildingColor;
             l.paint['fill-opacity'] = state.buildingOpacity;
           } else {
             l.paint['fill-extrusion-color'] = state.buildingColor;
             l.paint['fill-extrusion-opacity'] = state.buildingOpacity;
           }
        }
      }

      // --- LAND USE ---
      if (l.type === 'fill') {
        const check = (keys: string[], color: string) => {
          if (keys.some(k => id.includes(k))) {
            l.paint = l.paint || {};
            l.paint['fill-color'] = color;
            l.paint['fill-opacity'] = 1.0;
          }
        };
        check(['park', 'garden', 'green', 'grass', 'forest', 'wood', 'landcover', 'landuse'], landUseColors.park);
        check(['water', 'river', 'lake', 'ocean', 'sea'], landUseColors.water);
        check(['residential', 'neighborhood', 'house'], landUseColors.residential);
        check(['commercial', 'retail', 'business'], landUseColors.commercial);
        check(['industrial'], landUseColors.industrial);
      }

      // --- LABELS ---
      if (l.type === 'symbol') {
        const isRoad = ['road-label', 'highway-name', 'street', 'shield'].some(k => id.includes(k));
        const isPark = ['park', 'garden', 'green'].some(k => id.includes(k));
        const isWater = ['water', 'sea', 'ocean'].some(k => id.includes(k));
        
        let category: keyof typeof state.labelVisibility = 'poi';
        if (isRoad) category = 'road';
        else if (isPark) category = 'park';
        else if (isWater) category = 'water';

        l.layout = l.layout || {};
        l.layout.visibility = state.labelVisibility[category] ? 'visible' : 'none';
      }
    });

    // Background
    const bg = style.layers.find((l: any) => l.type === 'background');
    if (bg) {
      bg.paint = bg.paint || {};
      bg.paint['background-color'] = state.backgroundColor;
    }

    return style;
  }

  /**
   * ==========================================
   * 2. 動態模式 (應用於已載入的 Map 實例)
   * ==========================================
   */
  static applyAll(map: maplibregl.Map, state: MapPaintState) {
    if (!map.isStyleLoaded()) return;

    this.resetNeutral(map);
    console.log('[MapPaintEngine] Performing dynamic visual sync for:', state.activePresetId);
    
    this.applyRoads(map, state);
    this.applyBuildings(map, state);
    this.applyLandUse(map, state);
    this.applyLabels(map, state);
    this.applyEnvironment(map, state);
  }

  static resetNeutral(map: maplibregl.Map) {
    const layers = map.getStyle()?.layers || [];
    const TRANSIT_KEYWORDS = ['rail', 'railway', 'subway', 'tram', 'transit', 'bus'];
    layers.filter(l => l.type === 'line' && TRANSIT_KEYWORDS.some(k => l.id.toLowerCase().includes(k)))
          .forEach(l => this.safeSetLayout(map, l.id, 'visibility', 'none'));

    const INJECTED_PREFIXES = ['injected-3d-', 'injected-building-outline'];
    layers.filter(l => INJECTED_PREFIXES.some(p => l.id.startsWith(p)))
          .forEach(l => { try { map.removeLayer(l.id); } catch(e) {} });
  }

  static applyRoads(map: maplibregl.Map, state: MapPaintState) {
    const { roadColors } = state;
    const preset = state.activePresetId || '';
    const layers = map.getStyle()?.layers || [];
    const firstLabel = layers.find(l => l.type === 'symbol');

    Object.entries(this.ROAD_MAPPINGS).forEach(([type, keywords]) => {
      const color = (roadColors as any)[type];
      const targetIds = layers.filter(l => 
        l.type === 'line' && keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetIds.forEach(id => {
        if (type === 'transit_rail' || type === 'transit_mrt') {
          this.safeSetLayout(map, id, 'visibility', (preset === 'transit_network' ? 'visible' : 'none'));
          if (preset === 'transit_network' && color) this.safeSetPaint(map, id, 'line-color', color);
          return;
        }
        if (!color) { this.safeSetLayout(map, id, 'visibility', 'none'); return; }
        this.safeSetLayout(map, id, 'visibility', 'visible');
        this.safeSetPaint(map, id, 'line-color', color);
      });
    });
  }

  static applyBuildings(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    const buildings = layers.filter(l => 
      (l.id.toLowerCase().includes('building') || l.id.toLowerCase().includes('structure')) && 
      (l.type === 'fill' || l.type === 'fill-extrusion')
    );

    buildings.forEach(l => {
      this.safeSetLayout(map, l.id, 'visibility', state.buildingVisibility ? 'visible' : 'none');
      if (!state.buildingVisibility) return;
      if (l.type === 'fill') {
        this.safeSetPaint(map, l.id, 'fill-color', state.buildingColor);
        this.safeSetPaint(map, l.id, 'fill-opacity', state.buildingOpacity);
      } else if (l.type === 'fill-extrusion') {
        this.safeSetPaint(map, l.id, 'fill-extrusion-color', state.buildingColor);
        this.safeSetPaint(map, l.id, 'fill-extrusion-opacity', state.buildingOpacity);
      }
    });
  }

  static applyLandUse(map: maplibregl.Map, state: MapPaintState) {
    const { landUseColors } = state;
    const layers = map.getStyle()?.layers || [];
    const apply = (keywords: string[], color: string) => {
      if (!color) return;
      layers.filter(l => l.type === 'fill' && keywords.some(k => l.id.toLowerCase().includes(k)))
            .forEach(l => {
              this.safeSetPaint(map, l.id, 'fill-color', color);
              this.safeSetPaint(map, l.id, 'fill-opacity', 1.0);
            });
    };
    apply(['park', 'garden', 'green', 'grass', 'forest', 'wood', 'landcover', 'landuse'], landUseColors.park);
    apply(['water', 'river', 'lake', 'ocean', 'sea'], landUseColors.water);
    apply(['residential', 'neighborhood', 'house'], landUseColors.residential);
    apply(['commercial', 'retail', 'business'], landUseColors.commercial);
    apply(['industrial'], landUseColors.industrial);
  }

  static applyLabels(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    layers.filter(l => l.type === 'symbol').forEach(l => {
      const id = l.id.toLowerCase();
      let category: keyof typeof state.labelVisibility = 'poi';
      if (['road-label', 'highway-name', 'street', 'shield'].some(k => id.includes(k))) category = 'road';
      else if (['park', 'garden', 'green'].some(k => id.includes(k))) category = 'park';
      else if (['water', 'sea', 'ocean'].some(k => id.includes(k))) category = 'water';
      this.safeSetLayout(map, l.id, 'visibility', state.labelVisibility[category] ? 'visible' : 'none');
    });
  }

  static applyEnvironment(map: maplibregl.Map, state: MapPaintState) {
    this.safeSetPaint(map, 'background', 'background-color', state.backgroundColor);
  }

  static refreshBuildingCache(map: maplibregl.Map) {
    if (!map.isStyleLoaded()) return;
    const features = map.queryRenderedFeatures({ layers: map.getStyle()?.layers.filter(l => l.id.includes('building')).map(l => l.id) });
    console.log('[MapPaintEngine] Cache refreshed:', features.length);
  }

  static applySunlight(map: maplibregl.Map, state: SunlightState) {
    // Optional sunlight logic implementation if needed
  }
}
