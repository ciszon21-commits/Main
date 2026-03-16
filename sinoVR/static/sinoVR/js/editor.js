import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { TransformControls } from 'three/addons/controls/TransformControls.js';

// Django variables - will be injected by template
let SCENE_ID, SAVE_URL, UPLOAD_URL, CSRF_TOKEN;

// Function to initialize Django variables from template
export function initializeDjangoVars(sceneId, saveUrl, uploadUrl, csrfToken) {
    SCENE_ID = sceneId;
    SAVE_URL = saveUrl;
    UPLOAD_URL = uploadUrl;
    CSRF_TOKEN = csrfToken;
}

// Globals
let container, camera, scene, renderer;
let controls, transformControl;
let raycaster, pointer;
let skyboxMesh;
let clock = new THREE.Clock();

const objects = [];
let selectedObject = null;
let isInspectorUpdating = false;



// UI Inputs
const inputs = {
    pos: { x: null, y: null, z: null },
    rot: { x: null, y: null, z: null },
    scale: { x: null, y: null, z: null },
};

export function init() {
    container = document.getElementById('vr-container');

    // Initialize inputs
    inputs.pos.x = document.getElementById('inp-pos-x');
    inputs.pos.y = document.getElementById('inp-pos-y');
    inputs.pos.z = document.getElementById('inp-pos-z');
    inputs.rot.x = document.getElementById('inp-rot-x');
    inputs.rot.y = document.getElementById('inp-rot-y');
    inputs.rot.z = document.getElementById('inp-rot-z');
    inputs.scale.x = document.getElementById('inp-scale-x');
    inputs.scale.y = document.getElementById('inp-scale-y');
    inputs.scale.z = document.getElementById('inp-scale-z');

    // Three.js Scene Setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x303030);

    camera = new THREE.PerspectiveCamera(70, container.clientWidth / container.clientHeight, 0.1, 2000);
    camera.position.set(0, 1.6, 5);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(5, 10, 7.5);
    scene.add(dirLight);

    // Infinite Dirt Floor
    const textureLoader = new THREE.TextureLoader();
    const floorTexture = textureLoader.load('/static/sinoVR/images/dirt_floor.png');
    floorTexture.wrapS = THREE.RepeatWrapping;
    floorTexture.wrapT = THREE.RepeatWrapping;
    floorTexture.repeat.set(500, 500); // Repeat across the vast plane
    floorTexture.colorSpace = THREE.SRGBColorSpace;

    const floorGeometry = new THREE.PlaneGeometry(1000, 1000);
    const floorMaterial = new THREE.MeshPhongMaterial({
        map: floorTexture,
        side: THREE.DoubleSide
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.01;
    scene.add(floor);

    // Add fog for infinite horizon feel
    scene.fog = new THREE.Fog(0x303030, 10, 100);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.xr.enabled = true;
    container.appendChild(renderer.domElement);

    document.body.appendChild(VRButton.createButton(renderer));

    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.mouseButtons = {
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN
    }

    transformControl = new TransformControls(camera, renderer.domElement);
    transformControl.addEventListener('dragging-changed', (event) => controls.enabled = !event.value);
    transformControl.addEventListener('change', () => {
        // Prevent updates if not initialized or if drag just started
        if (selectedObject) updateInspectorFromObject();
    });
    scene.add(transformControl);

    raycaster = new THREE.Raycaster();
    pointer = new THREE.Vector2();

    // Listeners
    window.addEventListener('resize', onWindowResize);
    container.addEventListener('pointerdown', onPointerDown);
    container.addEventListener('pointerup', onPointerUp);
    container.addEventListener('pointermove', onPointerMove);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);

    // Prevent context menu on right click
    container.addEventListener('contextmenu', e => e.preventDefault());

    // UI Setup
    setupInspectorEvents();

    document.getElementById('loading').style.display = 'flex';
    // Hide loading after a bit roughly
    setTimeout(() => document.getElementById('loading').style.display = 'none', 1000);
}

// --- Core Logic ---

export function loadSkybox(skyboxUrl) {
    if (skyboxUrl) {
        new THREE.TextureLoader().load(skyboxUrl, (texture) => {
            texture.mapping = THREE.EquirectangularReflectionMapping;
            texture.colorSpace = THREE.SRGBColorSpace;
            const geo = new THREE.SphereGeometry(500, 60, 40);
            geo.scale(-1, 1, 1);
            const mat = new THREE.MeshBasicMaterial({ map: texture, fog: false });
            skyboxMesh = new THREE.Mesh(geo, mat);
            scene.add(skyboxMesh);
        });
    }
}

export function loadExistingObject(obj) {
    if (obj.isInfoCard) {
        addInfoCard(obj.id, obj.title, obj.content, {
            position: obj.position,
            rotation: obj.rotation,
            scale: obj.scale
        }, obj.bgColor, obj.fontSize);
    } else {
        loadModel(obj.assetId, obj.url, {
            position: obj.position,
            rotation: obj.rotation,
            scale: obj.scale
        }, obj.title);
    }
}

// InfoCard Functions
// Helper to calculate wrapping and optimal font size
function getOptimalFontSize(ctx, text, maxWidth, maxHeight, initialFontSize) {
    let fontSize = initialFontSize;
    const minFontSize = 20; // Minimum readable size

    while (fontSize >= minFontSize) {
        ctx.font = `${fontSize}px "Segoe UI", Arial`;
        const lineHeight = fontSize * 1.5;
        let y = 0; // Relative height accumulator
        const chars = text.split('');
        let line = '';

        // Simulate wrapping
        for (let i = 0; i < chars.length; i++) {
            const testLine = line + chars[i];
            const metrics = ctx.measureText(testLine);

            if (metrics.width > maxWidth && line.length > 0) {
                y += lineHeight;
                line = chars[i];
            } else {
                line = testLine;
            }
        }
        y += lineHeight; // Add last line

        if (y <= maxHeight) {
            return fontSize;
        }

        fontSize -= 2; // Reduce and try again
    }
    return minFontSize;
}

// InfoCard Functions
function addInfoCard(id, title, content, transform = {}, bgColor = 'rgba(173, 216, 230, 0.95)', fontSize = 50, showResizeAlert = false) {
    // Create Canvas for card texture
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 768;
    const ctx = canvas.getContext('2d');

    // Available height for text: Canvas Height - Top Offset (220) - Bottom Padding (50)
    const maxTextHeight = canvas.height - 220 - 50;
    const maxWidth = canvas.width - 120;

    // Calculate optimal font size
    const optimalFontSize = getOptimalFontSize(ctx, content, maxWidth, maxTextHeight, fontSize);

    // Check if resize happened and alert if requested
    if (showResizeAlert && optimalFontSize < fontSize) {
        alert(`您設定的字體大小 (${fontSize}px) 過大，系統將自動調整為 ${optimalFontSize}px 以確保內容完整顯示。`);

        // Auto-save the optimized font size to DB
        fetch(`/sinoVR/api/info-card/${id}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({
                content_font_size: optimalFontSize
            })
        }).then(r => r.json()).then(d => {
            console.log('Auto-saved font size:', optimalFontSize, d);
        }).catch(e => console.error('Auto-save failed:', e));
    }

    // Update the input fontSize to the optimal one for rendering
    fontSize = optimalFontSize;

    // Hi-Tech Background (Tinted by bgColor)
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    const baseColor = bgColor || '#101830';
    gradient.addColorStop(0, adjustOpacity(baseColor, 0.95));
    gradient.addColorStop(1, 'rgba(10, 15, 30, 0.95)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Tech Frame
    ctx.strokeStyle = adjustOpacity(baseColor, 0.6);
    ctx.lineWidth = 4;
    ctx.strokeRect(20, 20, canvas.width - 40, canvas.height - 40);

    // Corner Accents
    ctx.strokeStyle = baseColor;
    ctx.lineWidth = 12;
    const cornerSize = 80;
    // Top Left
    ctx.beginPath(); ctx.moveTo(20, 20 + cornerSize); ctx.lineTo(20, 20); ctx.lineTo(20 + cornerSize, 20); ctx.stroke();
    // Top Right
    ctx.beginPath(); ctx.moveTo(canvas.width - 20 - cornerSize, 20); ctx.lineTo(canvas.width - 20, 20); ctx.lineTo(canvas.width - 20, 20 + cornerSize); ctx.stroke();
    // Bottom Left
    ctx.beginPath(); ctx.moveTo(20, canvas.height - 20 - cornerSize); ctx.lineTo(20, canvas.height - 20); ctx.lineTo(20 + cornerSize, canvas.height - 20); ctx.stroke();
    // Bottom Right
    ctx.beginPath(); ctx.moveTo(canvas.width - 20 - cornerSize, canvas.height - 20); ctx.lineTo(canvas.width - 20, canvas.height - 20); ctx.lineTo(canvas.width - 20, canvas.height - 20 - cornerSize); ctx.stroke();

    // Title
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 76px "Segoe UI", Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.shadowBlur = 25;
    ctx.shadowColor = baseColor;
    ctx.fillText(title, canvas.width / 2, 60);
    ctx.shadowBlur = 0;

    // Separator line with glow
    ctx.strokeStyle = adjustOpacity(baseColor, 0.3);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(100, 165);
    ctx.lineTo(canvas.width - 100, 165);
    ctx.stroke();

    // Content text (multi-line with word wrap, custom font size)
    ctx.fillStyle = 'rgba(230, 245, 255, 0.95)';
    ctx.font = `${fontSize}px "Segoe UI", Arial`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';

    const lineHeight = fontSize * 1.5;
    let y = 220;

    // Character-based word wrap for content
    const chars = content.split('');
    let line = '';

    for (let i = 0; i < chars.length; i++) {
        const testLine = line + chars[i];
        const metrics = ctx.measureText(testLine);

        if (metrics.width > maxWidth && line.length > 0) {
            ctx.fillText(line, 60, y);
            line = chars[i];
            y += lineHeight;
            // if (y > canvas.height - 50) break; // Should not happen with optimal size
        } else {
            line = testLine;
        }
    }
    if (line) ctx.fillText(line, 60, y);

    // Create material and geometry
    const texture = new THREE.CanvasTexture(canvas);
    const geometry = new THREE.PlaneGeometry(3, 2.25);
    const material = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9
    });

    // Create Close Button (Top Right "X")
    const hideCanvas = document.createElement('canvas');
    hideCanvas.width = 120;
    hideCanvas.height = 120;
    const hideCtx = hideCanvas.getContext('2d');
    hideCtx.fillStyle = 'rgba(20, 25, 40, 0.8)';
    hideCtx.beginPath();
    hideCtx.arc(60, 60, 58, 0, Math.PI * 2);
    hideCtx.fill();
    hideCtx.strokeStyle = baseColor;
    hideCtx.lineWidth = 4;
    hideCtx.stroke();
    hideCtx.strokeStyle = '#ffffff';
    hideCtx.lineWidth = 8;
    hideCtx.lineCap = 'round';
    const closePadding = 35;
    hideCtx.beginPath();
    hideCtx.moveTo(closePadding, closePadding);
    hideCtx.lineTo(120 - closePadding, 120 - closePadding);
    hideCtx.moveTo(120 - closePadding, closePadding);
    hideCtx.lineTo(closePadding, 120 - closePadding);
    hideCtx.stroke();
    const hideTexture = new THREE.CanvasTexture(hideCanvas);
    const hideMat = new THREE.MeshBasicMaterial({
        map: hideTexture,
        transparent: true,
        opacity: 0.9
    });
    const hideMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.4), hideMat);
    hideMesh.position.set(1.4, 1.05, 0.05);
    hideMesh.userData.isInteractable = true;
    hideMesh.userData.isHideBtn = true;
    hideMesh.userData.parentCardId = id;


    // Create Show Button (Interactive Title Capsule) - Initially Hidden in Editor
    const showCanvas = document.createElement('canvas');
    showCanvas.width = 1024;
    showCanvas.height = 256;
    const showCtx = showCanvas.getContext('2d');
    const themeColor = bgColor || '#17a2b8';
    const rx = 512, ry = 128, rw = 800, rh = 160;
    const sx = rx - rw / 2, sy = ry - rh / 2;
    const btnGradient = showCtx.createLinearGradient(0, sy, 0, sy + rh);
    btnGradient.addColorStop(0, adjustOpacity(themeColor, 0.4));
    btnGradient.addColorStop(1, adjustOpacity(themeColor, 0.1));
    showCtx.fillStyle = btnGradient;
    const sRadius = 80;
    showCtx.beginPath();
    showCtx.moveTo(sx + sRadius, sy);
    showCtx.lineTo(sx + rw - sRadius, sy);
    showCtx.quadraticCurveTo(sx + rw, sy, sx + rw, sy + sRadius);
    showCtx.lineTo(sx + rw, sy + rh - sRadius);
    showCtx.quadraticCurveTo(sx + rw, sy + rh, sx + rw - sRadius, sy + rh);
    showCtx.lineTo(sx + sRadius, sy + rh);
    showCtx.quadraticCurveTo(sx, sy + rh, sx, sy + rh - sRadius);
    showCtx.lineTo(sx, sy + sRadius);
    showCtx.quadraticCurveTo(sx, sy, sx + sRadius, sy);
    showCtx.closePath();
    showCtx.fill();
    showCtx.strokeStyle = themeColor;
    showCtx.lineWidth = 10;
    showCtx.stroke();
    showCtx.shadowBlur = 15;
    showCtx.shadowColor = themeColor;
    showCtx.fillStyle = 'white';
    showCtx.textAlign = 'center';
    showCtx.font = 'bold 70px "Segoe UI", Arial';
    showCtx.textBaseline = 'middle';
    showCtx.fillText(title, 512, 110);
    showCtx.shadowBlur = 0;
    showCtx.font = '36px "Segoe UI", Arial';
    showCtx.fillStyle = adjustOpacity('#ffffff', 0.8);
    showCtx.fillText('(點擊開啟內容)', 512, 175);
    const showTexture = new THREE.CanvasTexture(showCanvas);
    const showMat = new THREE.MeshBasicMaterial({
        map: showTexture,
        transparent: true,
        opacity: 0.95
    });
    const showMesh = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.75), showMat);
    showMesh.position.set(0, 0, 0.1);
    showMesh.visible = false; // Hidden by default in editor
    showMesh.userData.isInteractable = true;
    showMesh.userData.isShowBtn = true;
    showMesh.userData.parentCardId = id;

    showMesh.userData.parentCardId = id;

    const mesh = new THREE.Mesh(geometry, material);
    mesh.add(hideMesh);
    mesh.add(showMesh);

    // Apply transform
    if (transform.position) mesh.position.set(transform.position.x, transform.position.y, transform.position.z);
    else mesh.position.set(0, 1.5, 0);

    if (transform.rotation) mesh.rotation.set(transform.rotation.x, transform.rotation.y, transform.rotation.z);
    if (transform.scale) mesh.scale.set(transform.scale.x, transform.scale.y, transform.scale.z);

    mesh.userData.isInteractable = true;
    mesh.userData.isInfoCard = true;
    mesh.userData.infoCardId = id;
    mesh.userData.cardTitle = title;
    mesh.userData.cardContent = content;
    mesh.userData.cardBgColor = bgColor;
    mesh.userData.cardFontSize = fontSize; // Store optimal font size
    mesh.name = `字卡: ${title}`;

    // Add double-click event for editing (non-play mode)
    mesh.userData.onDoubleClick = () => {
        openEditCardModal(id, title, content, bgColor, fontSize);
    };

    scene.add(mesh);
    objects.push(mesh);
    // Also push buttons to objects? No, usually we raycast scene children recursively or handle specifically.
    // The current raycaster uses `intersectObjects(objects, true)`. 
    // `true` means recursive, so children are checked.

    // Select if newly added (not loading existing)
    if (Object.keys(transform).length === 0) {
        selectObject(mesh);
    }

    updateHierarchy();
}

window.createInfoCard = function () {
    const title = document.getElementById('card-title').value;
    const content = document.getElementById('card-content').value;
    const bgColor = document.getElementById('card-bg-color').value;
    const fontSize = parseInt(document.getElementById('card-font-size').value);

    if (!title || !content) {
        alert('請輸入標題和內容');
        return;
    }

    document.getElementById('loading').style.display = 'flex';

    fetch(UPLOAD_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
            type: 'info_card',
            title: title,
            content: content,
            bg_color: bgColor,
            content_font_size: fontSize
        })
    })
        .then(r => r.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            if (data.type === 'info_card') {
                addInfoCard(data.id, data.title, content, {}, bgColor, fontSize, true); // True for alert
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('createCardModal'));
                if (modal) modal.hide();
                // Clear inputs
                document.getElementById('card-title').value = '';
                document.getElementById('card-content').value = '';
            }
        })
        .catch(e => {
            document.getElementById('loading').style.display = 'none';
            alert('建立失敗: ' + e);
        });
}

// Edit selected InfoCard
window.editSelectedCard = function () {
    if (!selectedObject) {
        alert('請先選取一個字卡');
        return;
    }

    if (!selectedObject.userData.isInfoCard) {
        alert('選取的物件不是字卡');
        return;
    }

    const data = selectedObject.userData;
    openEditCardModal(
        data.infoCardId,
        data.cardTitle,
        data.cardContent,
        data.cardBgColor || 'rgba(173, 216, 230, 0.95)',
        data.cardFontSize || 50
    );
}

// Open edit InfoCard modal
function openEditCardModal(cardId, title, content, bgColor, fontSize) {
    document.getElementById('edit-card-id').value = cardId;
    document.getElementById('edit-card-title').value = title;
    document.getElementById('edit-card-content').value = content;
    document.getElementById('edit-card-bg-color').value = bgColor;
    document.getElementById('edit-card-font-size').value = fontSize;

    const modal = new bootstrap.Modal(document.getElementById('editCardModal'));
    modal.show();
}

// Update InfoCard
window.updateInfoCard = function () {
    const cardId = document.getElementById('edit-card-id').value;
    const title = document.getElementById('edit-card-title').value;
    const content = document.getElementById('edit-card-content').value;
    const bgColor = document.getElementById('edit-card-bg-color').value;
    const fontSize = parseInt(document.getElementById('edit-card-font-size').value);

    if (!title || !content) {
        alert('請輸入標題和內容');
        return;
    }

    document.getElementById('loading').style.display = 'flex';

    fetch(`/sinoVR/api/info-card/${cardId}/update/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
            title: title,
            content: content,
            bg_color: bgColor,
            content_font_size: fontSize
        })
    })
        .then(r => r.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            if (data.status === 'success') {
                rerenderInfoCard(cardId, title, content, bgColor, fontSize, true);
                const modal = bootstrap.Modal.getInstance(document.getElementById('editCardModal'));
                if (modal) modal.hide();
            } else {
                alert('更新失敗: ' + (data.message || ''));
            }
        })
        .catch(e => {
            document.getElementById('loading').style.display = 'none';
            alert('更新失敗: ' + e);
        });
}

