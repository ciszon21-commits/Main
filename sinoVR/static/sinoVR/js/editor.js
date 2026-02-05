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
let isPlayMode = false;
let isInspectorUpdating = false;

// Fly Mode Variables
let isFPSMode = false;
const flySpeed = 5.0;
const flyRotateSpeed = 2.0;
const moveState = { w: false, a: false, s: false, d: false, q: false, e: false, shift: false };
const euler = new THREE.Euler(0, 0, 0, 'YXZ');

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

    // Grid Helper
    const gridHelper = new THREE.GridHelper(20, 20, 0x555555, 0x333333);
    scene.add(gridHelper);

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
        updateInspectorFromObject();
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
            const mat = new THREE.MeshBasicMaterial({ map: texture });
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
function addInfoCard(id, title, content, transform = {}, bgColor = 'rgba(173, 216, 230, 0.95)', fontSize = 50) {
    // Create Canvas for card texture
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 768;
    const ctx = canvas.getContext('2d');

    // Background - use custom color
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(70, 130, 180, 0.9)'; // Steel blue border
    ctx.lineWidth = 8;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    // Title text (bold and larger)
    ctx.fillStyle = 'rgba(25, 25, 112, 1)'; // Midnight blue
    ctx.font = 'bold 72px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(title, canvas.width / 2, 40);

    // Separator line
    ctx.strokeStyle = 'rgba(70, 130, 180, 0.7)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(50, 150);
    ctx.lineTo(canvas.width - 50, 150);
    ctx.stroke();

    // Content text (multi-line with word wrap, custom font size)
    ctx.fillStyle = 'rgba(25, 25, 112, 0.95)';
    ctx.font = `${fontSize}px Arial`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    const maxWidth = canvas.width - 100;
    const lineHeight = fontSize + 15;
    let y = 200;

    // Character-based word wrap for content
    const chars = content.split('');
    let line = '';

    for (let i = 0; i < chars.length; i++) {
        const testLine = line + chars[i];
        const metrics = ctx.measureText(testLine);

        if (metrics.width > maxWidth && line.length > 0) {
            ctx.fillText(line, 50, y);
            line = chars[i];
            y += lineHeight;
            if (y > canvas.height - 50) break;
        } else {
            line = testLine;
        }
    }
    if (line) ctx.fillText(line, 50, y);

    // Create material and geometry
    const texture = new THREE.CanvasTexture(canvas);
    const geometry = new THREE.PlaneGeometry(3, 2.25);
    const material = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.95
    });

    // Create Hide Button
    const hideCanvas = document.createElement('canvas');
    hideCanvas.width = 256;
    hideCanvas.height = 128;
    const hideCtx = hideCanvas.getContext('2d');
    hideCtx.fillStyle = '#dc3545'; // Danger Red
    hideCtx.fillRect(0, 0, 256, 128);
    hideCtx.fillStyle = 'white';
    hideCtx.font = 'bold 60px Arial';
    hideCtx.textAlign = 'center';
    hideCtx.textBaseline = 'middle';
    hideCtx.fillText('Hide', 128, 64);

    const hideTexture = new THREE.CanvasTexture(hideCanvas);
    const hideMat = new THREE.MeshBasicMaterial({ map: hideTexture });
    const hideMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.4), hideMat);
    hideMesh.position.set(-0.8, -1.3, 0.05); // Bottom Left
    hideMesh.userData.isInteractable = true;
    hideMesh.userData.isHideBtn = true;
    hideMesh.userData.parentCardId = id;

    // Create Read Button
    const readCanvas = document.createElement('canvas');
    readCanvas.width = 256;
    readCanvas.height = 128;
    const readCtx = readCanvas.getContext('2d');
    readCtx.fillStyle = '#28a745'; // Success Green
    readCtx.fillRect(0, 0, 256, 128);
    readCtx.fillStyle = 'white';
    readCtx.font = 'bold 60px Arial';
    readCtx.textAlign = 'center';
    readCtx.textBaseline = 'middle';
    readCtx.fillText('Read', 128, 64);

    const readTexture = new THREE.CanvasTexture(readCanvas);
    const readMat = new THREE.MeshBasicMaterial({ map: readTexture });
    const readMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.4), readMat);
    readMesh.position.set(0.8, -1.3, 0.05); // Bottom Right
    readMesh.userData.isInteractable = true;
    readMesh.userData.isReadBtn = true;
    readMesh.userData.parentCardId = id;

    const mesh = new THREE.Mesh(geometry, material);
    mesh.add(hideMesh);
    mesh.add(readMesh);

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
    mesh.userData.cardFontSize = fontSize;
    mesh.name = `字卡: ${title}`;

    // Add double-click event for editing (non-play mode)
    mesh.userData.onDoubleClick = () => {
        if (!isPlayMode) {
            openEditCardModal(id, title, content, bgColor, fontSize);
        }
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
                addInfoCard(data.id, data.title, content, {}, bgColor, fontSize);
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
                rerenderInfoCard(cardId, title, content, bgColor, fontSize);
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
function rerenderInfoCard(cardId, title, content, bgColor, fontSize) {
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

    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(70, 130, 180, 0.9)';
    ctx.lineWidth = 8;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = 'rgba(25, 25, 112, 1)';
    ctx.font = 'bold 72px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(title, canvas.width / 2, 40);

    ctx.strokeStyle = 'rgba(70, 130, 180, 0.7)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(50, 150);
    ctx.lineTo(canvas.width - 50, 150);
    ctx.stroke();

    ctx.fillStyle = 'rgba(25, 25, 112, 0.95)';
    ctx.font = `${fontSize}px Arial`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    const maxWidth = canvas.width - 100;
    const lineHeight = fontSize + 15;
    let y = 200;

    const chars = content.split('');
    let line = '';
    for (let i = 0; i < chars.length; i++) {
        const testLine = line + chars[i];
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && line.length > 0) {
            ctx.fillText(line, 50, y);
            line = chars[i];
            y += lineHeight;
            if (y > canvas.height - 50) break;
        } else {
            line = testLine;
        }
    }
    if (line) ctx.fillText(line, 50, y);

    const texture = new THREE.CanvasTexture(canvas);
    const geometry = new THREE.PlaneGeometry(3, 2.25);
    const material = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.95
    });

    const newMesh = new THREE.Mesh(geometry, material);
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
        if (!isPlayMode) {
            openEditCardModal(cardId, title, content, bgColor, fontSize);
        }
    };

    scene.add(newMesh);
    objects.push(newMesh);

    if (selectedObject === mesh) {
        selectObject(newMesh);
    }

    updateHierarchy();
}


