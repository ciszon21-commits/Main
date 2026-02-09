import * as THREE from 'three';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';

// Will be set by the HTML template
let SCENE_ID;
let SCENE_BACKGROUND_URL;
let SCENE_OBJECTS_DATA;

// Globals
let container, camera, scene, renderer;
let raycaster;
let clock = new THREE.Clock();
let objects = [];

// Movement & Rotation
const moveState = { w: false, a: false, s: false, d: false, shift: false, space: false };
let yVelocity = 0;
const gravity = -25.0;
const jumpForce = 10.0;
const groundHeight = 1.8;
const flySpeed = 5.0;
const rotateSpeed = 0.002;
let isRotating = false;
const euler = new THREE.Euler(0, 0, 0, 'YXZ');

export function initViewer(sceneId, backgroundUrl, objectsData) {
    SCENE_ID = sceneId;
    SCENE_BACKGROUND_URL = backgroundUrl;
    SCENE_OBJECTS_DATA = objectsData;

    init();
    animate();
}

function init() {
    container = document.getElementById('vr-container');

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111111);

    // Camera
    camera = new THREE.PerspectiveCamera(70, container.clientWidth / container.clientHeight, 0.1, 2000);
    camera.position.set(0, 1.8, 5); // Human height 1.8m
    camera.rotation.order = 'YXZ'; // Important for FPS style rotation

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(5, 10, 7.5);
    scene.add(dirLight);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.xr.enabled = true;
    container.appendChild(renderer.domElement);
    document.body.appendChild(VRButton.createButton(renderer));

    // Create Grid (Visual Reference) - Hidden in preview mode as requested
    // const gridHelper = new THREE.GridHelper(20, 20, 0x333333, 0x111111);
    // scene.add(gridHelper);

    // Raycaster
    raycaster = new THREE.Raycaster();

    // Load Content
    loadSkybox();
    loadExistingObjects();

    // Hide loading UI
    setTimeout(() => {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
    }, 1000);

    // Events
    window.addEventListener('resize', onWindowResize);
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);

    // Mouse Events
    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('mousemove', onMouseMove);
    container.addEventListener('contextmenu', (e) => e.preventDefault()); // Disable right-click menu
}

function loadSkybox() {
    if (SCENE_BACKGROUND_URL) {
        new THREE.TextureLoader().load(SCENE_BACKGROUND_URL, (texture) => {
            texture.mapping = THREE.EquirectangularReflectionMapping;
            texture.colorSpace = THREE.SRGBColorSpace;
            const geo = new THREE.SphereGeometry(500, 60, 40);
            geo.scale(-1, 1, 1);
            const mat = new THREE.MeshBasicMaterial({ map: texture });
            scene.add(new THREE.Mesh(geo, mat));
        });
    }
}

function loadExistingObjects() {
    if (!SCENE_OBJECTS_DATA) return;

    SCENE_OBJECTS_DATA.forEach(obj => {
        if (obj.type === 'info_card') {
            addInfoCard(
                obj.id,
                obj.title,
                obj.content,
                obj.position,
                obj.rotation,
                obj.scale,
                obj.bgColor,
                obj.fontSize
            );
        } else if (obj.type === 'model') {
            loadModel(obj.url, obj.position, obj.rotation, obj.scale);
        }
    });
}

