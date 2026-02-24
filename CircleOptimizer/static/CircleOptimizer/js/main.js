/**
 * Circle Optimizer - Main JavaScript
 * Updated for Manual 3-Arc Mode with Symmetry and Constrained Connections
 */

// Global State
let viewBoxState = { x: -10, y: -10, w: 20, h: 20 };
let isPanning = false;
let startPan = { x: 0, y: 0 };
let activeDragIndex = null;
let dragType = null; // 'center', 'radius', 'startAngle', 'endAngle'
let violatedPointIndices = []; // Indices of clearance points exceeding the boundary

// Default Clearance Envelope
const HIGHWAY_ENVELOPE = [
    { name: '點1', x: -4.9468, y: -1.0272 },
    { name: '點2', x: -4.9069, y: 0.9724 },
    { name: '點3', x: -3.9070, y: 0.9524 },
    { name: '點4', x: -3.8521, y: 3.7000 },
    { name: '點5', x: 4.0481, y: 3.5470 },
    { name: '點6', x: 3.9933, y: 0.8085 },
    { name: '點7', x: 4.9931, y: 0.8284 },
    { name: '點8', x: 5.0331, y: -1.1712 }
];

const TaiwanHighSpeedRail_ENVELOPE = [
    { name: 'THSR_1', x: -4.9468, y: -1.0272 },
    { name: 'THSR_2', x: -4.9069, y: 0.9724 },
    { name: 'THSR_3', x: -3.9070, y: 0.9524 },
    { name: 'THSR_4', x: -3.8521, y: 3.7000 },
    { name: 'THSR_5', x: 4.0481, y: 3.5470 },
    { name: 'THSR_6', x: 3.9933, y: 0.8085 },
    { name: 'THSR_7', x: 4.9931, y: 0.8284 },
    { name: 'THSR_8', x: 5.0331, y: -1.1712 }
];

// 7267C/Single Rail
const TaiwanRailwaySingleRail_ENVELOPE = [
    { name: 'TR_1', x: -1.8200, y: -2.6500 },
    { name: 'TR_2', x: -2.2000, y: -0.6000 },
    { name: 'TR_3', x: -2.2000, y: 0.2500 },
    { name: 'TR_4', x: -2.0767, y: 0.8000 },
    { name: 'TR_5', x: -1.7000, y: 1.9166 },
    { name: 'TR_6', x: -1.4500, y: 1.9166 },
    { name: 'TR_7', x: -1.4500, y: 2.5165 },
    { name: 'TR_8', x: -1.1630, y: 2.8238 },
    { name: 'TR_9', x: -0.8125, y: 3.0562 },
    { name: 'TR_10', x: -0.4177, y: 3.2009 },
    { name: 'TR_11', x: 0.0000, y: 3.2500 },
    { name: 'TR_12', x: 0.4177, y: 3.2009 },
    { name: 'TR_13', x: 0.4177, y: 3.2009 },
    { name: 'TR_14', x: 0.8125, y: 3.0562 },
    { name: 'TR_15', x: 1.1630, y: 2.8238 },
    { name: 'TR_16', x: 1.4500, y: 2.5165 },
    { name: 'TR_17', x: 1.4500, y: 1.9166 },
    { name: 'TR_18', x: 1.7000, y: 1.9166 },
    { name: 'TR_19', x: 2.0767, y: 0.8000 },
    { name: 'TR_20', x: 2.2000, y: 0.2500 },
    { name: 'TR_21', x: 2.2000, y: -0.6000 },
    { name: 'TR_22', x: 1.8200, y: -2.6500 }
];

const TaipeiMetro_ENVELOPE = [
    { name: 'MRT_1', x: -4.9468, y: -1.0272 },
    { name: 'MRT_2', x: -4.9069, y: 0.9724 },
    { name: 'MRT_3', x: -3.9070, y: 0.9524 },
    { name: 'MRT_4', x: -3.8521, y: 3.7000 },
    { name: 'MRT_5', x: 4.0481, y: 3.5470 },
    { name: 'MRT_6', x: 3.9933, y: 0.8085 },
    { name: 'MRT_7', x: 4.9931, y: 0.8284 },
    { name: 'MRT_8', x: 5.0331, y: -1.1712 }
];

const LightRail_ENVELOPE = [
    { name: 'LRT_1', x: -4.9468, y: -1.0272 },
    { name: 'LRT_2', x: -4.9069, y: 0.9724 },
    { name: 'LRT_3', x: -3.9070, y: 0.9524 },
    { name: 'LRT_4', x: -3.8521, y: 3.7000 },
    { name: 'LRT_5', x: 4.0481, y: 3.5470 },
    { name: 'LRT_6', x: 3.9933, y: 0.8085 },
    { name: 'LRT_7', x: 4.9931, y: 0.8284 },
    { name: 'LRT_8', x: 5.0331, y: -1.1712 }
];


// Envelopes State
let envelopes = [
    {
        id: 'env-1',
        name: '公路隧道淨空包絡線',
        type: 'highway',
        points: JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE)),
        color: '#000000',
        visible: true
    }
];

let activeEnvelopeIndex = null;
let activePointIndex = null;

// Main Data Structure for 3 Arcs
// Arc 1 & 3: Main arcs (Top/Bottom)
// Arc 2: Connector arc (Middle)
// We store state for all, but Arc 2 is heavily constrained.
let arcs = [
    { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 207.622, color: '#fd8f00ff' },      // Top
    { id: '2', cx: -3.1011, cy: -1.6227, r: 2.0000, startAngle: 207.622, endAngle: 254.622, color: '#28a745' }, // Connector
    { id: '3', cx: 0.0000, cy: 9.6526, r: 13.6940, startAngle: 254.622, endAngle: 270.000, color: '#007bff' },   // Bottom
    { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 205.000, color: '#c05600' },      // Top
    { id: '5', cx: -2.9002, cy: -1.4524, r: 2.8000, startAngle: 205.000, endAngle: 251.000, color: '#1e7e34' }, // Connector
    { id: '6', cx: 0.0, cy: 6.9704, r: 11.7080, startAngle: 251.000, endAngle: 270.000, color: '#0056b3' }   // Bottom
];

// Helper: Get point on circle
function getPointOnCircle(cx, cy, r, angleDeg) {
    const rad = angleDeg * Math.PI / 180;
    return {
        x: cx + r * Math.cos(rad),
        y: cy + r * Math.sin(rad)
    };
}

// Helper: Convert decimal degrees to DMS string (DD°MM'SS")
function toDMS(deg) {
    const absDeg = Math.abs(deg);
    const d = Math.floor(absDeg);
    const minFloat = (absDeg - d) * 60;
    const m = Math.floor(minFloat);
    const s = Math.round((minFloat - m) * 60);
    // Handle carry over if seconds is 60
    let finalS = s;
    let finalM = m;
    let finalD = d;
    if (finalS === 60) {
        finalS = 0;
        finalM += 1;
    }
    if (finalM === 60) {
        finalM = 0;
        finalD += 1;
    }
    return `${deg < 0 ? '-' : ''}${finalD}°${finalM.toString().padStart(2, '0')}'${finalS.toString().padStart(2, '0')}"`;
}

// Helper: Setup initial positions for connector arcs if needed
function initConnectors() {
    updateConnectorGeometry();
}

document.addEventListener('DOMContentLoaded', () => {
    bindZoomPanEvents();

    initConnectors(); // Calc initial geometry
    renderEnvelopeControls();
    drawSystem();
    autoFitViewBox();

    // Bind Auto Fit button
    const autoFitBtn = document.getElementById('autoFitBtn');
    if (autoFitBtn) {
        autoFitBtn.addEventListener('click', autoFitViewBox);
    }

    // Bind Add Envelope button
    const addEnvelopeBtn = document.getElementById('addEnvelopeBtn');
    if (addEnvelopeBtn) {
        addEnvelopeBtn.addEventListener('click', () => {
            addEnvelope();
        });
    }

    // Bind Init Section button
    const initSectionBtn = document.getElementById('initSectionBtn');
    if (initSectionBtn) {
        initSectionBtn.addEventListener('click', () => {
            loadDefaultSection();
        });
    }

    // Bind Import DXF button
    const importDxfBtn = document.getElementById('importDxfBtn');
    const dxfInput = document.getElementById('dxfInput');
    if (importDxfBtn && dxfInput) {
        importDxfBtn.addEventListener('click', () => {
            dxfInput.click();
        });
        dxfInput.addEventListener('change', (e) => {
            handleDxfImport(e.target.files);
            dxfInput.value = ''; // Reset for next use
        });
    }

    // Bind Excavation Thickness change
    const excavationThicknessInput = document.getElementById('excavationThickness');
    if (excavationThicknessInput) {
        excavationThicknessInput.addEventListener('input', () => {
            if (parseFloat(excavationThicknessInput.value) < 0) {
                excavationThicknessInput.value = 0;
            }
            updateInfoPanel();
        });
    }

    // Bind Min Thickness changes
    ['minThicknessTop', 'minThicknessBottom'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                if (parseFloat(el.value) < 0) {
                    el.value = 0;
                }
                drawSystem();
            });
        }
    });

    // Resize observer or initial fit
    setTimeout(autoFitViewBox, 100);

    // Bind Temp Save Section button
    const tempSaveSectionBtn = document.getElementById('tempSaveSectionBtn');
    if (tempSaveSectionBtn) {
        tempSaveSectionBtn.addEventListener('click', saveSectionTemp);
    }

    // Bind Restore Section button
    const restoreSectionBtn = document.getElementById('restoreSectionBtn');
    if (restoreSectionBtn) {
        restoreSectionBtn.addEventListener('click', () => {
            if (confirm('是否復原斷面？')) {
                restoreSectionFromDB();
            }
        });
    }
});

// ------------------------------------------------------------
// IndexedDB for Temporary Storage
// ------------------------------------------------------------
const DB_NAME = 'SinoNATM_DB';
const DB_VERSION = 1;
const STORE_NAME = 'TempSections';

function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME);
            }
        };
        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
    });
}