window.showCardDetail = function (title, content) {
    document.getElementById('card-detail-title').textContent = title;
    document.getElementById('card-detail-content').textContent = content;
    document.getElementById('card-detail-overlay').style.display = 'flex';
}

window.closeCardDetail = function () {
    document.getElementById('card-detail-overlay').style.display = 'none';
}

// Global exposed functions
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

window.togglePlayMode = function () {
    isPlayMode = !isPlayMode;

    const btn = document.getElementById('btn-play-toggle');
    const overlay = document.querySelector('.play-mode-overlay');

    if (isPlayMode) {
        btn.classList.replace('btn-light', 'btn-primary');
        btn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        overlay.style.display = 'block';

        // Hide helpers
        transformControl.detach();
        transformControl.visible = false;

        // Disable Orbit Controls
        controls.enabled = false;

        // capture initial rotation again just in case
        euler.setFromQuaternion(camera.quaternion);

    } else {
        btn.classList.replace('btn-primary', 'btn-light');
        btn.innerHTML = '<i class="fas fa-play"></i> Play';
        overlay.style.display = 'none';

        controls.enabled = true;
        transformControl.visible = true;
        if (selectedObject) transformControl.attach(selectedObject);
    }
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
        if (!isPlayMode) transformControl.attach(object);
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

// --- UI/Interaction ---

function onPointerDown(event) {
    if (isPlayMode) {
        // Check if clicking on InfoCard
        if (event.button === 0) { // Left click
            const rect = renderer.domElement.getBoundingClientRect();
            pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            raycaster.setFromCamera(pointer, camera);
            const intersects = raycaster.intersectObjects(objects, true);

            if (intersects.length > 0) {
                // Check if we hit a button first
                const hit = intersects[0].object;

                if (hit.userData.isHideBtn) {
                    // Hide the entire card group
                    const card = hit.parent;
                    if (card) card.visible = false;
                    return;
                }

                if (hit.userData.isReadBtn) {
                    const cardId = hit.userData.parentCardId;
                    const btnMesh = hit;

                    // Call API to mark as read
                    fetch(`/sinoVR/api/info-card/${cardId}/read/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': CSRF_TOKEN
                        }
                    })
                        .then(r => r.json())
                        .then(data => {
                            if (data.status === 'success') {
                                // Visual feedback: Change button color to green/darker green or add checkmark
                                // Simple way: redraw texture
                                const canvas = btnMesh.material.map.image; // It's a canvas
                                const ctx = canvas.getContext('2d');
                                ctx.fillStyle = '#218838'; // Darker Green
                                ctx.fillRect(0, 0, 256, 128);
                                ctx.fillStyle = 'white';
                                ctx.fillText('Read ✓', 128, 64);
                                btnMesh.material.map.needsUpdate = true;
                            }
                        });
                    return;
                }

                let target = intersects[0].object;
                // Find the root object
                while (target.parent && target.parent !== scene) {
                    target = target.parent;
                }

                if (target.userData.isInfoCard) {
                    showCardDetail(target.userData.cardTitle, target.userData.cardContent);
                    return;
                }
            }
        }

        // FPS Mode Check: Right Click holds to rotating
        if (event.button === 2) {
            isFPSMode = true;
            controls.enabled = false;
            euler.setFromQuaternion(camera.quaternion);
        }
        return;
    }

    // Don't deselect if clicking on the Gizmo
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(pointer, camera);
    const intersects = raycaster.intersectObjects(objects, true);

    if (intersects.length > 0) {
        let target = intersects[0].object;
        while (target.parent && target.parent !== scene) target = target.parent;

        if (target !== selectedObject) {
            selectObject(target);
        }
    }
}

function onPointerUp(event) {
    if (event.button === 2) {
        isFPSMode = false;
        if (!isPlayMode) controls.enabled = true;
    }
}

function onPointerMove(event) {
    if (isFPSMode && isPlayMode) {
        const movementX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
        const movementY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;

        euler.y -= movementX * 0.002 * flyRotateSpeed;
        euler.x -= movementY * 0.002 * flyRotateSpeed;

        euler.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, euler.x));

        camera.quaternion.setFromEuler(euler);
    }
}

function onKeyDown(event) {
    if (event.key === 'Escape' && isPlayMode) togglePlayMode();
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;

    if (isPlayMode) {
        switch (event.code) {
            case 'KeyW': moveState.w = true; break;
            case 'KeyA': moveState.a = true; break;
            case 'KeyS': moveState.s = true; break;
            case 'KeyD': moveState.d = true; break;
            case 'ShiftLeft':
            case 'ShiftRight': moveState.shift = true; break;
        }
        return;
    }

    switch (event.key.toLowerCase()) {
        case 't': setTool('translate'); break;
        case 'r': setTool('rotate'); break;
        case 's': setTool('scale'); break;
        case 'delete': deleteSelected(); break;
    }
}

function onKeyUp(event) {
    if (isPlayMode) {
        switch (event.code) {
            case 'KeyW': moveState.w = false; break;
            case 'KeyA': moveState.a = false; break;
            case 'KeyS': moveState.s = false; break;
            case 'KeyD': moveState.d = false; break;
            case 'ShiftLeft':
            case 'ShiftRight': moveState.shift = false; break;
        }
    }
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

    document.getElementById('file-upload').addEventListener('change', (e) => {
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
                const card = document.createElement('div');
                card.className = 'asset-card';
                card.onclick = () => addModel(d.id, d.url, d.title);
                card.innerHTML = `<div class="asset-icon"><i class="fas fa-cube"></i></div><div class="text-truncate">${d.title}</div>`;
                grid.prepend(card);
                alert('Asset Uploaded');
            } else {
                alert('Uploaded!'); // Panoramas
            }
        });
        e.target.value = '';
    });
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

    if (isPlayMode) {
        // Human FPS Movement (1.8m height, horizontal plane only)
        const actualSpeed = moveState.shift ? flySpeed * 2.0 : flySpeed;
        const moveDirection = new THREE.Vector3();

        if (moveState.w) moveDirection.z -= 1;
        if (moveState.s) moveDirection.z += 1;
        if (moveState.a) moveDirection.x -= 1;
        if (moveState.d) moveDirection.x += 1;

        if (moveDirection.lengthSq() > 0) {
            moveDirection.normalize();

            // Only apply horizontal rotation (Y-axis), ignore pitch
            const horizontalRotation = new THREE.Quaternion();
            horizontalRotation.setFromAxisAngle(new THREE.Vector3(0, 1, 0), euler.y);

            // Apply rotation to movement direction
            moveDirection.applyQuaternion(horizontalRotation);

            // Only move on XZ plane (horizontal)
            camera.position.x += moveDirection.x * actualSpeed * delta;
            camera.position.z += moveDirection.z * actualSpeed * delta;
        }

        // Boundary constraints (Grid is 20x20, centered at origin)
        const gridSize = 10; // Grid extends from -10 to +10
        const humanHeight = 1.8; // Fixed human eye height

        // Clamp X and Z position within grid boundaries
        camera.position.x = Math.max(-gridSize, Math.min(gridSize, camera.position.x));
        camera.position.z = Math.max(-gridSize, Math.min(gridSize, camera.position.z));

        // Lock camera height to human eye level
        camera.position.y = humanHeight;

    } else {
        controls.update();
    }

    renderer.render(scene, camera);
}