function addInfoCard(id, title, content, pos, rot, scale, bgColor, fontSize) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 768;
    const ctx = canvas.getContext('2d');

    // Hi-Tech Background (Tinted by bgColor)
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    // Darken bgColor for the bottom of the gradient
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

    // Content
    ctx.fillStyle = 'rgba(230, 245, 255, 0.95)';
    ctx.font = `${fontSize}px "Segoe UI", Arial`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    let y = 220;
    const lineHeight = fontSize * 1.5;
    const maxW = canvas.width - 120;

    let words = content.split('');
    let line = '';
    for (let n = 0; n < words.length; n++) {
        let testLine = line + words[n];
        let metrics = ctx.measureText(testLine);
        if (metrics.width > maxW && n > 0) {
            ctx.fillText(line, 60, y);
            line = words[n];
            y += lineHeight;
        } else {
            line = testLine;
        }
    }
    ctx.fillText(line, 60, y);

    const tex = new THREE.CanvasTexture(canvas);
    const mat = new THREE.MeshBasicMaterial({
        map: tex,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(3, 2.25), mat);

    // Create Close Button (Top Right "X")
    const hideCanvas = document.createElement('canvas');
    hideCanvas.width = 120;
    hideCanvas.height = 120;
    const hideCtx = hideCanvas.getContext('2d');

    // Circular background
    hideCtx.fillStyle = 'rgba(20, 25, 40, 0.8)';
    hideCtx.beginPath();
    hideCtx.arc(60, 60, 58, 0, Math.PI * 2);
    hideCtx.fill();

    // Glowing border
    hideCtx.strokeStyle = baseColor;
    hideCtx.lineWidth = 4;
    hideCtx.stroke();

    // "X" Symbol
    hideCtx.strokeStyle = '#ffffff';
    hideCtx.lineWidth = 8;
    hideCtx.lineCap = 'round';
    const padding = 35;
    hideCtx.beginPath();
    hideCtx.moveTo(padding, padding);
    hideCtx.lineTo(120 - padding, 120 - padding);
    hideCtx.moveTo(120 - padding, padding);
    hideCtx.lineTo(padding, 120 - padding);
    hideCtx.stroke();

    const hideTexture = new THREE.CanvasTexture(hideCanvas);
    const hideMat = new THREE.MeshBasicMaterial({
        map: hideTexture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9
    });
    const hideMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.4), hideMat);
    hideMesh.position.set(1.4, 1.05, 0.05); // Top right corner
    hideMesh.userData.isInteractable = true;
    hideMesh.userData.isHideBtn = true;
    hideMesh.userData.parentCardId = id;

    // Create Show Button (Interactive Title Capsule) - Initially Hidden
    const showCanvas = document.createElement('canvas');
    showCanvas.width = 1024;
    showCanvas.height = 256;
    const showCtx = showCanvas.getContext('2d');

    const themeColor = bgColor || '#17a2b8';

    // Draw Capsule/Rounded Rect background
    const rx = 512, ry = 128, rw = 800, rh = 160;
    const bx = rx - rw / 2, by = ry - rh / 2;

    // Gradient Background
    const btnGradient = showCtx.createLinearGradient(0, by, 0, by + rh);
    btnGradient.addColorStop(0, adjustOpacity(themeColor, 0.4));
    btnGradient.addColorStop(1, adjustOpacity(themeColor, 0.1));
    showCtx.fillStyle = btnGradient;

    // Rounded rect path
    const radius = 80;
    showCtx.beginPath();
    showCtx.moveTo(bx + radius, by);
    showCtx.lineTo(bx + rw - radius, by);
    showCtx.quadraticCurveTo(bx + rw, by, bx + rw, by + radius);
    showCtx.lineTo(bx + rw, by + rh - radius);
    showCtx.quadraticCurveTo(bx + rw, by + rh, bx + rw - radius, by + rh);
    showCtx.lineTo(bx + radius, by + rh);
    showCtx.quadraticCurveTo(bx, by + rh, bx, by + rh - radius);
    showCtx.lineTo(bx, by + radius);
    showCtx.quadraticCurveTo(bx, by, bx + radius, by);
    showCtx.closePath();
    showCtx.fill();

    // Glowing Border
    showCtx.strokeStyle = themeColor;
    showCtx.lineWidth = 10;
    showCtx.stroke();

    // Text Shadow
    showCtx.shadowBlur = 15;
    showCtx.shadowColor = themeColor;

    showCtx.fillStyle = 'white';
    showCtx.textAlign = 'center';
    showCtx.font = 'bold 70px "Segoe UI", Arial';
    showCtx.textBaseline = 'middle';
    showCtx.fillText(title, 512, 110);

    // Hint Text
    showCtx.shadowBlur = 0;
    showCtx.font = '36px "Segoe UI", Arial';
    showCtx.fillStyle = adjustOpacity('#ffffff', 0.8);
    showCtx.fillText('(點擊開啟內容)', 512, 175);

    const showTexture = new THREE.CanvasTexture(showCanvas);
    const showMat = new THREE.MeshBasicMaterial({
        map: showTexture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.95
    });
    const showMesh = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.75), showMat);
    showMesh.position.set(0, 0, 0.1);
    showMesh.visible = true;
    showMesh.userData.isInteractable = true;
    showMesh.userData.isShowBtn = true;
    showMesh.userData.parentCardId = id;

    // Default Hidden State for Body and Hide Button
    hideMesh.visible = false;
    // mesh.material.visible = false; // Main body

    // However, if we hide the main mesh material, the children might still be visible??
    // In Three.js, children inherit visibility only if parent.visible = false.
    // If parent.visible = true, children decide their own visibility.
    // We want the 'Show' button (child) to be VISIBLE.
    // So parent (mesh) must be VISIBLE.
    // We just hide the background plane material?
    // But mesh.material = mat.
    mat.visible = false;

    mesh.add(hideMesh);
    // mesh.add(readMesh); // Removed
    mesh.add(showMesh);

    mesh.position.set(pos.x, pos.y, pos.z);
    mesh.rotation.set(rot.x, rot.y, rot.z);
    mesh.scale.set(scale.x, scale.y, scale.z);

    mesh.userData.isInfoCard = true;
    mesh.userData.cardTitle = title;
    mesh.userData.cardContent = content;
    mesh.userData.infoCardId = id;

    scene.add(mesh);
    objects.push(mesh);
}