async function saveToDB(key, data) {
    try {
        const db = await initDB();
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        store.put(data, key);
        return new Promise((resolve, reject) => {
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    } catch (err) {
        console.error('IndexedDB Save Error:', err);
    }
}

async function getFromDB(key) {
    try {
        const db = await initDB();
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const request = store.get(key);
        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    } catch (err) {
        console.error('IndexedDB Load Error:', err);
        return null;
    }
}


// Bind Open Project Button
document.addEventListener('DOMContentLoaded', () => {
    const openProjectBtn = document.getElementById('openProjectBtn');
    if (openProjectBtn) {
        openProjectBtn.onclick = () => {
            openProject();
        };
    }
});

// Bind Save Project Button
document.addEventListener('DOMContentLoaded', () => {
    const saveProjectBtn = document.getElementById('saveProjectBtn');
    if (saveProjectBtn) {
        saveProjectBtn.onclick = () => {
            saveProject();
        };
    }
});


// Bind Export Button
document.addEventListener('DOMContentLoaded', () => {
    const saveAsCSVBtn = document.getElementById('saveAsCSVBtn');
    if (saveAsCSVBtn) {
        saveAsCSVBtn.onclick = () => {
            saveAsCSV();
        };
    }
});

// Bind Export Button
document.addEventListener('DOMContentLoaded', () => {
    const saveAsDXFBtn = document.getElementById('saveAsDXFBtn');
    if (saveAsDXFBtn) {
        saveAsDXFBtn.onclick = () => {
            saveAsDXF();
            alert('已成功匯出 DXF 檔案！');
        };
    }
});

// ------------------------------------------------------------
// Load Default Section (產生隧道初始斷面 / 重設斷面)
// ------------------------------------------------------------
function loadDefaultSection() {
    // 儲存目前斷面參數至 section.tmp (作為備份)
    saveSectionTemp();

    const tunnelType = document.getElementById('tunnelType');
    if (!tunnelType) return;

    const type = tunnelType.value;

    switch (type) {
        case 'triple': // 三心圓
            arcs[0] = { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 207.622, color: '#fd8f00ff' };
            arcs[1] = { id: '2', cx: -3.1011, cy: -1.6227, r: 2.0000, startAngle: 207.622, endAngle: 254.622, color: '#28a745' };
            arcs[2] = { id: '3', cx: 0.0000, cy: 9.6526, r: 13.6940, startAngle: 254.622, endAngle: 270.000, color: '#007bff' };
            arcs[3] = { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 205.000, color: '#c05600' };
            arcs[4] = { id: '5', cx: -2.9002, cy: -1.4524, r: 2.8000, startAngle: 205.000, endAngle: 251.000, color: '#1e7e34' };
            arcs[5] = { id: '6', cx: 0.0, cy: 6.9704, r: 11.7080, startAngle: 251.000, endAngle: 270.000, color: '#0056b3' };
            break;

        case 'circular': // 正圓形
            arcs[0] = { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 270.000, color: '#fd8f00ff' };
            arcs[1] = { id: '2', cx: -0.0001, cy: 0.0000, r: 0.0001, startAngle: 270.000, endAngle: 270.000, color: '#28a745' };
            arcs[2] = { id: '3', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 270.000, endAngle: 270.000, color: '#007bff' };
            arcs[3] = { id: '4', cx: 0.0000, cy: 0.0000, r: 6.0000, startAngle: 90.000, endAngle: 270.000, color: '#c05600' };
            arcs[4] = { id: '5', cx: -0.0001, cy: 0.0000, r: 0.0001, startAngle: 270.000, endAngle: 270.000, color: '#1e7e34' };
            arcs[5] = { id: '6', cx: 0.0000, cy: 0.0000, r: 6.0000, startAngle: 270.000, endAngle: 270.000, color: '#0056b3' };
            break;

        case 'horseshoe': // 馬蹄形
            arcs[0] = { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 225.000, color: '#fd8f00ff' };
            arcs[1] = { id: '2', cx: -3.5000, cy: -2.0000, r: 1.5000, startAngle: 225.000, endAngle: 260.000, color: '#28a745' };
            arcs[2] = { id: '3', cx: 0.0000, cy: 8.0000, r: 12.0000, startAngle: 260.000, endAngle: 270.000, color: '#007bff' };
            arcs[3] = { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 222.000, color: '#c05600' };
            arcs[4] = { id: '5', cx: -3.8000, cy: -2.2000, r: 1.8000, startAngle: 222.000, endAngle: 258.000, color: '#1e7e34' };
            arcs[5] = { id: '6', cx: 0.0, cy: 7.5000, r: 11.5000, startAngle: 258.000, endAngle: 270.000, color: '#0056b3' };
            break;

        case 'dual': // 雙心圓
            arcs[0] = { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 240.000, color: '#fd8f00ff' };
            arcs[1] = { id: '2', cx: -0.0001, cy: -5.4999, r: 0.0001, startAngle: 240.000, endAngle: 240.000, color: '#28a745' };
            arcs[2] = { id: '3', cx: 0.0000, cy: 12.0000, r: 16.0000, startAngle: 240.000, endAngle: 270.000, color: '#007bff' };
            arcs[3] = { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 238.000, color: '#c05600' };
            arcs[4] = { id: '5', cx: -0.0001, cy: -5.9999, r: 0.0001, startAngle: 238.000, endAngle: 238.000, color: '#1e7e34' };
            arcs[5] = { id: '6', cx: 0.0, cy: 11.0000, r: 15.0000, startAngle: 238.000, endAngle: 270.000, color: '#0056b3' };
            break;

        case 'quad': // 四心圓
            arcs[0] = { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 200.000, color: '#fd8f00ff' };
            arcs[1] = { id: '2', cx: -2.8000, cy: -1.2000, r: 2.5000, startAngle: 200.000, endAngle: 245.000, color: '#28a745' };
            arcs[2] = { id: '3', cx: 0.0000, cy: 10.0000, r: 14.0000, startAngle: 245.000, endAngle: 270.000, color: '#007bff' };
            arcs[3] = { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 198.000, color: '#c05600' };
            arcs[4] = { id: '5', cx: -3.0000, cy: -1.4000, r: 2.8000, startAngle: 198.000, endAngle: 243.000, color: '#1e7e34' };
            arcs[5] = { id: '6', cx: 0.0, cy: 9.5000, r: 13.5000, startAngle: 243.000, endAngle: 270.000, color: '#0056b3' };
            break;

        default:
            return;
    }

    updateConnectorGeometry();
    drawSystem();
    autoFitViewBox();
}

function renderEnvelopeControls() {
    const container = document.getElementById('envelopesContainer');
    if (!container) return;

    container.innerHTML = '';

    envelopes.forEach((env, envIdx) => {
        const envCard = document.createElement('div');
        envCard.className = 'envelope-card';
        envCard.style.borderLeft = `4px solid ${env.color}`;
        envCard.style.padding = '10px';
        envCard.style.marginBottom = '10px';
        envCard.style.background = '#fcfcfc';
        envCard.style.borderRadius = '4px';
        envCard.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';

        envCard.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                <div style="display: flex; gap: 8px; align-items: center; width: 60%;">
                    <input type="color" value="${env.color.substring(0, 7)}" 
                        onchange="updateEnvelopeColor(${envIdx}, this.value)" 
                        style="width: 30px; height: 30px; border: none; padding: 0; background: transparent; cursor: pointer;">
                    <input type="text" value="${env.name}" class="env-name-input" 
                        onchange="updateEnvelopeName(${envIdx}, this.value)" 
                        style="font-weight: bold; border: none; background: transparent; width: 80%; color: ${env.color}; font-size: 1.1rem;">
                </div>
                <div style="display: flex; gap: 5px; align-items: center;">
                    <select onchange="applyTemplate(${envIdx}, this.value)" style="font-size: 1.00em; padding: 2px;">
                        <option value="">套用樣板...</option>
                        <option value="highway">公路隧道淨空包絡線</option>
                        <option value="railway">鐵路隧道淨空包絡線</option>
                    </select>
                </div>
            </div>
            <div class="points-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 6px;">
                ${env.points.map((p, pIdx) => `
                    <div class="point-input" style="background: white; border: 1px solid #f0f0f0; padding: 4px; border-radius: 4px; display: flex; align-items: center; gap: 4px; justify-content: space-between; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="display: flex; align-items: center; gap: 4px; flex-grow: 1;">
                            <input type="text" value="${p.name || `點${pIdx + 1}`}" 
                                onchange="updateNodeName(${envIdx}, ${pIdx}, this.value)" 
                                style="width: 80px; font-size: 1.00em; padding: 2px; border: 1px solid #ddd; border-radius: 2px;">
                            <div style="display: flex; gap: 2px;">
                                <input type="number" step="0.0001" value="${p.x.toFixed(4)}" 
                                    onchange="updateNodeCoord(${envIdx}, ${pIdx}, 'x', this.value)" 
                                    style="width: 100px; font-size: 1.00em; padding: 2px; border: 1px solid #eee; border-radius: 2px;">
                                <input type="number" step="0.0001" value="${p.y.toFixed(4)}" 
                                    onchange="updateNodeCoord(${envIdx}, ${pIdx}, 'y', this.value)" 
                                    style="width: 100px; font-size: 1.00em; padding: 2px; border: 1px solid #eee; border-radius: 2px;">
                            </div>
                        </div>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeNode(${envIdx}, ${pIdx})" 
                            style="padding: 2px 6px; font-size: 0.9em; white-space: nowrap;">➖刪除</button>
                    </div>
                `).join('')}
            </div>
            <div style="display: flex; gap: 5px; margin-top: 10px; border-top: 1px solid #eee; padding-top: 5px; justify-content: flex-end;">
                <button class="btn btn-sm" onclick="addNode(${envIdx})" title="新增節點" style="padding: 6px 14px;font-size: 1.0rem">➕增加控制點</button>
                <button class="btn btn-sm btn-danger" onclick="removeEnvelope(${envIdx})" title="刪除包絡線" style="padding: 6px 14px;font-size: 1.0rem">⛔刪除包絡線</button>
            </div>
        `;
        container.appendChild(envCard);
    });
}

function addEnvelope(templateType = 'highway') {
    let points = [];
    let name = '';
    let color = '#000000';

    switch (templateType) {
        case 'highway':
            points = JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE));
            name = '公路隧道淨空包絡線';
            color = '#000000ff';
            break;
        case 'railway':
            points = JSON.parse(JSON.stringify(TaiwanRailwaySingleRail_ENVELOPE));
            name = '鐵路隧道淨空包絡線';
            color = '#2c3e50';
            break;
        default:
            points = [
                { name: '點1', x: -3, y: 0 },
                { name: '點2', x: -3, y: 3 },
                { name: '點3', x: 3, y: 3 },
                { name: '點4', x: 3, y: 0 }
            ];
            name = '自定義包絡線';
            color = '#000000';
    }

    const newEnv = {
        id: 'env-' + (envelopes.length + 1),
        name: name + ' ' + (envelopes.length + 1),
        type: templateType,
        points: points,
        color: color,
        visible: true
    };
    envelopes.push(newEnv);
    renderEnvelopeControls();
    drawSystem();
}

function removeEnvelope(index) {
    if (envelopes.length <= 1) {
        alert('請至少保留一個包絡線。');
        return;
    }
    if (confirm('確定要刪除此包絡線嗎？')) {
        envelopes.splice(index, 1);
        renderEnvelopeControls();
        drawSystem();
        checkClearance();
    }
}

function addNode(envIdx) {
    const env = envelopes[envIdx];
    const lastPoint = env.points[env.points.length - 1];
    const nextIdx = env.points.length + 1;
    env.points.push({
        name: `點${nextIdx}`,
        x: lastPoint.x + 0.5,
        y: lastPoint.y
    });
    renderEnvelopeControls();
    drawSystem();
}

function removeNode(envIdx, pIdx) {
    const env = envelopes[envIdx];
    if (env.points.length <= 3) {
        alert('包絡線必須至少有 3 個節點。');
        return;
    }
    env.points.splice(pIdx, 1);
    renderEnvelopeControls();
    drawSystem();
    checkClearance();
}

function updateEnvelopeName(envIdx, name) {
    envelopes[envIdx].name = name;
    renderEnvelopeControls(); // Refresh to update title color
}

function updateEnvelopeColor(envIdx, color) {
    envelopes[envIdx].color = color;
    renderEnvelopeControls();
    drawSystem();
}

function applyTemplate(envIdx, templateType) {
    if (!templateType) return;
    let points = [];
    if (templateType === 'highway') points = JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE));
    else if (templateType === 'railway') points = JSON.parse(JSON.stringify(TaiwanRailwaySingleRail_ENVELOPE));

    envelopes[envIdx].points = points;
    envelopes[envIdx].type = templateType;
    renderEnvelopeControls();
    drawSystem();
}

function updateNodeCoord(envIdx, pIdx, axis, value) {
    envelopes[envIdx].points[pIdx][axis] = parseFloat(value);
    drawSystem();
}

function updateNodeName(envIdx, pIdx, name) {
    envelopes[envIdx].points[pIdx].name = name;
    drawSystem();
}

// ------------------------------------------------------------
// DXF Import Logic
// ------------------------------------------------------------

async function handleDxfImport(files) {
    if (!files || files.length === 0) return;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        try {
            const text = await file.text();
            const polylines = parseDxfPolylines(text);

            if (polylines.length === 0) {
                console.warn(`No polylines found in ${file.name}`);
                continue;
            }

            polylines.forEach((poly, polyIdx) => {
                // 過濾掉 0,0 點
                const filteredPoints = poly.points.filter(pt => !(pt.x === 0 && pt.y === 0));

                if (filteredPoints.length === 0) {
                    console.warn(`Polyline ${polyIdx + 1} in ${file.name} has only 0,0 points, skipping.`);
                    return;
                }

                const envName = files.length > 1 || polylines.length > 1
                    ? `${file.name.replace('.dxf', '')}_${polyIdx + 1}`
                    : file.name.replace('.dxf', '');

                const newEnv = {
                    id: 'env-' + (envelopes.length + 1),
                    name: envName,
                    type: 'dxf_import',
                    points: filteredPoints, // 使用過濾後的點
                    color: '#e67e22',
                    visible: true
                };
                envelopes.push(newEnv);
            });
        } catch (err) {
            console.error(`Error parsing ${file.name}:`, err);
            alert(`讀取 ${file.name} 失敗: ${err.message}`);
        }
    }

    renderEnvelopeControls();
    drawSystem();
}

/**
 * Lightweight DXF Parser for LWPOLYLINE and POLYLINE
 */
function parseDxfPolylines(dxfText) {
    const lines = dxfText.split(/\r?\n/);
    const polylines = [];
    let currentPoly = null;
    let inEntities = false;
    let i = 0;

    function nextPair() {
        if (i + 1 >= lines.length) return null;
        const code = lines[i++].trim();
        const value = lines[i++].trim();
        return { code: parseInt(code), value };
    }

    while (i < lines.length) {
        const line = lines[i].trim();
        if (line === 'ENTITIES') {
            inEntities = true;
            i++;
            continue;
        }
        if (line === 'ENDSEC' && inEntities) {
            inEntities = false;
            i++;
            continue;
        }

        if (!inEntities) {
            i++;
            continue;
        }

        const pair = nextPair();
        if (!pair) break;

        if (pair.code === 0) {
            if (pair.value === 'LWPOLYLINE') {
                currentPoly = { type: 'LWPOLYLINE', points: [], closed: false };
                polylines.push(currentPoly);
            } else if (pair.value === 'POLYLINE') {
                currentPoly = { type: 'POLYLINE', points: [], closed: false };
                polylines.push(currentPoly);
            } else if (pair.value === 'VERTEX' && currentPoly && currentPoly.type === 'POLYLINE') {
                // Vertex for POLYLINE
                let vx = 0, vy = 0;
                let vPair = nextPair();
                while (vPair && vPair.code !== 0) {
                    if (vPair.code === 10) vx = parseFloat(vPair.value);
                    if (vPair.code === 20) vy = parseFloat(vPair.value);
                    vPair = nextPair();
                }
                currentPoly.points.push({ name: `點${currentPoly.points.length + 1}`, x: vx, y: vy });
                i -= 2; // Step back to let the next loop handle the code 0
            } else if (pair.value === 'SEQEND') {
                // End of POLYLINE vertices
                currentPoly = null;
            }
        } else if (currentPoly && currentPoly.type === 'LWPOLYLINE') {
            if (pair.code === 10) {
                // New point start
                const x = parseFloat(pair.value);
                const nextP = nextPair();
                if (nextP && nextP.code === 20) {
                    const y = parseFloat(nextP.value);
                    currentPoly.points.push({ name: `點${currentPoly.points.length + 1}`, x, y });
                } else {
                    i -= 2; // Should not happen in valid DXF
                }
            } else if (pair.code === 70) {
                const flag = parseInt(pair.value);
                currentPoly.closed = (flag & 1) !== 0;
            }
        } else if (currentPoly && currentPoly.type === 'POLYLINE') {
            if (pair.code === 70) {
                const flag = parseInt(pair.value);
                currentPoly.closed = (flag & 1) !== 0;
            }
        }
    }

    return polylines.filter(p => p.points.length > 0);
}

// ------------------------------------------------------------
// Geometry & Constraints
// ------------------------------------------------------------

function getLineIntersection(p1, p2, p3, p4) {
    // Line 1: p1 -> p2
    // Line 2: p3 -> p4
    // Return intersection point {x, y} or null if parallel

    const x1 = p1.x, y1 = p1.y, x2 = p2.x, y2 = p2.y;
    const x3 = p3.x, y3 = p3.y, x4 = p4.x, y4 = p4.y;

    const denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
    if (Math.abs(denom) < 1e-10) return null; // Parallel

    const ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
    const ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;

    return {
        x: x1 + ua * (x2 - x1),
        y: y1 + ua * (y2 - y1)
    };
}

function updateConnectorGeometry() {
    const p1 = arcs[0];
    const p2 = arcs[1];
    const p3 = arcs[2];
    const p4 = arcs[3];
    const p5 = arcs[4];
    const p6 = arcs[5];
    // 1. Maintain Tangency Chains
    let d12 = Math.sqrt(Math.pow(p2.cx - p1.cx, 2) + Math.pow(p2.cy - p1.cy, 2));
    if (d12 > p1.r) {
        const factor12 = (p1.r - 0.001) / d12;
        p2.cx = p1.cx + (p2.cx - p1.cx) * factor12;
        p2.cy = p1.cy + (p2.cy - p1.cy) * factor12;
        d12 = p1.r - 0.001;
    }
    p2.r = Math.max(0.0001, Math.abs(p1.r - d12)); // Enforce R2 > 0

    // Constraint: d(P2, P3) <= R3
    let d23 = Math.sqrt(Math.pow(p3.cx - p2.cx, 2) + Math.pow(p3.cy - p2.cy, 2));
    if (d23 > p3.r) {
        // Clamp P3 center towards P2 so that distance = R3
        d23 = Math.min(d23, p3.r);
    }
    p3.r = p2.r + d23;

    // 2. Update Connection Angles for Tangency
    // Arc 1 End = Arc 2 Start
    p1.endAngle = Math.atan2(p2.cy - p1.cy, p2.cx - p1.cx) * 180 / Math.PI;
    while (p1.endAngle < p1.startAngle) p1.endAngle += 360;
    while (p1.endAngle >= p1.startAngle + 360) p1.endAngle -= 360;
    // Hard limit: p1.endAngle <= 270
    if (p1.endAngle > 270) p1.endAngle = 270;
    p2.startAngle = p1.endAngle;

    // Arc 3 Start = Arc 2 End
    p3.startAngle = Math.atan2(p2.cy - p3.cy, p2.cx - p3.cx) * 180 / Math.PI;
    while (p3.startAngle < p2.startAngle) p3.startAngle += 360;
    while (p3.startAngle >= p2.startAngle + 360) p3.startAngle -= 360;
    // Hard limit: p3.startAngle <= 270
    if (p3.startAngle > 270) p3.startAngle = 270;
    p2.endAngle = p3.startAngle;

    // Standardize sweep direction for Arc 2 (Ensuring θ2 > 0 for startAngle <= endAngle)
    let diff = p2.endAngle - p2.startAngle;
    if (diff < 0) diff += 360;

    // Enforce θ2 > 2
    if (diff < 2.0 && p2.startAngle < 268) {
        diff = 2.0;
    } else if (p2.startAngle >= 270) {
        diff = 0;
    }
    p2.endAngle = Math.min(270, p2.startAngle + diff);

    // Ensure Arc 3 End (270 or axis) is >= Arc 3 Start and <= 270
    p3.endAngle = Math.min(270, Math.max(p3.startAngle, p3.endAngle));
    if (p3.endAngle > 270) p3.endAngle = 270;

    // ============================================================
    // Arc 4/5/6 Tangency Chain (mirrors Arc 1/2/3)
    // ============================================================
    let d45 = Math.sqrt(Math.pow(p5.cx - p4.cx, 2) + Math.pow(p5.cy - p4.cy, 2));
    if (d45 > p4.r) {
        const factor45 = (p4.r - 0.001) / d45;
        p5.cx = p4.cx + (p5.cx - p4.cx) * factor45;
        p5.cy = p4.cy + (p5.cy - p4.cy) * factor45;
        d45 = p4.r - 0.001;
    }
    p5.r = Math.max(0.0001, Math.abs(p4.r - d45)); // Enforce R5 > 0

    // Constraint: d(P5, P6) <= R6
    let d56 = Math.sqrt(Math.pow(p6.cx - p5.cx, 2) + Math.pow(p6.cy - p5.cy, 2));
    if (d56 > p6.r) {
        d56 = Math.min(d56, p6.r);
    }
    p6.r = p5.r + d56;

    // Arc 4 End = Arc 5 Start
    p4.endAngle = Math.atan2(p5.cy - p4.cy, p5.cx - p4.cx) * 180 / Math.PI;
    while (p4.endAngle < p4.startAngle) p4.endAngle += 360;
    while (p4.endAngle >= p4.startAngle + 360) p4.endAngle -= 360;
    if (p4.endAngle > 270) p4.endAngle = 270;
    p5.startAngle = p4.endAngle;

    // Arc 6 Start = Arc 5 End
    p6.startAngle = Math.atan2(p5.cy - p6.cy, p5.cx - p6.cx) * 180 / Math.PI;
    while (p6.startAngle < p5.startAngle) p6.startAngle += 360;
    while (p6.startAngle >= p5.startAngle + 360) p6.startAngle -= 360;
    if (p6.startAngle > 270) p6.startAngle = 270;
    p5.endAngle = p6.startAngle;

    // Standardize sweep direction for Arc 5
    let diff5 = p5.endAngle - p5.startAngle;
    if (diff5 < 0) diff5 += 360;

    // Enforce θ5 > 2
    if (diff5 < 2.0 && p5.startAngle < 268) {
        diff5 = 2.0;
    } else if (p5.startAngle >= 270) {
        diff5 = 0;
    }
    p5.endAngle = Math.min(270, p5.startAngle + diff5);

    // Ensure Arc 6 End is >= Arc 6 Start and <= 270
    p6.endAngle = Math.min(270, Math.max(p6.startAngle, p6.endAngle));
    if (p6.endAngle > 270) p6.endAngle = 270;

    // 3. User Requested Constraints: P4S.y - P1S.y >= Tt; P3E.y - P6E.y >= Tb
    // ============================================================
    const tt = Math.max(0, parseFloat(document.getElementById('minThicknessTop')?.value || 0.3));
    const tb = Math.max(0, parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3));

    const p1s = getPointOnCircle(p1.cx, p1.cy, p1.r, p1.startAngle);
    const p4s = getPointOnCircle(p4.cx, p4.cy, p4.r, p4.startAngle);
    if (p4s.y - p1s.y < tt) {
        const sin4s = Math.sin(p4.startAngle * Math.PI / 180);
        p4.cy = (p1s.y + tt) - (p4.r * sin4s);
    }

    const p3e = getPointOnCircle(p3.cx, p3.cy, p3.r, p3.endAngle);
    const p6e = getPointOnCircle(p6.cx, p6.cy, p6.r, p6.endAngle);
    if (p3e.y - p6e.y < tb) {
        const sin3e = Math.sin(p3.endAngle * Math.PI / 180);
        p3.cy = (p6e.y + tb) - (p3.r * sin3e);
    }

    // ============================================================
    // 4. Comprehensive Generalized Boundary Constraints (v2)
    // Enforcing specific distance rules between transition points and opposite arcs.
    // ============================================================

    // Helper to get all transition points for both sides (Left implied by arcs 0-5)
    function getTransitionPoints() {
        return [
            { name: 'P1E', p: getPointOnCircle(p1.cx, p1.cy, p1.r, p1.endAngle), side: 'inner' },
            { name: 'P3S', p: getPointOnCircle(p3.cx, p3.cy, p3.r, p3.startAngle), side: 'inner' },
            { name: 'P4E', p: getPointOnCircle(p4.cx, p4.cy, p4.r, p4.endAngle), side: 'outer' },
            { name: 'P6S', p: getPointOnCircle(p6.cx, p6.cy, p6.r, p6.startAngle), side: 'outer' }
        ];
    }

    const tPoints = getTransitionPoints();
    const innerArr = [p1, p3];
    const outerArr = [p4, p6];

    tPoints.forEach(item => {
        const pt = item.p;
        if (item.side === 'inner') {
            // Inner Points vs Outer Arcs (4, 5, 6)
            outerArr.forEach((oa, idx) => {
                const angle = Math.atan2(pt.y - oa.cy, pt.x - oa.cx) * 180 / Math.PI;
                if (isAngleInRange(angle, oa.startAngle, oa.endAngle)) {
                    const dist = Math.sqrt(Math.pow(pt.x - oa.cx, 2) + Math.pow(pt.y - oa.cy, 2));
                    // Logic: P1E < R4/5/6; P2S, P2E, P3S > R4 but < R5/6
                    let violation = false;
                    if (oa.id === '4') { // Arc 4
                        if (item.name === 'P1E') {
                            if (dist >= oa.r) violation = true;
                        } else { // P2S, P2E, P3S
                            if (dist <= oa.r) violation = true;
                        }
                    } else { // Arc 5 or 6
                        if (dist >= oa.r) violation = true;
                    }

                    if (violation) {
                        // Adjust oa center vertically if possible (Arcs 4, 6)
                        if (oa.id === '4' || oa.id === '6') {
                            const sinVal = Math.sin(angle * Math.PI / 180);
                            if (Math.abs(sinVal) > 0.01) {
                                const targetDist = (oa.id === '4' && item.name !== 'P1E') ? oa.r + 0.001 : oa.r - 0.001;
                                oa.cy = pt.y - targetDist * sinVal;
                            }
                        }
                    }
                }
            });
        } else {
            // Outer Points vs Inner Arcs (1, 2, 3)
            innerArr.forEach((ia, idx) => {
                const angle = Math.atan2(pt.y - ia.cy, pt.x - ia.cx) * 180 / Math.PI;
                if (isAngleInRange(angle, ia.startAngle, ia.endAngle)) {
                    const dist = Math.sqrt(Math.pow(pt.x - ia.cx, 2) + Math.pow(pt.y - ia.cy, 2));
                    // Logic: All Outer Points > R(Inner)
                    if (dist <= ia.r) {
                        // Adjust item.arcObj (the outer arc containing point) center vertically
                        const arcObj = (item.name === 'P4E' || item.name === 'P5S') ? p4 : p6;
                        const ptAngleInOwnArc = (item.name === 'P4E' || item.name === 'P5S') ? arcObj.endAngle : arcObj.startAngle;
                        const sinVal = Math.sin(ptAngleInOwnArc * Math.PI / 180);
                        if (Math.abs(sinVal) > 0.01) {
                            arcObj.cy = (ia.cy + (ia.r + 0.001) * Math.sin(angle * Math.PI / 180)) - (arcObj.r * sinVal);
                        }
                    }
                }
            });
        }
    });

    // Final Tangency Synchronization
    updateConnectorTangencyOnly();
}

/**
 * Helper to update only the calculated parts of the tangency chain 
 * without re-triggering the full constraint logic to avoid infinite loops.
 */
function updateConnectorTangencyOnly() {
    const p1 = arcs[0];
    const p2 = arcs[1];
    const p3 = arcs[2];
    const p4 = arcs[3];
    const p5 = arcs[4];
    const p6 = arcs[5];

    // P1->P2->P3
    let d12 = Math.sqrt(Math.pow(p2.cx - p1.cx, 2) + Math.pow(p2.cy - p1.cy, 2));
    p2.r = Math.max(0.0001, Math.abs(p1.r - d12));
    let d23 = Math.sqrt(Math.pow(p3.cx - p2.cx, 2) + Math.pow(p3.cy - p2.cy, 2));
    p3.r = p2.r + d23;

    // P4->P5->P6
    let d45 = Math.sqrt(Math.pow(p5.cx - p4.cx, 2) + Math.pow(p5.cy - p4.cy, 2));
    p5.r = Math.max(0.0001, Math.abs(p4.r - d45));
    let d56 = Math.sqrt(Math.pow(p6.cx - p5.cx, 2) + Math.pow(p6.cy - p5.cy, 2));
    p6.r = p5.r + d56;
}

// ------------------------------------------------------------
// Rendering
// ------------------------------------------------------------

function getOrCreateMarker(color, rotation = 0) {
    const canvas = document.getElementById('canvas');
    let defs = canvas.querySelector('defs');
    if (!defs) {
        defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        canvas.insertBefore(defs, canvas.firstChild);
    }

    // ID includes rotation
    const id = `arrow-${color.replace('#', '')}-rot${rotation}`;
    if (document.getElementById(id)) return id;

    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', id);
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '10');
    marker.setAttribute('refX', '5');
    marker.setAttribute('refY', '5');
    marker.setAttribute('orient', 'auto');
    marker.setAttribute('markerUnits', 'strokeWidth');

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '5');
    circle.setAttribute('cy', '5');
    circle.setAttribute('r', '3');
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', color);
    circle.setAttribute('stroke-width', '1');

    marker.appendChild(circle);
    defs.appendChild(marker);

    return id;
}

function getVisualScale() {
    // Base scale on current ViewBox size relative to a reference size (e.g., 100)
    // Using min dimension protects against extremely wide or tall aspect ratios
    const minDim = Math.min(viewBoxState.w, viewBoxState.h);
    // Reference 100 => multiplier 1. If VB is 50 => multiplier 0.5.
    return minDim / 100;
}

function drawSystem() {
    const canvas = document.getElementById('canvas');
    if (!canvas) return;

    // Clear Groups
    const shapeGroup = document.getElementById('shapeGroup');
    const circlesGroup = document.getElementById('circlesGroup');
    const overlayGroup = document.getElementById('overlayGroup');
    if (shapeGroup) shapeGroup.innerHTML = '';
    if (circlesGroup) circlesGroup.innerHTML = '';
    if (overlayGroup) overlayGroup.innerHTML = '';

    // 0.5 Draw Intersection Fills (Bottom Layer)
    if (arcs.length >= 6) {
        const pairs = [[0, 3], [1, 4], [2, 5]];
        pairs.forEach(([i1, i2]) => {
            const arc1 = arcs[i1];
            const arc2 = arcs[i2];

            // Left Fill
            drawArcDiffFill(shapeGroup, arc1, arc2, false);

            // Right Fill (Mirror)
            const mArc1 = { cx: -arc1.cx, cy: arc1.cy, r: arc1.r, startAngle: 180 - arc1.startAngle, endAngle: 180 - arc1.endAngle };
            const mArc2 = { cx: -arc2.cx, cy: arc2.cy, r: arc2.r, startAngle: 180 - arc2.startAngle, endAngle: 180 - arc2.endAngle };
            drawArcDiffFill(shapeGroup, mArc1, mArc2, true);
        });
    }

    // 1. Draw Background Polygons (Envelopes)
    envelopes.forEach((env, index) => {
        if (env.visible) {
            drawPolygon(shapeGroup, env, index);
        }
    });

    // 2. Draw Arcs (L and R)
    arcs.forEach((arc, index) => {
        // Draw Left Arc (Original)
        drawArc(circlesGroup, arc, index, false);

        // Draw Right Arc (Mirror)
        const mirrorArc = {
            id: arc.id.replace('L', 'R'),
            cx: -arc.cx,
            cy: arc.cy, // Keep Y
            r: arc.r,
            // Original: 180 - end -> 180 - start
            // New: Swap order (180 - start -> 180 - end)
            startAngle: 180 - arc.startAngle,
            endAngle: 180 - arc.endAngle,
            color: arc.color
        };

        drawArc(circlesGroup, mirrorArc, index, true);
    });

    // 4. Draw Info Table
    updateInfoPanel();
}

function drawPolygon(container, env, envIdx) {
    const points = env.points;
    if (points.length < 3) return;

    const scale = getVisualScale();
    const d = points.map((p, i) => (i === 0 ? 'M' : 'L') + ` ${p.x} ${-p.y}`).join(' ') + ' Z';

    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    poly.setAttribute('d', d);
    poly.setAttribute('fill', env.color); // Dynamic fill color
    poly.setAttribute('fill-opacity', '0.1'); // Transparency 20%
    poly.setAttribute('stroke', env.color); // Envelope Stroke
    poly.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    poly.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`);
    container.appendChild(poly);

    // Draw Vertices and Labels
    const fontSize = (2.2 * scale).toFixed(4);
    const labelOffset = (1.5 * scale);

    points.forEach((p, pIdx) => {
        // Violation Highlight Marker (Need to check if this point is in violated list)
        // Note: violatedPointIndices might need to be structured per envelope
        const isViolated = (violatedPointIndices[envIdx] || []).includes(pIdx);

        if (isViolated) {
            const hDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            hDot.setAttribute('cx', p.x);
            hDot.setAttribute('cy', -p.y);
            hDot.setAttribute('r', (1.5 * scale).toFixed(4));
            hDot.setAttribute('fill', 'yellow');
            hDot.setAttribute('stroke', 'red');
            hDot.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
            overlayGroup.appendChild(hDot);

            // N.G. Label
            const errorText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            errorText.setAttribute('x', p.x);
            errorText.setAttribute('y', -p.y + labelOffset + (2.0 * scale));
            errorText.setAttribute('fill', 'red');
            errorText.setAttribute('font-size', (2.5 * scale).toFixed(4));
            errorText.setAttribute('font-weight', 'bold');
            errorText.setAttribute('text-anchor', 'middle');
            errorText.textContent = "N.G.";
            overlayGroup.appendChild(errorText);
        }

        // Handle
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('cx', p.x);
        dot.setAttribute('cy', -p.y);
        dot.setAttribute('r', (0.8 * scale).toFixed(4));
        dot.setAttribute('fill', '#ffffff');
        dot.setAttribute('stroke', env.color);
        dot.setAttribute('stroke-width', (0.4 * scale).toFixed(4));

        dot.setAttribute('class', 'interactive-handle');
        dot.style.cursor = 'move';

        // Update bindDrag to handle envIdx and pIdx
        dot.addEventListener('mousedown', (e) => startDrag(e, envIdx, 'envelopePoint', pIdx));
        dot.addEventListener('touchstart', (e) => startDrag(e, envIdx, 'envelopePoint', pIdx));
        overlayGroup.appendChild(dot);

        // Coordinate Label (Simplify for multiple envelopes)
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', p.x);
        text.setAttribute('y', -p.y - labelOffset);
        text.setAttribute('font-size', fontSize);
        text.setAttribute('fill', '#333');
        text.setAttribute('text-anchor', 'middle');
        text.style.pointerEvents = 'none';
        const pName = p.name || `點${pIdx + 1}`;
        text.textContent = `${pName}(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`;
        overlayGroup.appendChild(text);
    });
}

function drawArc(container, arc, index, isMirror = false) {
    const scale = getVisualScale();
    // Arc Path (Thinner Line Width: 0.5)
    // For Mirror Arcs, we use sweepFlag "1" because angles are reversed
    const d = describeArc(arc.cx, -arc.cy, arc.r, arc.startAngle, arc.endAngle, isMirror ? "1" : "0");
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', arc.color);
    path.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    container.appendChild(path);

    // handles logic
    if (!isMirror) {
        const handleSize = 1.5 * scale;

        // Center Handle (Solid Circle)
        const cHandle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        cHandle.setAttribute('cx', arc.cx);
        cHandle.setAttribute('cy', -arc.cy);
        cHandle.setAttribute('r', handleSize / 1.5);
        cHandle.setAttribute('fill', arc.color);
        cHandle.setAttribute('class', 'interactive-handle');
        cHandle.style.cursor = 'move';
        bindDrag(cHandle, index, 'center');
        container.appendChild(cHandle);

        // Center Label
        const cLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        const cyOffset = (index < 3) ? -(2 * scale) : (2 * scale); // Top-right for P1-3, Bottom-right for P4-6
        cLabel.setAttribute('x', arc.cx + (1.5 * scale));
        cLabel.setAttribute('y', -arc.cy + cyOffset);
        cLabel.setAttribute('font-size', (2.2 * scale).toFixed(4));
        cLabel.setAttribute('fill', arc.color);
        cLabel.setAttribute('dominant-baseline', 'middle');
        cLabel.style.pointerEvents = 'none';
        cLabel.textContent = `P${arc.id.replace('L', '')}(${arc.cx.toFixed(4)}, ${arc.cy.toFixed(4)})`;
        overlayGroup.appendChild(cLabel);

        // Start/End Handles (Hidden for Arc 2)
        if (index !== 1) {
            const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
            const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);

            // Start Handle

            // Labels and Handles
            if (index === 0 || index === 3 || index === 2 || index === 5) {
                // Start Label (Show only for Arc 1 and 4)
                if (index === 0 || index === 3) {
                    const sLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    sLabel.setAttribute('x', pStart.x);
                    sLabel.setAttribute('y', -pStart.y - (2 * scale));
                    sLabel.setAttribute('font-size', (2.2 * scale).toFixed(4));
                    sLabel.setAttribute('fill', arc.color);
                    sLabel.setAttribute('text-anchor', 'middle');
                    sLabel.style.pointerEvents = 'none';
                    sLabel.textContent = `P${arc.id.replace('L', '')}S(${pStart.x.toFixed(4)}, ${(pStart.y).toFixed(4)})`;
                    overlayGroup.appendChild(sLabel);
                }

                // End Handle (Only for Arc 1 and 4 as they are adjustable by dragging end point)
                if (index === 0 || index === 3) {
                    let eHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    eHandle.setAttribute('x', pEnd.x - handleSize / 2);
                    eHandle.setAttribute('y', -pEnd.y - handleSize / 2);
                    eHandle.setAttribute('width', handleSize);
                    eHandle.setAttribute('height', handleSize);
                    eHandle.setAttribute('class', 'interactive-handle');
                    eHandle.style.cursor = 'move';
                    eHandle.setAttribute('fill', arc.color);
                    eHandle.setAttribute('stroke', arc.color);
                    eHandle.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
                    bindDrag(eHandle, index, 'endAngle');
                    container.appendChild(eHandle);
                }

                // End Label (Visible for 0, 3, 2, 5)
                const eLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                eLabel.setAttribute('x', pEnd.x);
                // Adjust label position for bottom arcs (2 and 5) to avoid overlapping with the arc itself
                let labelYOffset = (index === 2 || index === 5) ? (4 * scale) : -(2 * scale);
                eLabel.setAttribute('y', -pEnd.y + labelYOffset);
                eLabel.setAttribute('font-size', (2.2 * scale).toFixed(4));
                eLabel.setAttribute('fill', arc.color);
                eLabel.setAttribute('text-anchor', 'middle');
                eLabel.style.pointerEvents = 'none';
                eLabel.textContent = `P${arc.id.replace('L', '')}E(${pEnd.x.toFixed(4)}, ${(pEnd.y).toFixed(4)})`;
                overlayGroup.appendChild(eLabel);
            }

            // Dashed Radial Lines: Center to Start, Center to End
            const lineS = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineS.setAttribute('x1', arc.cx);
            lineS.setAttribute('y1', -arc.cy);
            lineS.setAttribute('x2', pStart.x);
            lineS.setAttribute('y2', -pStart.y);
            lineS.setAttribute('stroke', arc.color);
            lineS.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineS.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`);
            container.appendChild(lineS);

            const lineE = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineE.setAttribute('x1', arc.cx);
            lineE.setAttribute('y1', -arc.cy);
            lineE.setAttribute('x2', pEnd.x);
            lineE.setAttribute('y2', -pEnd.y);
            lineE.setAttribute('stroke', arc.color);
            lineE.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineE.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`);
            container.appendChild(lineE);

            // Radius Label
            const rMidX = (arc.cx + pStart.x) / 2;
            const rMidY = (-arc.cy + (-pStart.y)) / 2;
            const rDx = pStart.x - arc.cx;
            const rDy = (-pStart.y) - (-arc.cy);
            let rAngle = Math.atan2(rDy, rDx) * 180 / Math.PI;
            if (rAngle > 90) rAngle -= 180;
            if (rAngle < -90) rAngle += 180;
            const rLen = Math.sqrt(rDx * rDx + rDy * rDy);
            const rOffDistSize = (index < 3) ? -1.5 * scale : 1.5 * scale; // Above for R1-3, Below for R4-6
            const rPerpX = -rDy / rLen * rOffDistSize;
            const rPerpY = rDx / rLen * rOffDistSize;

            const rLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            rLabel.setAttribute('x', rMidX + rPerpX);
            rLabel.setAttribute('y', rMidY + rPerpY);
            rLabel.setAttribute('font-size', (2.2 * scale).toFixed(4));
            rLabel.setAttribute('fill', arc.color);
            rLabel.setAttribute('text-anchor', 'middle');
            rLabel.setAttribute('dominant-baseline', 'middle');
            rLabel.setAttribute('transform', `rotate(${rAngle.toFixed(1)}, ${(rMidX + rPerpX).toFixed(4)}, ${(rMidY + rPerpY).toFixed(4)})`);
            rLabel.style.pointerEvents = 'none';
            rLabel.textContent = `R${arc.id.replace("L", "")}=${arc.r.toFixed(4)}`;
            overlayGroup.appendChild(rLabel);

            // Angle Label (θ1, θ2, θ3)
            const theta = Math.abs(arc.endAngle - arc.startAngle);
            const midAngle = (arc.startAngle + arc.endAngle) / 2;
            const pMid = getPointOnCircle(arc.cx, arc.cy, arc.r, midAngle);
            const aLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');

            // Offset label slightly outside or inside for visibility
            const offset = 1.5 * scale;
            aLabel.setAttribute('x', pMid.x + offset * Math.cos(midAngle * Math.PI / 180));
            aLabel.setAttribute('y', -pMid.y - offset * Math.sin(midAngle * Math.PI / 180));
            aLabel.setAttribute('font-size', (2.2 * scale).toFixed(4));
            aLabel.setAttribute('fill', arc.color);
            aLabel.setAttribute('text-anchor', 'middle');
            aLabel.setAttribute('dominant-baseline', 'middle');
            aLabel.style.pointerEvents = 'none';

            let labelRot = midAngle - 90;
            if (labelRot > 90) labelRot -= 180;
            if (labelRot < -90) labelRot += 180;
            aLabel.setAttribute('transform', `rotate(${-labelRot.toFixed(1)}, ${(pMid.x + offset * Math.cos(midAngle * Math.PI / 180)).toFixed(4)}, ${(-pMid.y - offset * Math.sin(midAngle * Math.PI / 180)).toFixed(4)})`);
            aLabel.textContent = `θ${index + 1}=${toDMS(theta)}`;
            overlayGroup.appendChild(aLabel);
        } else if (index === 1) { // Arc 2
            const theta2 = Math.abs(arc.endAngle - arc.startAngle);
            const midAngle2 = (arc.startAngle + arc.endAngle) / 2;
            const pMid2 = getPointOnCircle(arc.cx, arc.cy, arc.r, midAngle2);
            const aLabel2 = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            const offset2 = 1.5 * scale;
            aLabel2.setAttribute('x', pMid2.x + offset2 * Math.cos(midAngle2 * Math.PI / 180));
            aLabel2.setAttribute('y', -pMid2.y - offset2 * Math.sin(midAngle2 * Math.PI / 180));
            aLabel2.setAttribute('font-size', (2.2 * scale).toFixed(4));
            aLabel2.setAttribute('fill', arc.color);
            aLabel2.setAttribute('text-anchor', 'middle');
            aLabel2.setAttribute('dominant-baseline', 'middle');
            aLabel2.style.pointerEvents = 'none';
            let labelRot2 = midAngle2 - 90;
            if (labelRot2 > 90) labelRot2 -= 180;
            if (labelRot2 < -90) labelRot2 += 180;
            aLabel2.setAttribute('transform', `rotate(${-labelRot2.toFixed(1)}, ${(pMid2.x + offset2 * Math.cos(midAngle2 * Math.PI / 180)).toFixed(4)}, ${(-pMid2.y - offset2 * Math.sin(midAngle2 * Math.PI / 180)).toFixed(3)})`);
            aLabel2.textContent = `θ2=${toDMS(theta2)}`;
            overlayGroup.appendChild(aLabel2);

            // Radial Lines for Arc 2 (P2~P1E and P2~P3S)
            const pStart2 = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
            const pEnd2 = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);

            const lineS2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineS2.setAttribute('x1', arc.cx);
            lineS2.setAttribute('y1', -arc.cy);
            lineS2.setAttribute('x2', pStart2.x);
            lineS2.setAttribute('y2', -pStart2.y);
            lineS2.setAttribute('stroke', arc.color);
            lineS2.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineS2.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`);
            overlayGroup.appendChild(lineS2);

            const lineE2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineE2.setAttribute('x1', arc.cx);
            lineE2.setAttribute('y1', -arc.cy);
            lineE2.setAttribute('x2', pEnd2.x);
            lineE2.setAttribute('y2', -pEnd2.y);
            lineE2.setAttribute('stroke', arc.color);
            lineE2.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineE2.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`);
            overlayGroup.appendChild(lineE2);

            // R2 Label on P2~P1E line
            const rMidX2 = (arc.cx + pStart2.x) / 2;
            const rMidY2 = (-arc.cy + (-pStart2.y)) / 2;
            const rDx2 = pStart2.x - arc.cx;
            const rDy2 = (-pStart2.y) - (-arc.cy);
            let rAngle2 = Math.atan2(rDy2, rDx2) * 180 / Math.PI;
            if (rAngle2 > 90) rAngle2 -= 180;
            if (rAngle2 < -90) rAngle2 += 180;
            const rLen2 = Math.sqrt(rDx2 * rDx2 + rDy2 * rDy2);
            const rOffDistSize2 = (index < 3) ? -1.5 * scale : 1.5 * scale; // Above for R1-3, Below for R4-6
            const rPerpX2 = -rDy2 / rLen2 * rOffDistSize2;
            const rPerpY2 = rDx2 / rLen2 * rOffDistSize2;

            const rLabel2 = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            rLabel2.setAttribute('x', rMidX2 + rPerpX2);
            rLabel2.setAttribute('y', rMidY2 + rPerpY2);
            rLabel2.setAttribute('font-size', (2.2 * scale).toFixed(4));
            rLabel2.setAttribute('fill', arc.color);
            rLabel2.setAttribute('text-anchor', 'middle');
            rLabel2.setAttribute('dominant-baseline', 'middle');
            rLabel2.setAttribute('transform', `rotate(${rAngle2.toFixed(1)}, ${(rMidX2 + rPerpX2).toFixed(4)}, ${(rMidY2 + rPerpY2).toFixed(4)})`);
            rLabel2.style.pointerEvents = 'none';
            rLabel2.textContent = `R2=${arc.r.toFixed(4)}`;
            overlayGroup.appendChild(rLabel2);
        }
    }
}

