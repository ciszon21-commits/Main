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
const moveState = { w: false, a: false, s: false, d: false, shift: false };
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

    // Create Grid (Visual Reference)
    const gridHelper = new THREE.GridHelper(20, 20, 0x333333, 0x111111);
    scene.add(gridHelper);

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

function addInfoCard(title, content, pos, rot, scale, bgColor, fontSize) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 768;
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(70, 130, 180, 0.9)';
    ctx.lineWidth = 10;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    // Title
    ctx.fillStyle = '#111';
    ctx.font = 'bold 72px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(title, canvas.width / 2, 40);

    // Separator
    ctx.beginPath();
    ctx.moveTo(50, 150);
    ctx.lineTo(canvas.width - 50, 150);
    ctx.stroke();

    // Content
    ctx.font = `${fontSize}px Arial`;
    ctx.textAlign = 'left';
    let y = 200;
    const lineHeight = fontSize * 1.4;
    const maxW = canvas.width - 100;

    let words = content.split(''); // Char split for CJK
    let line = '';
    for (let n = 0; n < words.length; n++) {
        let testLine = line + words[n];
        let metrics = ctx.measureText(testLine);
        if (metrics.width > maxW && n > 0) {
            ctx.fillText(line, 50, y);
            line = words[n];
            y += lineHeight;
        } else {
            line = testLine;
        }
    }
    ctx.fillText(line, 50, y);

    const tex = new THREE.CanvasTexture(canvas);
    const mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(3, 2.25), mat);

    mesh.position.set(pos.x, pos.y, pos.z);
    mesh.rotation.set(rot.x, rot.y, rot.z);
    mesh.scale.set(scale.x, scale.y, scale.z);

    mesh.userData.isInfoCard = true;
    mesh.userData.cardTitle = title;
    mesh.userData.cardContent = content;

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
            const target = intersects[0].object;
            if (target.userData.isInfoCard) {
                showCardDetail(target.userData.cardTitle, target.userData.cardContent);
            }
        }
    }
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

    // Match Editor Play Mode Constraints (Grid 20x20, Height 1.8)
    const gridSize = 10;
    camera.position.x = Math.max(-gridSize, Math.min(gridSize, camera.position.x));
    camera.position.z = Math.max(-gridSize, Math.min(gridSize, camera.position.z));
    camera.position.y = 1.8;

    renderer.render(scene, camera);
}

function onKeyDown(e) {
    switch (e.code) {
        case 'KeyW': moveState.w = true; break;
        case 'KeyA': moveState.a = true; break;
        case 'KeyS': moveState.s = true; break;
        case 'KeyD': moveState.d = true; break;
        case 'ShiftLeft': moveState.shift = true; break;
    }
}

function onKeyUp(e) {
    switch (e.code) {
        case 'KeyW': moveState.w = false; break;
        case 'KeyA': moveState.a = false; break;
        case 'KeyS': moveState.s = false; break;
        case 'KeyD': moveState.d = false; break;
        case 'ShiftLeft': moveState.shift = false; break;
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