// Re-render InfoCard with new properties
function rerenderInfoCard(cardId, title, content, bgColor, fontSize, showResizeAlert = false) {
    const mesh = objects.find(obj => obj.userData.isInfoCard && obj.userData.infoCardId == cardId);
    if (!mesh) return;

    const transform = {
        position: mesh.position.clone(),
        rotation: mesh.rotation.clone(),
        scale: mesh.scale.clone()
    };

    scene.remove(mesh);
    const index = objects.indexOf(mesh);
    if (index > -1) objects.splice(index, 1);

    // Create new canvas
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 768;
    const ctx = canvas.getContext('2d');

    // Available height for text: Canvas Height - Top Offset (220) - Bottom Padding (50)
    const maxTextHeight = canvas.height - 220 - 50;
    const maxWidth = canvas.width - 120;

    // Calculate optimal font size
    const optimalFontSize = getOptimalFontSize(ctx, content, maxWidth, maxTextHeight, fontSize);

    // Update the input fontSize to the optimal one for rendering
    // Check if resize happened and alert if requested
    if (showResizeAlert && optimalFontSize < fontSize) {
        alert(`您設定的字體大小 (${fontSize}px) 過大，系統將自動調整為 ${optimalFontSize}px 以確保內容完整顯示。`);
    }
    fontSize = optimalFontSize;

    // Hi-Tech Background (Tinted by bgColor)
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    const baseColor = bgColor || '#101830';
    gradient.addColorStop(0, adjustOpacity(baseColor, 0.95));
    gradient.addColorStop(1, 'rgba(10, 15, 30, 0.95)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Tech Frame
    ctx.strokeStyle = adjustOpacity(baseColor, 0.6);
    ctx.lineWidth = 4;
    ctx.strokeRect(20, 20, canvas.width - 40, canvas.height - 40);

    // Corner Accents
    ctx.strokeStyle = baseColor;
    ctx.lineWidth = 12;
    const cornerSize = 80;
    // Top Left
    ctx.beginPath(); ctx.moveTo(20, 20 + cornerSize); ctx.lineTo(20, 20); ctx.lineTo(20 + cornerSize, 20); ctx.stroke();
    // Top Right
    ctx.beginPath(); ctx.moveTo(canvas.width - 20 - cornerSize, 20); ctx.lineTo(canvas.width - 20, 20); ctx.lineTo(canvas.width - 20, 20 + cornerSize); ctx.stroke();
    // Bottom Left
    ctx.beginPath(); ctx.moveTo(20, canvas.height - 20 - cornerSize); ctx.lineTo(20, canvas.height - 20); ctx.lineTo(20 + cornerSize, canvas.height - 20); ctx.stroke();
    // Bottom Right
    ctx.beginPath(); ctx.moveTo(canvas.width - 20 - cornerSize, canvas.height - 20); ctx.lineTo(canvas.width - 20, canvas.height - 20); ctx.lineTo(canvas.width - 20, canvas.height - 20 - cornerSize); ctx.stroke();

    // Title
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 76px "Segoe UI", Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.shadowBlur = 25;
    ctx.shadowColor = baseColor;
    ctx.fillText(title, canvas.width / 2, 60);
    ctx.shadowBlur = 0;

    // Separator line with glow
    ctx.strokeStyle = adjustOpacity(baseColor, 0.3);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(100, 165);
    ctx.lineTo(canvas.width - 100, 165);
    ctx.stroke();

    // Content text (multi-line with word wrap, custom font size)
    ctx.fillStyle = 'rgba(230, 245, 255, 0.95)';
    ctx.font = `${fontSize}px "Segoe UI", Arial`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';

    const lineHeight = fontSize * 1.5;
    let y = 220;

    const chars = content.split('');
    let line = '';
    for (let i = 0; i < chars.length; i++) {
        const testLine = line + chars[i];
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && line.length > 0) {
            ctx.fillText(line, 60, y);
            line = chars[i];
            y += lineHeight;
            // if (y > canvas.height - 50) break;
        } else {
            line = testLine;
        }
    }
    if (line) ctx.fillText(line, 60, y);

    const texture = new THREE.CanvasTexture(canvas);
    const geometry = new THREE.PlaneGeometry(3, 2.25);
    const material = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.95
    });

    // Create Close Button (Top Right "X")
    const hideCanvas = document.createElement('canvas');
    hideCanvas.width = 120;
    hideCanvas.height = 120;
    const hideCtx = hideCanvas.getContext('2d');
    hideCtx.fillStyle = 'rgba(20, 25, 40, 0.8)';
    hideCtx.beginPath();
    hideCtx.arc(60, 60, 58, 0, Math.PI * 2);
    hideCtx.fill();
    hideCtx.strokeStyle = baseColor;
    hideCtx.lineWidth = 4;
    hideCtx.stroke();
    hideCtx.strokeStyle = '#ffffff';
    hideCtx.lineWidth = 8;
    hideCtx.lineCap = 'round';
    const closePadding = 35;
    hideCtx.beginPath();
    hideCtx.moveTo(closePadding, closePadding);
    hideCtx.lineTo(120 - closePadding, 120 - closePadding);
    hideCtx.moveTo(120 - closePadding, closePadding);
    hideCtx.lineTo(closePadding, 120 - closePadding);
    hideCtx.stroke();
    const hideTexture = new THREE.CanvasTexture(hideCanvas);
    const hideMat = new THREE.MeshBasicMaterial({
        map: hideTexture,
        transparent: true,
        opacity: 0.9
    });
    const hideMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.4), hideMat);
    hideMesh.position.set(1.4, 1.05, 0.05);


    // Create Show Button (Interactive Title Capsule) - Initially Hidden in Editor
    const showCanvas = document.createElement('canvas');
    showCanvas.width = 1024;
    showCanvas.height = 256;
    const showCtx = showCanvas.getContext('2d');
    const themeColor = bgColor || '#17a2b8';
    const rx = 512, ry = 128, rw = 800, rh = 160;
    const sx = rx - rw / 2, sy = ry - rh / 2;
    const btnGradient = showCtx.createLinearGradient(0, sy, 0, sy + rh);
    btnGradient.addColorStop(0, adjustOpacity(themeColor, 0.4));
    btnGradient.addColorStop(1, adjustOpacity(themeColor, 0.1));
    showCtx.fillStyle = btnGradient;
    const sRadius = 80;
    showCtx.beginPath();
    showCtx.moveTo(sx + sRadius, sy);
    showCtx.lineTo(sx + rw - sRadius, sy);
    showCtx.quadraticCurveTo(sx + rw, sy, sx + rw, sy + sRadius);
    showCtx.lineTo(sx + rw, sy + rh - sRadius);
    showCtx.quadraticCurveTo(sx + rw, sy + rh, sx + rw - sRadius, sy + rh);
    showCtx.lineTo(sx + sRadius, sy + rh);
    showCtx.quadraticCurveTo(sx, sy + rh, sx, sy + rh - sRadius);
    showCtx.lineTo(sx, sy + sRadius);
    showCtx.quadraticCurveTo(sx, sy, sx + sRadius, sy);
    showCtx.closePath();
    showCtx.fill();
    showCtx.strokeStyle = themeColor;
    showCtx.lineWidth = 10;
    showCtx.stroke();
    showCtx.shadowBlur = 15;
    showCtx.shadowColor = themeColor;
    showCtx.fillStyle = 'white';
    showCtx.textAlign = 'center';
    showCtx.font = 'bold 70px "Segoe UI", Arial';
    showCtx.textBaseline = 'middle';
    showCtx.fillText(title, 512, 110);
    showCtx.shadowBlur = 0;
    showCtx.font = '36px "Segoe UI", Arial';
    showCtx.fillStyle = adjustOpacity('#ffffff', 0.8);
    showCtx.fillText('(點擊開啟內容)', 512, 175);
    const showTexture = new THREE.CanvasTexture(showCanvas);
    const showMat = new THREE.MeshBasicMaterial({
        map: showTexture,
        transparent: true,
        opacity: 0.95
    });
    const showMesh = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.75), showMat);
    showMesh.position.set(0, 0, 0.1);
    showMesh.visible = false; // Hidden by default in editor
    showMesh.userData.isInteractable = true;
    showMesh.userData.isShowBtn = true;
    showMesh.userData.parentCardId = cardId;

    showMesh.userData.parentCardId = cardId;

    const newMesh = new THREE.Mesh(geometry, material);
    newMesh.add(hideMesh);
    newMesh.add(showMesh);
    newMesh.position.copy(transform.position);
    newMesh.rotation.copy(transform.rotation);
    newMesh.scale.copy(transform.scale);

    newMesh.userData.isInteractable = true;
    newMesh.userData.isInfoCard = true;
    newMesh.userData.infoCardId = cardId;
    newMesh.userData.cardTitle = title;
    newMesh.userData.cardContent = content;
    newMesh.userData.cardBgColor = bgColor;
    newMesh.userData.cardFontSize = fontSize;
    newMesh.name = `字卡: ${title}`;

    newMesh.userData.onDoubleClick = () => {
        openEditCardModal(cardId, title, content, bgColor, fontSize);
    };

    scene.add(newMesh);
    objects.push(newMesh);

    if (selectedObject === mesh) {
        selectObject(newMesh);
    }

    updateHierarchy();
}