// ------------------------------------------------------------
// Interaction
// ------------------------------------------------------------

function drawArcDiffFill(container, arc1, arc2, isMirror = false) {
    const p1S = getPointOnCircle(arc1.cx, arc1.cy, arc1.r, arc1.startAngle);
    const p1E = getPointOnCircle(arc1.cx, arc1.cy, arc1.r, arc1.endAngle);
    const p2S = getPointOnCircle(arc2.cx, arc2.cy, arc2.r, arc2.startAngle);
    const p2E = getPointOnCircle(arc2.cx, arc2.cy, arc2.r, arc2.endAngle);

    const sweepFlag = isMirror ? "1" : "0";
    const reverseSweepFlag = isMirror ? "0" : "1";

    const arc1Large = Math.abs(arc1.endAngle - arc1.startAngle) > 180 ? "1" : "0";
    const arc2Large = Math.abs(arc2.endAngle - arc2.startAngle) > 180 ? "1" : "0";

    const pathData = [
        "M", p1S.x.toFixed(4), (-p1S.y).toFixed(4),
        "A", arc1.r.toFixed(4), arc1.r.toFixed(4), 0, arc1Large, sweepFlag, p1E.x.toFixed(4), (-p1E.y).toFixed(4),
        "L", p2E.x.toFixed(4), (-p2E.y).toFixed(4),
        "A", arc2.r.toFixed(4), arc2.r.toFixed(4), 0, arc2Large, reverseSweepFlag, p2S.x.toFixed(4), (-p2S.y).toFixed(4),
        "Z"
    ].join(" ");

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('fill', 'lightyellow');
    path.setAttribute('fill-opacity', '0.8');
    path.setAttribute('stroke', 'none');
    path.setAttribute('style', 'pointer-events: none;');
    container.appendChild(path);
}

