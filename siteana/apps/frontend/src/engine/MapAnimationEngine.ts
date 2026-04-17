import maplibregl from 'maplibregl';

type AnimationMode = 'orbit' | 'spiral' | 'pan';

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
    const startZoom = Math.max(targetZoom - 5, 1);
    const startPitch = 0;
    const targetPitch = 60;

    map.jumpTo({ zoom: startZoom, pitch: startPitch });

    let lastTime = performance.now();
    const totalDuration = 8000 / speedModifier; // ms
    const startTime = performance.now();

    const frame = (time: number) => {
      if (!this.isAnimating || this.currentMode !== 'flyin') return;
      const elapsed = time - startTime;
      const t = Math.min(elapsed / totalDuration, 1);
      // Ease in-out cubic
      const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

      map.setZoom(startZoom + (targetZoom - startZoom) * eased);
      map.setPitch(startPitch + (targetPitch - startPitch) * eased);
      map.setBearing(map.getBearing() + (10 * speedModifier * (time - lastTime) / 1000));
      lastTime = time;

      if (t < 1) {
        this.animationId = requestAnimationFrame(frame);
      } else {
        // Auto-switch to orbit after fly-in completes
        this.currentMode = null;
        this.isAnimating = false;
      }
    };

    lastTime = performance.now();
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