window.showCardDetail = function (title, content, themeColor) {
    document.getElementById('card-detail-title').textContent = title;
    document.getElementById('card-detail-content').textContent = content;
    const overlay = document.getElementById('card-detail-overlay');
    const box = overlay.querySelector('.card-detail-box');

    if (themeColor) {
        box.style.borderColor = adjustOpacity(themeColor, 0.5);
        box.style.boxShadow = `0 0 40px rgba(0, 0, 0, 0.6), 0 0 20px ${adjustOpacity(themeColor, 0.3)}`;
    }

    overlay.style.display = 'flex';
}

window.closeCardDetail = function () {
    document.getElementById('card-detail-overlay').style.display = 'none';
}


window.addModel = function (id, url, title) {
    document.getElementById('loading').style.display = 'flex';
    loadModel(id, url, {}, title, () => {
        document.getElementById('loading').style.display = 'none';
    });
};

window.setTool = function (mode) {
    if (!selectedObject) return;
    transformControl.setMode(mode);
    transformControl.attach(selectedObject);
}



window.saveScene = function (silent = false) {
    const dataToSave = objects.map(obj => {
        const data = {
            transform: {
                position: obj.position,
                rotation: { x: obj.rotation.x, y: obj.rotation.y, z: obj.rotation.z },
                scale: obj.scale
            }
        };

        if (obj.userData.isInfoCard) {
            data.info_card_id = obj.userData.infoCardId;
        } else {
            data.asset_id = obj.userData.assetId;
        }

        return data;
    });

    // Return the promise
    return fetch(SAVE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body: JSON.stringify({ objects: dataToSave })
    }).then(r => r.json()).then(d => {
        if (d.status === 'success') {
            if (!silent) alert('Saved!');
        }
        else alert('Error: ' + d.message);
        return d;
    });
}