function bindDrag(el, index, type) {
    el.addEventListener('mousedown', (e) => startDrag(e, index, type));
    el.addEventListener('touchstart', (e) => startDrag(e, index, type));
}

function startDrag(e, index, type, pIdx = null) {
    e.preventDefault();
    e.stopPropagation();
    activeDragIndex = index;
    dragType = type;
    activePointIndex = pIdx;

    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', endDrag);
    document.addEventListener('touchmove', onDrag);
    document.addEventListener('touchend', endDrag);
}

function onDrag(e) {
    if (activeDragIndex === null) return;
    e.preventDefault();

    const canvas = document.getElementById('canvas');
    const CTM = canvas.getScreenCTM();
    let cx, cy;
    if (e.touches) {
        cx = e.touches[0].clientX;
        cy = e.touches[0].clientY;
    } else {
        cx = e.clientX;
        cy = e.clientY;
    }

    const svgX = (cx - CTM.e) / CTM.a;
    const svgY = (cy - CTM.f) / CTM.d;
    const mx = svgX;
    const my = -svgY;

    if (dragType === 'envelopePoint') {
        const env = envelopes[activeDragIndex];
        const p = env.points[activePointIndex];
        p.x = parseFloat(mx.toFixed(4));
        p.y = parseFloat(my.toFixed(4));

        // Update UI
        renderEnvelopeControls();
        drawSystem();
        return;
    }

    const arc = arcs[activeDragIndex];

    if (activeDragIndex === 0 || activeDragIndex === 1 || activeDragIndex === 2) {
        if (dragType === 'center') {
            if (activeDragIndex === 0 || activeDragIndex === 2) { // Arc 1LI, 3L: Y-Axis Constrained
                arc.cx = 0;
                arc.cy = my;
            } else if (activeDragIndex === 1) { // Arc 2LI: Constrained to X < 0
                arc.cx = Math.min(-0.0001, mx);
                arc.cy = my;
            }
            updateConnectorGeometry();

        } else if (dragType === 'startAngle' || dragType === 'endAngle') {
            // Check constraints
            const isArc1End = (activeDragIndex === 0 && dragType === 'endAngle'); // P1E
            const isArc3Start = (activeDragIndex === 2 && dragType === 'startAngle'); // P2S (Arc 3 Start)
            //const isArc3End = (activeDragIndex === 2 && dragType === 'endAngle'); // P3E

            // P1S Constraint (Axis)
            const isP1S = (activeDragIndex === 0 && dragType === 'startAngle');

            let targetX = mx, targetY = my;

            // Constraints
            if (isP1S) { // P1S.y > P1.y (SVG y < cy)
                targetX = 0;
                if (targetY <= arcs[0].cy) targetY = arcs[0].cy + 0.001;
            }
            //if (isArc3End) { // P3E.y < P2.y (SVG y > p2.cy)
            //    targetX = 0;
            //    if (targetY >= arcs[1].cy) targetY = arcs[1].cy - 0.001;
            //}

            // Calculation
            const rawAngle = Math.atan2(targetY - arc.cy, targetX - arc.cx) * 180 / Math.PI;
            let r = Math.sqrt(Math.pow(targetX - arc.cx, 2) + Math.pow(targetY - arc.cy, 2));

            // New Constraint: P3S.y < P1E.y (P3S Visually Above P1E -> SVG y < p1e.y)
            if (isArc3Start) {
                const p1e_pt = getPointOnCircle(arcs[0].cx, arcs[0].cy, arcs[0].r, arcs[0].endAngle);
                // Constraint might need adjustment due to 180 rotation
            }

            if (isArc1End) {
                // P1E: Adjust Radius and Angle
                arc.r = r;
                let diffE = rawAngle - arc.startAngle;
                while (diffE < 0) diffE += 360;
                while (diffE >= 360) diffE -= 360;
                if (diffE >= 270 - arc.startAngle) diffE = 270 - arc.startAngle;
                if (diffE < 0) diffE = 0;
                arc.endAngle = arc.startAngle + diffE;
            }
        }
    } else if (activeDragIndex === 3 || activeDragIndex === 4 || activeDragIndex === 5) {
        // Arc 4/5/6 drag handling (mirrors Arc 1/2/3)
        if (dragType === 'center') {
            if (activeDragIndex === 3 || activeDragIndex === 5) { // P4, P6: Y-Axis Constrained
                arc.cx = 0;
                arc.cy = my;
            } else if (activeDragIndex === 4) { // P5: Constrained to X < 0
                arc.cx = Math.min(-0.0001, mx);
                arc.cy = my;
            }
            updateConnectorGeometry();

        } else if (dragType === 'endAngle' && activeDragIndex === 3) {
            // P4E: Adjust Arc 4 Radius and Angle
            let rawAngle4 = Math.atan2(my - arc.cy, mx - arc.cx) * 180 / Math.PI;
            let r4 = Math.sqrt(Math.pow(mx - arc.cx, 2) + Math.pow(my - arc.cy, 2));
            arc.r = r4;
            let diffE4 = rawAngle4 - arc.startAngle;
            while (diffE4 < 0) diffE4 += 360;
            while (diffE4 >= 360) diffE4 -= 360;
            if (diffE4 >= 270 - arc.startAngle) diffE4 = 270 - arc.startAngle;
            if (diffE4 < 0) diffE4 = 0;
            arc.endAngle = arc.startAngle + diffE4;
            updateConnectorGeometry();
        }
    }

    updateConnectorGeometry();
    drawSystem();
    // checkClearance(); // Don't alert during drag, only at the end
}

