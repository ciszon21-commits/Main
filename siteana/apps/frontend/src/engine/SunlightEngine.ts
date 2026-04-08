import * as turf from '@turf/turf';

/**
 * SunlightEngine v2
 * 1. Computes solar position (Azimuth & Altitude) using NOAA astronomical math.
 * 2. Computes sunrise / solar noon / sunset times using binary search.
 * 3. Projects shadow polygons based on building footprints and heights.
 */

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
  const P = rad * 102.9372;
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

function getSunAltitudeForDate(date: Date, lat: number, lng: number): number {
  const lw = rad * -lng;
  const phi = rad * lat;
  const d = getJulianDays(date);
  const c = getSunCoords(d);
  const H = getSiderealTime(d, lw) - c.ra;
  return getAltitude(H, phi, c.dec);
}

export interface SunPosition {
  azimuth: number;    // radians, 0 = South, positive = West
  altitude: number;   // radians, 0 = horizon, PI/2 = zenith
  azimuthDeg: number; // 0-360, compass bearing from North
  altitudeDeg: number;
  isDay: boolean;
}

export interface SunTimes {
  sunrise: Date | null;
  sunset: Date | null;
  solarNoon: Date | null;
  sunriseHour: number | null;  // decimal hour e.g. 5.7 = 05:42
  sunsetHour: number | null;
}

export class SunlightEngine {
  /**
   * Calculate sun position for given date/location.
   */
  static getSunPosition(date: Date, lat: number, lng: number): SunPosition {
    const lw = rad * -lng;
    const phi = rad * lat;
    const d = getJulianDays(date);
    const c = getSunCoords(d);
    const H = getSiderealTime(d, lw) - c.ra;

    const azimuth = getAzimuth(H, phi, c.dec);
    const altitude = getAltitude(H, phi, c.dec);

    // Convert azimuth (0=South, +West) to compass bearing (0=North, clockwise)
    const azimuthDeg = ((azimuth * 180 / PI) + 180) % 360;

    return {
      azimuth,
      altitude,
      azimuthDeg,
      altitudeDeg: altitude * 180 / PI,
      isDay: altitude > 0
    };
  }

  /**
   * Calculate sunrise, sunset and solar noon for given date/location.
   * Uses binary search for accuracy.
   */
  static getSunTimes(date: Date, lat: number, lng: number): SunTimes {
    const dateStr = date.toISOString().split('T')[0];
    
    // Helper: get altitude at hour h
    const altAt = (h: number) => {
      const d = new Date(`${dateStr}T00:00:00`);
      d.setHours(Math.floor(h), Math.round((h % 1) * 60), 0, 0);
      return getSunAltitudeForDate(d, lat, lng);
    };

    // Binary search for sunrise (when alt crosses 0 going positive)
    const findCrossing = (start: number, end: number, rising: boolean): number | null => {
      for (let i = 0; i < 30; i++) {
        const mid = (start + end) / 2;
        const alt = altAt(mid);
        if (rising) {
          if (alt > 0) end = mid; else start = mid;
        } else {
          if (alt < 0) end = mid; else start = mid;
        }
      }
      return (start + end) / 2;
    };

    // Find solar noon (max altitude) between 10:00 and 14:00
    let noonH = 12;
    let maxAlt = -Infinity;
    for (let h = 10; h <= 14; h += 0.1) {
      const a = altAt(h);
      if (a > maxAlt) { maxAlt = a; noonH = h; }
    }

    let sunriseH: number | null = null;
    let sunsetH: number | null = null;

    // Find sunrise: search 4-10 for rising crossing
    let hRise: number | null = null;
    for (let h = 4; h < 10; h += 0.5) {
      if (altAt(h) < 0 && altAt(h + 0.5) > 0) {
        hRise = findCrossing(h, h + 0.5, true);
        break;
      }
    }

    // Find sunset: search 14-22 for falling crossing
    let hSet: number | null = null;
    for (let h = 14; h < 22; h += 0.5) {
      if (altAt(h) > 0 && altAt(h + 0.5) < 0) {
        hSet = findCrossing(h, h + 0.5, false);
        break;
      }
    }

    sunriseH = hRise;
    sunsetH = hSet;

    const makeTime = (h: number | null) => {
      if (h === null) return null;
      const d = new Date(`${dateStr}T00:00:00`);
      d.setHours(Math.floor(h), Math.round((h % 1) * 60), 0, 0);
      return d;
    };

    const noonDate = makeTime(noonH);

    return {
      sunrise: makeTime(sunriseH),
      sunset: makeTime(sunsetH),
      solarNoon: noonDate,
      sunriseHour: sunriseH,
      sunsetHour: sunsetH
    };
  }

  /**
   * Projects a shadow polygon for a given building feature.
   */
  static generateShadowPolygon(
    feature: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>,
    altitudeRad: number,
    azimuthRad: number
  ): GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon> | null {
    if (altitudeRad <= 0.02) return null; // < ~1 degree, skip sunrise/sunset fringe

    const height = feature.properties?.render_height || feature.properties?.height || 3;
    const shadowLengthMeters = height / Math.tan(altitudeRad);

    // Cap to prevent absurd shadows near sunrise/sunset
    const maxShadow = 300;
    if (shadowLengthMeters > maxShadow) return null;

    // bearing = sun azimuth direction + 180° (shadow falls AWAY from sun)
    const sunBearing = (azimuthRad * 180 / PI + 180) % 360;
    const shadowBearing = (sunBearing + 180) % 360;

    try {
      const shadowEnd = turf.transformTranslate(feature, shadowLengthMeters / 1000, shadowBearing, { units: 'kilometers' });

      const points: number[][] = [];
      turf.coordEach(feature, (coord) => points.push(coord));
      turf.coordEach(shadowEnd, (coord) => points.push(coord));

      if (points.length < 3) return null;

      const hullPointFC = turf.featureCollection(points.map(p => turf.point(p)));
      const shadowHull = turf.convex(hullPointFC as any);

      if (!shadowHull) return null;

      shadowHull.properties = {
        type: 'shadow',
        source_id: feature.properties?.id || 'unknown'
      };

      return shadowHull as any;
    } catch {
      return null;
    }
  }

  /**
   * Processes a list of building features and returns shadows FeatureCollection.
   */
  static computeShadowsForBuildings(
    buildings: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>[],
    date: Date,
    lat: number,
    lng: number
  ): GeoJSON.FeatureCollection {
    const pos = this.getSunPosition(date, lat, lng);

    if (!pos.isDay) {
      return turf.featureCollection([]);
    }

    const shadows: any[] = [];

    for (const bldg of buildings) {
      const shadow = this.generateShadowPolygon(bldg, pos.altitude, pos.azimuth);
      if (shadow) shadows.push(shadow);
    }

    return turf.featureCollection(shadows);
  }
}
