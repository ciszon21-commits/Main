import maplibregl from 'maplibregl';

type AnimationMode = 'orbit' | 'spiral' | 'flyin' | 'helicopter' | 'dolly';

export class MapAnimationEngine {
  private static animationId: number | null = null;
  private static isAnimating = false;
  private static currentMode: AnimationMode | null = null;

  /**
   * Starts a continuous orbit camera rotation around the current center point.
   */
  static startOrbit(map: maplibregl.Map, speedModifier: number = 1.0) {
    this.stop();
    this.isAnimating = true;
    this.currentMode = 'orbit';
    
    // Ensure 3D tilt for a better orbit view
    if (map.getPitch() < 45) {
      map.easeTo({ pitch: 60, duration: 1500 });
    }

    let lastTime = performance.now();
    const frame = (time: number) => {
      if (!this.isAnimating || this.currentMode !== 'orbit') return;
      const delta = (time - lastTime) / 1000;
      lastTime = time;
      
      const speed = 10 * speedModifier; // Degrees per second
      const newBearing = map.getBearing() + (speed * delta);
      map.setBearing(newBearing % 360);
      
      this.animationId = requestAnimationFrame(frame);
    };
    
    // Small delay to let pitch ease finish naturally
    setTimeout(() => {
        if (this.currentMode === 'orbit') {
            lastTime = performance.now();
            this.animationId = requestAnimationFrame(frame);
        }
    }, 1500);
  }

  /**
   * Starts a spiral animation: Orbiting while zooming out and elevating the camera.
   */
  static startSpiral(map: maplibregl.Map, speedModifier: number = 1.0) {
    this.stop();
    this.isAnimating = true;
    this.currentMode = 'spiral';

    let lastTime = performance.now();

    const frame = (time: number) => {
      if (!this.isAnimating || this.currentMode !== 'spiral') return;
      const delta = (time - lastTime) / 1000;
      lastTime = time;

      const speed = 15 * speedModifier;
      const newBearing = map.getBearing() + (speed * delta);
      const newZoom = map.getZoom() - (0.1 * speedModifier * delta);
      const newPitch = Math.max(0, map.getPitch() - (2 * speedModifier * delta));

      map.setBearing(newBearing % 360);
      map.setZoom(newZoom);
      map.setPitch(newPitch);

      this.animationId = requestAnimationFrame(frame);
    };

    lastTime = performance.now();
    this.animationId = requestAnimationFrame(frame);
  }

  /**
   * Fly-In: Dramatically approaches from a high altitude while tilting and zooming in.
   * Best used as a cinematic intro. Stops automatically when zoom target is reached.
   */
  static startFlyIn(map: maplibregl.Map, speedModifier: number = 1.0) {
    this.stop();
    this.isAnimating = true;
    this.currentMode = 'flyin';

    const targetZoom = map.getZoom();
    const startZoom = Math.max(targetZoom - 3.5, 10.0);
    const targetPitch = 60;
    const currentBearing = map.getBearing();

    // Jump to high altitude quickly (without easing)
    map.jumpTo({ zoom: startZoom, pitch: 0 });

    const duration = 3000 / speedModifier;

    // Use MapLibre's native, highly optimized easeTo instead of manual RAF
    map.easeTo({
      zoom: targetZoom,
      pitch: targetPitch,
      bearing: currentBearing + 60, // dramatic rotation
      duration,
      easing: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
    });

    setTimeout(() => {
      if (this.currentMode === 'flyin') {
        this.currentMode = null;
        this.isAnimating = false;
      }
    }, duration + 100);
  }

  /**
   * Helicopter: Circular orbit with a smooth sinusoidal elevation (pitch) oscillation
   * to create a more dynamic aerial surveillance feel.
   */
  static startHelicopter(map: maplibregl.Map, speedModifier: number = 1.0) {
    this.stop();
    this.isAnimating = true;
    this.currentMode = 'helicopter';

    let lastTime = performance.now();
    const startTime = performance.now();

    const frame = (time: number) => {
      if (!this.isAnimating || this.currentMode !== 'helicopter') return;
      const delta = (time - lastTime) / 1000;
      const elapsed = (time - startTime) / 1000;
      lastTime = time;

      const speed = 12 * speedModifier; 
      const newBearing = map.getBearing() + (speed * delta);
      
      // Pitch oscillates between 45 and 75 degrees over a 10s cycle
      const newPitch = 60 + Math.sin(elapsed * 0.5 * speedModifier) * 15;
      
      map.setBearing(newBearing % 360);
      map.setPitch(newPitch);

      this.animationId = requestAnimationFrame(frame);
    };

    this.animationId = requestAnimationFrame(frame);
  }

  /**
   * Dolly Pan: Linear horizontal movement across the site while maintaining
   * fixed camera bearing and pitch. Useful for neighborhood scans.
   */
  static startDollyPan(map: maplibregl.Map, speedModifier: number = 1.0) {
    this.stop();
    this.isAnimating = true;
    this.currentMode = 'dolly';

    const center = map.getCenter();
    // Move towards North-East by default
    const velocity = { lng: 0.0001 * speedModifier, lat: 0.00005 * speedModifier };

    let lastTime = performance.now();
    const frame = (time: number) => {
      if (!this.isAnimating || this.currentMode !== 'dolly') return;
      const delta = (time - lastTime) / 1000;
      lastTime = time;

      const current = map.getCenter();
      map.setCenter([
        current.lng + velocity.lng * delta,
        current.lat + velocity.lat * delta
      ]);

      this.animationId = requestAnimationFrame(frame);
    };

    this.animationId = requestAnimationFrame(frame);
  }

  /**
   * Stops any ongoing animation.
   */
  static stop() {
    this.isAnimating = false;
    this.currentMode = null;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  static getActiveMode(): AnimationMode | null {
    return this.currentMode;
  }
}