function isAngleInRange(angle, start, end) {
    // Normalize all to [0, 360)
    angle = (angle % 360 + 360) % 360;
    start = (start % 360 + 360) % 360;
    end = (end % 360 + 360) % 360;

    if (start <= end) {
        return angle >= start && angle <= end;
    } else {
        // Range spans across 0/360
        return angle >= start || angle <= end;
    }
}

function checkClearance() {
    const violations = [];
    violatedPointIndices = []; // Reset violations: will be an array of arrays [envIdx][pIdx]

    envelopes.forEach((env, envIdx) => {
        violatedPointIndices[envIdx] = [];
        env.points.forEach((p, pIdx) => {
            // Use symmetry: mirror right-side points to the left side
            const absX = Math.abs(p.x);
            const testX = -absX; // Map to left side coordinates
            const testY = p.y;

            const thetaOrigin = (Math.atan2(testY, testX) * 180 / Math.PI + 360) % 360;

            let selectedArcIndex = 0; // Default to Arc 1

            // Deterministic sector selection based on angle from origin
            // Left side sectors: 90 -> 270 (approx)
            // Re-calculate boundaries based on current geometry
            const j12 = getPointOnCircle(arcs[0].cx, arcs[0].cy, arcs[0].r, arcs[0].endAngle);
            const j23 = getPointOnCircle(arcs[1].cx, arcs[1].cy, arcs[1].r, arcs[1].endAngle);
            const norm12 = (Math.atan2(j12.y, j12.x) * 180 / Math.PI + 360) % 360;
            const norm23 = (Math.atan2(j23.y, j23.x) * 180 / Math.PI + 360) % 360;

            if (thetaOrigin >= 90 && thetaOrigin < norm12) {
                selectedArcIndex = 0; // Arc 1
            } else if (thetaOrigin >= norm12 && thetaOrigin < norm23) {
                selectedArcIndex = 1; // Arc 2
            } else {
                selectedArcIndex = 2; // Arc 3
            }

            const arc = arcs[selectedArcIndex];
            const dx = testX - arc.cx;
            const dy = testY - arc.cy;
            const dist = Math.sqrt(dx * dx + dy * dy);

            // Check if point is outside the tunnel arc
            if (dist > arc.r + 0.001) { // 1mm tolerance
                const pName = p.name || `點${pIdx + 1}`;
                violations.push(`[${env.name}] ${pName} (${p.x.toFixed(4)}, ${p.y.toFixed(4)})`);
                violatedPointIndices[envIdx].push(pIdx);
            }
        });
    });

    if (violations.length > 0) {
        alert("⚠️ 淨空包絡線超出範圍！請檢查下列點位：\n" + violations.join("\n"));
    }

    drawSystem(); // Refresh to show/hide highlights
}

