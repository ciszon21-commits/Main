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

      // --- BUILDINGS (3 modes: Urban 3D gradient / Generic 3D grey / 2D flat) ---
      // 'building'    = fill layer (2D footprint)
      // 'building-3d' = fill-extrusion layer (3D massing)
      const isUrban = state.activePresetId === 'urban_density';

      if (id === 'building' && l.type === 'fill') {
        l.layout = l.layout || {};
        l.layout.visibility = state.buildingVisibility ? 'visible' : 'none';
        if (state.buildingVisibility) {
          l.paint = l.paint || {};
          // [NEW] 2D/3D SIMULTANEOUS: Always keep 2D visible as "capping" / "context" layer
          // even when 3D is active. This provides sharp outlines on top of extruded massings.
          delete l.maxzoom;
          l.paint['fill-color'] = state.buildingColor;
          l.paint['fill-opacity'] = state.building3D ? 0.35 : state.buildingOpacity; // Faint if 3D is on
          if (state.buildingOutlineColor) {
            l.paint['fill-outline-color'] = state.buildingOutlineColor;
          }
        }
      }
      if (id === 'building-3d' && l.type === 'fill-extrusion') {
        l.layout = l.layout || {};
        if (!state.buildingVisibility || !state.building3D) {
          // 3D OFF or buildings hidden: hide 3D layer entirely
          l.layout.visibility = 'none';
        } else {
          l.layout.visibility = 'visible';
          l.paint = l.paint || {};
          if (isUrban) {
            // Urban Density: height-based gradient
            l.paint['fill-extrusion-color'] = [
              'interpolate', ['linear'], ['get', 'render_height'],
              0,   '#4575B4',
              10,  '#74ADD1',
              20,  '#E0F3F8',
              35,  '#FFD700',
              55,  '#FDAE61',
              80,  '#F46D43',
              120, '#D73027'
            ];
            l.paint['fill-extrusion-opacity'] = state.buildingOpacity;
          } else {
            // Other presets with 3D ON: light grey semi-transparent volume
            l.paint['fill-extrusion-color'] = '#d1d5db';
            l.paint['fill-extrusion-opacity'] = 0.45;
          }
        }
      }

      // --- LAND USE ---
      // [KEY] Skip building layers — they are handled separately above
      const isBuildingLayer = (id === 'building' || id === 'building-3d' || id.includes('structure'));
      if (l.type === 'fill' && !isBuildingLayer) {
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
  static applyAll(map: maplibregl.Map, state: MapPaintState, _retries = 0) {
    if (!map.isStyleLoaded()) {
      if (_retries < 10) {
        // Retry up to 10 times with increasing delay — style may not be registered yet
        console.warn(`[MapPaintEngine] Style not ready, retry ${_retries + 1}/10 in ${150 * (_retries + 1)}ms`);
        setTimeout(() => this.applyAll(map, state, _retries + 1), 150 * (_retries + 1));
      } else {
        console.error('[MapPaintEngine] Style never became ready after 10 retries.');
      }
      return;
    }

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

  // The user-specified Urban Density height gradient
  static readonly HEIGHT_GRADIENT = [
    'interpolate', ['linear'], ['get', 'render_height'],
    0,   '#4575B4',   // 低層：沉穩湛藍
    10,  '#74ADD1',   // 中低層：灰調水藍
    20,  '#E0F3F8',   // 過渡層(中低)：晨霧雪藍
    35,  '#FFD700',   // 中層：明亮金黃
    55,  '#FDAE61',   // 過渡層(中高)：溫潤琥珀
    80,  '#F46D43',   // 中高層：活力暖橘
    120, '#D73027',   // 超高層：權威赭紅
  ];

  static applyBuildings(map: maplibregl.Map, state: MapPaintState) {
    if (!state.buildingVisibility) {
      this.safeSetLayout(map, 'building', 'visibility', 'none');
      this.safeSetLayout(map, 'building-3d', 'visibility', 'none');
      return;
    }

    const isUrban = state.activePresetId === 'urban_density';

    if (state.building3D) {
      // ============================================
      // 3D ON: Show 3D volumes + 2D as low-zoom preview
      // ============================================

      // 2D preview (zoom 13-14)
      this.safeSetLayout(map, 'building', 'visibility', 'visible');
      if (map.getLayer('building')) {
        try { map.setLayerZoomRange('building', 13, 14); } catch(e) {}
      }
      this.safeSetPaint(map, 'building', 'fill-color', isUrban ? '#4575B4' : '#d1d5db');
      this.safeSetPaint(map, 'building', 'fill-opacity', 0.7);

      // 3D volumes (zoom 14+)
      this.safeSetLayout(map, 'building-3d', 'visibility', 'visible');
      if (map.getLayer('building-3d')) {
        try { map.setLayerZoomRange('building-3d', 14, 24); } catch(e) {}
      }
      // Restore original height data
      this.safeSetPaint(map, 'building-3d', 'fill-extrusion-height', ['get', 'render_height']);
      this.safeSetPaint(map, 'building-3d', 'fill-extrusion-base', ['get', 'render_min_height']);

      if (isUrban) {
        // Urban Density: height-based color gradient
        this.safeSetPaint(map, 'building-3d', 'fill-extrusion-color', this.HEIGHT_GRADIENT as any);
        this.safeSetPaint(map, 'building-3d', 'fill-extrusion-opacity', state.buildingOpacity);
      } else {
        // Other presets: light grey semi-transparent volumes
        this.safeSetPaint(map, 'building-3d', 'fill-extrusion-color', '#d1d5db');
        this.safeSetPaint(map, 'building-3d', 'fill-extrusion-opacity', 0.45);
      }

    } else {
      // ============================================
      // 3D OFF: 2D only, extend to all zoom levels
      // Hide 3D layer entirely (so fill-outline-color works)
      // ============================================
      this.safeSetLayout(map, 'building-3d', 'visibility', 'none');

      this.safeSetLayout(map, 'building', 'visibility', 'visible');
      if (map.getLayer('building')) {
        try { map.setLayerZoomRange('building', 13, 24); } catch(e) {}
      }
      this.safeSetPaint(map, 'building', 'fill-color', state.buildingColor);
      this.safeSetPaint(map, 'building', 'fill-opacity', state.buildingOpacity);
      if (state.buildingOutlineColor) {
        this.safeSetPaint(map, 'building', 'fill-outline-color', state.buildingOutlineColor);
      }
    }
  }

  static applyLandUse(map: maplibregl.Map, state: MapPaintState) {
    const { landUseColors } = state;
    const layers = map.getStyle()?.layers || [];
    // [KEY] Exclude building layers from land use injection
    const BUILDING_IDS = ['building', 'building-3d'];
    const apply = (keywords: string[], color: string) => {
      if (!color) return;
      layers.filter(l => 
        l.type === 'fill' && 
        !BUILDING_IDS.includes(l.id) &&
        !l.id.toLowerCase().includes('structure') &&
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).forEach(l => {
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
    // Scan for background layer — ID varies by basemap
    const layers = map.getStyle()?.layers || [];
    const bgLayer = layers.find(l => l.type === 'background');
    if (bgLayer) {
      this.safeSetPaint(map, bgLayer.id, 'background-color', state.backgroundColor);
    }
  }

  static refreshBuildingCache(map: maplibregl.Map) {
    if (!map.isStyleLoaded()) return;
    const features = map.queryRenderedFeatures({ layers: map.getStyle()?.layers.filter(l => l.id.includes('building')).map(l => l.id) });
    console.log('[MapPaintEngine] Cache refreshed:', features.length);
  }

  static applySunlight(map: maplibregl.Map, state: SunlightState) {
    if (!state.enabled || !map.isStyleLoaded()) {
      if (map.getLayer('dynamic-shadows')) {
        map.setLayoutProperty('dynamic-shadows', 'visibility', 'none');
      }
      return;
    }

    const { lat: latitude, lng: longitude } = map.getCenter() || { lat: 25.04, lng: 121.51 };
    const date = new Date(state.date);
    date.setHours(Math.floor(state.time), Math.floor((state.time % 1) * 60));

    // Get buildings from cache or directly query
    const layers = map.getStyle()?.layers.filter(l => l.id.includes('building') && l.type === 'fill-extrusion').map(l => l.id);
    const buildings = map.queryRenderedFeatures({ layers });

    if (!buildings.length) return;

    // Use SunlightEngine to project actual shadows
    const shadowsGeoJSON = SunlightEngine.computeShadows(buildings as any, date, latitude, longitude);

    const sourceId = 'dynamic-shadow-source';
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, { type: 'geojson', data: shadowsGeoJSON });
      
      // Find the optimal layer to place shadows under (below 3D buildings, above ground)
      const buildingLayer = map.getStyle()?.layers.find(l => l.id.includes('building-3d'));
      
      map.addLayer({
        id: 'dynamic-shadows',
        type: 'fill',
        source: sourceId,
        paint: {
          'fill-color': '#000000',
          'fill-opacity': state.opacity || 0.4
        }
      }, buildingLayer ? buildingLayer.id : undefined);
    } else {
      (map.getSource(sourceId) as maplibregl.GeoJSONSource).setData(shadowsGeoJSON);
      map.setLayoutProperty('dynamic-shadows', 'visibility', 'visible');
      map.setPaintProperty('dynamic-shadows', 'fill-opacity', state.opacity || 0.4);
    }
  }
}