window.saveAndExit = function (exitUrl) {
    // Show lightweight loading indicator or just change button text
    const btn = document.querySelector('button[title="保存並返回場景列表"]');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';

    saveScene(true).then(data => {
        if (data && data.status === 'success') {
            window.location.href = exitUrl;
        } else {
            if (btn) btn.innerHTML = '<i class="fas fa-arrow-left"></i> 返回';
        }
    });
}

function loadModel(assetId, url, transform = {}, title = 'Model', callback) {
    new FBXLoader().load(url, (object) => {
        if (transform.position) object.position.set(transform.position.x, transform.position.y, transform.position.z);
        if (transform.rotation) object.rotation.set(transform.rotation.x, transform.rotation.y, transform.rotation.z);
        if (transform.scale) object.scale.set(transform.scale.x, transform.scale.y, transform.scale.z);

        object.userData.isInteractable = true;
        object.userData.assetId = assetId;
        object.name = title;

        scene.add(object);
        objects.push(object);

        // Select it newly added (unless loading existing)
        if (Object.keys(transform).length === 0) {
            selectObject(object);
        }

        updateHierarchy();
        if (callback) callback(object);
    });
}

function selectObject(object) {
    selectedObject = object;


    if (object) {
        transformControl.attach(object);
        updateInspectorFromObject();
    } else {
        transformControl.detach();
    }

    // Highlight in Hierarchy
    updateHierarchyUI();
}