function endDrag() {
    activeDragIndex = null;
    dragType = null;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', endDrag);
    document.removeEventListener('touchmove', onDrag);
    document.removeEventListener('touchend', endDrag);

    // Check clearance when user finishes adjustment
    checkClearance();
}


// ------------------------------------------------------------
// View Control
// ------------------------------------------------------------

function autoFitViewBox() {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    // Consider both left and right (mirrored) arcs
    arcs.forEach(a => {
        // Sample points on the arc to get bounding box
        const samples = [a.startAngle, a.endAngle, (a.startAngle + a.endAngle) / 2];
        samples.forEach(ang => {
            const pL = getPointOnCircle(a.cx, a.cy, a.r, ang);
            const pR = getPointOnCircle(-a.cx, a.cy, a.r, 180 - ang);

            minX = Math.min(minX, pL.x, pR.x);
            maxX = Math.max(maxX, pL.x, pR.x);
            minY = Math.min(minY, pL.y, pR.y);
            maxY = Math.max(maxY, pL.y, pR.y);
        });

        // Also check extreme points (top, bottom, left, right) if they are within the arc range
        [0, 90, 180, 270].forEach(ang => {
            if (isAngleInRange(ang, a.startAngle, a.endAngle)) {
                const pL = getPointOnCircle(a.cx, a.cy, a.r, ang);
                minX = Math.min(minX, pL.x);
                maxX = Math.max(maxX, pL.x);
                minY = Math.min(minY, pL.y);
                maxY = Math.max(maxY, pL.y);
            }
            const mirrAng = (180 - ang + 360) % 360;
            if (isAngleInRange(mirrAng, 180 - a.endAngle, 180 - a.startAngle)) {
                const pR = getPointOnCircle(-a.cx, a.cy, a.r, mirrAng);
                minX = Math.min(minX, pR.x);
                maxX = Math.max(maxX, pR.x);
                minY = Math.min(minY, pR.y);
                maxY = Math.max(maxY, pR.y);
            }
        });
    });

    envelopes.forEach(env => {
        env.points.forEach(p => {
            minX = Math.min(minX, p.x);
            maxX = Math.max(maxX, p.x);
            minY = Math.min(minY, p.y);
            maxY = Math.max(maxY, p.y);
        });
    });

    if (minX === Infinity) return;

    const w = maxX - minX;
    const h = maxY - minY;

    // Better padding: 10% of the larger dimension
    const pad = Math.max(w, h, 2) * 0.15;

    viewBoxState.w = w + pad * 2;
    viewBoxState.h = h + pad * 2;
    viewBoxState.x = minX - pad;
    // Note: SVG Y is inverted in our coordinate system logic (mx, my = svgX, -svgY)
    // So if minY/maxY are the "true" world coordinates, 
    // the SVG coordinates are -maxY to -minY.
    viewBoxState.y = -(maxY + pad);

    updateCanvasViewBox();
}

function updateCanvasViewBox() {
    const canvas = document.getElementById('canvas');
    if (canvas) {
        canvas.setAttribute('viewBox', `${viewBoxState.x} ${viewBoxState.y} ${viewBoxState.w} ${viewBoxState.h}`);
        drawSystem(); // Redraw everything to update scales
        drawAxisWithTicks();
    }
}

function bindZoomPanEvents() {
    const container = document.getElementById('svgContainer');
    const canvas = document.getElementById('canvas');
    if (!container || !canvas) return;

    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        const zoomRate = 1.1;
        const zoomIn = e.deltaY < 0;

        if (zoomIn) {
            viewBoxState.w /= zoomRate;
            viewBoxState.h /= zoomRate;
            viewBoxState.x += (viewBoxState.w * (zoomRate - 1)) / 2;
            viewBoxState.y += (viewBoxState.h * (zoomRate - 1)) / 2;
        } else {
            viewBoxState.w *= zoomRate;
            viewBoxState.h *= zoomRate;
            viewBoxState.x -= (viewBoxState.w * (1 - 1 / zoomRate)) / 2;
            viewBoxState.y -= (viewBoxState.h * (1 - 1 / zoomRate)) / 2;
        }
        updateCanvasViewBox();
    });

    canvas.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'svg' || e.target.id === 'circlesGroup' || e.target.id === 'axisGroup') {
            isPanning = true;
            startPan = { x: e.clientX, y: e.clientY };
            canvas.style.cursor = 'grabbing';
        }
    });

    window.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        e.preventDefault();

        const dx = e.clientX - startPan.x;
        const dy = e.clientY - startPan.y;

        const rect = canvas.getBoundingClientRect();
        const scaleX = viewBoxState.w / rect.width;
        const scaleY = viewBoxState.h / rect.height;

        viewBoxState.x -= dx * scaleX;
        viewBoxState.y -= dy * scaleY;

        startPan = { x: e.clientX, y: e.clientY };
        updateCanvasViewBox();
    });

    window.addEventListener('mouseup', () => {
        isPanning = false;
        canvas.style.cursor = 'default';
    });
}

// ------------------------------------------------------------
// Utilities (Area Calc, etc.)
// ------------------------------------------------------------

function calculateTriangleArea(p1, p2, p3) {
    // Area using coordinates: 0.5 * |x1(y2-y3) + x2(y3-y1) + x3(y1-y2)|
    return Math.abs(0.5 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y)));
}


function calculateTotalArea(arc1, arc2, arc3) {

    // Formula provided: 2 * (Arc1扇形 + Arc2扇形 + Arc3扇形 - (P1,P2,P3)三角形面積)
    // Sector Area = 0.5 * r^2 * theta (in radians)
    const sectorArea1 = 0.5 * arc1.r * arc1.r * (Math.abs(arc1.endAngle - arc1.startAngle) * Math.PI / 180);
    const sectorArea2 = 0.5 * arc2.r * arc2.r * (Math.abs(arc2.endAngle - arc2.startAngle) * Math.PI / 180);
    const sectorArea3 = 0.5 * arc3.r * arc3.r * (Math.abs(arc3.endAngle - arc3.startAngle) * Math.PI / 180);

    const triangleArea = calculateTriangleArea(
        { x: arc1.cx, y: arc1.cy },
        { x: arc2.cx, y: arc2.cy },
        { x: arc3.cx, y: arc3.cy }
    );

    const halfArea = sectorArea1 + sectorArea2 + sectorArea3 - triangleArea;

    // Final area is doubled for symmetry
    return Math.abs(halfArea * 2);
}
function calculateExcavationArea(arc1, arc2, arc3, t) {
    // 計算單個圓弧長度的輔助函數
    const getArcLength = (arc) => {
        // 角度轉弧度: theta = degree * (PI / 180)
        const theta = Math.abs(arc.endAngle - arc.startAngle) * Math.PI / 180;
        return arc.r * theta;
    };

    const L1 = getArcLength(arc1);
    const L2 = getArcLength(arc2);
    const L3 = getArcLength(arc3);
    const totalArea = 2 * (L1 + L2 + L3) * t;

    return totalArea;
}

