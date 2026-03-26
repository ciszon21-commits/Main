// LumaSite Viewer Logic
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Map
    const map = new maplibregl.Map({
        container: 'map',
        style: 'https://tiles.openfreemap.org/styles/bright', // 使用 OpenFreeMap 穩定樣式
        center: [121.5135, 25.042], // 台北車站附近
        zoom: 16,
        pitch: 60,
        bearing: 0,
        antialias: true
    });

    // 2. Add Layers (地形與 3D 建物)
    map.on('load', () => {
        // 加入 3D 建物層
        // OpenFreeMap 的 bright 樣式通常包含 openmaptiles 來源
        map.addLayer({
            'id': '3d-buildings',
            'source': 'openmaptiles',
            'source-layer': 'building',
            'type': 'fill-extrusion',
            'minzoom': 15,
            'paint': {
                'fill-extrusion-color': '#e2e8f0',
                'fill-extrusion-height': ['get', 'render_height'],
                'fill-extrusion-base': ['get', 'render_min_height'],
                'fill-extrusion-opacity': 0.8
            }
        });

        updateSunPosition();
    });

    // 3. UI Elements
    const dateInput = document.getElementById('date-input');
    const timeSlider = document.getElementById('time-slider');
    const timeDisplay = document.getElementById('time-display');
    const azimuthDisplay = document.getElementById('azimuth-display');
    const elevationDisplay = document.getElementById('elevation-display');
    const projectSelect = document.getElementById('project-select');

    // 4. Update Logic
    function updateSunPosition() {
        const date = dateInput.value;
        const minutes = timeSlider.value;
        
        // 更新時間顯示 (HH:MM)
        const hh = Math.floor(minutes / 60);
        const mm = minutes % 60;
        timeDisplay.textContent = `${hh.toString().padStart(2, '0')}:${mm.toString().padStart(2, '0')}`;

        // 向後端 API 請求太陽角度
        const center = map.getCenter();
        fetch(`/lumasite/sun-position/?lat=${center.lat}&lng=${center.lng}&date=${date}&minutes=${minutes}`)
            .then(res => res.json())
            .then(data => {
                azimuthDisplay.textContent = `Azimuth: ${data.azimuth.toFixed(2)}°`;
                elevationDisplay.textContent = `Elevation: ${data.elevation.toFixed(2)}°`;
                
                // TODO: 根據角度更新地圖陰影效果 (如果引擎支援)
                // MapLibre 的原生陰影較弱，這部分通常需要 Custom WebGL Layer
            })
            .catch(err => console.error('Sun position fetch error:', err));
    }

    // 5. Event Listeners
    dateInput.addEventListener('change', updateSunPosition);
    timeSlider.addEventListener('input', updateSunPosition);
    
    // 監聽地圖移動以更新對應中心點的太陽角度 (選用)
    // map.on('moveend', updateSunPosition);

    // 6. 模擬專案載入
    function fetchProjects() {
        fetch('/lumasite/api/projects/')
            .then(res => res.json())
            .then(data => {
                projectSelect.innerHTML = '<option value="">請選擇專案...</option>';
                data.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.name;
                    projectSelect.appendChild(opt);
                });
            });
    }

    // fetchProjects(); // 暫時註解，避免 403 (如果尚未登入)
});