window.deleteSelected = function () {
    if (selectedObject && confirm('Delete ' + selectedObject.name + '?')) {
        transformControl.detach();
        scene.remove(selectedObject);
        const idx = objects.indexOf(selectedObject);
        if (idx > -1) objects.splice(idx, 1);
        selectedObject = null;
        updateHierarchy();
    }
}

// Model Tools
window.centerSelected = function () {
    if (!selectedObject) return alert('Select model first');
    const obj = selectedObject;
    transformControl.detach();

    const box = new THREE.Box3().setFromObject(obj);
    const center = box.getCenter(new THREE.Vector3());

    // World Offset from visual center to pivot
    const offset = obj.position.clone().sub(center);

    // Apply offset to children (Inverse of rotation/scale of parent)
    const inverseRot = obj.quaternion.clone().invert();
    const localOffset = offset.applyQuaternion(inverseRot).divide(obj.scale);

    obj.children.forEach(c => c.position.add(localOffset));

    transformControl.attach(obj);
    alert('Pivot Centered');
};

window.scaleSelected = function () {
    if (!selectedObject) return alert('Select model first');
    const obj = selectedObject;
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3());
    const max = Math.max(size.x, size.y, size.z);
    if (max > 0) {
        obj.scale.multiplyScalar(2.0 / max);
        updateInspectorFromObject();
        alert('Scaled to 2m');
    }
}