function describeArc(x, y, radius, startAngle, endAngle, sweepFlag = "0") {
    const start = {
        x: x + radius * Math.cos(startAngle * Math.PI / 180),
        y: y - radius * Math.sin(startAngle * Math.PI / 180)
    };
    const end = {
        x: x + radius * Math.cos(endAngle * Math.PI / 180),
        y: y - radius * Math.sin(endAngle * Math.PI / 180)
    };

    let angleDiff = Math.abs(endAngle - startAngle);
    // largeArcFlag for sweep logic: if diff > 180, it's the large arc
    const largeArcFlag = angleDiff > 180 ? "1" : "0";

    return [
        "M", start.x, start.y,
        "A", radius, radius, 0, largeArcFlag, sweepFlag, end.x, end.y
    ].join(" ");
}

function updateInfoPanel() {
    const resultsContainer = document.getElementById('resultsContainer');
    const areaResultsContainer = document.getElementById('areaResultsContainer');
    if (!resultsContainer || !areaResultsContainer) return;

    const outerArea = calculateTotalArea(arcs[3], arcs[4], arcs[5]);
    const innerArea = calculateTotalArea(arcs[0], arcs[1], arcs[2]);
    const liningArea = outerArea - innerArea;
    const t_val = Math.max(0, parseFloat(document.getElementById('excavationThickness')?.value || 0.2));
    const excavationArea = outerArea + calculateExcavationArea(arcs[3], arcs[4], arcs[5], t_val);

    const allArcs = getAllArcs();

    // 1. Area Results HTML
    let areaHtml = `
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #fae1e1ff; border: 2px solid #f37171ff; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; white-space: nowrap;">
            <span style="color: #ca2222ff; font-weight: bold; font-size: 0.95rem;">預估開挖面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #ca2222ff; font-family: 'Courier New', monospace;"> ${excavationArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #ffddaaff; border: 2px solid #f3a566ff; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; white-space: nowrap;">
            <span style="color: #fd7200ff; font-weight: bold; font-size: 0.95rem;">襯砌外廓面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #fd7200ff; font-family: 'Courier New', monospace;"> ${outerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e8f5e9; border: 2px solid #68ac6dff; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; white-space: nowrap;">
            <span style="color: #1b5e20; font-weight: bold; font-size: 0.95rem;">襯砌內廓面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #1b5e20; font-family: 'Courier New', monospace;"> ${innerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; white-space: nowrap;">
            <span style="color: #1565c0; font-weight: bold; font-size: 0.95rem;">襯砌斷面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #0d47a1; font-family: 'Courier New', monospace;">${liningArea.toFixed(2)} m²</span>
        </div>
    </div>
    `;
    areaResultsContainer.innerHTML = areaHtml;

    // 2. Arc Results HTML
    let arcHtml = `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">`;
    const displayOrder = [0, 6, 3, 9, 1, 7, 4, 10, 2, 8, 5, 11];
    displayOrder.forEach((idx) => {
        const a = allArcs[idx];
        if (!a) return;

        arcHtml += `
        <div class="result-item" style="border-left: 6px solid ${a.color}; margin-bottom: 0px; padding: 12px; background: #f8f9fa; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h4 style="margin:0 0 8px 0; color: ${a.color}; border-bottom: 1px solid #eee; padding-bottom: 4px;">圓弧 ${a.name}</h4>
            <div style="font-size: 0.80em; line-height: 1.6;">
                <div><strong>圓弧圓心 P:</strong> (${a.cx.toFixed(4)}, ${a.cy.toFixed(4)})</div>
                <div><strong>圓弧半徑 R:</strong> ${a.r.toFixed(4)}</div>
                <div><strong>起始弧角 θs:</strong> ${toDMS(a.startAngle - 90)}</div> 
                <div><strong>結束弧角 θe:</strong> ${toDMS(a.endAngle - 90)}</div>                
                <div><strong>圓弧長度 S:</strong> ${a.length.toFixed(4)}</div>
                <div><strong>圓弧起點 Ps:</strong> (${a.startX.toFixed(4)}, ${a.startY.toFixed(4)})</div>
                <div><strong>圓弧終點 Pe:</strong> (${a.endX.toFixed(4)}, ${a.endY.toFixed(4)})</div>
            </div>
        </div>
        `;
    });
    arcHtml += `</div>`;

    resultsContainer.innerHTML = arcHtml;
    document.getElementById('resultsCard').style.display = 'block';
}

function calculateTickInterval(range) {
    const rawInterval = range / 8;
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawInterval)));
    const normalized = rawInterval / magnitude;
    let interval;
    if (normalized <= 1.5) interval = 1;
    else if (normalized <= 3) interval = 2;
    else if (normalized <= 7) interval = 5;
    else interval = 10;
    return interval * magnitude;
}

function drawAxisWithTicks() {
    const canvas = document.getElementById('canvas');
    let axisGroup = document.getElementById('axisGroup');
    if (axisGroup) axisGroup.remove();

    axisGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    axisGroup.setAttribute('id', 'axisGroup');
    canvas.insertBefore(axisGroup, canvas.firstChild);

    const vb = viewBoxState;
    const minX = vb.x, maxX = vb.x + vb.w;
    const minY = vb.y, maxY = vb.y + vb.h; // SVG Y

    const realMinY = -maxY;
    const realMaxY = -minY;

    // Use Shared Scale
    const scale = getVisualScale();

    // Grid/Tick styling
    // Previous fixed was based on min(w,h) * 0.015. 
    // If min(w,h) is 100, that's 1.5.
    // Our scale is normalized to 1 unit at 100.
    // So 1.5 * scale matches previous logic.
    const fontSize = (1.2 * scale).toFixed(3);
    const majorTickLen = 1.0 * scale;
    const minorTickLen = majorTickLen * 0.6;
    const strokeWidth = (0.3 * scale).toFixed(3);

    // Fixed Intervals
    const majorInterval = 5;
    const minorInterval = 1;

    // X Axis
    const xStart = Math.ceil(minX / minorInterval) * minorInterval;

    for (let x = xStart; x <= maxX; x += minorInterval) {
        // Use epsilon for float comparison
        const isMajor = Math.abs(x % majorInterval) < 0.0001;
        const tickLen = isMajor ? majorTickLen : minorTickLen;

        const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick.setAttribute('x1', x);
        tick.setAttribute('y1', -tickLen);
        tick.setAttribute('x2', x);
        tick.setAttribute('y2', tickLen);
        tick.setAttribute('stroke', '#bbb');
        tick.setAttribute('stroke-width', strokeWidth);
        axisGroup.appendChild(tick);

        if (isMajor && Math.abs(x) > 0.0001) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', majorTickLen + parseFloat(fontSize));
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', fontSize);
            text.setAttribute('fill', '#999');
            text.textContent = parseFloat(x.toFixed(2));
            axisGroup.appendChild(text);
        }
    }

    // Y Axis
    const yStart = Math.ceil(realMinY / minorInterval) * minorInterval;

    for (let y = yStart; y <= realMaxY; y += minorInterval) {
        const isMajor = Math.abs(y % majorInterval) < 0.0001;
        const tickLen = isMajor ? majorTickLen : minorTickLen;

        const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick.setAttribute('x1', -tickLen);
        tick.setAttribute('y1', -y);
        tick.setAttribute('x2', tickLen);
        tick.setAttribute('y2', -y);
        tick.setAttribute('stroke', '#bbb');
        tick.setAttribute('stroke-width', strokeWidth);
        axisGroup.appendChild(tick);

        if (isMajor && Math.abs(y) > 0.0001) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', -majorTickLen - (parseFloat(fontSize) * 0.5));
            text.setAttribute('y', -y + (parseFloat(fontSize) * 0.4));
            text.setAttribute('text-anchor', 'end');
            text.setAttribute('font-size', fontSize);
            text.setAttribute('fill', '#999');
            text.textContent = parseFloat(y.toFixed(2));
            axisGroup.appendChild(text);
        }
    }

    // Main Axes Lines
    const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    xAxis.setAttribute('x1', minX);
    xAxis.setAttribute('y1', 0);
    xAxis.setAttribute('x2', maxX);
    xAxis.setAttribute('y2', 0);
    xAxis.setAttribute('stroke', '#999');
    xAxis.setAttribute('stroke-width', (0.2 * scale).toFixed(3)); // Thinner axis
    axisGroup.appendChild(xAxis);

    const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    yAxis.setAttribute('x1', 0);
    yAxis.setAttribute('y1', minY);
    yAxis.setAttribute('x2', 0);
    yAxis.setAttribute('y2', maxY);
    yAxis.setAttribute('stroke', '#999');
    yAxis.setAttribute('stroke-width', (0.2 * scale).toFixed(3)); // Thinner axis
    axisGroup.appendChild(yAxis);
}

// ------------------------------------------------------------
// Data Export (DXF & CSV)
// ------------------------------------------------------------

function getAllArcs() {
    const allArcs = [];

    // -------------------------
    // LEFT SIDE
    // -------------------------
    arcs.forEach((arc, i) => {
        const no = i + 1;   // 1~6
        const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
        const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);
        const theta = (arc.endAngle - arc.startAngle) * Math.PI / 180;

        allArcs.push({
            name: `Arc ${no}L`,
            cx: arc.cx, cy: arc.cy, r: arc.r,
            startAngle: arc.startAngle, endAngle: arc.endAngle,
            length: Math.abs(arc.r * theta),
            startX: pStart.x, startY: pStart.y,
            endX: pEnd.x, endY: pEnd.y,
            color: arc.color
        });
    });

    // -------------------------
    // RIGHT SIDE (MIRROR)
    // -------------------------
    arcs.forEach((arc, i) => {
        const no = i + 1;   // 1~6
        const startA = 180 - arc.startAngle;
        const endA = 180 - arc.endAngle;

        const pStart = getPointOnCircle(-arc.cx, arc.cy, arc.r, startA);
        const pEnd = getPointOnCircle(-arc.cx, arc.cy, arc.r, endA);
        const theta = (endA - startA) * Math.PI / 180;

        allArcs.push({
            name: `Arc ${no}R`,
            cx: -arc.cx, cy: arc.cy, r: arc.r,
            startAngle: startA, endAngle: endA,
            length: Math.abs(arc.r * theta),
            startX: pStart.x, startY: pStart.y,
            endX: pEnd.x, endY: pEnd.y,
            color: arc.color
        });
    });

    return allArcs;
}

