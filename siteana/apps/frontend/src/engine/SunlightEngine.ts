import * as turf from '@turf/turf';

/**
 * SunlightEngine
 * 1. Computes solar position (Azimuth & Altitude) using astronomical math.
 * 2. Projects shadow polygons based on building footprints and heights.
 */

// --- Solar Position Formulas (Adapted from standard NOAA / SunCalc math) ---
const PI = Math.PI;
const rad = PI / 180;
const e = rad * 23.4397; // obliquity of the Earth

function getJulianDate(date: Date) {
  return date.valueOf() / 86400000 - date.getTimezoneOffset() / 1440 + 2440587.5;
}

function getJulianDays(date: Date) {
  return getJulianDate(date) - 2451545.0;
}

function getRightAscension(l: number, b: number) {
  return Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
}

function getDeclination(l: number, b: number) {
  return Math.asin(Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l));
}

function getAzimuth(H: number, phi: number, dec: number) {
  return Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi));
}

function getAltitude(H: number, phi: number, dec: number) {
  return Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
}

function getSiderealTime(d: number, lw: number) {
  return rad * (280.16 + 360.9856235 * d) - lw;
}

function getSolarMeanAnomaly(d: number) {
  return rad * (357.5291 + 0.98560028 * d);
}

function getEclipticLongitude(M: number) {
  const C = rad * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
  const P = rad * 102.9372; // perihelion of the Earth
  return M + C + P + PI;
}

function getSunCoords(d: number) {
  const M = getSolarMeanAnomaly(d);
  const L = getEclipticLongitude(M);

  return {
    dec: getDeclination(L, 0),
    ra: getRightAscension(L, 0)
  };
}

export class SunlightEngine {
  /**
   * Calculate sun position for a given date and location.
   * @returns azimuth and altitude in radians.
   */
  static getSunPosition(date: Date, lat: number, lng: number) {
    const lw = rad * -lng;
    const phi = rad * lat;
    const d = getJulianDays(date);

    const c = getSunCoords(d);
    const H = getSiderealTime(d, lw) - c.ra;

    return {
      azimuth: getAzimuth(H, phi, c.dec), // 0 is South
      altitude: getAltitude(H, phi, c.dec)
    };
  }

  /**
   * Projects a shadow polygon for a given building feature.
   * Uses MapLibre query features format.
   */
  static generateShadowPolygon(
    feature: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>,
    altitudeParams: number, // in radians
    azimuthParams: number // in radians
  ): GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon> | null {
    // If sun is below horizon, no shadow
    if (altitudeParams <= 0) return null;

    // Get height from feature properties (fallback to typical 3m if missing)
    const height = feature.properties?.render_height || feature.properties?.height || 3;
    
    // Shadow length = height / tan(altitude)
    const shadowLengthMeters = height / Math.tan(altitudeParams);
    
    // Cap shadow length to avoid crazy polygons at sunset/sunrise
    if (shadowLengthMeters > 500) return null; 

    // Azimuth from south. Turf needs bearing from North (-180 to 180)
    // Azimuth 0 is south, moving west.
    const bearing = (azimuthParams * 180) / PI + 180;

    try {
      // Create a translated copy of the original polygon
      const shadowEnd = turf.transformTranslate(feature, shadowLengthMeters / 1000, bearing, { units: 'kilometers' });
      
      // To create the actual volume mapping, we need the convex hull of the original + translated.
      const points: number[][] = [];
      turf.coordEach(feature, (coord) => points.push(coord));
      turf.coordEach(shadowEnd, (coord) => points.push(coord));
      
      if (points.length < 3) return null;
      
      const hullPointFC = turf.featureCollection(points.map(p => turf.point(p)));
      const shadowHull = turf.convex(hullPointFC as any);
      
      if (!shadowHull) return null;

      // Retain some basic properties
      shadowHull.properties = {
        type: 'shadow',
        source_id: feature.properties?.id || 'unknown'
      };

      return shadowHull as any;
    } catch (e) {
      return null;
    }
  }

  /**
   * Processes a list of building features and returns a FeatureCollection of shadows.
   */
  static computeShadowsForBuildings(
    buildings: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>[],
    date: Date,
    lat: number,
    lng: number
  ): GeoJSON.FeatureCollection {
    const { azimuth, altitude } = this.getSunPosition(date, lat, lng);
    
    if (altitude <= 0) {
      return turf.featureCollection([]); // Night time
    }

    const shadows: any[] = [];
    
    for (const bldg of buildings) {
       const shadow = this.generateShadowPolygon(bldg, altitude, azimuth);
       if (shadow) shadows.push(shadow);
    }

    return turf.featureCollection(shadows);
  }
}