window.quickScale = function (factor) {
    if (!selectedObject) return alert('Select model first');
    selectedObject.scale.multiplyScalar(factor);
    updateInspectorFromObject();
}

// --- UI/Interaction ---

function onPointerDown(event) {
    if (event.button === 2) return; // Ignore right click (was FPS mode)

    // Don't deselect if clicking on the Gizmo
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(pointer, camera);
    const intersects = raycaster.intersectObjects(objects, true);

    if (intersects.length > 0) {
        let hit = intersects[0].object;

        // Handle Hide/Show toggles in editor too for preview
        if (hit.userData.isHideBtn) {
            const card = hit.parent;
            if (card) {
                card.material.visible = false;
                card.children.forEach(c => {
                    if (c.userData.isHideBtn) c.visible = false;
                    if (c.userData.isShowBtn) c.visible = true;
                });
                selectObject(card);
            }
            return;
        }
        if (hit.userData.isShowBtn) {
            const card = hit.parent;
            if (card) {
                card.material.visible = true;
                card.children.forEach(c => {
                    if (c.userData.isHideBtn) c.visible = true;
                    if (c.userData.isShowBtn) c.visible = false;
                });
                selectObject(card);
            }
            return;
        }

        let target = hit;
        while (target.parent && target.parent !== scene) target = target.parent;

        if (target !== selectedObject) {
            selectObject(target);
        }
    }
}