function saveAsDXF() {

    if (!arcs || arcs.length === 0) {
        alert("No geometry to export.");
        return;
    }

    let dxf = "";

    const fmt = (num) => {
        const n = parseFloat(num);
        return isNaN(n) ? "0.0000" : n.toFixed(4);
    };

    // =====================================================
    // 1. HEADER (R12)
    // =====================================================
    dxf += "0\nSECTION\n2\nHEADER\n";
    dxf += "9\n$ACADVER\n1\nAC1009\n";
    dxf += "0\nENDSEC\n";

    // =====================================================
    // 2. TABLES
    // =====================================================
    dxf += "0\nSECTION\n2\nTABLES\n";

    // ---------- LTYPE ----------
    dxf += "0\nTABLE\n2\nLTYPE\n70\n4\n";
    dxf += "0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid\n72\n65\n73\n0\n40\n0.0\n";
    dxf += "0\nLTYPE\n2\nDASHED\n70\n0\n3\nDashed\n72\n65\n73\n2\n40\n0.5\n49\n0.3\n49\n-0.2\n";
    dxf += "0\nLTYPE\n2\nDASHDOT\n70\n0\n3\nDashDot\n72\n65\n73\n4\n40\n0.6\n49\n0.3\n49\n-0.1\n49\n0.05\n49\n-0.1\n";
    dxf += "0\nLTYPE\n2\nCENTER\n70\n0\n3\nCenter\n72\n65\n73\n4\n40\n2.0\n49\n1.25\n49\n-0.25\n49\n0.25\n49\n-0.25\n";
    dxf += "0\nENDTAB\n";

    // ---------- LAYER ----------
    dxf += "0\nTABLE\n2\nLAYER\n70\n5\n";

    const layers = [
        { name: "01_Tunnel", color: 7, ltype: "CONTINUOUS" },
        { name: "02_Radial", color: 8, ltype: "DASHED" },
        { name: "03_Clearance", color: 4, ltype: "DASHDOT" },
        { name: "04_Center", color: 1, ltype: "CENTER" },
        { name: "05_Text", color: 7, ltype: "CONTINUOUS" }
    ];

    layers.forEach(l => {
        dxf += `0\nLAYER\n2\n${l.name}\n70\n0\n62\n${l.color}\n6\n${l.ltype}\n`;
    });

    dxf += "0\nENDTAB\n";

    // ---------- STYLE ----------
    dxf += "0\nTABLE\n2\nSTYLE\n70\n1\n";
    dxf += "0\nSTYLE\n2\nROMANS\n70\n0\n40\n0.0\n41\n1.0\n50\n0.0\n71\n0\n42\n0.2\n3\nromans.shx\n4\n\n";
    dxf += "0\nENDTAB\n0\nENDSEC\n";

    // =====================================================
    // 3. ENTITIES
    // =====================================================
    dxf += "0\nSECTION\n2\nENTITIES\n";

    const textHeight = arcs[0].r * 0.05;
    const clRange = 1.5 * arcs[0].r;

    arcs.forEach((a, i) => {

        if (a.startAngle === a.endAngle) return;

        const no = i + 1;

        // ---------------------------
        // ARC 右側
        // ---------------------------
        dxf += "0\nARC\n8\n01_Tunnel\n";
        dxf += `10\n${fmt(a.cx)}\n20\n${fmt(a.cy)}\n30\n0.0\n`;
        dxf += `40\n${fmt(a.r)}\n`;
        dxf += `50\n${fmt(a.startAngle)}\n`;
        dxf += `51\n${fmt(a.endAngle)}\n`;

        // ---------------------------
        // ARC 鏡像
        // ---------------------------
        const mirrorStart = 180 - a.endAngle;
        const mirrorEnd = 180 - a.startAngle;

        dxf += "0\nARC\n8\n01_Tunnel\n";
        dxf += `10\n${fmt(-a.cx)}\n20\n${fmt(a.cy)}\n30\n0.0\n`;
        dxf += `40\n${fmt(a.r)}\n`;
        dxf += `50\n${fmt(mirrorStart)}\n`;
        dxf += `51\n${fmt(mirrorEnd)}\n`;

        // ---------------------------
        // 徑向線
        // ---------------------------
        const pts = [
            getPointOnCircle(a.cx, a.cy, a.r, a.startAngle),
            getPointOnCircle(a.cx, a.cy, a.r, a.endAngle)
        ];

        pts.forEach(p => {
            dxf += "0\nLINE\n8\n02_Radial\n";
            dxf += `10\n${fmt(a.cx)}\n20\n${fmt(a.cy)}\n30\n0.0\n`;
            dxf += `11\n${fmt(p.x)}\n21\n${fmt(p.y)}\n31\n0.0\n`;
        });

        // ---------------------------
        // 文字
        // ---------------------------
        const normalizeRotation = (angle) => {
            let a = angle % 360;
            if (a < 0) a += 360;
            if (a > 90 && a < 270) return (a + 180) % 360;
            return a;
        };

        // 圓中心點標記 (Pi)
        dxf += "0\nTEXT\n8\n05_Text\n7\nROMANS\n";
        dxf += `10\n${fmt(a.cx)}\n20\n${fmt(a.cy)}\n30\n0.0\n`;
        dxf += `40\n${fmt(textHeight)}\n`;
        dxf += `1\nP${no}\n`;

        // 1. 半徑標示於控制線(徑向線)中心外側 (用 startAngle 側的徑向線, 約 0.7 * R)
        const pStart = getPointOnCircle(a.cx, a.cy, a.r, a.startAngle);
        const radiusLabelFactor = 0.7;
        const midRX = a.cx + (pStart.x - a.cx) * radiusLabelFactor;
        const midRY = a.cy + (pStart.y - a.cy) * radiusLabelFactor;
        const rotRadius = normalizeRotation(a.startAngle);

        dxf += "0\nTEXT\n8\n05_Text\n7\nROMANS\n";
        dxf += `10\n${fmt(midRX)}\n20\n${fmt(midRY)}\n30\n0.0\n`;
        dxf += `11\n${fmt(midRX)}\n21\n${fmt(midRY)}\n31\n0.0\n`;
        dxf += `40\n${fmt(textHeight)}\n`;
        dxf += `50\n${fmt(rotRadius)}\n`;
        dxf += `72\n1\n73\n2\n`; // Justify: Center, Middle
        dxf += `1\nR${no}=${parseFloat(a.r.toFixed(4))}\n`;

        // 2. 弧角標示於圓弧外側中心 (增加 offset 以免重疊)
        const midAngle = (a.startAngle + a.endAngle) / 2;
        const offset = textHeight * 2.5; // 往外移動更多
        const midArcPos = getPointOnCircle(a.cx, a.cy, a.r + offset, midAngle);
        const rotTheta = normalizeRotation(midAngle + 90);

        const arcAngle = Math.abs(a.endAngle - a.startAngle);
        dxf += "0\nTEXT\n8\n05_Text\n7\nROMANS\n";
        dxf += `10\n${fmt(midArcPos.x)}\n20\n${fmt(midArcPos.y)}\n30\n0.0\n`;
        dxf += `11\n${fmt(midArcPos.x)}\n21\n${fmt(midArcPos.y)}\n31\n0.0\n`;
        dxf += `40\n${fmt(textHeight)}\n`;
        dxf += `50\n${fmt(rotTheta)}\n`;
        dxf += `72\n1\n73\n2\n`; // Justify: Center, Middle
        dxf += `1\nθ${no}=${toDMS(arcAngle)}\n`;
    });

    // ---------------------------
    // 中心線
    // ---------------------------
    dxf += "0\nLINE\n8\n04_Center\n";
    dxf += `10\n${fmt(-clRange)}\n20\n0\n30\n0\n`;
    dxf += `11\n${fmt(clRange)}\n21\n0\n31\n0\n`;

    dxf += "0\nLINE\n8\n04_Center\n";
    dxf += `10\n0\n20\n${fmt(-clRange)}\n30\n0\n`;
    dxf += `11\n0\n21\n${fmt(clRange)}\n31\n0\n`;

    // ---------------------------
    // 淨空包絡線 (R12 POLYLINE)
    // ---------------------------
    if (typeof envelopes !== 'undefined') {
        envelopes.forEach(env => {
            // 1. 過濾無效點 (0,0)
            let pts = env.points.filter(pt => pt.x !== 0 || pt.y !== 0);

            if (pts.length >= 2) {
                const first = pts[0];
                const last = pts[pts.length - 1];

                // 2. 判斷終點是否等於起點 (考慮微小浮點數誤差)
                const epsilon = 0.0001;
                const isClosedData = Math.abs(first.x - last.x) < epsilon &&
                    Math.abs(first.y - last.y) < epsilon;

                // 3. 如果資料已手動閉合，則去掉最後一點，避免與起點重合
                //    如果資料未閉合，則使用原始點位，依靠 70\n1 旗標自動連回第一點
                const polyPts = isClosedData ? pts.slice(0, -1) : pts;

                // 70\n1 代表閉合屬性，AutoCAD 會自動連接最後頂點與起始頂點
                dxf += "0\nPOLYLINE\n8\n03_Clearance\n66\n1\n70\n1\n";

                polyPts.forEach(pt => {
                    dxf += "0\nVERTEX\n8\n03_Clearance\n";
                    dxf += `10\n${fmt(pt.x)}\n20\n${fmt(pt.y)}\n30\n0.0\n`;
                });

                dxf += "0\nSEQEND\n";
            }
        });
    }

    dxf += "0\nENDSEC\n0\nEOF\n";

    // =====================================================
    // 下載
    // =====================================================
    const tunnelName = document.getElementById('tunnelName')?.value || 'Tunnel_Design';

    const blob = new Blob([dxf], { type: 'application/dxf' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${tunnelName}.dxf`;
    link.click();
}

function openProject() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';

    input.onchange = e => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = event => {
            const text = event.target.result;
            loadProjectFromText(text);
        };

        reader.readAsText(file);
    };

    input.click();
}

function loadProjectFromText(text) {
    try {
        const data = JSON.parse(text);

        if (data.projectNumber !== undefined) document.getElementById('projectNumber').value = data.projectNumber;
        if (data.projectName !== undefined) document.getElementById('projectName').value = data.projectName;
        if (data.tunnelName !== undefined) document.getElementById('tunnelName').value = data.tunnelName;

        if (data.arcs) {
            arcs = data.arcs;
        }

        if (data.envelopes) {
            envelopes = data.envelopes;
        }

        renderEnvelopeControls();
        updateConnectorGeometry();
        drawSystem();
        autoFitViewBox();
        updateInfoPanel();

        alert('專案載入成功！');
    } catch (err) {
        console.error('Error parsing project file:', err);
        // Fallback for old simple format if needed
        if (text.includes('"projectNumber"')) {
            try {
                // Try to parse the old pseudo-JSON format if it exists
                const pseudoJson = '{' + text + '}';
                const data = JSON.parse(pseudoJson);
                if (data.projectNumber) document.getElementById('projectNumber').value = data.projectNumber;
                if (data.projectName) document.getElementById('projectName').value = data.projectName;
                if (data.tunnelName) document.getElementById('tunnelName').value = data.tunnelName;
                alert('專案載入成功 (舊格式)！');
            } catch (e) {
                alert('無法解析專案檔案。');
            }
        } else {
            alert('無法解析專案檔案。');
        }
    }
}

async function saveProject() {
    const projectNumber = document.getElementById('projectNumber')?.value.trim() || '0000B';
    const projectName = document.getElementById('projectName')?.value.trim() || '';
    const tunnelName = document.getElementById('tunnelName')?.value.trim() || '';

    const projectData = {
        projectNumber,
        projectName,
        tunnelName,
        arcs,
        envelopes,
        timestamp: new Date().toISOString()
    };

    const text = JSON.stringify(projectData, null, 2);
    const fileName = `${projectNumber}${projectName}${tunnelName}.txt`;

    if (window.showSaveFilePicker) {
        try {
            const handle = await window.showSaveFilePicker({
                suggestedName: fileName,
                types: [{
                    description: 'Project Text File',
                    accept: { 'text/plain': ['.txt'] },
                }],
            });
            const writable = await handle.createWritable();
            await writable.write(text);
            await writable.close();
            alert(`專案已成功儲存！`);
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error saving file:', err);
                // Fallback to traditional download
                traditionalDownload(text, fileName);
            }
        }
    } else {
        traditionalDownload(text, fileName);
    }
}

function traditionalDownload(text, fileName) {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
    alert(`專案 ${fileName} 已下載儲存`);
}

async function saveSectionTemp() {
    const sectionData = {
        arcs: JSON.parse(JSON.stringify(arcs)),
        timestamp: new Date().toISOString()
    };
    await saveToDB('latest_section', sectionData);
    alert('斷面已暫存！');
}

async function restoreSectionFromDB() {
    const data = await getFromDB('latest_section');
    if (data && data.arcs) {
        arcs = data.arcs;
        updateConnectorGeometry();
        drawSystem();
        autoFitViewBox();
        updateInfoPanel();
        alert('斷面已恢復！');
    } else {
        alert('無瀏覽器暫存紀錄。');
    }
}



async function saveAsCSV() {
    // 1. 取得資料與欄位名稱
    const allArcs = getAllArcs();
    const projectNumber = document.getElementById('projectNumber')?.value || '';
    const projectName = document.getElementById('projectName')?.value || '';
    const tunnelName = document.getElementById('tunnelName')?.value || 'Tunnel_Design';

    if (!allArcs || allArcs.length === 0) {
        alert("沒有資料可以匯出！");
        return;
    }

    // 2. 轉換資料為 CSV 字串
    // 取得物件的所有 Key 作為表頭
    const headers = Object.keys(allArcs[0]);
    const csvRows = [];

    // 加入表頭
    csvRows.push(headers.join(','));

    // 加入每一筆資料內容
    for (const row of allArcs) {
        const values = headers.map(header => {
            let val = row[header];
            // 如果是數字，格式化為小數點4位
            if (typeof val === 'number') {
                val = val.toFixed(4);
            }
            const escaped = ('' + val).replace(/"/g, '\\"'); // 處理雙引號防止格式跑掉
            return `"${escaped}"`; // 用雙引號包覆欄位值，處理含逗號的資料
        });
        csvRows.push(values.join(','));
    }

    // 3. 組合完整的 CSV 字串並加上 BOM (解決 Excel 開啟中文亂碼問題)
    const csvString = "\ufeff" + csvRows.join('\n');

    // 4. 建立 Blob 與 下載連結
    try {
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');

        a.href = downloadUrl;
        // 組合檔名
        const fullFilename = `${projectNumber}_${projectName}_${tunnelName}`.replace(/\s+/g, '_');
        a.download = `${fullFilename}.csv`;

        // 5. 觸發下載
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);

        alert('已成功匯出 CSV 檔案！');
    } catch (err) {
        console.error('CSV Export error:', err);
        alert('匯出 CSV 時發生錯誤。');
    }
}

// Helper to get CSRF token
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

function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