function loadModel(url, pos, rot, scale) {
    new FBXLoader().load(url, (obj) => {
        obj.position.set(pos.x, pos.y, pos.z);
        obj.rotation.set(rot.x, rot.y, rot.z);
        obj.scale.set(scale.x, scale.y, scale.z);
        scene.add(obj);
    });
}

function onMouseDown(event) {
    if (event.button === 2) { // Right click
        isRotating = true;
        euler.setFromQuaternion(camera.quaternion);
    } else if (event.button === 0) { // Left click
        const rect = renderer.domElement.getBoundingClientRect();
        const mouse = new THREE.Vector2(
            ((event.clientX - rect.left) / rect.width) * 2 - 1,
            -((event.clientY - rect.top) / rect.height) * 2 + 1
        );

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(objects);

        if (intersects.length > 0) {
            const hit = intersects[0].object;
            const target = hit.userData.isInfoCard ? hit : hit.parent;

            if (hit.userData.isHideBtn) {
                // Hide card content and buttons, show restore button
                const card = hit.parent;
                if (card) {
                    card.material.visible = false;
                    card.children.forEach(c => {
                        if (c.userData.isHideBtn) c.visible = false;
                        if (c.userData.isShowBtn) c.visible = true;
                    });
                }
                return;
            }

            if (hit.userData.isShowBtn) {
                // Restore card
                const card = hit.parent;
                if (card) {
                    card.material.visible = true;
                    card.children.forEach(c => {
                        if (c.userData.isHideBtn) c.visible = true;
                        if (c.userData.isShowBtn) c.visible = false;
                    });
                }

                // Call Read API
                const cardId = hit.userData.parentCardId;
                console.log("Marking card as read:", cardId);
                fetch(`/sinoVR/api/info-card/${cardId}/read/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                }).then(r => r.json()).then(console.log).catch(console.error);

                return;
            }

            if (target && target.userData.isInfoCard) {
                showCardDetail(target.userData.cardTitle, target.userData.cardContent);
            }
        }
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function onMouseUp(event) {
    if (event.button === 2) {
        isRotating = false;
    }
}

function onMouseMove(event) {
    if (!isRotating) return;

    const movementX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
    const movementY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;

    euler.y -= movementX * rotateSpeed;
    euler.x -= movementY * rotateSpeed;

    // Clamp pitch (up/down)
    euler.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, euler.x));

    camera.quaternion.setFromEuler(euler);
}

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    // Movement logic
    const actualSpeed = moveState.shift ? flySpeed * 2.0 : flySpeed;
    const velocity = new THREE.Vector3();

    if (moveState.w) velocity.z -= 1;
    if (moveState.s) velocity.z += 1;
    if (moveState.a) velocity.x -= 1;
    if (moveState.d) velocity.x += 1;

    if (velocity.lengthSq() > 0) {
        velocity.normalize().multiplyScalar(actualSpeed * delta);

        // Move relative to camera yaw (Y rotation) only
        const yawQuat = new THREE.Quaternion();
        yawQuat.setFromAxisAngle(new THREE.Vector3(0, 1, 0), euler.y);
        velocity.applyQuaternion(yawQuat);

        camera.position.add(velocity);
    }

    // Jump logic
    if (moveState.space && camera.position.y <= groundHeight + 0.01) {
        yVelocity = jumpForce;
    }

    // Apply Gravity
    yVelocity += gravity * delta;
    camera.position.y += yVelocity * delta;

    // Ground Collision
    if (camera.position.y < groundHeight) {
        camera.position.y = groundHeight;
        yVelocity = 0;
    }

    // Match Editor Play Mode Constraints (Grid 20x20)
    const gridSize = 10;
    camera.position.x = Math.max(-gridSize, Math.min(gridSize, camera.position.x));
    camera.position.z = Math.max(-gridSize, Math.min(gridSize, camera.position.z));

    renderer.render(scene, camera);
}

function onKeyDown(e) {
    switch (e.code) {
        case 'KeyW': moveState.w = true; break;
        case 'KeyA': moveState.a = true; break;
        case 'KeyS': moveState.s = true; break;
        case 'KeyD': moveState.d = true; break;
        case 'ShiftLeft': moveState.shift = true; break;
        case 'Space': moveState.space = true; e.preventDefault(); break;
    }
}

function onKeyUp(e) {
    switch (e.code) {
        case 'KeyW': moveState.w = false; break;
        case 'KeyA': moveState.a = false; break;
        case 'KeyS': moveState.s = false; break;
        case 'KeyD': moveState.d = false; break;
        case 'ShiftLeft': moveState.shift = false; break;
        case 'Space': moveState.space = false; break;
    }
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function showCardDetail(title, content) {
    document.getElementById('card-detail-title').textContent = title;
    document.getElementById('card-detail-content').textContent = content;
    document.getElementById('card-detail-overlay').style.display = 'flex';
}

window.showCardDetail = showCardDetail;

window.closeCardDetail = function () {
    document.getElementById('card-detail-overlay').style.display = 'none';
    isRotating = false;
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