function onPointerUp(event) {
    // Legacy onPointerUp removed
}

function onPointerMove(event) {
    // Legacy onPointerMove removed
}

function onKeyDown(event) {
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;

    switch (event.key.toLowerCase()) {
        case 't': setTool('translate'); break;
        case 'r': setTool('rotate'); break;
        case 's': setTool('scale'); break;
        case 'delete': deleteSelected(); break;
    }
}

function onKeyUp(event) {
    // Legacy onKeyUp removed
}

// Hierarchy System
window.updateHierarchy = function () {
    const tree = document.getElementById('hierarchy-tree');
    tree.innerHTML = '';

    objects.forEach((obj, index) => {
        const el = document.createElement('div');
        el.className = 'hierarchy-item';
        el.dataset.uuid = obj.uuid;
        if (selectedObject === obj) el.classList.add('selected');

        el.innerHTML = `<i class="fas fa-cube small mr-2" style="margin-right:5px; color:#aaa;"></i> ${obj.name || 'Object'}`;
        el.onclick = () => selectObject(obj);

        tree.appendChild(el);
    });

    if (objects.length === 0) {
        tree.innerHTML = '<div class="text-muted small text-center mt-2">Scene is Empty</div>';
    }
}

function updateHierarchyUI() {
    // Highlighting
    const items = document.querySelectorAll('.hierarchy-item');
    items.forEach(el => {
        if (selectedObject && el.dataset.uuid === selectedObject.uuid) el.classList.add('selected');
        else el.classList.remove('selected');
    });
}

// Inspector System
function setupInspectorEvents() {
    document.querySelectorAll('.transform-input').forEach(inp => {
        inp.addEventListener('input', updateObjectFromInspector);
    });

    const fileUpload = document.getElementById('file-upload');
    if (fileUpload) {
        fileUpload.addEventListener('change', (e) => {
            if (!e.target.files[0]) return;
            const formData = new FormData();
            formData.append('file', e.target.files[0]);

            document.getElementById('loading').style.display = 'flex';
            fetch(UPLOAD_URL, {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
                body: formData
            }).then(r => r.json()).then(d => {
                document.getElementById('loading').style.display = 'none';
                if (d.id && d.type === 'model') {
                    // Refresh assets list simply by appending
                    const grid = document.getElementById('asset-list');
                    if (grid) {
                        const card = document.createElement('div');
                        card.className = 'asset-card';
                        card.onclick = () => addModel(d.id, d.url, d.title);
                        card.innerHTML = `<div class="asset-icon"><i class="fas fa-cube"></i></div><div class="text-truncate">${d.title}</div>`;
                        grid.prepend(card);
                    }
                    alert('Asset Uploaded');
                } else {
                    alert('Uploaded!'); // Panoramas
                }
            });
            e.target.value = '';
        });
    }
}

function updateInspectorFromObject() {
    if (!selectedObject || isInspectorUpdating) return;
    isInspectorUpdating = true;

    const r2d = THREE.MathUtils.radToDeg;
    const o = selectedObject;

    inputs.pos.x.value = +o.position.x.toFixed(2);
    inputs.pos.y.value = +o.position.y.toFixed(2);
    inputs.pos.z.value = +o.position.z.toFixed(2);

    inputs.rot.x.value = +r2d(o.rotation.x).toFixed(1);
    inputs.rot.y.value = +r2d(o.rotation.y).toFixed(1);
    inputs.rot.z.value = +r2d(o.rotation.z).toFixed(1);

    inputs.scale.x.value = +o.scale.x.toFixed(4);
    inputs.scale.y.value = +o.scale.y.toFixed(4);
    inputs.scale.z.value = +o.scale.z.toFixed(4);

    isInspectorUpdating = false;
}

function updateObjectFromInspector() {
    if (!selectedObject || isInspectorUpdating) return;
    const d2r = THREE.MathUtils.degToRad;
    const o = selectedObject;

    o.position.set(+inputs.pos.x.value, +inputs.pos.y.value, +inputs.pos.z.value);
    o.rotation.set(d2r(+inputs.rot.x.value), d2r(+inputs.rot.y.value), d2r(+inputs.rot.z.value));
    o.scale.set(+inputs.scale.x.value, +inputs.scale.y.value, +inputs.scale.z.value);
}

function onWindowResize() {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

export function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    controls.update();

    renderer.render(scene, camera);
}

// Utility to adjust opacity of any color string
function adjustOpacity(color, opacity) {
    if (color.startsWith('rgba')) {
        return color.replace(/[\d\.]+\)$/g, `${opacity})`);
    } else if (color.startsWith('rgb')) {
        return color.replace('rgb', 'rgba').replace(')', `, ${opacity})`);
    } else if (color.startsWith('#')) {
        // Simple hex to rgba
        let r = parseInt(color.slice(1, 3), 16);
        let g = parseInt(color.slice(3, 5), 16);
        let b = parseInt(color.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    return color;
}
