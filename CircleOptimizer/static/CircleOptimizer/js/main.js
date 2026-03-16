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

const MAINTENANCE_WALKWAY_LEFT_ENVELOPE = [
    { name: 'L1', x: -3.0101, y: -2.8750 },
    { name: 'L2', x: -3.0101, y: -0.6750 },
    { name: 'L3', x: -2.2101, y: -0.6750 },
    { name: 'L4', x: -2.2101, y: -2.8750 }
];

const MAINTENANCE_WALKWAY_RIGHT_ENVELOPE = [
    { name: 'R1', x: 2.2101, y: -2.8750 },
    { name: 'R2', x: 2.2101, y: -0.6750 },
    { name: 'R3', x: 3.0101, y: -0.6750 },
    { name: 'R4', x: 3.0101, y: -2.8750 }
];


// Envelopes State
let envelopes = [
    {
        id: 'env-1',
        name: '公路隧道標準段',
        type: 'highway',
        points: JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE)),
        color: '#000000',
        visible: true,
        expanded: false
    }
];

let activeEnvelopeIndex = null;
let activePointIndex = null;

// ---- 正圓形 (Circular) Mode State ----
let circularArcs = {
    inner: { cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 270.000, color: '#fd8f00ff' },
    outer: { cx: 0.0000, cy: 0.0000, r: 6.0000, startAngle: 90.000, endAngle: 270.000, color: '#c05600' }
};

// ---- 馬蹄形 (Horseshoe) Mode State ----
let horseshoeArcs = {
    inner: {
        cx: 0.0000, cy: 0.0000, r: 3.3000, startAngle: 90.000, endAngle: 180.000,
        p2e: { x: -3.0000, y: -3.3500 },
        p3e: { x: 0.0000, y: -3.3500 },
        color: '#fd8f00ff'
    },
    outer: {
        cx: 0.0000, cy: 0.0000, r: 3.8500, startAngle: 90.000, endAngle: 180.000,
        p5e: { x: -3.800, y: -4.250 },
        p6e: { x: 0.0000, y: -4.250 },
        color: '#c05600'
    }
};

// ---- 雙心圓 (Double-Circle) Mode State ----
let doubleCircleArcs = {
    inner: {
        p1: { cx: 0.0000, cy: 0.0000, r: 3.3000, startAngle: 90.000, endAngle: 180.000, color: '#fd8f00ff' },
        line2: { ps: { x: -3.30000, y: 0.0000 }, pe: { x: -2.9511, y: -3.4598 }, color: '#28a745' },
        p3: { cx: 0.0000, cy: 1.0000, r: 5.3478, startAngle: 236.506, endAngle: 270.000, color: '#007bff' }
    },
    outer: {
        p4: { cx: 0.0000, cy: 0.0000, r: 3.7000, startAngle: 90.000, endAngle: 180.000, color: '#c05600' },
        line5: { ps: { x: -3.70000, y: 0.0000 }, pe: { x: -3.3283, y: -3.6861 }, color: '#1e7e34' },
        p6: { cx: 0.0000, cy: 1.0000, r: 5.7478, startAngle: 234.616, endAngle: 270.000, color: '#0056b3' }
    }
};

// ---- 三心圓 (Triple-Circle) Mode State ----
// Arc 1 & 3: Main arcs (Top/Bottom)
// Arc 2: Connector arc (Middle)
// We store state for all, but Arc 2 is heavily constrained.
let tripleCircleArcs = [
    { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 207.622, color: '#fd8f00ff' },      // Top
    { id: '2', cx: -3.1011, cy: -1.6227, r: 2.0000, startAngle: 207.622, endAngle: 254.622, color: '#28a745' }, // Connector
    { id: '3', cx: 0.0000, cy: 9.6526, r: 13.6940, startAngle: 254.622, endAngle: 270.000, color: '#007bff' },   // Bottom
    { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 205.000, color: '#c05600' },      // Top
    { id: '5', cx: -2.9002, cy: -1.4524, r: 2.8000, startAngle: 205.000, endAngle: 251.000, color: '#1e7e34' }, // Connector
    { id: '6', cx: 0.0, cy: 6.9704, r: 11.7080, startAngle: 251.000, endAngle: 270.000, color: '#0056b3' }   // Bottom
];

// ---- 四心圓 (Quad-Circle) Mode State ----
// Inner arcs: 1L(top), 2L(mid-upper), 3L(mid-lower), 4L(bottom)
// Outer arcs: 5L(top), 6L(mid-upper), 7L(mid-lower), 8L(bottom)
let quadCircleArcs = [
    { id: '1', cx: 0.0000, cy: -2.5980, r: 8.5000, startAngle: 90.000, endAngle: 120.000, color: '#fd8f00ff' },
    { id: '2', cx: -1.5000, cy: 0.0000, r: 5.5000, startAngle: 120.000, endAngle: 207.622, color: '#28a745' },
    { id: '3', cx: -4.6009, cy: -1.6226, r: 2.0000, startAngle: 207.622, endAngle: 254.622, color: '#007bff' },
    { id: '4', cx: 0.0000, cy: 15.1060, r: 19.3500, startAngle: 254.622, endAngle: 270.000, color: '#9c27b0' },
    { id: '5', cx: 0.0000, cy: -2.6980, r: 9.2000, startAngle: 90.000, endAngle: 120.000, color: '#c05600' },
    { id: '6', cx: -1.5000, cy: -0.1000, r: 6.2000, startAngle: 120.000, endAngle: 205.000, color: '#1e7e34' },
    { id: '7', cx: -4.4003, cy: -1.4524, r: 2.9999, startAngle: 205.000, endAngle: 251.000, color: '#0056b3' },
    { id: '8', cx: 0.0000, cy: 11.3270, r: 16.5160, startAngle: 251.000, endAngle: 270.000, color: '#7b1fa2' }
];

// 國4緊急停車彎淨空包絡線 (Emergency Parking Clearance Envelope)
const EMERGENCY_PARKING_ENVELOPE = [
    { name: '點1', x: -6.4468, y: -1.0272 },
    { name: '點2', x: -6.4069, y: 0.9724 },
    { name: '點3', x: -5.4070, y: 0.9524 },
    { name: '點4', x: -5.3520, y: 3.7050 },
    { name: '點5', x: 2.4529, y: 3.5489 },
    { name: '點6', x: 5.3752, y: 3.5936 },
    { name: '點7', x: 5.4172, y: 0.8458 },
    { name: '點8', x: 6.4171, y: 0.8611 },
    { name: '點9', x: 6.4570, y: -1.1352 }
];

// 噴流風扇1 (Jet Fan 1)
const JET_FAN_1_ENVELOPE = [
    { name: 'JF1', x: -3.0457, y: 5.2783 },
    { name: 'JF2', x: -2.0789, y: 5.4694 },
    { name: 'JF3', x: -2.2999, y: 4.9085 },
    { name: 'JF4', x: -2.0803, y: 4.6889 },
    { name: 'JF5', x: -1.9999, y: 4.3889 },
    { name: 'JF6', x: -2.0803, y: 4.0889 },
    { name: 'JF7', x: -2.2999, y: 3.8693 },
    { name: 'JF8', x: -2.5999, y: 3.7889 },
    { name: 'JF9', x: -2.8999, y: 3.8693 },
    { name: 'JF10', x: -3.1195, y: 4.0889 },
    { name: 'JF11', x: -3.1999, y: 4.3889 },
    { name: 'JF12', x: -3.1195, y: 4.6889 },
    { name: 'JF13', x: -2.8999, y: 4.9085 }
];

// 噴流風扇2 (Jet Fan 2)
const JET_FAN_2_ENVELOPE = [
    { name: 'JF1', x: -0.9210, y: 5.4694 },
    { name: 'JF2', x: 0.0458, y: 5.2782 },
    { name: 'JF3', x: -0.1000, y: 4.9085 },
    { name: 'JF4', x: 0.1196, y: 4.6889 },
    { name: 'JF5', x: 0.2000, y: 4.3889 },
    { name: 'JF6', x: 0.1196, y: 4.0889 },
    { name: 'JF7', x: -0.1000, y: 3.8693 },
    { name: 'JF8', x: -0.4000, y: 3.7889 },
    { name: 'JF9', x: -0.7000, y: 3.8693 },
    { name: 'JF10', x: -0.9196, y: 4.0889 },
    { name: 'JF11', x: -1.0000, y: 4.3889 },
    { name: 'JF12', x: -0.9196, y: 4.6889 },
    { name: 'JF13', x: -0.7000, y: 4.9085 }
];

// 高鐵緊急走道 (HSR Emergency Walkway)
const HSR_WALKWAY_LEFT_ENVELOPE = [
    { name: 'EW_1', x: -5.5152, y: -2.2000 },
    { name: 'EW_2', x: -5.5152, y: 0.0000 },
    { name: 'EW_3', x: -4.3152, y: 0.0000 },
    { name: 'EW_4', x: -4.3152, y: -2.2000 }
];

const HSR_WALKWAY_RIGHT_ENVELOPE = [
    { name: 'EW_1', x: 5.5152, y: -2.2000 },
    { name: 'EW_2', x: 5.5152, y: 0.0000 },
    { name: 'EW_3', x: 4.3152, y: 0.0000 },
    { name: 'EW_4', x: 4.3152, y: -2.2000 }
];

// 高鐵車輛動態 (HSR Rolling Stock Dynamic)
const HSR_DYNAMIC_LEFT_ENVELOPE = [
    { name: 'KE_1', x: -3.4500, y: -2.3249 },
    { name: 'KE_2', x: -3.8000, y: -2.0099 },
    { name: 'KE_3', x: -3.8750, y: -2.0099 },
    { name: 'KE_4', x: -3.8750, y: -1.3099 },
    { name: 'KE_5', x: -3.9000, y: -1.2849 },
    { name: 'KE_6', x: -3.9000, y: 0.6901 },
    { name: 'KE_7', x: -3.7745, y: 1.0736 },
    { name: 'KE_8', x: -3.5432, y: 1.4042 },
    { name: 'KE_9', x: -3.2260, y: 1.6535 },
    { name: 'KE_10', x: -2.8500, y: 1.8001 },
    { name: 'KE_11', x: -1.6500, y: 1.8001 },
    { name: 'KE_12', x: -1.2740, y: 1.6535 },
    { name: 'KE_13', x: -0.9568, y: 1.4042 },
    { name: 'KE_14', x: -0.7255, y: 1.0736 },
    { name: 'KE_15', x: -0.6000, y: 0.6901 },
    { name: 'KE_16', x: -0.6000, y: -1.2849 },
    { name: 'KE_17', x: -0.6250, y: -1.3099 },
    { name: 'KE_18', x: -0.6250, y: -2.0093 },
    { name: 'KE_19', x: -0.7000, y: -2.0093 },
    { name: 'KE_20', x: -1.0500, y: -2.3249 }
];

const HSR_DYNAMIC_RIGHT_ENVELOPE = [
    { name: 'KE_1', x: 3.4500, y: -2.3249 },
    { name: 'KE_2', x: 3.8000, y: -2.0099 },
    { name: 'KE_3', x: 3.8750, y: -2.0099 },
    { name: 'KE_4', x: 3.8750, y: -1.3099 },
    { name: 'KE_5', x: 3.9000, y: -1.2849 },
    { name: 'KE_6', x: 3.9000, y: 0.6901 },
    { name: 'KE_7', x: 3.7745, y: 1.0736 },
    { name: 'KE_8', x: 3.5432, y: 1.4042 },
    { name: 'KE_9', x: 3.2260, y: 1.6535 },
    { name: 'KE_10', x: 2.8500, y: 1.8001 },
    { name: 'KE_11', x: 1.6500, y: 1.8001 },
    { name: 'KE_12', x: 1.2740, y: 1.6535 },
    { name: 'KE_13', x: 0.9568, y: 1.4042 },
    { name: 'KE_14', x: 0.7255, y: 1.0736 },
    { name: 'KE_15', x: 0.6000, y: 0.6901 },
    { name: 'KE_16', x: 0.6000, y: -1.2849 },
    { name: 'KE_17', x: 0.6250, y: -1.3099 },
    { name: 'KE_18', x: 0.6250, y: -2.0093 },
    { name: 'KE_19', x: 0.7000, y: -2.0093 },
    { name: 'KE_20', x: 1.0500, y: -2.3249 }
];

// 高鐵絕緣淨空 (HSR Insulation Clearance)
const HSR_INSULATION_LEFT_ENVELOPE = [
    { name: 'IC_1', x: -3.3545, y: 2.4001 },
    { name: 'IC_2', x: -3.0647, y: 2.9645 },
    { name: 'IC_3', x: -2.8371, y: 2.9645 },
    { name: 'IC_4', x: -2.8371, y: 3.3123 },
    { name: 'IC_5', x: -2.6694, y: 3.5005 },
    { name: 'IC_6', x: -1.9003, y: 3.5005 },
    { name: 'IC_7', x: -1.6957, y: 3.3149 },
    { name: 'IC_8', x: -1.6957, y: 2.9489 },
    { name: 'IC_9', x: -1.4656, y: 2.9489 },
    { name: 'IC_10', x: -1.1455, y: 2.4001 }
];

const HSR_INSULATION_RIGHT_ENVELOPE = [
    { name: 'IC_1', x: 3.3545, y: 2.4001 },
    { name: 'IC_2', x: 3.0647, y: 2.9645 },
    { name: 'IC_3', x: 2.8371, y: 2.9645 },
    { name: 'IC_4', x: 2.8371, y: 3.3123 },
    { name: 'IC_5', x: 2.6694, y: 3.5005 },
    { name: 'IC_6', x: 1.9003, y: 3.5005 },
    { name: 'IC_7', x: 1.6957, y: 3.3149 },
    { name: 'IC_8', x: 1.6957, y: 2.9489 },
    { name: 'IC_9', x: 1.4656, y: 2.9489 },
    { name: 'IC_10', x: 1.1455, y: 2.4001 }
];

function getCurrentMode() {
    return document.getElementById('tunnelType')?.value || 'triple';
}


// Helper: Get point on circle
function getPointOnCircle(cx, cy, r, angleDeg) {
    const rad = angleDeg * Math.PI / 180;
    return {
        x: cx + r * Math.cos(rad),
        y: cy + r * Math.sin(rad)
    };
}

/**
 * Standardized coordinate label placement for arc endpoints
 * @param {SVGElement} group - The target overlay group
 * @param {object} p - {x, y} coordinate
 * @param {string} name - Label name (e.g. "P1S")
 * @param {number} angle - Arc angle in degrees
 * @param {boolean} isInner - True for inner arc, false for outer
 * @param {number} scale - Visual scale
 * @param {string} color - Text color
 */
function renderArcEndpointLabel(group, p, name, angle, isInner, scale, color) {
    const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    let anchor, baseline, xOffset = 0, yOffset = 0;

    // Normalize angle to 0-360 range for logic
    let normAngle = Math.round(angle % 360);
    while (normAngle < 0) normAngle += 360;

    if (isInner) {
        if (normAngle === 90) {
            anchor = 'start'; baseline = 'hanging'; yOffset = 1.6 * scale;
        } else if (normAngle > 90 && normAngle < 180) {
            anchor = 'start'; baseline = 'hanging'; yOffset = 1.6 * scale;
        } else if (normAngle === 180) {
            anchor = 'start'; baseline = 'middle'; xOffset = 1.6 * scale;
        } else if (normAngle > 180 && normAngle < 270) {
            anchor = 'start'; baseline = 'alphabetic'; yOffset = -1.6 * scale;
        } else if (normAngle === 270) {
            anchor = 'start'; baseline = 'alphabetic'; yOffset = -1.6 * scale;
        } else {
            // Default/Fallback
            anchor = 'start'; baseline = 'alphabetic'; yOffset = -1.6 * scale;
        }
    } else {
        if (normAngle === 90) {
            anchor = 'start'; baseline = 'alphabetic'; yOffset = -1.6 * scale;
        } else if (normAngle > 90 && normAngle < 180) {
            anchor = 'end'; baseline = 'alphabetic'; yOffset = -1.6 * scale;
        } else if (normAngle === 180) {
            anchor = 'end'; baseline = 'middle'; xOffset = -1.6 * scale;
        } else if (normAngle > 180 && normAngle < 270) {
            anchor = 'end'; baseline = 'hanging'; yOffset = 1.6 * scale;
        } else if (normAngle === 270) {
            anchor = 'start'; baseline = 'hanging'; yOffset = 1.6 * scale;
        } else {
            // Default/Fallback
            anchor = 'end'; baseline = 'hanging'; yOffset = 1.6 * scale;
        }
    }

    t.setAttribute('x', (p.x + xOffset).toFixed(4));
    t.setAttribute('y', (-p.y + yOffset).toFixed(4));
    t.setAttribute('font-size', (2.0 * scale).toFixed(4));
    t.setAttribute('fill', color);
    t.setAttribute('text-anchor', anchor);
    t.setAttribute('dominant-baseline', baseline);
    t.style.pointerEvents = 'none';
    t.textContent = `${name}(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`;
    group.appendChild(t);
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
    updateTripleCircleArcsConnectorGeometry();
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
        };
    }
});

// --- Previous state tracking for undo/reset ---
let lastConfirmedMode = 'circular'; // Tracks the ACTIVE mode before any dropdown change
let previousTunnelMode = 'circular';
let previousTunnelData = null; // Snapshot of arcs and envelopes

function captureTunnelState() {
    previousTunnelMode = lastConfirmedMode; // Use tracked mode, NOT current dropdown value
    previousTunnelData = {
        circularArcs: JSON.parse(JSON.stringify(circularArcs)),
        horseshoeArcs: JSON.parse(JSON.stringify(horseshoeArcs)),
        doubleCircleArcs: JSON.parse(JSON.stringify(doubleCircleArcs)),
        tripleCircleArcs: JSON.parse(JSON.stringify(tripleCircleArcs)),
        quadCircleArcs: JSON.parse(JSON.stringify(quadCircleArcs)),
        envelopes: JSON.parse(JSON.stringify(envelopes))
    };
}

function restoreTunnelState() {
    if (previousTunnelData) {
        circularArcs = previousTunnelData.circularArcs;
        horseshoeArcs = previousTunnelData.horseshoeArcs;
        doubleCircleArcs = previousTunnelData.doubleCircleArcs;
        tripleCircleArcs = previousTunnelData.tripleCircleArcs;
        quadCircleArcs = previousTunnelData.quadCircleArcs;
        envelopes = previousTunnelData.envelopes;

        const tunnelType = document.getElementById('tunnelType');
        if (tunnelType) tunnelType.value = previousTunnelMode;
        lastConfirmedMode = previousTunnelMode;

        renderEnvelopeControls();
        drawSystem();
        autoFitViewBox();
        updateInfoPanel();
    }
}

/**
 * Handle confirmation before resetting or changing tunnel type
 */
function handleResetConfirmation(selectElement) {
    // Capture current state BEFORE loading new defaults
    captureTunnelState();

    const typeMap = {
        'circular': '正圓形',
        'horseshoe': '馬蹄形',
        'double_circle': '雙心圓',
        'triple': '三心圓',
        'quad': '四心圓'
    };
    const currentType = document.getElementById('tunnelType')?.value || 'circular';
    const typeDisplayName = typeMap[currentType] || currentType;

    if (confirm(`是否將目前斷面重置為${typeDisplayName}？\n(目前的變更將會遺失)`)) {
        loadDefaultSection();
        // Update tracked mode to the new selection
        lastConfirmedMode = document.getElementById('tunnelType')?.value || 'circular';
    } else {
        // Cancel → restore captured state (including dropdown)
        restoreTunnelState();
    }
}

// Bind Init Section Button (Manual Reset)
document.addEventListener('DOMContentLoaded', () => {
    const initSectionBtn = document.getElementById('initSectionBtn');
    if (initSectionBtn) {
        initSectionBtn.onclick = () => {
            handleResetConfirmation(null);
        };
    }
});

function loadDefaultSection() {

    const tunnelType = document.getElementById('tunnelType');
    if (!tunnelType) return;

    const type = tunnelType.value;

    const globalVisible = document.getElementById('globalEnvVisible')?.checked ?? true;
    const globalLabels = document.getElementById('globalEnvLabels')?.checked ?? false;

    switch (type) {
        case 'circular': // 正圓形 — handled by circularArcs state
            circularArcs.inner = { cx: 0.0000, cy: 0.0000, r: 6.0000, startAngle: 90.000, endAngle: 270.000, color: '#fd8f00ff' };
            circularArcs.outer = { cx: 0.0000, cy: 0.0000, r: 6.5000, startAngle: 90.000, endAngle: 270.000, color: '#c05600' };
            // Initialize highway envelope for Circular
            envelopes = [
                { id: 'env-1', name: '高鐵車輛動態(左)', type: 'hsr_dynamic_left', points: JSON.parse(JSON.stringify(HSR_DYNAMIC_LEFT_ENVELOPE)), color: '#007bff', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-2', name: '高鐵車輛動態(右)', type: 'hsr_dynamic_right', points: JSON.parse(JSON.stringify(HSR_DYNAMIC_RIGHT_ENVELOPE)), color: '#007bff', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-3', name: '高鐵絕緣淨空(左)', type: 'hsr_insulation_left', points: JSON.parse(JSON.stringify(HSR_INSULATION_LEFT_ENVELOPE)), color: '#6f42c1', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-4', name: '高鐵絕緣淨空(右)', type: 'hsr_insulation_right', points: JSON.parse(JSON.stringify(HSR_INSULATION_RIGHT_ENVELOPE)), color: '#6f42c1', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-5', name: '高鐵緊急走道(左)', type: 'hsr_walkway_left', points: JSON.parse(JSON.stringify(HSR_WALKWAY_LEFT_ENVELOPE)), color: '#28a745', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-6', name: '高鐵緊急走道(右)', type: 'hsr_walkway_right', points: JSON.parse(JSON.stringify(HSR_WALKWAY_RIGHT_ENVELOPE)), color: '#28a745', visible: globalVisible, showLabels: globalLabels, expanded: false }
            ];
            renderEnvelopeControls();
            drawSystem();
            autoFitViewBox();
            break;

        case 'horseshoe': // 馬蹄形
            horseshoeArcs.inner = {
                cx: 0.0000, cy: 0.0000, r: 3.3000, startAngle: 90.000, endAngle: 180.000,
                p2e: { x: -3.0000, y: -3.3500 },
                p3e: { x: 0.0000, y: -3.3500 },
                color: '#fd8f00ff'
            };
            horseshoeArcs.outer = {
                cx: 0.0000, cy: 0.0000, r: 3.8000, startAngle: 90.000, endAngle: 180.000,
                p5e: { x: -3.800, y: -4.250 },
                p6e: { x: 0.0000, y: -4.250 },
                color: '#c05600'
            };
            // Initialize multiple envelopes for Horseshoe
            envelopes = [
                { id: 'env-1', name: '鐵路隧道', type: 'railway', points: JSON.parse(JSON.stringify(TaiwanRailwaySingleRail_ENVELOPE)), color: '#2c3e50', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-2', name: '鐵路隧道維修步道(左)', type: 'walkway_left', points: JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_LEFT_ENVELOPE)), color: '#2c3e50', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-3', name: '鐵路隧道維修步道(右)', type: 'walkway_right', points: JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_RIGHT_ENVELOPE)), color: '#2c3e50', visible: globalVisible, showLabels: globalLabels, expanded: false }
            ];
            renderEnvelopeControls();
            drawSystem();
            autoFitViewBox();
            break;

        case 'double_circle': // 雙心圓
            doubleCircleArcs.inner = {
                p1: { cx: 0.0000, cy: 0.0000, r: 3.3000, startAngle: 90.000, endAngle: 180.000, color: '#fd8f00ff' },
                line2: { ps: { x: -3.30000, y: 0.0000 }, pe: { x: -2.9511, y: -3.4598 }, color: '#28a745' },
                p3: { cx: 0.0000, cy: 1.0000, r: 5.3478, startAngle: 236.506, endAngle: 270.000, color: '#007bff' }
            };
            doubleCircleArcs.outer = {
                p4: { cx: 0.0000, cy: 0.0000, r: 3.7000, startAngle: 90.000, endAngle: 180.000, color: '#c05600' },
                line5: { ps: { x: -3.70000, y: 0.0000 }, pe: { x: -3.3283, y: -3.6861 }, color: '#1e7e34' },
                p6: { cx: 0.0000, cy: 1.0000, r: 5.7478, startAngle: 234.616, endAngle: 270.000, color: '#0056b3' }
            };
            // Initialize railway and walkway envelopes for Double-Circle
            envelopes = [
                { id: 'env-1', name: '鐵路隧道', type: 'railway', points: JSON.parse(JSON.stringify(TaiwanRailwaySingleRail_ENVELOPE)), color: '#2c3e50', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-2', name: '鐵路隧道維修步道(左)', type: 'walkway_left', points: JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_LEFT_ENVELOPE)), color: '#2c3e50', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-3', name: '鐵路隧道維修步道(右)', type: 'walkway_right', points: JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_RIGHT_ENVELOPE)), color: '#2c3e50', visible: globalVisible, showLabels: globalLabels, expanded: false }
            ];
            updateDoubleCircleGeometry();
            renderEnvelopeControls();
            drawSystem();
            autoFitViewBox();
            break;

        case 'triple': // 三心圓
            tripleCircleArcs[0] = { id: '1', cx: 0.0000, cy: 0.0000, r: 5.5000, startAngle: 90.000, endAngle: 207.622, color: '#fd8f00ff' };
            tripleCircleArcs[1] = { id: '2', cx: -3.1011, cy: -1.6227, r: 2.0000, startAngle: 207.622, endAngle: 254.622, color: '#28a745' };
            tripleCircleArcs[2] = { id: '3', cx: 0.0000, cy: 9.6526, r: 13.6940, startAngle: 254.622, endAngle: 270.000, color: '#007bff' };
            tripleCircleArcs[3] = { id: '4', cx: 0.0, cy: -0.1000, r: 6.0000, startAngle: 90.000, endAngle: 205.000, color: '#c05600' };
            tripleCircleArcs[4] = { id: '5', cx: -2.9002, cy: -1.4524, r: 2.8000, startAngle: 205.000, endAngle: 251.000, color: '#1e7e34' };
            tripleCircleArcs[5] = { id: '6', cx: 0.0, cy: 6.9704, r: 11.7080, startAngle: 251.000, endAngle: 270.000, color: '#0056b3' };
            // Initialize HSR envelopes for Triple-Circle
            envelopes = [
                { id: 'env-1', name: '公路隧道標準段', type: 'highway', points: JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE)), color: '#000000', visible: globalVisible, showLabels: globalLabels, expanded: false }
            ];
            renderEnvelopeControls();
            drawSystem();
            autoFitViewBox();
            break;

        case 'quad': // 四心圓
            quadCircleArcs[0] = { id: '1', cx: 0.0000, cy: -2.5980, r: 8.5000, startAngle: 90.000, endAngle: 120.000, color: '#fd8f00ff' };
            quadCircleArcs[1] = { id: '2', cx: -1.5000, cy: 0.0000, r: 5.5000, startAngle: 120.000, endAngle: 207.622, color: '#28a745' };
            quadCircleArcs[2] = { id: '3', cx: -4.6009, cy: -1.6226, r: 2.0000, startAngle: 207.622, endAngle: 254.622, color: '#007bff' };
            quadCircleArcs[3] = { id: '4', cx: 0.0000, cy: 15.1060, r: 19.3500, startAngle: 254.622, endAngle: 270.000, color: '#9c27b0' };
            quadCircleArcs[4] = { id: '5', cx: 0.0000, cy: -2.6980, r: 9.2000, startAngle: 90.000, endAngle: 120.000, color: '#c05600' };
            quadCircleArcs[5] = { id: '6', cx: -1.5000, cy: -0.1000, r: 6.2000, startAngle: 120.000, endAngle: 205.000, color: '#1e7e34' };
            quadCircleArcs[6] = { id: '7', cx: -4.4003, cy: -1.4524, r: 2.9999, startAngle: 205.000, endAngle: 251.000, color: '#0056b3' };
            quadCircleArcs[7] = { id: '8', cx: 0.0000, cy: 11.3270, r: 16.5160, startAngle: 251.000, endAngle: 270.000, color: '#7b1fa2' };
            envelopes = [
                { id: 'env-1', name: '公路隧道緊急停車彎', type: 'emergency_parking', points: JSON.parse(JSON.stringify(EMERGENCY_PARKING_ENVELOPE)), color: '#000000', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-2', name: '公路隧道噴流風扇1', type: 'jet_fan_1', points: JSON.parse(JSON.stringify(JET_FAN_1_ENVELOPE)), color: '#000000', visible: globalVisible, showLabels: globalLabels, expanded: false },
                { id: 'env-3', name: '公路隧道噴流風扇2', type: 'jet_fan_2', points: JSON.parse(JSON.stringify(JET_FAN_2_ENVELOPE)), color: '#000000', visible: globalVisible, showLabels: globalLabels, expanded: false }
            ];
            updateQuadCircleArcsConnectorGeometry();
            renderEnvelopeControls();
            drawSystem();
            autoFitViewBox();
            break;

        default:
            return;
    }

    updateTripleCircleArcsConnectorGeometry();
    drawSystem();
    autoFitViewBox();
    saveNewSection();// 儲存目前斷面參數至 section.tmp (作為備份)

    // Initial check for checkbox dependency
    const showEnv = document.getElementById('globalEnvVisible');
    const labelEnv = document.getElementById('globalEnvLabels');
    if (showEnv && labelEnv && !showEnv.checked) {
        labelEnv.disabled = true;
        labelEnv.checked = false;
    }
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
                <div style="display: flex; flex-direction: column; gap: 4px; width: 100%;">
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="color" value="${env.color.substring(0, 7)}" 
                            onchange="updateEnvelopeColor(${envIdx}, this.value)" 
                            style="width: 90px; height: 30px; border: none; padding: 0; background: transparent; cursor: pointer;">
                        <input type="text" value="${env.name}" class="env-name-input" 
                            onchange="updateEnvelopeName(${envIdx}, this.value)" 
                            style="font-weight: bold; border: none; background: transparent; width:250%; min-width:150px; color: ${env.color}; font-size: 1.1rem;">
                        <button class="btn btn-sm btn-outline-secondary btn-black-font" onclick="toggleEnvelopeExpansion(${envIdx})" title="展開/收合淨空包絡線" style="padding: 4px 4px; font-size: 1.0em; white-space: nowrap;">${env.expanded ? '🙉 收合' : '🙈 展開'}</button>
                        <button class="btn btn-sm btn-outline-secondary btn-black-font" onclick="removeEnvelope(${envIdx})" title="清除淨空包絡線" style="padding: 4px 4px;font-size: 1.0em">⛔ 清除</button>
                    </div>
                </div>
            </div>
            <div style="${env.expanded ? '' : 'display: none;'}">
                <div class="points-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 6px;">
                    ${env.points.map((p, pIdx) => `
                        <div class="point-input" style="background: white; border: 1px solid #f0f0f0; padding: 4px; border-radius: 4px; display: flex; align-items: center; gap: 4px; justify-content: space-between; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);">
                            <div style="display: flex; align-items: center; gap: 4px; flex-grow: 1;">
                                <input type="text" value="${p.name || `點${pIdx + 1}`}" 
                                    onchange="updateNodeName(${envIdx}, ${pIdx}, this.value)" 
                                    style="width: 90px; font-size: 1.00em; padding: 2px; border: 1px solid #ddd; border-radius: 2px;">
                                <div style="display: flex; gap: 2px;">
                                    <input type="number" step="0.0001" value="${p.x.toFixed(4)}" 
                                        onchange="updateNodeCoord(${envIdx}, ${pIdx}, 'x', this.value)" 
                                        style="width: 90px; font-size: 1.00em; padding: 2px; border: 1px solid #eee; border-radius: 2px;">
                                    <input type="number" step="0.0001" value="${p.y.toFixed(4)}" 
                                        onchange="updateNodeCoord(${envIdx}, ${pIdx}, 'y', this.value)" 
                                        style="width: 90px; font-size: 1.00em; padding: 2px; border: 1px solid #eee; border-radius: 2px;">
                                </div>
                            </div>
                            <button class="btn btn-sm btn-outline-secondary btn-black-font" onclick="removeNode(${envIdx}, ${pIdx})" 
                                title="刪除淨空包絡上控制節點" style="padding: 2px 6px;  font-size: 1.0rem; white-space: nowrap;">➖刪除</button>
                        </div>
                    `).join('')}
                </div>
                <div style="display: flex; gap: 5px; margin-top: 10px; border-top: 1px solid #eee; padding-top: 5px; justify-content: center; align-items: center;">            
                    <button class="btn btn-sm btn-outline-secondary btn-black-font" onclick="toggleTemplateMenu(${envIdx})" title="套用淨空包絡線樣板" style="padding: 4px 16px; font-size: 1.0rem;">💡套用標準樣板</button>
                    <button class="btn btn-sm btn-outline-secondary btn-black-font" onclick="addNode(${envIdx})" title="增加淨空包絡線上控制點" style= "padding: 4px 16px; font-size: 1.0rem">➕增加控制節點</button>                    
                </div>
                <div id="template-menu-${envIdx}" style="display: none; margin-top: 8px; background: #f8f9fa; padding: 10px; border-radius: 4px; border: 1px solid #e9ecef; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 0.9rem; color: #555; font-weight: bold;">選擇樣板:</span>
                        <select onchange="applyTemplate(${envIdx}, this.value)" style="flex-grow: 1; font-size: 0.9rem; padding: 4px; border: 1px solid #ced4da; border-radius: 4px;">
                            <option value="">...</option>
                            <option value="highway">公路隧道標準段</option>
                            <option value="emergency_parking">公路隧道緊急停車彎</option>
                            <option value="jet_fan_1">公路隧道噴流風扇1</option>
                            <option value="jet_fan_2">公路隧道噴流風扇2</option>
                            <option value="railway">鐵路隧道</option>
                            <option value="walkway_left">鐵路隧道維修步道(左)</option>
                            <option value="walkway_right">鐵路隧道維修步道(右)</option>                            
                            <option value="hsr_walkway_left">高鐵緊急走道(左)</option>
                            <option value="hsr_walkway_right">高鐵緊急走道(右)</option>
                            <option value="hsr_dynamic_left">高鐵車輛動態(左)</option>
                            <option value="hsr_dynamic_right">高鐵車輛動態(右)</option>
                            <option value="hsr_insulation_left">高鐵絕緣淨空(左)</option>
                            <option value="hsr_insulation_right">高鐵絕緣淨空(右)</option>
                            <!--<option value="thsr">高鐵隧道</option>-->
                            <!--<option value="mrt">捷運隧道</option>-->
                            <!--<option value="lrt">輕軌隧道</option>-->
                        </select>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(envCard);
    });
}

function toggleEnvelopeExpansion(envIdx) {
    envelopes[envIdx].expanded = !envelopes[envIdx].expanded;
    renderEnvelopeControls();
}

/**
 * Toggle visibility for all envelopes
 */
function toggleAllEnvelopesVisible(visible) {
    envelopes.forEach(env => {
        env.visible = visible;
    });

    // If "Show" is unchecked, also uncheck and disable "Labels"
    const labelsCheckbox = document.getElementById('globalEnvLabels');
    if (labelsCheckbox) {
        if (!visible) {
            labelsCheckbox.checked = false;
            labelsCheckbox.disabled = true;
            toggleAllEnvelopeLabels(false);
        } else {
            labelsCheckbox.disabled = false;
        }
    }

    drawSystem();
}

/**
 * Toggle labels for all envelopes
 */
function toggleAllEnvelopeLabels(showLabels) {
    envelopes.forEach(env => {
        env.showLabels = showLabels;
    });
    drawSystem();
}

function addEnvelope(templateType = 'highway') {
    let points = [];
    let name = '';
    let color = '#000000';

    switch (templateType) {
        case 'highway':
            points = JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE));
            name = '公路隧道標準段';
            color = '#000000ff';
            break;
        case 'railway':
            points = JSON.parse(JSON.stringify(TaiwanRailwaySingleRail_ENVELOPE));
            name = '鐵路隧道';
            color = '#2c3e50';
            break;
        case 'thsr':
            points = JSON.parse(JSON.stringify(TaiwanHighSpeedRail_ENVELOPE));
            name = '高鐵隧道';
            color = '#006400';
            break;
        case 'mrt':
            points = JSON.parse(JSON.stringify(TaipeiMetro_ENVELOPE));
            name = '捷運隧道';
            color = '#00008b';
            break;
        case 'lrt':
            points = JSON.parse(JSON.stringify(LightRail_ENVELOPE));
            name = '輕軌隧道';
            color = '#8b0000';
            break;
        case 'walkway_left':
            points = JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_LEFT_ENVELOPE));
            name = '鐵路隧道維修步道(左)';
            color = '#2c3e50';
            break;
        case 'walkway_right':
            points = JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_RIGHT_ENVELOPE));
            name = '鐵路隧道維修步道(右)';
            color = '#2c3e50';
            break;
        case 'emergency_parking':
            points = JSON.parse(JSON.stringify(EMERGENCY_PARKING_ENVELOPE));
            name = '公路隧道緊急停車彎';
            color = '#000000';
            break;
        case 'jet_fan_1':
            points = JSON.parse(JSON.stringify(JET_FAN_1_ENVELOPE));
            name = '公路隧道噴流風扇1';
            color = '#000000';
            break;
        case 'jet_fan_2':
            points = JSON.parse(JSON.stringify(JET_FAN_2_ENVELOPE));
            name = '公路隧道噴流風扇2';
            color = '#000000';
            break;
        case 'hsr_walkway_left':
            points = JSON.parse(JSON.stringify(HSR_WALKWAY_LEFT_ENVELOPE));
            name = '高鐵緊急走道(左)';
            color = '#28a745';
            break;
        case 'hsr_walkway_right':
            points = JSON.parse(JSON.stringify(HSR_WALKWAY_RIGHT_ENVELOPE));
            name = '高鐵緊急走道(右)';
            color = '#28a745';
            break;
        case 'hsr_dynamic_left':
            points = JSON.parse(JSON.stringify(HSR_DYNAMIC_LEFT_ENVELOPE));
            name = '高鐵車輛動態(左)';
            color = '#007bff';
            break;
        case 'hsr_dynamic_right':
            points = JSON.parse(JSON.stringify(HSR_DYNAMIC_RIGHT_ENVELOPE));
            name = '高鐵車輛動態(右)';
            color = '#007bff';
            break;
        case 'hsr_insulation_left':
            points = JSON.parse(JSON.stringify(HSR_INSULATION_LEFT_ENVELOPE));
            name = '高鐵絕緣淨空(左)';
            color = '#6f42c1';
            break;
        case 'hsr_insulation_right':
            points = JSON.parse(JSON.stringify(HSR_INSULATION_RIGHT_ENVELOPE));
            name = '高鐵絕緣淨空(右)';
            color = '#6f42c1';
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

    const globalVisible = document.getElementById('globalEnvVisible')?.checked ?? true;
    const globalLabels = document.getElementById('globalEnvLabels')?.checked ?? false;

    const newEnv = {
        id: 'env-' + (envelopes.length + 1),
        name: name + ' ' + (envelopes.length + 1),
        type: templateType,
        points: points,
        color: color,
        visible: globalVisible,
        showLabels: globalLabels,
        expanded: false
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
    if (confirm('是否刪除淨空包絡線?')) {
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
        name: `點${nextIdx} `,
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
    let name = '';
    let color = '';

    if (templateType === 'highway') {
        points = JSON.parse(JSON.stringify(HIGHWAY_ENVELOPE));
        name = '公路隧道標準段';
        color = '#000000ff';
    } else if (templateType === 'railway') {
        points = JSON.parse(JSON.stringify(TaiwanRailwaySingleRail_ENVELOPE));
        name = '鐵路隧道';
        color = '#2c3e50';
    } else if (templateType === 'thsr') {
        points = JSON.parse(JSON.stringify(TaiwanHighSpeedRail_ENVELOPE));
        name = '高鐵隧道';
        color = '#006400';
    } else if (templateType === 'mrt') {
        points = JSON.parse(JSON.stringify(TaipeiMetro_ENVELOPE));
        name = '捷運隧道';
        color = '#00008b';
    } else if (templateType === 'lrt') {
        points = JSON.parse(JSON.stringify(LightRail_ENVELOPE));
        name = '輕軌隧道';
        color = '#8b0000';
    } else if (templateType === 'walkway_left') {
        points = JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_LEFT_ENVELOPE));
        name = '鐵路隧道維修步道(左)';
        color = '#2c3e50';
    } else if (templateType === 'walkway_right') {
        points = JSON.parse(JSON.stringify(MAINTENANCE_WALKWAY_RIGHT_ENVELOPE));
        name = '鐵路隧道維修步道(右)';
        color = '#2c3e50';
    } else if (templateType === 'emergency_parking') {
        points = JSON.parse(JSON.stringify(EMERGENCY_PARKING_ENVELOPE));
        name = '緊急停車彎';
        color = '#000000';
    } else if (templateType === 'jet_fan_1') {
        points = JSON.parse(JSON.stringify(JET_FAN_1_ENVELOPE));
        name = '噴流風扇1';
        color = '#000000';
    } else if (templateType === 'jet_fan_2') {
        points = JSON.parse(JSON.stringify(JET_FAN_2_ENVELOPE));
        name = '噴流風扇2';
        color = '#000000';
    } else if (templateType === 'hsr_walkway_left') {
        points = JSON.parse(JSON.stringify(HSR_WALKWAY_LEFT_ENVELOPE));
        name = '高鐵緊急走道(左)';
        color = '#28a745';
    } else if (templateType === 'hsr_walkway_right') {
        points = JSON.parse(JSON.stringify(HSR_WALKWAY_RIGHT_ENVELOPE));
        name = '高鐵緊急走道(右)';
        color = '#28a745';
    } else if (templateType === 'hsr_dynamic_left') {
        points = JSON.parse(JSON.stringify(HSR_DYNAMIC_LEFT_ENVELOPE));
        name = '高鐵車輛動態(左)';
        color = '#007bff';
    } else if (templateType === 'hsr_dynamic_right') {
        points = JSON.parse(JSON.stringify(HSR_DYNAMIC_RIGHT_ENVELOPE));
        name = '高鐵車輛動態(右)';
        color = '#007bff';
    } else if (templateType === 'hsr_insulation_left') {
        points = JSON.parse(JSON.stringify(HSR_INSULATION_LEFT_ENVELOPE));
        name = '高鐵絕緣淨空(左)';
        color = '#6f42c1';
    } else if (templateType === 'hsr_insulation_right') {
        points = JSON.parse(JSON.stringify(HSR_INSULATION_RIGHT_ENVELOPE));
        name = '高鐵絕緣淨空(右)';
        color = '#6f42c1';
    }

    if (points.length > 0) {
        envelopes[envIdx].points = points;
        envelopes[envIdx].type = templateType;
        if (name) envelopes[envIdx].name = name;
        if (color) envelopes[envIdx].color = color;
    }

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
                console.warn(`No polylines found in ${file.name} `);
                continue;
            }

            polylines.forEach((poly, polyIdx) => {
                // 過濾掉 0,0 點
                const filteredPoints = poly.points.filter(pt => !(pt.x === 0 && pt.y === 0));

                if (filteredPoints.length === 0) {
                    console.warn(`Polyline ${polyIdx + 1} in ${file.name} has only 0, 0 points, skipping.`);
                    return;
                }

                const envName = files.length > 1 || polylines.length > 1
                    ? `${file.name.replace('.dxf', '')}_${polyIdx + 1} `
                    : file.name.replace('.dxf', '');

                const newEnv = {
                    id: 'env-' + (envelopes.length + 1),
                    name: envName,
                    type: 'dxf_import',
                    points: filteredPoints, // 使用過濾後的點
                    color: '#e67e22',
                    visible: true,
                    showLabels: true,
                    expanded: false
                };
                envelopes.push(newEnv);
            });
        } catch (err) {
            console.error(`Error parsing ${file.name}: `, err);
            alert(`讀取 ${file.name} 失敗: ${err.message} `);
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
                currentPoly.points.push({ name: `點${currentPoly.points.length + 1} `, x: vx, y: vy });
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
                    currentPoly.points.push({ name: `點${currentPoly.points.length + 1} `, x, y });
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

function updateTripleCircleArcsConnectorGeometry(movingSide = null, movingPoint = null) {
    const p1 = tripleCircleArcs[0];
    const p2 = tripleCircleArcs[1];
    const p3 = tripleCircleArcs[2];
    const p4 = tripleCircleArcs[3];
    const p5 = tripleCircleArcs[4];
    const p6 = tripleCircleArcs[5];

    const tt = Math.max(0, parseFloat(document.getElementById('minThicknessTop')?.value || 0.3));
    const tb = Math.max(0, parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3));

    // Enforce axis/limit constraints
    p1.cx = 0; p4.cx = 0;
    p3.cx = 0;
    p2.cx = Math.min(0, p2.cx);
    p5.cx = Math.min(0, p5.cx);
    p6.cx = 0; // P6 usually stays on center in Triple-Circle if symmetrical? 
    // Wait, the request only mentions P5 and P3.

    // --- Inner Chain Update ---
    if (movingSide === 'inner' || movingSide === null) {
        // Radius Synchronization: P1=P3 => R3=R1
        const epsilon = 0.001;
        if (Math.abs(p1.cx - p3.cx) < epsilon && Math.abs(p1.cy - p3.cy) < epsilon) {
            p3.r = p1.r;
        }

        // Thickness: P4S.y - P1S.y >= Tt; P3E.y - P6E.y >= Tb
        const p4s = getPointOnCircle(p4.cx, p4.cy, p4.r, p4.startAngle);
        const p6e = getPointOnCircle(p6.cx, p6.cy, p6.r, p6.endAngle);
        const sin1s = Math.sin(p1.startAngle * Math.PI / 180);
        const sin3e = Math.sin(p3.endAngle * Math.PI / 180);

        function applyInnerThickness() {
            const p1s_curr = getPointOnCircle(p1.cx, p1.cy, p1.r, p1.startAngle);
            if (p4s.y - p1s_curr.y < tt) {
                if (movingPoint === 'p1e' || movingPoint === null) {
                    p1.r = (p4s.y - tt - p1.cy) / sin1s;
                } else {
                    p1.cy = (p4s.y - tt) - (p1.r * sin1s);
                }
            }
            const p3e_curr = getPointOnCircle(p3.cx, p3.cy, p3.r, p3.endAngle);
            if (p3e_curr.y - p6e.y < tb) {
                p3.cy = (p6e.y + tb) - (p3.r * sin3e);
            }
        }

        applyInnerThickness();

        // Analytical Junction Solver (P2 tangent to Arc1 at P1E and tangent to Arc3)
        if (movingPoint === 'p1e') {
            const rayAngleRad = p1.endAngle * Math.PI / 180;
            const ux = Math.cos(rayAngleRad), uy = Math.sin(rayAngleRad);
            const vx = p3.cx - p1.cx, vy = p3.cy - p1.cy;
            const v2 = vx * vx + vy * vy;
            const dotUV = ux * vx + uy * vy;
            const D = p3.r - p1.r;
            const denom = 2 * (D + dotUV);
            if (Math.abs(denom) > 1e-6) {
                let d12 = (v2 - D * D) / denom;
                const maxD12 = p1.r - 0.001;
                if (d12 > maxD12) d12 = maxD12;
                p2.cx = p1.cx + d12 * ux;
                p2.cy = p1.cy + d12 * uy;
                p2.r = Math.max(0.0001, p1.r - d12);
            }
        }

        // Standard Tangency Chains
        if (movingPoint !== 'p1e') {
            let d12 = Math.sqrt(Math.pow(p2.cx - p1.cx, 2) + Math.pow(p2.cy - p1.cy, 2));
            if (d12 > p1.r) {
                const factor12 = (p1.r - 0.001) / d12;
                p2.cx = p1.cx + (p2.cx - p1.cx) * factor12;
                p2.cy = p1.cy + (p2.cy - p1.cy) * factor12;
                d12 = p1.r - 0.001;
            }
            p2.r = Math.max(0.0001, Math.abs(p1.r - d12));
            let d23 = Math.sqrt(Math.pow(p3.cx - p2.cx, 2) + Math.pow(p3.cy - p2.cy, 2));
            if (d23 > p3.r) d23 = Math.min(d23, p3.r);
            p3.r = p2.r + d23;

            p1.endAngle = Math.atan2(p2.cy - p1.cy, p2.cx - p1.cx) * 180 / Math.PI;
            while (p1.endAngle < p1.startAngle + 0.1) p1.endAngle += 360;
            while (p1.endAngle >= p1.startAngle + 360) p1.endAngle -= 360;
        }
        if (p1.endAngle > 269.8) p1.endAngle = 269.8;
        p2.startAngle = p1.endAngle;

        const p3_start_raw = Math.atan2(p2.cy - p3.cy, p2.cx - p3.cx) * 180 / Math.PI;
        let p3_start = (p3_start_raw + 360) % 360;
        while (p3_start < p2.startAngle + 0.1) p3_start += 360;
        while (p3_start >= p2.startAngle + 360) p3_start -= 360;
        if (p3_start > 269.9) p3_start = 269.9;
        p3.startAngle = p3_start;
        p2.endAngle = p3.startAngle;

        if (p2.endAngle - p2.startAngle < 0.1) p2.endAngle = p2.startAngle + 0.1;
        p3.endAngle = Math.min(270, Math.max(p3.startAngle + 0.1, p3.endAngle));

        // Boundary Constraints (Inner only)
        const outerArcsList = [p4, p6];
        const p1e_pt = getPointOnCircle(p1.cx, p1.cy, p1.r, p1.endAngle);
        const p3s_pt = getPointOnCircle(p3.cx, p3.cy, p3.r, p3.startAngle);

        // P1E and P3S violations against P4 and P6 (Don't move P4/P6, instead move P1/P3 if needed?)
        // Actually, the original logic moved the OTHER arc. If moving inner, we should cap inner.
        [{ pt: p1e_pt, name: 'P1E' }, { pt: p3s_pt, name: 'P3S' }].forEach(item => {
            outerArcsList.forEach(oa => {
                const angle = Math.atan2(item.pt.y - oa.cy, item.pt.x - oa.cx) * 180 / Math.PI;
                if (isAngleInRange(angle, oa.startAngle, oa.endAngle)) {
                    const dist = Math.sqrt(Math.pow(item.pt.x - oa.cx, 2) + Math.pow(item.pt.y - oa.cy, 2));
                    let violation = false;
                    if (oa.id === '4') {
                        if (item.name === 'P1E') { if (dist >= oa.r) violation = true; }
                        else { if (dist <= oa.r) violation = true; }
                    } else { if (dist >= oa.r) violation = true; }

                    if (violation) {
                        // Cap the point causing violation (move inner arc p1/p3)
                        const sinVal = Math.sin(Math.atan2(item.pt.y - (item.name === 'P1E' ? p1.cy : p3.cy), item.pt.x - (item.name === 'P1E' ? p1.cx : p3.cx)));
                        if (Math.abs(sinVal) > 0.01) {
                            if (item.name === 'P1E') p1.cy = p1.cy; // Complex to resolve without feedback, but we must favor outer
                        }
                    }
                }
            });
        });

        // Center Height Constraints
        const hBuffer = 0.001;
        if (p3.cy <= p1.cy + hBuffer) p3.cy = p1.cy + hBuffer;
    }

    // --- Outer Chain Update ---
    if (movingSide === 'outer' || movingSide === null) {
        // Radius Synchronization: P4=P6 => R6=R4
        const epsilon = 0.001;
        if (Math.abs(p4.cx - p6.cx) < epsilon && Math.abs(p4.cy - p6.cy) < epsilon) {
            p6.r = p4.r;
        }

        // Thickness: P4S.y - P1S.y >= Tt; P3E.y - P6E.y >= Tb
        const p1s = getPointOnCircle(p1.cx, p1.cy, p1.r, p1.startAngle);
        const p3e = getPointOnCircle(p3.cx, p3.cy, p3.r, p3.endAngle);
        const sin4s = Math.sin(p4.startAngle * Math.PI / 180);
        const sin6e = Math.sin(p6.endAngle * Math.PI / 180);

        function applyOuterThickness() {
            const p4s_curr = getPointOnCircle(p4.cx, p4.cy, p4.r, p4.startAngle);
            if (p4s_curr.y - p1s.y < tt) {
                if (movingPoint === 'p4e' || movingPoint === null) {
                    p4.r = (p1s.y + tt - p4.cy) / sin4s;
                } else {
                    p4.cy = (p1s.y + tt) - (p4.r * sin4s);
                }
            }
            const p6e_curr = getPointOnCircle(p6.cx, p6.cy, p6.r, p6.endAngle);
            if (p3e.y - p6e_curr.y < tb) {
                p6.cy = p3e.y - tb - (p6.r * sin6e);
            }
        }

        applyOuterThickness();

        // Analytical Junction Solver (P5 tangent to Arc4 at P4E and tangent to Arc6)
        if (movingPoint === 'p4e') {
            const rayAngleRad = p4.endAngle * Math.PI / 180;
            const ux = Math.cos(rayAngleRad), uy = Math.sin(rayAngleRad);
            const vx = p6.cx - p4.cx, vy = p6.cy - p4.cy;
            const v2 = vx * vx + vy * vy;
            const dotUV = ux * vx + uy * vy;
            const D = p6.r - p4.r;
            const denom = 2 * (D + dotUV);
            if (Math.abs(denom) > 1e-6) {
                let d45 = (v2 - D * D) / denom;
                const maxD45 = p4.r - 0.001;
                if (d45 > maxD45) d45 = maxD45;
                p5.cx = p4.cx + d45 * ux;
                p5.cy = p4.cy + d45 * uy;
                p5.r = Math.max(0.0001, p4.r - d45);
            }
        }

        // Standard Tangency Chains
        if (movingPoint !== 'p4e') {
            let d45 = Math.sqrt(Math.pow(p5.cx - p4.cx, 2) + Math.pow(p5.cy - p4.cy, 2));
            if (d45 > p4.r) {
                const factor45 = (p4.r - 0.001) / d45;
                p5.cx = p4.cx + (p5.cx - p4.cx) * factor45;
                p5.cy = p4.cy + (p5.cy - p4.cy) * factor45;
                d45 = p4.r - 0.001;
            }
            p5.r = Math.max(0.0001, Math.abs(p4.r - d45));
            let d56 = Math.sqrt(Math.pow(p6.cx - p5.cx, 2) + Math.pow(p6.cy - p5.cy, 2));
            if (d56 > p6.r) d56 = Math.min(d56, p6.r);
            p6.r = p5.r + d56;

            p4.endAngle = Math.atan2(p5.cy - p4.cy, p5.cx - p4.cx) * 180 / Math.PI;
            while (p4.endAngle < p4.startAngle + 0.1) p4.endAngle += 360;
            while (p4.endAngle >= p4.startAngle + 360) p4.endAngle -= 360;
        }
        if (p4.endAngle > 269.8) p4.endAngle = 269.8;
        p5.startAngle = p4.endAngle;

        const p6_start_raw = Math.atan2(p5.cy - p6.cy, p5.cx - p6.cx) * 180 / Math.PI;
        let p6_start = (p6_start_raw + 360) % 360;
        while (p6_start < p5.startAngle + 0.1) p6_start += 360;
        while (p6_start >= p5.startAngle + 360) p6_start -= 360;
        if (p6_start > 269.9) p6_start = 269.9;
        p6.startAngle = p6_start;
        p5.endAngle = p6.startAngle;

        if (p5.endAngle - p5.startAngle < 0.1) p5.endAngle = p5.startAngle + 0.1;
        p6.endAngle = Math.min(270, Math.max(p6.startAngle + 0.1, p6.endAngle));

        // Center Height Constraints
        const hBuffer = 0.001;
        if (p6.cy <= p4.cy + hBuffer) p6.cy = p4.cy + hBuffer;
    }
}

function updateQuadCircleArcsConnectorGeometry(movingSide = null) {
    const p1 = quadCircleArcs[0];
    const p2 = quadCircleArcs[1];
    const p3 = quadCircleArcs[2];
    const p4 = quadCircleArcs[3];
    const p5 = quadCircleArcs[4];
    const p6 = quadCircleArcs[5];
    const p7 = quadCircleArcs[6];
    const p8 = quadCircleArcs[7];

    const tt = Math.max(0, parseFloat(document.getElementById('minThicknessTop')?.value || 0.3));
    const tb = Math.max(0, parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3));

    // Enforce axis constraints
    p1.cx = 0; p4.cx = 0; p5.cx = 0; p8.cx = 0;

    // --- Inner Chain Logic ---
    if (movingSide === 'inner' || movingSide === null) {
        function calcInner() {
            let d12 = Math.sqrt(Math.pow(p2.cx - p1.cx, 2) + Math.pow(p2.cy - p1.cy, 2));
            if (d12 > p1.r) {
                const factor = (p1.r - 0.001) / d12;
                p2.cx = p1.cx + (p2.cx - p1.cx) * factor;
                p2.cy = p1.cy + (p2.cy - p1.cy) * factor;
                d12 = p1.r - 0.001;
            }
            p2.r = Math.max(0.0001, Math.abs(p1.r - d12));
            p1.endAngle = Math.atan2(p2.cy - p1.cy, p2.cx - p1.cx) * 180 / Math.PI;
            while (p1.endAngle < p1.startAngle) p1.endAngle += 360;
            if (p1.endAngle > 270) p1.endAngle = 270;
            p2.startAngle = p1.endAngle;

            let d23 = Math.sqrt(Math.pow(p3.cx - p2.cx, 2) + Math.pow(p3.cy - p2.cy, 2));
            if (d23 > p2.r) {
                const factor = (p2.r - 0.001) / d23;
                p3.cx = p2.cx + (p3.cx - p2.cx) * factor;
                p3.cy = p2.cy + (p3.cy - p2.cy) * factor;
                d23 = p2.r - 0.001;
            }
            p3.r = Math.max(0.0001, Math.abs(p2.r - d23));
            p2.endAngle = Math.atan2(p3.cy - p2.cy, p3.cx - p2.cx) * 180 / Math.PI;
            while (p2.endAngle < p2.startAngle) p2.endAngle += 360;
            if (p2.endAngle > 270) p2.endAngle = 270;
            p3.startAngle = p2.endAngle;

            let d34 = Math.sqrt(Math.pow(p4.cx - p3.cx, 2) + Math.pow(p4.cy - p3.cy, 2));
            p4.r = Math.max(0.0001, p3.r + d34);
            p3.endAngle = Math.atan2(p3.cy - p4.cy, p3.cx - p4.cx) * 180 / Math.PI;
            while (p3.endAngle < p3.startAngle) p3.endAngle += 360;
            if (p3.endAngle > 270) p3.endAngle = 270;
            p4.startAngle = p3.endAngle;
            p4.endAngle = 270;
        }

        calcInner();

        // Thickness Capping for Inner (checks against fixed outer)
        const p5s = getPointOnCircle(p5.cx, p5.cy, p5.r, p5.startAngle);
        const p8e = getPointOnCircle(p8.cx, p8.cy, p8.r, p8.endAngle);
        let p1s = getPointOnCircle(p1.cx, p1.cy, p1.r, p1.startAngle);
        let p4e = getPointOnCircle(p4.cx, p4.cy, p4.r, p4.endAngle);

        let adjusted = false;
        if (p5s.y - p1s.y < tt) {
            if (movingPoint === 'p1s') {
                p1.r = (p5s.y - tt - p1.cy) / Math.sin(p1.startAngle * Math.PI / 180);
            } else {
                p1.cy = (p5s.y - tt) - (p1.r * Math.sin(p1.startAngle * Math.PI / 180));
            }
            adjusted = true;
        }
        if (p4e.y - p8e.y < tb) {
            p4.cy = (p8e.y + tb) - (p4.r * Math.sin(p4.endAngle * Math.PI / 180));
            adjusted = true;
        }
        if (adjusted) calcInner();
    }

    // --- Outer Chain Logic ---
    if (movingSide === 'outer' || movingSide === null) {
        function calcOuter() {
            let d56 = Math.sqrt(Math.pow(p6.cx - p5.cx, 2) + Math.pow(p6.cy - p5.cy, 2));
            if (d56 > p5.r) {
                const factor = (p5.r - 0.001) / d56;
                p6.cx = p5.cx + (p6.cx - p5.cx) * factor;
                p6.cy = p5.cy + (p6.cy - p5.cy) * factor;
                d56 = p5.r - 0.001;
            }
            p6.r = Math.max(0.0001, Math.abs(p5.r - d56));
            p5.endAngle = Math.atan2(p6.cy - p5.cy, p6.cx - p5.cx) * 180 / Math.PI;
            while (p5.endAngle < p5.startAngle) p5.endAngle += 360;
            if (p5.endAngle > 270) p5.endAngle = 270;
            p6.startAngle = p5.endAngle;

            let d67 = Math.sqrt(Math.pow(p7.cx - p6.cx, 2) + Math.pow(p7.cy - p6.cy, 2));
            if (d67 > p6.r) {
                const factor = (p6.r - 0.001) / d67;
                p7.cx = p6.cx + (p7.cx - p6.cx) * factor;
                p7.cy = p6.cy + (p7.cy - p6.cy) * factor;
                d67 = p6.r - 0.001;
            }
            p7.r = Math.max(0.0001, Math.abs(p6.r - d67));
            p6.endAngle = Math.atan2(p7.cy - p6.cy, p7.cx - p6.cx) * 180 / Math.PI;
            while (p6.endAngle < p6.startAngle) p6.endAngle += 360;
            if (p6.endAngle > 270) p6.endAngle = 270;
            p7.startAngle = p6.endAngle;

            let d78 = Math.sqrt(Math.pow(p8.cx - p7.cx, 2) + Math.pow(p8.cy - p7.cy, 2));
            p8.r = Math.max(0.0001, p7.r + d78);
            p7.endAngle = Math.atan2(p7.cy - p8.cy, p7.cx - p8.cx) * 180 / Math.PI;
            while (p7.endAngle < p7.startAngle) p7.endAngle += 360;
            if (p7.endAngle > 270) p7.endAngle = 270;
            p8.startAngle = p7.endAngle;
            p8.endAngle = 270;
        }

        calcOuter();

        const p1s = getPointOnCircle(p1.cx, p1.cy, p1.r, p1.startAngle);
        const p4e = getPointOnCircle(p4.cx, p4.cy, p4.r, p4.endAngle);
        let p5s = getPointOnCircle(p5.cx, p5.cy, p5.r, p5.startAngle);
        let p8e = getPointOnCircle(p8.cx, p8.cy, p8.r, p8.endAngle);

        let adjusted = false;
        if (p5s.y - p1s.y < tt) {
            if (movingPoint === 'p5s') {
                p5.r = (p1s.y + tt - p5.cy) / Math.sin(p5.startAngle * Math.PI / 180);
            } else {
                p5.cy = (p1s.y + tt) - (p5.r * Math.sin(p5.startAngle * Math.PI / 180));
            }
            adjusted = true;
        }
        if (p4e.y - p8e.y < tb) {
            p8.cy = (p4e.y - tb) - (p8.r * Math.sin(p8.endAngle * Math.PI / 180));
            adjusted = true;
        }
        if (adjusted) calcOuter();
    }

    [p1, p2, p3, p4, p5, p6, p7, p8].forEach(a => {
        if (a.endAngle < a.startAngle) a.endAngle = a.startAngle;
    });
}


/**
 * Recalculate side lines for Double-Circle mode based on arc centers and radii
 */
function updateDoubleCircleGeometry() {
    const inner = doubleCircleArcs.inner;
    const outer = doubleCircleArcs.outer;

    // Line 2: ps = P1E, pe = P3S
    inner.line2.ps = getPointOnCircle(inner.p1.cx, inner.p1.cy, inner.p1.r, inner.p1.endAngle);
    inner.line2.pe = getPointOnCircle(inner.p3.cx, inner.p3.cy, inner.p3.r, inner.p3.startAngle);

    // Line 5: ps = P4E, pe = P6S
    outer.line5.ps = getPointOnCircle(outer.p4.cx, outer.p4.cy, outer.p4.r, outer.p4.endAngle);
    outer.line5.pe = getPointOnCircle(outer.p6.cx, outer.p6.cy, outer.p6.r, outer.p6.startAngle);
}

/**
 * Helper to update only the calculated parts of the tangency chain 
 * without re-triggering the full constraint logic to avoid infinite loops.
 */
function updateConnectorTangencyOnly() {
    const p1 = tripleCircleArcs[0];
    const p2 = tripleCircleArcs[1];
    const p3 = tripleCircleArcs[2];
    const p4 = tripleCircleArcs[3];
    const p5 = tripleCircleArcs[4];
    const p6 = tripleCircleArcs[5];

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
    const id = `arrow - ${color.replace('#', '')} -rot${rotation} `;
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

function getOrCreateArrowMarker(color) {
    const canvas = document.getElementById('canvas');
    let defs = canvas.querySelector('defs');
    if (!defs) {
        defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        canvas.insertBefore(defs, canvas.firstChild);
    }
    const id = `arrow-${color.replace('#', '')}`;
    if (document.getElementById(id)) return id;

    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', id);
    marker.setAttribute('viewBox', '0 0 10 10');
    marker.setAttribute('refX', '5');
    marker.setAttribute('refY', '5');
    marker.setAttribute('markerWidth', '4');
    marker.setAttribute('markerHeight', '4');
    marker.setAttribute('orient', 'auto-start-reverse'); // Support double arrowheads

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
    path.setAttribute('fill', color);
    marker.appendChild(path);
    defs.appendChild(marker);
    return id;
}

function drawDimensionLine(container, p1, p2, labelPrefix, color, overlay) {
    const scale = getVisualScale();

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', p1.x.toFixed(4));
    line.setAttribute('y1', (-p1.y).toFixed(4));
    line.setAttribute('x2', p2.x.toFixed(4));
    line.setAttribute('y2', (-p2.y).toFixed(4));
    line.setAttribute('stroke', '#000000'); // Black
    line.setAttribute('stroke-width', (0.3 * scale).toFixed(4)); // Thin
    line.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`); // Dashed
    container.appendChild(line);

    const len = Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
    const midX = (p1.x + p2.x) / 2;
    const midY = (-p1.y - p2.y) / 2;

    // Label at midpoint, horizontal, left-aligned
    const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    t.setAttribute('x', (midX + 0.5 * scale).toFixed(4));
    t.setAttribute('y', midY.toFixed(4));
    t.setAttribute('font-size', (2.0 * scale).toFixed(4));
    t.setAttribute('fill', '#000000'); // Black
    t.setAttribute('text-anchor', 'start');
    t.setAttribute('dominant-baseline', 'middle');
    t.style.pointerEvents = 'none';
    t.textContent = `${labelPrefix}=${len.toFixed(4)}`;
    overlay.appendChild(t);
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

    // Branch on mode
    if (getCurrentMode() === 'circular') {
        drawCircularSystem(shapeGroup, circlesGroup, overlayGroup);
        updateInfoPanel();
        return;
    }
    if (getCurrentMode() === 'horseshoe') {
        drawHorseshoeSystem(shapeGroup, circlesGroup, overlayGroup);
        updateInfoPanel();
        return;
    }
    if (getCurrentMode() === 'double_circle') {
        drawDoubleCircleSystem(shapeGroup, circlesGroup, overlayGroup);
        updateInfoPanel();
        return;
    }
    if (getCurrentMode() === 'quad') {
        drawQuadCircleSystem(shapeGroup, circlesGroup, overlayGroup);
        updateInfoPanel();
        return;
    }

    // 0.5 Draw Intersection Fills (Bottom Layer)
    if (tripleCircleArcs.length >= 6) {
        const pairs = [[0, 3], [1, 4], [2, 5]];
        pairs.forEach(([i1, i2]) => {
            const arc1 = tripleCircleArcs[i1];
            const arc2 = tripleCircleArcs[i2];

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
    tripleCircleArcs.forEach((arc, index) => {
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

    // 5. Thickness Dimension Lines ($Tt, $Tb) for Triple-Circle
    if (tripleCircleArcs.length >= 6) {
        const arc1 = tripleCircleArcs[0];
        const arc4 = tripleCircleArcs[3];
        const arc3 = tripleCircleArcs[2];
        const arc6 = tripleCircleArcs[5];

        const p1s = getPointOnCircle(arc1.cx, arc1.cy, arc1.r, arc1.startAngle);
        const p4s = getPointOnCircle(arc4.cx, arc4.cy, arc4.r, arc4.startAngle);
        const p3e = getPointOnCircle(arc3.cx, arc3.cy, arc3.r, arc3.endAngle);
        const p6e = getPointOnCircle(arc6.cx, arc6.cy, arc6.r, arc6.endAngle);

        drawDimensionLine(overlayGroup, p1s, p4s, 'Tt', arc1.color, overlayGroup);
        drawDimensionLine(overlayGroup, p3e, p6e, 'Tb', arc3.color, overlayGroup);
    }
}

// ============================================================
// 正圓形 (Circular) Drawing System
// ============================================================
function drawCircularSystem(shapeGroup, circlesGroup, overlayGroup) {
    const scale = getVisualScale();
    const inner = circularArcs.inner;
    const outer = circularArcs.outer;

    // ---- Thickness constraints - Logic moved to onDrag for independence ----
    const tt = Math.max(0, parseFloat(document.getElementById('minThicknessTop')?.value || 0.50));
    const tb = Math.max(0, parseFloat(document.getElementById('minThicknessBottom')?.value || 0.50));

    // We no longer modify outer.r here to allow independent dragging.

    function svgTxtRotated(cx, cy, text, color, angleDeg, anchor = 'middle', baseline = 'middle') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', cx); t.setAttribute('y', cy);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color);
        t.setAttribute('text-anchor', anchor);
        t.setAttribute('dominant-baseline', baseline);
        let rot = angleDeg % 360;
        if (rot > 90 && rot < 270) rot -= 180;
        if (rot < -90 && rot > -270) rot += 180;
        t.setAttribute('transform', `rotate(${rot.toFixed(2)}, ${cx.toFixed(4)}, ${cy.toFixed(4)})`);
        t.style.pointerEvents = 'none';
        t.textContent = text;
        overlayGroup.appendChild(t);
        return t;
    }

    function svgTxt(x, y, text, color, anchor = 'start', baseline = 'auto') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', x); t.setAttribute('y', y);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color);
        t.setAttribute('text-anchor', anchor);
        t.setAttribute('dominant-baseline', baseline);
        t.style.pointerEvents = 'none';
        t.textContent = text;
        overlayGroup.appendChild(t);
        return t;
    }

    function drawDashedLine(x1, y1, x2, y2, color) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
        line.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
        line.style.pointerEvents = 'none';
        overlayGroup.appendChild(line);
    }

    const p1S = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.startAngle);
    const p1E = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
    const p2S = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.startAngle);
    const p2E = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);

    const p1SR = { x: -p1S.x, y: p1S.y };
    const p1ER = { x: -p1E.x, y: p1E.y };
    const p2SR = { x: -p2S.x, y: p2S.y };
    const p2ER = { x: -p2E.x, y: p2E.y };

    violatedPointIndices = [];
    envelopes.forEach((env, envIdx) => {
        violatedPointIndices[envIdx] = [];
        env.points.forEach((p, pIdx) => {
            const dx = p.x - inner.cx;
            const dy = p.y - inner.cy;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist > inner.r + 0.001) violatedPointIndices[envIdx].push(pIdx);
        });
    });

    const outerPathL = `M ${p2S.x.toFixed(4)} ${(-p2S.y).toFixed(4)} A ${outer.r.toFixed(4)} ${outer.r.toFixed(4)} 0 1 0 ${p2E.x.toFixed(4)} ${(-p2E.y).toFixed(4)} L ${p1E.x.toFixed(4)} ${(-p1E.y).toFixed(4)} A ${inner.r.toFixed(4)} ${inner.r.toFixed(4)} 0 1 1 ${p1S.x.toFixed(4)} ${(-p1S.y).toFixed(4)} Z`;
    const fillPathL = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    fillPathL.setAttribute('d', outerPathL); fillPathL.setAttribute('fill', 'lightyellow'); fillPathL.setAttribute('fill-opacity', '0.8');
    shapeGroup.appendChild(fillPathL);

    const outerPathR = `M ${p2SR.x.toFixed(4)} ${(-p2SR.y).toFixed(4)} A ${outer.r.toFixed(4)} ${outer.r.toFixed(4)} 0 1 1 ${p2ER.x.toFixed(4)} ${(-p2ER.y).toFixed(4)} L ${p1ER.x.toFixed(4)} ${(-p1ER.y).toFixed(4)} A ${inner.r.toFixed(4)} ${inner.r.toFixed(4)} 0 1 0 ${p1SR.x.toFixed(4)} ${(-p1SR.y).toFixed(4)} Z`;
    const fillPathR = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    fillPathR.setAttribute('d', outerPathR); fillPathR.setAttribute('fill', 'lightyellow'); fillPathR.setAttribute('fill-opacity', '0.8');
    shapeGroup.appendChild(fillPathR);

    envelopes.forEach((env, index) => {
        if (env.visible) drawPolygon(shapeGroup, env, index);
    });

    const arcPath1L = describeArc(inner.cx, -inner.cy, inner.r, inner.startAngle, inner.endAngle, '0');
    const path1L = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path1L.setAttribute('d', arcPath1L); path1L.setAttribute('fill', 'none'); path1L.setAttribute('stroke', inner.color); path1L.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    circlesGroup.appendChild(path1L);

    const arcPath1R = describeArc(-inner.cx, -inner.cy, inner.r, 180 - inner.startAngle, 180 - inner.endAngle, '1');
    const path1R = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path1R.setAttribute('d', arcPath1R); path1R.setAttribute('fill', 'none'); path1R.setAttribute('stroke', inner.color); path1R.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    circlesGroup.appendChild(path1R);

    const arcPath2L = describeArc(outer.cx, -outer.cy, outer.r, outer.startAngle, outer.endAngle, '0');
    const path2L = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path2L.setAttribute('d', arcPath2L); path2L.setAttribute('fill', 'none'); path2L.setAttribute('stroke', outer.color); path2L.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    circlesGroup.appendChild(path2L);

    const arcPath2R = describeArc(-outer.cx, -outer.cy, outer.r, 180 - outer.startAngle, 180 - outer.endAngle, '1');
    const path2R = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path2R.setAttribute('d', arcPath2R); path2R.setAttribute('fill', 'none'); path2R.setAttribute('stroke', outer.color); path2R.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    circlesGroup.appendChild(path2R);

    const handleSize = 1.5 * scale;

    const cHandle1 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    cHandle1.setAttribute('cx', inner.cx); cHandle1.setAttribute('cy', -inner.cy); cHandle1.setAttribute('r', (handleSize / 1.5).toFixed(4));
    cHandle1.setAttribute('fill', inner.color); cHandle1.setAttribute('class', 'interactive-handle'); cHandle1.style.cursor = 'move';
    cHandle1.setAttribute('title', 'P1');
    cHandle1.setAttribute('data-name', 'P1');
    cHandle1.addEventListener('mousedown', (e) => startDrag(e, 0, 'circularP1'));
    overlayGroup.appendChild(cHandle1);
    svgTxt(inner.cx + 1.5 * scale, -inner.cy - 1.5 * scale, `P1(${inner.cx.toFixed(4)}, ${inner.cy.toFixed(4)})`, inner.color);

    const sq1 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    sq1.setAttribute('x', (p1S.x - handleSize / 2).toFixed(4)); sq1.setAttribute('y', (-p1S.y - handleSize / 2).toFixed(4));
    sq1.setAttribute('width', handleSize); sq1.setAttribute('height', handleSize);
    sq1.setAttribute('fill', inner.color); sq1.setAttribute('class', 'interactive-handle'); sq1.style.cursor = 'ns-resize';
    sq1.setAttribute('title', 'P1S');
    sq1.setAttribute('data-name', 'P1S');
    sq1.addEventListener('mousedown', (e) => startDrag(e, 0, 'circularP1S'));
    overlayGroup.appendChild(sq1);
    renderArcEndpointLabel(overlayGroup, p1S, 'P1S', inner.startAngle, true, scale, inner.color);
    renderArcEndpointLabel(overlayGroup, p1E, 'P1E', inner.endAngle, true, scale, inner.color);

    drawDashedLine(inner.cx, -inner.cy, p1S.x, -p1S.y, inner.color);
    let lineAngle1;
    {
        const dx = p1S.x - inner.cx; const dy = (-p1S.y) - (-inner.cy);
        lineAngle1 = Math.atan2(dy, dx) * 180 / Math.PI;
        const mx = (inner.cx + p1S.x) / 2;
        const my = (-inner.cy - p1S.y) / 2;
        const offset = 2.0 * scale;
        // Left side perpendicular offset: (u.y, -u.x)
        const tx = mx + (dy / inner.r) * offset;
        const ty = my - (dx / inner.r) * offset;
        svgTxtRotated(tx, ty, `R1 = ${inner.r.toFixed(4)} `, inner.color, lineAngle1);
    }

    {
        const theta1 = Math.abs(inner.endAngle - inner.startAngle);
        const midAngle1 = (inner.startAngle + inner.endAngle) / 2;
        const pMid1 = getPointOnCircle(inner.cx, inner.cy, inner.r, midAngle1);
        const offset = -2.5 * scale;
        const tx = pMid1.x + offset * Math.cos(midAngle1 * Math.PI / 180);
        const ty = -pMid1.y - offset * Math.sin(midAngle1 * Math.PI / 180);
        svgTxtRotated(tx, ty, `θ1 = ${toDMS(theta1)} `, inner.color, 90 - midAngle1);
    }

    const cHandle2 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    cHandle2.setAttribute('cx', outer.cx); cHandle2.setAttribute('cy', -outer.cy); cHandle2.setAttribute('r', (handleSize / 1.5).toFixed(4));
    cHandle2.setAttribute('fill', outer.color); cHandle2.setAttribute('class', 'interactive-handle'); cHandle2.style.cursor = 'move';
    cHandle2.setAttribute('title', 'P2');
    cHandle2.setAttribute('data-name', 'P2');
    cHandle2.addEventListener('mousedown', (e) => startDrag(e, 1, 'circularP2'));
    overlayGroup.appendChild(cHandle2);
    svgTxt(outer.cx + 1.5 * scale, -outer.cy + 3.0 * scale, `P2(${outer.cx.toFixed(4)}, ${outer.cy.toFixed(4)})`, outer.color);

    const sq2 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    sq2.setAttribute('x', (p2S.x - handleSize / 2).toFixed(4)); sq2.setAttribute('y', (-p2S.y - handleSize / 2).toFixed(4));
    sq2.setAttribute('width', handleSize); sq2.setAttribute('height', handleSize);
    sq2.setAttribute('fill', outer.color); sq2.setAttribute('class', 'interactive-handle'); sq2.style.cursor = 'ns-resize';
    sq2.setAttribute('title', 'P2S');
    sq2.setAttribute('data-name', 'P2S');
    sq2.addEventListener('mousedown', (e) => startDrag(e, 1, 'circularP2S'));
    overlayGroup.appendChild(sq2);
    renderArcEndpointLabel(overlayGroup, p2S, 'P2S', outer.startAngle, false, scale, outer.color);
    renderArcEndpointLabel(overlayGroup, p2E, 'P2E', outer.endAngle, false, scale, outer.color);

    drawDashedLine(outer.cx, -outer.cy, p2S.x, -p2S.y, outer.color);
    {
        const dx = p2S.x - outer.cx; const dy = (-p2S.y) - (-outer.cy);
        const mx = (outer.cx + p2S.x) / 2;
        const my = (-outer.cy - p2S.y) / 2;
        const offset = 2.0 * scale;
        // Right side perpendicular offset: (-u.y, u.x)
        const tx = mx - (dy / outer.r) * offset;
        const ty = my + (dx / outer.r) * offset;
        // Rotation specifically follows P1-P1S as requested
        svgTxtRotated(tx, ty, `R2 = ${outer.r.toFixed(4)} `, outer.color, lineAngle1);
    }

    {
        const theta2 = Math.abs(outer.endAngle - outer.startAngle);
        const midAngle2 = (outer.startAngle + outer.endAngle) / 2;
        const pMid2 = getPointOnCircle(outer.cx, outer.cy, outer.r, midAngle2);
        const offset = 1.5 * scale;
        const tx = pMid2.x + offset * Math.cos(midAngle2 * Math.PI / 180);
        const ty = -pMid2.y - offset * Math.sin(midAngle2 * Math.PI / 180);
        svgTxtRotated(tx, ty, `θ2 = ${toDMS(theta2)} `, outer.color, 90 - midAngle2);
    }

    // --- Thickness Dimension Lines ($Tt, $Tb) ---
    drawDimensionLine(overlayGroup, p1S, p2S, 'Tt', inner.color, overlayGroup);
    drawDimensionLine(overlayGroup, p1E, p2E, 'Tb', inner.color, overlayGroup);
}

// ============================================================
// 馬蹄形 (Horseshoe) Drawing System
// ============================================================
function drawHorseshoeSystem(shapeGroup, circlesGroup, overlayGroup) {
    const scale = getVisualScale();
    const inner = horseshoeArcs.inner;
    const outer = horseshoeArcs.outer;

    function svgTxt(x, y, text, color, anchor = 'start', baseline = 'auto') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', x); t.setAttribute('y', y);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color); t.setAttribute('text-anchor', anchor); t.setAttribute('dominant-baseline', baseline);
        t.style.pointerEvents = 'none'; t.textContent = text;
        overlayGroup.appendChild(t);
        return t;
    }

    function svgTxtRotated(cx, cy, text, color, angleDeg, anchor = 'middle', baseline = 'middle') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', cx); t.setAttribute('y', cy);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color); t.setAttribute('text-anchor', anchor); t.setAttribute('dominant-baseline', baseline);
        let rot = angleDeg % 360;
        if (rot > 90 && rot < 270) rot -= 180;
        if (rot < -90 && rot > -270) rot += 180;
        t.setAttribute('transform', `rotate(${rot.toFixed(2)}, ${cx.toFixed(4)}, ${cy.toFixed(4)})`);
        t.style.pointerEvents = 'none'; t.textContent = text;
        overlayGroup.appendChild(t);
        return t;
    }

    function drawDashedLine(x1, y1, x2, y2, color) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        line.setAttribute('stroke', color); line.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
        line.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
        line.style.pointerEvents = 'none'; overlayGroup.appendChild(line);
    }

    const p1s = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.startAngle);
    const p1e = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
    const p2e = inner.p2e;
    const p3e = inner.p3e;

    const p4s = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.startAngle);
    const p4e = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);
    const p5e = outer.p5e;
    const p6e = outer.p6e;

    const p1sr = { x: -p1s.x, y: p1s.y }; const p1er = { x: -p1e.x, y: p1e.y };
    const p2er = { x: -p2e.x, y: p2e.y }; const p3er = { x: -p3e.x, y: p3e.y };
    const p4sr = { x: -p4s.x, y: p4s.y }; const p4er = { x: -p4e.x, y: p4e.y };
    const p5er = { x: -p5e.x, y: p5e.y }; const p6er = { x: -p6e.x, y: p6e.y };

    violatedPointIndices = [];
    envelopes.forEach((env, envIdx) => {
        violatedPointIndices[envIdx] = [];
        env.points.forEach((p, pIdx) => {
            let inside = true; const ax = Math.abs(p.x);
            if (p.y >= p1e.y) {
                if (Math.sqrt((ax - inner.cx) ** 2 + (p.y - inner.cy) ** 2) > inner.r + 0.001) inside = false;
            } else if (p.y >= p2e.y) {
                const tx = p1e.x + (p2e.x - p1e.x) * (p.y - p1e.y) / (p2e.y - p1e.y || 1e-6);
                if (ax > Math.abs(tx) + 0.001) inside = false;
            } else {
                if (p.y < p3e.y - 0.001) inside = false;
            }
            if (!inside) violatedPointIndices[envIdx].push(pIdx);
        });
    });



    const dFillArcL = `M ${p4s.x.toFixed(4)} ${(-p4s.y).toFixed(4)} A ${outer.r.toFixed(4)} ${outer.r.toFixed(4)} 0 0 0 ${p4e.x.toFixed(4)} ${(-p4e.y).toFixed(4)} L ${p1e.x.toFixed(4)} ${(-p1e.y).toFixed(4)} A ${inner.r.toFixed(4)} ${inner.r.toFixed(4)} 0 0 1 ${p1s.x.toFixed(4)} ${(-p1s.y).toFixed(4)} Z`;
    const dFillArcR = `M ${p4sr.x.toFixed(4)} ${(-p4sr.y).toFixed(4)} A ${outer.r.toFixed(4)} ${outer.r.toFixed(4)} 0 0 1 ${p4er.x.toFixed(4)} ${(-p4er.y).toFixed(4)} L ${p1er.x.toFixed(4)} ${(-p1er.y).toFixed(4)} A ${inner.r.toFixed(4)} ${inner.r.toFixed(4)} 0 0 0 ${p1sr.x.toFixed(4)} ${(-p1sr.y).toFixed(4)} Z`;
    const dFillDiagL = `M ${p4e.x.toFixed(4)} ${(-p4e.y).toFixed(4)} L ${p5e.x.toFixed(4)} ${(-p5e.y).toFixed(4)} L ${p2e.x.toFixed(4)} ${(-p2e.y).toFixed(4)} L ${p1e.x.toFixed(4)} ${(-p1e.y).toFixed(4)} Z`;
    const dFillDiagR = `M ${p4er.x.toFixed(4)} ${(-p4er.y).toFixed(4)} L ${p5er.x.toFixed(4)} ${(-p5er.y).toFixed(4)} L ${p2er.x.toFixed(4)} ${(-p2er.y).toFixed(4)} L ${p1er.x.toFixed(4)} ${(-p1er.y).toFixed(4)} Z`;
    const dFillBotL = `M ${p5e.x.toFixed(4)} ${(-p5e.y).toFixed(4)} L ${p6e.x.toFixed(4)} ${(-p6e.y).toFixed(4)} L ${p3e.x.toFixed(4)} ${(-p3e.y).toFixed(4)} L ${p2e.x.toFixed(4)} ${(-p2e.y).toFixed(4)} Z`;
    const dFillBotR = `M ${p5er.x.toFixed(4)} ${(-p5er.y).toFixed(4)} L ${p6er.x.toFixed(4)} ${(-p6er.y).toFixed(4)} L ${p3er.x.toFixed(4)} ${(-p3er.y).toFixed(4)} L ${p2er.x.toFixed(4)} ${(-p2er.y).toFixed(4)} Z`;

    [dFillArcL, dFillArcR, dFillDiagL, dFillDiagR, dFillBotL, dFillBotR].forEach(d => {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d); path.setAttribute('fill', 'lightyellow'); path.setAttribute('fill-opacity', '0.8');
        shapeGroup.appendChild(path);
    });

    envelopes.forEach((env, idx) => { if (env.visible) drawPolygon(shapeGroup, env, idx); });

    const color2 = '#28a745'; // Line 2L, 2R
    const color3 = '#007bff'; // Line 3L, 3R
    const color5 = '#1e7e34'; // Line 5L, 5R
    const color6 = '#0056b3'; // Line 6L, 6R

    function drawLine(x1, y1, x2, y2, color) {
        const l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        l.setAttribute('x1', x1.toFixed(4)); l.setAttribute('y1', (-y1).toFixed(4));
        l.setAttribute('x2', x2.toFixed(4)); l.setAttribute('y2', (-y2).toFixed(4));
        l.setAttribute('stroke', color); l.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
        circlesGroup.appendChild(l);
    }

    function drawSeg(d, color) {
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', d); p.setAttribute('fill', 'none'); p.setAttribute('stroke', color); p.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
        circlesGroup.appendChild(p);
    }
    // Inner
    drawSeg(describeArc(inner.cx, -inner.cy, inner.r, inner.startAngle, inner.endAngle, '0'), inner.color);
    drawSeg(describeArc(-inner.cx, -inner.cy, inner.r, 180 - inner.startAngle, 180 - inner.endAngle, '1'), inner.color);
    drawLine(p1e.x, p1e.y, p2e.x, p2e.y, color2); drawLine(p1er.x, p1er.y, p2er.x, p2er.y, color2);
    drawLine(p2e.x, p2e.y, p3e.x, p3e.y, color3); drawLine(p2er.x, p2er.y, p3er.x, p3er.y, color3);

    // Outer
    drawSeg(describeArc(outer.cx, -outer.cy, outer.r, outer.startAngle, outer.endAngle, '0'), outer.color);
    drawSeg(describeArc(-outer.cx, -outer.cy, outer.r, 180 - outer.startAngle, 180 - outer.endAngle, '1'), outer.color);
    drawLine(p4e.x, p4e.y, p5e.x, p5e.y, color5); drawLine(p4er.x, p4er.y, p5er.x, p5er.y, color5);
    drawLine(p5e.x, p5e.y, p6e.x, p6e.y, color6); drawLine(p5er.x, p5er.y, p6er.x, p6er.y, color6);

    const hsz = 1.5 * scale;
    const hP1 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    hP1.setAttribute('cx', inner.cx); hP1.setAttribute('cy', -inner.cy); hP1.setAttribute('r', (hsz / 1.5).toFixed(4));
    hP1.setAttribute('fill', inner.color); hP1.setAttribute('class', 'interactive-handle'); hP1.style.cursor = 'move';
    hP1.setAttribute('data-name', 'P1');
    hP1.addEventListener('mousedown', e => startDrag(e, 0, 'horseshoeP1')); overlayGroup.appendChild(hP1);
    svgTxt(inner.cx, -inner.cy - 1.5 * scale, `P1(${inner.cx.toFixed(4)}, ${inner.cy.toFixed(4)})`, inner.color, 'middle');

    [
        { pt: p1s, name: 'P1S', angle: inner.startAngle, isInner: true, type: 'horseshoeP1S', cursor: 'ns-resize', color: inner.color },
        { pt: p1e, name: 'P1E', angle: inner.endAngle, isInner: true, type: 'horseshoeP1E', cursor: 'move', color: inner.color },
        { pt: p4s, name: 'P4S', angle: outer.startAngle, isInner: false, type: 'horseshoeP4S', cursor: 'ns-resize', color: outer.color },
        { pt: p4e, name: 'P4E', angle: outer.endAngle, isInner: false, type: 'horseshoeP4E', cursor: 'move', color: outer.color }
    ].forEach(p => {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', p.pt.x - hsz / 2); rect.setAttribute('y', -p.pt.y - hsz / 2); rect.setAttribute('width', hsz); rect.setAttribute('height', hsz);
        rect.setAttribute('fill', p.color); rect.setAttribute('class', 'interactive-handle'); rect.style.cursor = p.cursor;
        rect.setAttribute('data-name', p.name);
        rect.addEventListener('mousedown', e => startDrag(e, 0, p.type)); overlayGroup.appendChild(rect);
        renderArcEndpointLabel(overlayGroup, p.pt, p.name, p.angle, p.isInner, scale, p.color);
    });

    [
        { x: p2e.x, y: p2e.y, name: 'P3S', type: 'horseshoeP3S', cursor: 'move', color: color3 }
    ].forEach(pt => {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', pt.x - hsz / 2); rect.setAttribute('y', -pt.y - hsz / 2); rect.setAttribute('width', hsz); rect.setAttribute('height', hsz);
        rect.setAttribute('fill', pt.color); rect.setAttribute('class', 'interactive-handle'); rect.style.cursor = pt.cursor;
        rect.setAttribute('data-name', pt.name);
        rect.addEventListener('mousedown', e => startDrag(e, 0, pt.type)); overlayGroup.appendChild(rect);
        svgTxt(pt.x + 1 * scale, -pt.y - 1 * scale, `${pt.name}(${pt.x.toFixed(4)}, ${pt.y.toFixed(4)})`, pt.color, 'start', 'alphabetic');
    });
    // P3E Label
    svgTxt(p3e.x + 1 * scale, -p3e.y - 1 * scale, `P3E(${p3e.x.toFixed(4)}, ${p3e.y.toFixed(4)})`, color3, 'start', 'alphabetic');

    const hP4 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    hP4.setAttribute('cx', outer.cx); hP4.setAttribute('cy', -outer.cy); hP4.setAttribute('r', (hsz / 1.5).toFixed(4));
    hP4.setAttribute('fill', outer.color); hP4.setAttribute('class', 'interactive-handle'); hP4.style.cursor = 'move';
    hP4.setAttribute('data-name', 'P4');
    hP4.addEventListener('mousedown', e => startDrag(e, 1, 'horseshoeP4')); overlayGroup.appendChild(hP4);
    svgTxt(outer.cx, -outer.cy - 1.5 * scale, `P4(${outer.cx.toFixed(4)}, ${outer.cy.toFixed(4)})`, outer.color, 'middle');

    [
        { x: p5e.x, y: p5e.y, name: 'P6S', type: 'horseshoeP6S', cursor: 'move', color: color6 }
    ].forEach(pt => {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', pt.x - hsz / 2); rect.setAttribute('y', -pt.y - hsz / 2); rect.setAttribute('width', hsz); rect.setAttribute('height', hsz);
        rect.setAttribute('fill', pt.color); rect.setAttribute('class', 'interactive-handle'); rect.style.cursor = pt.cursor;
        rect.setAttribute('data-name', pt.name);
        rect.addEventListener('mousedown', e => startDrag(e, 1, pt.type)); overlayGroup.appendChild(rect);

        // P6S: Below, Left-aligned
        svgTxt(pt.x + 1 * scale, -pt.y + 1 * scale, `${pt.name}(${pt.x.toFixed(4)}, ${pt.y.toFixed(4)})`, pt.color, 'start', 'hanging');
    });
    // P6E Label: Below, Left-aligned
    svgTxt(p6e.x + 1 * scale, -p6e.y + 1 * scale, `P6E(${p6e.x.toFixed(4)}, ${p6e.y.toFixed(4)})`, color6, 'start', 'hanging');

    drawDashedLine(inner.cx, -inner.cy, p1e.x, -p1e.y, inner.color);
    {
        const dx = p1e.x - inner.cx; const dy = -p1e.y - (-inner.cy);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        svgTxtRotated((inner.cx + p1e.x) / 2, (-inner.cy - p1e.y) / 2 - 1.5 * scale, `R1 = ${inner.r.toFixed(4)} `, inner.color, ang);
    }
    {
        const theta1 = Math.abs(inner.endAngle - inner.startAngle);
        const midAngle1 = (inner.startAngle + inner.endAngle) / 2;
        const pMid = getPointOnCircle(inner.cx, inner.cy, inner.r, midAngle1);
        const offset = -2.5 * scale;
        const tx = pMid.x + offset * Math.cos(midAngle1 * Math.PI / 180);
        const ty = -pMid.y - offset * Math.sin(midAngle1 * Math.PI / 180);
        svgTxtRotated(tx, ty, `θ1 = ${toDMS(theta1)} `, inner.color, 90 - midAngle1);
    }
    // L2 (Line 2L: p1e to p2e) - Diagonal, shifted right
    {
        const dx = p2e.x - p1e.x; const dy = -p2e.y - (-p1e.y);
        const len = Math.sqrt(dx * dx + dy * dy);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        // Perpendicular offset to the right: normal vector (dy/len, -dx/len)
        // Shifting "more": use 2.5 * scale total gap (baseline shift + coordinate shift)
        const dist = 1.0 * scale;
        const pMid = {
            x: (p1e.x + p2e.x) / 2 + (dy / len) * dist,
            y: (p1e.y + p2e.y) / 2 - (-dx / len) * dist
        };
        svgTxtRotated(pMid.x, -pMid.y, `L2 = ${len.toFixed(4)}`, color2, ang, 'middle', 'alphabetic');
    }
    // L3 (Line 3L: p2e to p3e) - Horizontal, below
    {
        const pMid = { x: (p2e.x + p3e.x) / 2, y: (p2e.y + p3e.y) / 2 };
        const len = Math.sqrt((p3e.x - p2e.x) ** 2 + (p3e.y - p2e.y) ** 2);
        // Below, shift "less": 1.0 * scale
        svgTxt(pMid.x, -pMid.y + 0.8 * scale, `L3 = ${len.toFixed(4)}`, color3, 'middle', 'hanging');
    }

    drawDashedLine(outer.cx, -outer.cy, p4e.x, -p4e.y, outer.color);
    {
        const dx = p4e.x - outer.cx; const dy = -p4e.y - (-outer.cy);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        svgTxtRotated((outer.cx + p4e.x) / 2, (-outer.cy - p4e.y) / 2 + 1.5 * scale, `R4 = ${outer.r.toFixed(4)} `, outer.color, ang);
    }
    {
        const theta4 = Math.abs(outer.endAngle - outer.startAngle);
        const midAngle4 = (outer.startAngle + outer.endAngle) / 2;
        const pMid = getPointOnCircle(outer.cx, outer.cy, outer.r, midAngle4);
        const offset = 1.5 * scale;
        const tx = pMid.x + offset * Math.cos(midAngle4 * Math.PI / 180);
        const ty = -pMid.y - offset * Math.sin(midAngle4 * Math.PI / 180);
        svgTxtRotated(tx, ty, `θ4 = ${toDMS(theta4)} `, outer.color, 90 - midAngle4);
    }
    // L5 (Line 5L: p4e to p5e) - Diagonal, shifted left
    {
        const dx = p5e.x - p4e.x; const dy = -p5e.y - (-p4e.y);
        const len = Math.sqrt(dx * dx + dy * dy);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        // Perpendicular offset to the left
        const dist = 1.0 * scale;
        const pMid = {
            x: (p4e.x + p5e.x) / 2 - (dy / len) * dist,
            y: (p4e.y + p5e.y) / 2 + (-dx / len) * dist
        };
        svgTxtRotated(pMid.x, -pMid.y, `L5 = ${len.toFixed(4)}`, color5, ang, 'middle', 'hanging');
    }
    // L6 (Line 6L: p5e to p6e) - Horizontal, above
    {
        const pMid = { x: (p5e.x + p6e.x) / 2, y: (p5e.y + p6e.y) / 2 };
        const len = Math.sqrt((p6e.x - p5e.x) ** 2 + (p6e.y - p5e.y) ** 2);
        // Above, shift "less": -1.0 * scale
        svgTxt(pMid.x, -pMid.y - 0.8 * scale, `L6 = ${len.toFixed(4)}`, color6, 'middle', 'alphabetic');
    }

    // --- Thickness Dimension Lines ($Tt, $Tb) ---
    drawDimensionLine(overlayGroup, p1s, p4s, 'Tt', inner.color, overlayGroup);
    drawDimensionLine(overlayGroup, p3e, p6e, 'Tb', inner.color, overlayGroup);
}

// ============================================================
// 雙心圓 (Double-Circle) Drawing System
// ============================================================
function drawDoubleCircleSystem(shapeGroup, circlesGroup, overlayGroup) {
    const scale = getVisualScale();
    const inner = doubleCircleArcs.inner;
    const outer = doubleCircleArcs.outer;

    function svgTxt(x, y, text, color, anchor = 'start', baseline = 'auto') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', x); t.setAttribute('y', y);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color); t.setAttribute('text-anchor', anchor); t.setAttribute('dominant-baseline', baseline);
        t.style.pointerEvents = 'none'; t.textContent = text;
        overlayGroup.appendChild(t);
        return t;
    }

    function svgTxtRotated(cx, cy, text, color, angleDeg, anchor = 'middle', baseline = 'middle') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', cx); t.setAttribute('y', cy);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color); t.setAttribute('text-anchor', anchor); t.setAttribute('dominant-baseline', baseline);
        let rot = angleDeg % 360;
        if (rot > 90 && rot < 270) rot -= 180;
        if (rot < -90 && rot > -270) rot += 180;
        t.setAttribute('transform', `rotate(${rot.toFixed(2)}, ${cx.toFixed(4)}, ${cy.toFixed(4)})`);
        t.style.pointerEvents = 'none'; t.textContent = text;
        overlayGroup.appendChild(t);
        return t;
    }

    function drawDashedLine(x1, y1, x2, y2, color) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        line.setAttribute('stroke', color); line.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
        line.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
        line.style.pointerEvents = 'none'; overlayGroup.appendChild(line);
    }

    // Points
    const p1s_pt = getPointOnCircle(inner.p1.cx, inner.p1.cy, inner.p1.r, inner.p1.startAngle);
    const p1e_pt = getPointOnCircle(inner.p1.cx, inner.p1.cy, inner.p1.r, inner.p1.endAngle);
    const p3s_pt = getPointOnCircle(inner.p3.cx, inner.p3.cy, inner.p3.r, inner.p3.startAngle);
    const p3e_pt = getPointOnCircle(inner.p3.cx, inner.p3.cy, inner.p3.r, inner.p3.endAngle);

    const p4s_pt = getPointOnCircle(outer.p4.cx, outer.p4.cy, outer.p4.r, outer.p4.startAngle);
    const p4e_pt = getPointOnCircle(outer.p4.cx, outer.p4.cy, outer.p4.r, outer.p4.endAngle);
    const p6s_pt = getPointOnCircle(outer.p6.cx, outer.p6.cy, outer.p6.r, outer.p6.startAngle);
    const p6e_pt = getPointOnCircle(outer.p6.cx, outer.p6.cy, outer.p6.r, outer.p6.endAngle);

    // Mirrors
    const p1sr_pt = { x: -p1s_pt.x, y: p1s_pt.y };
    const p1er_pt = { x: -p1e_pt.x, y: p1e_pt.y };
    const p3sr_pt = { x: -p3s_pt.x, y: p3s_pt.y };
    const p3er_pt = { x: -p3e_pt.x, y: p3e_pt.y };
    const p4sr_pt = { x: -p4s_pt.x, y: p4s_pt.y };
    const p4er_pt = { x: -p4e_pt.x, y: p4e_pt.y };
    const p6sr_pt = { x: -p6s_pt.x, y: p6s_pt.y };
    const p6er_pt = { x: -p6e_pt.x, y: p6e_pt.y };

    // Intersection NG check
    violatedPointIndices = [];
    envelopes.forEach((env, envIdx) => {
        violatedPointIndices[envIdx] = [];
        env.points.forEach((p, pIdx) => {
            let inside = true; const ax = Math.abs(p.x);
            if (p.y >= p1e_pt.y) {
                if (Math.sqrt((ax - inner.p1.cx) ** 2 + (p.y - inner.p1.cy) ** 2) > inner.p1.r + 0.001) inside = false;
            } else if (p.y >= p3s_pt.y) {
                if (ax > Math.abs(inner.line2.ps.x) + 0.001) inside = false;
            } else {
                if (Math.sqrt((ax - inner.p3.cx) ** 2 + (p.y - inner.p3.cy) ** 2) > inner.p3.r + 0.001) inside = false;
            }
            if (!inside) violatedPointIndices[envIdx].push(pIdx);
        });
    });

    // Fills
    const dFill14 = `M ${p4s_pt.x.toFixed(4)} ${(-p4s_pt.y).toFixed(4)} A ${outer.p4.r.toFixed(4)} ${outer.p4.r.toFixed(4)} 0 0 0 ${p4e_pt.x.toFixed(4)} ${(-p4e_pt.y).toFixed(4)} L ${p1e_pt.x.toFixed(4)} ${(-p1e_pt.y).toFixed(4)} A ${inner.p1.r.toFixed(4)} ${inner.p1.r.toFixed(4)} 0 0 1 ${p1s_pt.x.toFixed(4)} ${(-p1s_pt.y).toFixed(4)} Z`;
    const dFill14R = `M ${p4sr_pt.x.toFixed(4)} ${(-p4sr_pt.y).toFixed(4)} A ${outer.p4.r.toFixed(4)} ${outer.p4.r.toFixed(4)} 0 0 1 ${p4er_pt.x.toFixed(4)} ${(-p4er_pt.y).toFixed(4)} L ${p1er_pt.x.toFixed(4)} ${(-p1er_pt.y).toFixed(4)} A ${inner.p1.r.toFixed(4)} ${inner.p1.r.toFixed(4)} 0 0 0 ${p1sr_pt.x.toFixed(4)} ${(-p1sr_pt.y).toFixed(4)} Z`;
    const dFill25 = `M ${outer.line5.ps.x.toFixed(4)} ${(-outer.line5.ps.y).toFixed(4)} L ${outer.line5.pe.x.toFixed(4)} ${(-outer.line5.pe.y).toFixed(4)} L ${inner.line2.pe.x.toFixed(4)} ${(-inner.line2.pe.y).toFixed(4)} L ${inner.line2.ps.x.toFixed(4)} ${(-inner.line2.ps.y).toFixed(4)} Z`;
    const dFill25R = `M ${(-outer.line5.ps.x).toFixed(4)} ${(-outer.line5.ps.y).toFixed(4)} L ${(-outer.line5.pe.x).toFixed(4)} ${(-outer.line5.pe.y).toFixed(4)} L ${(-inner.line2.pe.x).toFixed(4)} ${(-inner.line2.pe.y).toFixed(4)} L ${(-inner.line2.ps.x).toFixed(4)} ${(-inner.line2.ps.y).toFixed(4)} Z`;
    const dFill36 = `M ${p6s_pt.x.toFixed(4)} ${(-p6s_pt.y).toFixed(4)} A ${outer.p6.r.toFixed(4)} ${outer.p6.r.toFixed(4)} 0 0 0 ${p6e_pt.x.toFixed(4)} ${(-p6e_pt.y).toFixed(4)} L ${p3e_pt.x.toFixed(4)} ${(-p3e_pt.y).toFixed(4)} A ${inner.p3.r.toFixed(4)} ${inner.p3.r.toFixed(4)} 0 0 1 ${p3s_pt.x.toFixed(4)} ${(-p3s_pt.y).toFixed(4)} Z`;
    const dFill36R = `M ${p6sr_pt.x.toFixed(4)} ${(-p6sr_pt.y).toFixed(4)} A ${outer.p6.r.toFixed(4)} ${outer.p6.r.toFixed(4)} 0 0 1 ${p6er_pt.x.toFixed(4)} ${(-p6er_pt.y).toFixed(4)} L ${p3er_pt.x.toFixed(4)} ${(-p3er_pt.y).toFixed(4)} A ${inner.p3.r.toFixed(4)} ${inner.p3.r.toFixed(4)} 0 0 0 ${p3sr_pt.x.toFixed(4)} ${(-p3sr_pt.y).toFixed(4)} Z`;

    [dFill14, dFill14R, dFill25, dFill25R, dFill36, dFill36R].forEach(d => {
        if (!d) return;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d); path.setAttribute('fill', 'lightyellow'); path.setAttribute('fill-opacity', '0.8');
        shapeGroup.appendChild(path);
    });

    envelopes.forEach((env, idx) => { if (env.visible) drawPolygon(shapeGroup, env, idx); });

    function drawLine(ps, pe, color) {
        const l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        l.setAttribute('x1', ps.x.toFixed(4)); l.setAttribute('y1', (-ps.y).toFixed(4));
        l.setAttribute('x2', pe.x.toFixed(4)); l.setAttribute('y2', (-pe.y).toFixed(4));
        l.setAttribute('stroke', color); l.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
        circlesGroup.appendChild(l);
    }
    function drawArcSeg(arc, isMirror) {
        const d = describeArc(arc.cx, -arc.cy, arc.r, arc.startAngle, arc.endAngle, isMirror ? '1' : '0');
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        if (isMirror) {
            const dMirror = describeArc(-arc.cx, -arc.cy, arc.r, 180 - arc.startAngle, 180 - arc.endAngle, '1');
            p.setAttribute('d', dMirror);
        } else {
            p.setAttribute('d', d);
        }
        p.setAttribute('fill', 'none'); p.setAttribute('stroke', arc.color); p.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
        circlesGroup.appendChild(p);
    }

    // Inner
    drawArcSeg(inner.p1, false); drawArcSeg(inner.p1, true);
    drawLine(inner.line2.ps, inner.line2.pe, inner.line2.color);
    drawLine({ x: -inner.line2.ps.x, y: inner.line2.ps.y }, { x: -inner.line2.pe.x, y: inner.line2.pe.y }, inner.line2.color);
    drawArcSeg(inner.p3, false); drawArcSeg(inner.p3, true);

    // Outer
    drawArcSeg(outer.p4, false); drawArcSeg(outer.p4, true);
    drawLine(outer.line5.ps, outer.line5.pe, outer.line5.color);
    drawLine({ x: -outer.line5.ps.x, y: outer.line5.ps.y }, { x: -outer.line5.pe.x, y: outer.line5.pe.y }, outer.line5.color);
    drawArcSeg(outer.p6, false); drawArcSeg(outer.p6, true);

    const hsz = 1.5 * scale;
    // P1, P3, P4, P6 (Circles)
    const centers = [
        { pt: { x: inner.p1.cx, y: inner.p1.cy }, color: inner.p1.color, name: 'P1', type: 'doubleCircleP1', labelDir: 'TR' },
        { pt: { x: inner.p3.cx, y: inner.p3.cy }, color: inner.p3.color, name: 'P3', type: 'doubleCircleP3', labelDir: 'TR' },
        { pt: { x: outer.p4.cx, y: outer.p4.cy }, color: outer.p4.color, name: 'P4', type: 'doubleCircleP4', labelDir: 'BR' },
        { pt: { x: outer.p6.cx, y: outer.p6.cy }, color: outer.p6.color, name: 'P6', type: 'doubleCircleP6', labelDir: 'BR' }
    ];
    centers.forEach(c => {
        const circ = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circ.setAttribute('cx', c.pt.x); circ.setAttribute('cy', -c.pt.y); circ.setAttribute('r', (hsz / 1.5).toFixed(4));
        circ.setAttribute('fill', c.color); circ.setAttribute('class', 'interactive-handle'); circ.style.cursor = 'move';
        circ.setAttribute('data-name', c.name);
        circ.addEventListener('mousedown', e => startDrag(e, 0, c.type)); overlayGroup.appendChild(circ);
        const yOff = c.labelDir === 'TR' ? -1.5 * scale : 3 * scale;
        svgTxt(c.pt.x + 1.5 * scale, -c.pt.y + yOff, `${c.name}(${c.pt.x.toFixed(4)},${c.pt.y.toFixed(4)})`, c.color);
    });

    // P1S, P1E, P3S, P3E etc (Rects)
    const rects = [
        { pt: p1s_pt, name: 'P1S', angle: inner.p1.startAngle, isInner: true, type: 'doubleCircleP1S', cursor: 'ns-resize', color: inner.p1.color },
        { pt: p1e_pt, name: 'P1E', angle: inner.p1.endAngle, isInner: true, type: 'doubleCircleP1E', cursor: 'move', color: inner.p1.color },
        { pt: p3s_pt, name: 'P3S', angle: inner.p3.startAngle, isInner: true, type: 'doubleCircleP3S', cursor: 'move', color: inner.p3.color },
        { pt: p3e_pt, name: 'P3E', angle: inner.p3.endAngle, isInner: true, type: 'doubleCircleP3E', cursor: 'ns-resize', color: inner.p3.color },
        { pt: p4s_pt, name: 'P4S', angle: outer.p4.startAngle, isInner: false, type: 'doubleCircleP4S', cursor: 'ns-resize', color: outer.p4.color },
        { pt: p4e_pt, name: 'P4E', angle: outer.p4.endAngle, isInner: false, type: 'doubleCircleP4E', cursor: 'move', color: outer.p4.color },
        { pt: p6s_pt, name: 'P6S', angle: outer.p6.startAngle, isInner: false, type: 'doubleCircleP6S', cursor: 'move', color: outer.p6.color },
        { pt: p6e_pt, name: 'P6E', angle: outer.p6.endAngle, isInner: false, type: 'doubleCircleP6E', cursor: 'ns-resize', color: outer.p6.color }
    ];
    rects.forEach(r => {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', r.pt.x - hsz / 2); rect.setAttribute('y', -r.pt.y - hsz / 2); rect.setAttribute('width', hsz); rect.setAttribute('height', hsz);
        rect.setAttribute('fill', r.color); rect.setAttribute('class', 'interactive-handle'); rect.style.cursor = r.cursor;
        rect.setAttribute('data-name', r.name);
        rect.addEventListener('mousedown', e => startDrag(e, 0, r.type)); overlayGroup.appendChild(rect);
        renderArcEndpointLabel(overlayGroup, r.pt, r.name, r.angle, r.isInner, scale, r.color);
    });

    // Dashed lines and Radius labels
    const dashed = [
        { p1: { x: inner.p1.cx, y: inner.p1.cy }, p2: p1e_pt, color: inner.p1.color, name: 'R1', side: 'top', r: inner.p1.r },
        { p1: { x: inner.p3.cx, y: inner.p3.cy }, p2: p3s_pt, color: inner.p3.color, name: 'R3', side: 'top', r: inner.p3.r },
        { p1: { x: outer.p4.cx, y: outer.p4.cy }, p2: p4e_pt, color: outer.p4.color, name: 'R4', side: 'bot', r: outer.p4.r },
        { p1: { x: outer.p6.cx, y: outer.p6.cy }, p2: p6s_pt, color: outer.p6.color, name: 'R6', side: 'bot', r: outer.p6.r }
    ];
    dashed.forEach(d => {
        drawDashedLine(d.p1.x, -d.p1.y, d.p2.x, -d.p2.y, d.color);
        const dx = d.p2.x - d.p1.x; const dy = -d.p2.y - (-d.p1.y);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        const yOff = d.side === 'top' ? -1.5 * scale : 2 * scale;
        svgTxtRotated((d.p1.x + d.p2.x) / 2, (-d.p1.y - d.p2.y) / 2 + yOff, `${d.name}=${d.r.toFixed(4)}`, d.color, ang);
    });

    // Angle labels
    const angles = [
        { arc: inner.p1, name: 'θ1' }, { arc: inner.p3, name: 'θ3' },
        { arc: outer.p4, name: 'θ4' }, { arc: outer.p6, name: 'θ6' }
    ];
    angles.forEach(a => {
        const theta = Math.abs(a.arc.endAngle - a.arc.startAngle);
        const midA = (a.arc.startAngle + a.arc.endAngle) / 2;
        const pMid = getPointOnCircle(a.arc.cx, a.arc.cy, a.arc.r, midA);
        // θ1, θ3 are inner arcs (inner array has .p1, .p3)
        const isInner = a.name === 'θ1' || a.name === 'θ3';
        const offset = isInner ? -2.5 * scale : 1.5 * scale;
        const tx = pMid.x + offset * Math.cos(midA * Math.PI / 180);
        const ty = -pMid.y - offset * Math.sin(midA * Math.PI / 180);
        svgTxtRotated(tx, ty, `${a.name}=${toDMS(theta)}`, a.arc.color, 90 - midA);
    });
    // L2 (Line 2L: p1e to p3s)
    {
        const dx = inner.line2.pe.x - inner.line2.ps.x; const dy = -inner.line2.pe.y - (-inner.line2.ps.y);
        const len = Math.sqrt(dx * dx + dy * dy);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        // Perpendicular offset to the right
        const dist = 1.0 * scale;
        const pMid = {
            x: (inner.line2.ps.x + inner.line2.pe.x) / 2 + (dy / len) * dist,
            y: (inner.line2.ps.y + inner.line2.pe.y) / 2 - (-dx / len) * dist
        };
        svgTxtRotated(pMid.x, -pMid.y, `L2 = ${len.toFixed(4)}`, inner.line2.color, ang, 'middle', 'alphabetic');
    }
    // L5 (Line 5L: p4e to p6s) - Diagonal, shifted left
    {
        const dx = outer.line5.pe.x - outer.line5.ps.x; const dy = -outer.line5.pe.y - (-outer.line5.ps.y);
        const len = Math.sqrt(dx * dx + dy * dy);
        const ang = Math.atan2(dy, dx) * 180 / Math.PI;
        // Perpendicular offset to the left
        const dist = 1.0 * scale;
        const pMid = {
            x: (outer.line5.ps.x + outer.line5.pe.x) / 2 - (dy / len) * dist,
            y: (outer.line5.ps.y + outer.line5.pe.y) / 2 + (-dx / len) * dist
        };
        svgTxtRotated(pMid.x, -pMid.y, `L5 = ${len.toFixed(4)}`, outer.line5.color, ang, 'middle', 'hanging');
    }

    // --- Thickness Dimension Lines ($Tt, $Tb) ---
    drawDimensionLine(overlayGroup, p1s_pt, p4s_pt, 'Tt', inner.p1.color, overlayGroup);
    drawDimensionLine(overlayGroup, p3e_pt, p6e_pt, 'Tb', inner.p3.color, overlayGroup);
}

function drawArcDiffFillPath(arc1, arc2, isMirror) {
    const p1s = getPointOnCircle(arc1.cx, arc1.cy, arc1.r, arc1.startAngle);
    const p1e = getPointOnCircle(arc1.cx, arc1.cy, arc1.r, arc1.endAngle);
    const p2s = getPointOnCircle(arc2.cx, arc2.cy, arc2.r, arc2.startAngle);
    const p2e = getPointOnCircle(arc2.cx, arc2.cy, arc2.r, arc2.endAngle);

    const arc1Large = Math.abs(arc1.endAngle - arc1.startAngle) > 180 ? "1" : "0";
    const arc2Large = Math.abs(arc2.endAngle - arc2.startAngle) > 180 ? "1" : "0";

    if (isMirror) {
        const p1sr = { x: -p1s.x, y: p1s.y }; const p1er = { x: -p1e.x, y: p1e.y };
        const p2sr = { x: -p2s.x, y: p2s.y }; const p2er = { x: -p2e.x, y: p2e.y };
        return `M ${p2er.x.toFixed(4)} ${(-p2er.y).toFixed(4)} A ${arc2.r.toFixed(4)} ${arc2.r.toFixed(4)} 0 ${arc2Large} 1 ${p2sr.x.toFixed(4)} ${(-p2sr.y).toFixed(4)} L ${p1sr.x.toFixed(4)} ${(-p1sr.y).toFixed(4)} A ${arc1.r.toFixed(4)} ${arc1.r.toFixed(4)} 0 ${arc1Large} 0 ${p1er.x.toFixed(4)} ${(-p1er.y).toFixed(4)} Z`;
    }
    return `M ${p2s.x.toFixed(4)} ${(-p2s.y).toFixed(4)} A ${arc2.r.toFixed(4)} ${arc2.r.toFixed(4)} 0 ${arc2Large} 0 ${p2e.x.toFixed(4)} ${(-p2e.y).toFixed(4)} L ${p1e.x.toFixed(4)} ${(-p1e.y).toFixed(4)} A ${arc1.r.toFixed(4)} ${arc1.r.toFixed(4)} 0 ${arc1Large} 1 ${p1s.x.toFixed(4)} ${(-p1s.y).toFixed(4)} Z`;
}


// ============================================================
// 四心圓 (Quad-Circle) Drawing System
// ============================================================
function drawQuadCircleSystem(shapeGroup, circlesGroup, overlayGroup) {
    const scale = getVisualScale();

    // Helper: SVG text
    function svgTxt(x, y, text, color, anchor = 'start', baseline = 'auto') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', x); t.setAttribute('y', y);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color);
        t.setAttribute('text-anchor', anchor);
        t.setAttribute('dominant-baseline', baseline);
        t.style.pointerEvents = 'none';
        t.textContent = text;
        return t;
    }

    // Helper: SVG rotated text
    function svgTxtRotated(cx, cy, text, color, angleDeg, anchor = 'middle', baseline = 'middle') {
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', cx); t.setAttribute('y', cy);
        t.setAttribute('font-size', (2.0 * scale).toFixed(4));
        t.setAttribute('fill', color);
        t.setAttribute('text-anchor', anchor);
        t.setAttribute('dominant-baseline', baseline);
        t.setAttribute('transform', `rotate(${angleDeg.toFixed(1)}, ${cx.toFixed(4)}, ${cy.toFixed(4)})`);
        t.style.pointerEvents = 'none';
        t.textContent = text;
        return t;
    }

    // Helper: Dashed line
    function drawDashedLine(x1, y1, x2, y2, color) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
        line.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)}`);
        return line;
    }

    // Helper: Draw a single arc path
    function drawArcSeg(arc, isMirror) {
        const cx = isMirror ? -arc.cx : arc.cx;
        const sa = isMirror ? 180 - arc.startAngle : arc.startAngle;
        const ea = isMirror ? 180 - arc.endAngle : arc.endAngle;
        const d = describeArc(cx, -arc.cy, arc.r, sa, ea, isMirror ? "1" : "0");
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', arc.color);
        path.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
        circlesGroup.appendChild(path);
    }

    // Helper: Draw arc-diff fill between outer and inner arc pair
    function drawQuadArcDiffFill(innerArc, outerArc, isMirror) {
        const icx = isMirror ? -innerArc.cx : innerArc.cx;
        const isa = isMirror ? 180 - innerArc.startAngle : innerArc.startAngle;
        const iea = isMirror ? 180 - innerArc.endAngle : innerArc.endAngle;
        const ocx = isMirror ? -outerArc.cx : outerArc.cx;
        const osa = isMirror ? 180 - outerArc.startAngle : outerArc.startAngle;
        const oea = isMirror ? 180 - outerArc.endAngle : outerArc.endAngle;
        const sweepOuter = isMirror ? "1" : "0";
        const sweepInner = isMirror ? "0" : "1";

        const oS = getPointOnCircle(ocx, outerArc.cy, outerArc.r, osa);
        const oE = getPointOnCircle(ocx, outerArc.cy, outerArc.r, oea);
        const iS = getPointOnCircle(icx, innerArc.cy, innerArc.r, isa);
        const iE = getPointOnCircle(icx, innerArc.cy, innerArc.r, iea);

        const outerDiff = Math.abs(oea - osa);
        const innerDiff = Math.abs(iea - isa);
        const outerLargeArc = outerDiff > 180 ? "1" : "0";
        const innerLargeArc = innerDiff > 180 ? "1" : "0";

        const d = [
            "M", oS.x, -oS.y,
            "A", outerArc.r, outerArc.r, 0, outerLargeArc, sweepOuter, oE.x, -oE.y,
            "L", iE.x, -iE.y,
            "A", innerArc.r, innerArc.r, 0, innerLargeArc, sweepInner, iS.x, -iS.y,
            "Z"
        ].join(" ");

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('fill', 'lightyellow');
        path.setAttribute('fill-opacity', '0.8');
        path.setAttribute('stroke', 'none');
        shapeGroup.appendChild(path);
    }

    // ==== 0. Draw Fills (Bottom Layer) ====
    const fillPairs = [[0, 4], [1, 5], [2, 6], [3, 7]]; // inner→outer pairs
    fillPairs.forEach(([iIdx, oIdx]) => {
        drawQuadArcDiffFill(quadCircleArcs[iIdx], quadCircleArcs[oIdx], false);
        drawQuadArcDiffFill(quadCircleArcs[iIdx], quadCircleArcs[oIdx], true);
    });

    // ==== 1. Draw Envelopes ====
    envelopes.forEach((env, index) => {
        if (env.visible) drawPolygon(shapeGroup, env, index);
    });

    // ==== 2. Draw All Arcs (Left + Right Mirror) ====
    quadCircleArcs.forEach((arc) => {
        drawArcSeg(arc, false);
        drawArcSeg(arc, true);
    });

    // ==== 3. Draw Control Points, Labels, Dashed Lines, Radius/Angle Labels ====
    const handleSize = 1.5 * scale;

    quadCircleArcs.forEach((arc, index) => {
        const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
        const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);

        // --- Center Handle (Solid Circle ●) ---
        const cHandle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        cHandle.setAttribute('cx', arc.cx);
        cHandle.setAttribute('cy', -arc.cy);
        cHandle.setAttribute('r', handleSize / 1.5);
        cHandle.setAttribute('fill', arc.color);
        cHandle.setAttribute('class', 'interactive-handle');
        cHandle.style.cursor = 'move';
        cHandle.setAttribute('data-name', `P${index + 1}`);
        bindDrag(cHandle, index, 'quadCenter');
        circlesGroup.appendChild(cHandle);

        // --- Center Label ---
        // P1-P4: upper-right; P5-P8: lower-right
        const cyOffset = (index < 4) ? -(2 * scale) : (2 * scale);
        const cLabel = svgTxt(
            arc.cx + (1.5 * scale), -arc.cy + cyOffset,
            `P${index + 1}(${arc.cx.toFixed(4)}, ${arc.cy.toFixed(4)})`,
            arc.color
        );
        overlayGroup.appendChild(cLabel);

        // --- Endpoint Handles ---
        // P1 handles: P1S (start) for R1, P1E (end) for angle
        if (index === 0) {
            // P1S Handle (index=0 start)
            const sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            sHandle.setAttribute('x', pStart.x - handleSize / 2);
            sHandle.setAttribute('y', -pStart.y - handleSize / 2);
            sHandle.setAttribute('width', handleSize);
            sHandle.setAttribute('height', handleSize);
            sHandle.setAttribute('fill', arc.color);
            sHandle.setAttribute('class', 'interactive-handle');
            sHandle.style.cursor = 'move';
            sHandle.setAttribute('data-name', 'P1S');
            bindDrag(sHandle, index, 'quadP1S');
            circlesGroup.appendChild(sHandle);

            // P1E Handle (index=0 end)
            const eHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            eHandle.setAttribute('x', pEnd.x - handleSize / 2);
            eHandle.setAttribute('y', -pEnd.y - handleSize / 2);
            eHandle.setAttribute('width', handleSize);
            eHandle.setAttribute('height', handleSize);
            eHandle.setAttribute('fill', arc.color);
            eHandle.setAttribute('class', 'interactive-handle');
            eHandle.style.cursor = 'move';
            eHandle.setAttribute('data-name', 'P1E');
            bindDrag(eHandle, index, 'quadP1E');
            circlesGroup.appendChild(eHandle);
        }
        // P4S (index=3): rectangle handle to adjust R4 and startAngle
        if (index === 3) {
            const sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            sHandle.setAttribute('x', pStart.x - handleSize / 2);
            sHandle.setAttribute('y', -pStart.y - handleSize / 2);
            sHandle.setAttribute('width', handleSize);
            sHandle.setAttribute('height', handleSize);
            sHandle.setAttribute('fill', arc.color);
            sHandle.setAttribute('class', 'interactive-handle');
            sHandle.style.cursor = 'move';
            sHandle.setAttribute('title', 'P4S');
            sHandle.setAttribute('data-name', 'P4S');
            bindDrag(sHandle, index, 'quadP4S');
            circlesGroup.appendChild(sHandle);
        }
        // P5 handles: P5S (start) for R5, P5E (end) for angle
        if (index === 4) {
            // P5S Handle (index=4 start)
            const sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            sHandle.setAttribute('x', pStart.x - handleSize / 2);
            sHandle.setAttribute('y', -pStart.y - handleSize / 2);
            sHandle.setAttribute('width', handleSize);
            sHandle.setAttribute('height', handleSize);
            sHandle.setAttribute('fill', arc.color);
            sHandle.setAttribute('class', 'interactive-handle');
            sHandle.style.cursor = 'move';
            sHandle.setAttribute('data-name', 'P5S');
            bindDrag(sHandle, index, 'quadP5S');
            circlesGroup.appendChild(sHandle);

            // P5E Handle (index=4 end)
            const eHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            eHandle.setAttribute('x', pEnd.x - handleSize / 2);
            eHandle.setAttribute('y', -pEnd.y - handleSize / 2);
            eHandle.setAttribute('width', handleSize);
            eHandle.setAttribute('height', handleSize);
            eHandle.setAttribute('fill', arc.color);
            eHandle.setAttribute('class', 'interactive-handle');
            eHandle.style.cursor = 'move';
            eHandle.setAttribute('data-name', 'P5E');
            bindDrag(eHandle, index, 'quadP5E');
            circlesGroup.appendChild(eHandle);
        }
        // P8S (index=7): rectangle handle
        if (index === 7) {
            const sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            sHandle.setAttribute('x', pStart.x - handleSize / 2);
            sHandle.setAttribute('y', -pStart.y - handleSize / 2);
            sHandle.setAttribute('width', handleSize);
            sHandle.setAttribute('height', handleSize);
            sHandle.setAttribute('fill', arc.color);
            sHandle.setAttribute('class', 'interactive-handle');
            sHandle.style.cursor = 'move';
            sHandle.setAttribute('data-name', 'P8S');
            bindDrag(sHandle, index, 'quadP8S');
            circlesGroup.appendChild(sHandle);
        }

        // --- Endpoint Coordinate Labels (centered above) ---
        // P1S (index=0 start), P1E (index=0 end), P2E (index=1 end),
        // P4S (index=3 start), P4E (index=3 end),
        // P5S (index=4 start), P5E (index=4 end), P6E (index=5 end),
        // P8S (index=7 start), P8E (index=7 end)
        const showStartLabel = [0, 3, 4, 7];
        const showEndLabel = [0, 1, 3, 4, 5, 7];

        if (showStartLabel.includes(index)) {
            renderArcEndpointLabel(overlayGroup, pStart, `P${index + 1}S`, arc.startAngle, (index < 4), scale, arc.color);
        }
        if (showEndLabel.includes(index)) {
            renderArcEndpointLabel(overlayGroup, pEnd, `P${index + 1}E`, arc.endAngle, (index < 4), scale, arc.color);
        }

        // --- Dashed Control Lines ---
        // P1~P1S, P2~P2S, P3~P3S, P4~P4S, P5~P5E, P6~P6S, P7~P7S, P8~P8S
        let lineTarget;
        if (index === 0) {
            // R1: P1~P1S
            lineTarget = pStart;
        } else if (index === 4) {
            // R5: P5~P5S
            lineTarget = pStart;
        } else if (index === 6) {
            // R7: P7~P7E
            lineTarget = pEnd;
        } else if (index === 1 || index === 2 || index === 3 || index === 5 || index === 7) {
            // R2, R3, R4, R6, R8: center to start point
            lineTarget = pStart;
        } else {
            // Default (e.g., fallback for index 0 and 4 which was pEnd before)
            lineTarget = pEnd;
        }

        const dashedLine = drawDashedLine(arc.cx, -arc.cy, lineTarget.x, -lineTarget.y, arc.color);
        circlesGroup.appendChild(dashedLine);

        // Also draw the other radial line for context (center to the other endpoint)
        if (index === 0 || index === 4 || index === 6) {
            // For R1, R5, R7, draw the line to the endpoint NOT used for the radius label
            const otherTarget = (index === 6) ? pStart : pEnd;
            const lineOther = drawDashedLine(arc.cx, -arc.cy, otherTarget.x, -otherTarget.y, arc.color);
            circlesGroup.appendChild(lineOther);
        } else {
            const lineE = drawDashedLine(arc.cx, -arc.cy, pEnd.x, -pEnd.y, arc.color);
            circlesGroup.appendChild(lineE);
        }

        // --- Radius Label (rotated along control line) ---
        const rMidX = (arc.cx + lineTarget.x) / 2;
        const rMidY = (-arc.cy + (-lineTarget.y)) / 2;
        const rDx = lineTarget.x - arc.cx;
        const rDy = (-lineTarget.y) - (-arc.cy);
        let rAngle = Math.atan2(rDy, rDx) * 180 / Math.PI;
        if (rAngle > 90) rAngle -= 180;
        if (rAngle < -90) rAngle += 180;
        const rLen = Math.sqrt(rDx * rDx + rDy * rDy);

        // Position offsets:
        // R1(0), R3(2), R4(3), R7(6) -> Above control line (positive/negative perpendicular offset depending on quadrant)
        // R5(4) -> Below control line
        let rOffDist = (index < 4) ? -1.5 * scale : 1.5 * scale;
        if (index === 4) rOffDist = 1.5 * scale; // R5 should be below
        if (index === 6) rOffDist = -1.5 * scale; // R7 should be above

        const rPerpX = rLen > 0 ? -rDy / rLen * rOffDist : 0;
        const rPerpY = rLen > 0 ? rDx / rLen * rOffDist : 0;

        const rLabel = svgTxtRotated(
            rMidX + rPerpX, rMidY + rPerpY,
            `R${index + 1}=${arc.r.toFixed(4)}`,
            arc.color, rAngle
        );
        overlayGroup.appendChild(rLabel);

        // --- Arc Angle Label (θ at arc midpoint, outside or inside) ---
        const theta = Math.abs(arc.endAngle - arc.startAngle);
        const midAngle = (arc.startAngle + arc.endAngle) / 2;
        const pMid = getPointOnCircle(arc.cx, arc.cy, arc.r, midAngle);
        // index 0,1,2,3 are inner arcs (θ1, θ2, θ3, θ4)
        const isInner = index < 4;
        const offset = isInner ? -2.5 * scale : 1.5 * scale;
        const aLabelX = pMid.x + offset * Math.cos(midAngle * Math.PI / 180);
        const aLabelY = -pMid.y - offset * Math.sin(midAngle * Math.PI / 180);
        let labelRot = midAngle - 90;
        if (labelRot > 90) labelRot -= 180;
        if (labelRot < -90) labelRot += 180;

        const aLabel = svgTxtRotated(
            aLabelX, aLabelY,
            `θ${index + 1}=${toDMS(theta)}`,
            arc.color, -labelRot
        );
        overlayGroup.appendChild(aLabel);
    });

    // --- Thickness Dimension Lines ($Tt, $Tb) ---
    const p1s = getPointOnCircle(quadCircleArcs[0].cx, quadCircleArcs[0].cy, quadCircleArcs[0].r, quadCircleArcs[0].startAngle);
    const p5s = getPointOnCircle(quadCircleArcs[4].cx, quadCircleArcs[4].cy, quadCircleArcs[4].r, quadCircleArcs[4].startAngle);
    const p4e = getPointOnCircle(quadCircleArcs[3].cx, quadCircleArcs[3].cy, quadCircleArcs[3].r, quadCircleArcs[3].endAngle);
    const p8e = getPointOnCircle(quadCircleArcs[7].cx, quadCircleArcs[7].cy, quadCircleArcs[7].r, quadCircleArcs[7].endAngle);

    drawDimensionLine(overlayGroup, p1s, p5s, 'Tt', quadCircleArcs[0].color, overlayGroup);
    drawDimensionLine(overlayGroup, p4e, p8e, 'Tb', quadCircleArcs[3].color, overlayGroup);
}



function drawPolygon(container, env, envIdx) {
    const points = env.points;
    if (points.length < 3) return;

    const scale = getVisualScale();
    const d = points.map((p, i) => (i === 0 ? 'M' : 'L') + ` ${p.x} ${-p.y} `).join(' ') + ' Z';

    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    poly.setAttribute('d', d);
    poly.setAttribute('fill', env.color); // Dynamic fill color
    poly.setAttribute('fill-opacity', '0.1'); // Transparency 20%
    poly.setAttribute('stroke', env.color); // Envelope Stroke
    poly.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
    poly.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
    container.appendChild(poly);

    // Draw Vertices and Labels
    const fontSize = (2.0 * scale).toFixed(4);
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
            errorText.setAttribute('font-size', (2.0 * scale).toFixed(4));
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
        dot.setAttribute('data-name', p.name || `點${pIdx + 1}`);

        // Update bindDrag to handle envIdx and pIdx
        dot.addEventListener('mousedown', (e) => startDrag(e, envIdx, 'envelopePoint', pIdx));
        dot.addEventListener('touchstart', (e) => startDrag(e, envIdx, 'envelopePoint', pIdx));
        overlayGroup.appendChild(dot);

        // Coordinate Label (Simplify for multiple envelopes)
        if (env.showLabels !== false) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', p.x);
            text.setAttribute('y', -p.y - labelOffset);
            text.setAttribute('font-size', fontSize);
            text.setAttribute('fill', '#333');
            text.setAttribute('text-anchor', 'middle');
            text.style.pointerEvents = 'none';
            const pName = p.name || `點${pIdx + 1} `;
            text.textContent = `${pName} (${p.x.toFixed(4)}, ${p.y.toFixed(4)})`;
            overlayGroup.appendChild(text);
        }
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
        cHandle.setAttribute('data-name', `P${arc.id.replace('L', '')}`);
        bindDrag(cHandle, index, 'center');
        container.appendChild(cHandle);

        // Center Label
        const cLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        const cyOffset = (index < 3) ? -(2 * scale) : (2 * scale); // Top-right for P1-3, Bottom-right for P4-6
        cLabel.setAttribute('x', arc.cx + (1.5 * scale));
        cLabel.setAttribute('y', -arc.cy + cyOffset);
        cLabel.setAttribute('font-size', (2.0 * scale).toFixed(4));
        cLabel.setAttribute('fill', arc.color);
        cLabel.setAttribute('dominant-baseline', 'middle');
        cLabel.style.pointerEvents = 'none';
        cLabel.textContent = `P${arc.id.replace('L', '')} (${arc.cx.toFixed(4)}, ${arc.cy.toFixed(4)})`;
        overlayGroup.appendChild(cLabel);

        // Start/End Handles (Hidden for Arc 2 and 5 - Side Arcs)
        if (index !== 1 && index !== 4) {
            // Start Handle
            const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
            const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);

            // Labels and Handles
            if (index === 0 || index === 3 || index === 2 || index === 5) {
                // Start Label (Show only for Arc 1 and 4)
                if (index === 0 || index === 3) {
                    renderArcEndpointLabel(overlayGroup, pStart, `P${arc.id.replace('L', '')}S`, arc.startAngle, (index < 3), scale, arc.color);

                    // Start Handle (Only for Arc 1 and 4)
                    let sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    sHandle.setAttribute('x', pStart.x - handleSize / 2);
                    sHandle.setAttribute('y', -pStart.y - handleSize / 2);
                    sHandle.setAttribute('width', handleSize);
                    sHandle.setAttribute('height', handleSize);
                    sHandle.setAttribute('class', 'interactive-handle');
                    sHandle.style.cursor = 'move';
                    sHandle.setAttribute('data-name', `P${arc.id.replace('L', '')}S`);
                    sHandle.setAttribute('fill', arc.color);
                    sHandle.setAttribute('stroke', arc.color);
                    sHandle.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
                    bindDrag(sHandle, index, 'startAngle');
                    container.appendChild(sHandle);
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
                    eHandle.setAttribute('data-name', `P${arc.id.replace('L', '')}E`);
                    eHandle.setAttribute('fill', arc.color);
                    eHandle.setAttribute('stroke', arc.color);
                    eHandle.setAttribute('stroke-width', (0.5 * scale).toFixed(4));
                    bindDrag(eHandle, index, 'endAngle');
                    container.appendChild(eHandle);
                }

                // End Label (Visible for 0, 3, 2, 5)
                renderArcEndpointLabel(overlayGroup, pEnd, `P${arc.id.replace('L', '')}E`, arc.endAngle, (index < 3), scale, arc.color);
            }

            // Dashed Radial Lines: Center to Start, Center to End
            const lineS = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineS.setAttribute('x1', arc.cx);
            lineS.setAttribute('y1', -arc.cy);
            lineS.setAttribute('x2', pStart.x);
            lineS.setAttribute('y2', -pStart.y);
            lineS.setAttribute('stroke', arc.color);
            lineS.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineS.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
            container.appendChild(lineS);

            const lineE = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineE.setAttribute('x1', arc.cx);
            lineE.setAttribute('y1', -arc.cy);
            lineE.setAttribute('x2', pEnd.x);
            lineE.setAttribute('y2', -pEnd.y);
            lineE.setAttribute('stroke', arc.color);
            lineE.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineE.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
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

            // R1-3 Above (-1.5), R4-6 Below (1.5)
            // Special Case: Triple-Circle R3 (index 2) is also Above
            let rOffDistSize = (index < 3) ? -1.5 * scale : 1.5 * scale;

            const rPerpX = -rDy / rLen * rOffDistSize;
            const rPerpY = rDx / rLen * rOffDistSize;

            const rLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            rLabel.setAttribute('x', rMidX + rPerpX);
            rLabel.setAttribute('y', rMidY + rPerpY);
            rLabel.setAttribute('font-size', (2.0 * scale).toFixed(4));
            rLabel.setAttribute('fill', arc.color);
            rLabel.setAttribute('text-anchor', 'middle');
            rLabel.setAttribute('dominant-baseline', 'middle');
            rLabel.setAttribute('transform', `rotate(${rAngle.toFixed(1)}, ${(rMidX + rPerpX).toFixed(4)}, ${(rMidY + rPerpY).toFixed(4)})`);
            rLabel.style.pointerEvents = 'none';
            rLabel.textContent = `R${arc.id.replace("L", "")}=${arc.r.toFixed(4)} `;
            overlayGroup.appendChild(rLabel);

            // Angle Label (θ1, θ2, θ3)
            const theta = Math.abs(arc.endAngle - arc.startAngle);
            const midAngle = (arc.startAngle + arc.endAngle) / 2;
            const pMid = getPointOnCircle(arc.cx, arc.cy, arc.r, midAngle);
            const aLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');

            // Offset label slightly outside or inside for visibility
            // index 0,1,2 are inner arcs (Arc 1, 2, 3)
            const isInner = index < 3;
            const offset = isInner ? -2.5 * scale : 1.5 * scale;
            aLabel.setAttribute('x', pMid.x + offset * Math.cos(midAngle * Math.PI / 180));
            aLabel.setAttribute('y', -pMid.y - offset * Math.sin(midAngle * Math.PI / 180));
            aLabel.setAttribute('font-size', (2.0 * scale).toFixed(4));
            aLabel.setAttribute('fill', arc.color);
            aLabel.setAttribute('text-anchor', 'middle');
            aLabel.setAttribute('dominant-baseline', 'middle');
            aLabel.style.pointerEvents = 'none';

            let labelRot = midAngle - 90;
            if (labelRot > 90) labelRot -= 180;
            if (labelRot < -90) labelRot += 180;
            aLabel.setAttribute('transform', `rotate(${- labelRot.toFixed(1)}, ${(pMid.x + offset * Math.cos(midAngle * Math.PI / 180)).toFixed(4)}, ${(-pMid.y - offset * Math.sin(midAngle * Math.PI / 180)).toFixed(4)})`);
            aLabel.textContent = `θ${index + 1}=${toDMS(theta)} `;
            overlayGroup.appendChild(aLabel);
        } else if (index === 1 || index === 4) { // Side Arcs (Arc 2 and Arc 5)
            const theta = Math.abs(arc.endAngle - arc.startAngle);
            const midAngle = (arc.startAngle + arc.endAngle) / 2;
            const pMid = getPointOnCircle(arc.cx, arc.cy, arc.r, midAngle);
            const aLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            const isInner = index < 3;
            const offset = isInner ? -2.5 * scale : 1.5 * scale;
            aLabel.setAttribute('x', pMid.x + offset * Math.cos(midAngle * Math.PI / 180));
            aLabel.setAttribute('y', -pMid.y - offset * Math.sin(midAngle * Math.PI / 180));
            aLabel.setAttribute('font-size', (2.0 * scale).toFixed(4));
            aLabel.setAttribute('fill', arc.color);
            aLabel.setAttribute('text-anchor', 'middle');
            aLabel.setAttribute('dominant-baseline', 'middle');
            aLabel.style.pointerEvents = 'none';
            let labelRot = midAngle - 90;
            if (labelRot > 90) labelRot -= 180;
            if (labelRot < -90) labelRot += 180;
            aLabel.setAttribute('transform', `rotate(${- labelRot.toFixed(1)}, ${(pMid.x + offset * Math.cos(midAngle * Math.PI / 180)).toFixed(4)}, ${(-pMid.y - offset * Math.sin(midAngle * Math.PI / 180)).toFixed(3)})`);
            aLabel.textContent = `θ${index + 1 === 2 ? 2 : 5} = ${toDMS(theta)} `;
            overlayGroup.appendChild(aLabel);

            // Radial Lines for Side Arcs (P2~P1E and P2~P3S for index 1, P5~P4E and P5~P6S for index 4)
            const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
            const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);

            // R5 (index 4) target is pEnd (P5E)
            const lineTarget = (index === 4) ? pEnd : pStart;

            const lineS = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineS.setAttribute('x1', arc.cx);
            lineS.setAttribute('y1', -arc.cy);
            lineS.setAttribute('x2', pStart.x);
            lineS.setAttribute('y2', -pStart.y);
            lineS.setAttribute('stroke', arc.color);
            lineS.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineS.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
            overlayGroup.appendChild(lineS);

            const lineE = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            lineE.setAttribute('x1', arc.cx);
            lineE.setAttribute('y1', -arc.cy);
            lineE.setAttribute('x2', pEnd.x);
            lineE.setAttribute('y2', -pEnd.y);
            lineE.setAttribute('stroke', arc.color);
            lineE.setAttribute('stroke-width', (0.3 * scale).toFixed(4));
            lineE.setAttribute('stroke-dasharray', `${(1 * scale).toFixed(4)},${(1 * scale).toFixed(4)} `);
            overlayGroup.appendChild(lineE);

            // Radius Label on control line (P2~P1E or P5~P5E)
            const rMidX = (arc.cx + lineTarget.x) / 2;
            const rMidY = (-arc.cy + (-lineTarget.y)) / 2;
            const rDx = lineTarget.x - arc.cx;
            const rDy = (-lineTarget.y) - (-arc.cy);
            let rAngle = Math.atan2(rDy, rDx) * 180 / Math.PI;
            if (rAngle > 90) rAngle -= 180;
            if (rAngle < -90) rAngle += 180;
            const rLen = Math.sqrt(rDx * rDx + rDy * rDy);

            // R2 Above (-), R5 Below (+)
            let rOffDistSize = (index === 1) ? -1.5 * scale : 1.5 * scale;
            const rPerpX = -rDy / rLen * rOffDistSize;
            const rPerpY = rDx / rLen * rOffDistSize;

            const rLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            rLabel.setAttribute('x', rMidX + rPerpX);
            rLabel.setAttribute('y', rMidY + rPerpY);
            rLabel.setAttribute('font-size', (2.0 * scale).toFixed(4));
            rLabel.setAttribute('fill', arc.color);
            rLabel.setAttribute('text-anchor', 'middle');
            rLabel.setAttribute('dominant-baseline', 'middle');
            rLabel.setAttribute('transform', `rotate(${rAngle.toFixed(1)}, ${(rMidX + rPerpX).toFixed(4)}, ${(rMidY + rPerpY).toFixed(4)})`);
            rLabel.style.pointerEvents = 'none';
            rLabel.textContent = `R${index + 1 === 2 ? 2 : 5} = ${arc.r.toFixed(4)} `;
            overlayGroup.appendChild(rLabel);
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

let savedQuadEndpoint = null;   // Saved P1E/P5E for P1/P5 center drag
let savedQuadStartpoint = null; // Saved P4S/P8S for P4/P8 center drag

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

    // Capture the name for the custom tooltip during drag
    let dragName = '';
    if (e.target && e.target.getAttribute) {
        dragName = e.target.getAttribute('data-name') || '';
    }
    document.body.setAttribute('data-active-drag-name', dragName);

    // Save P1E/P5E at drag start for P1/P5 center drags (P1E/P5E stays fixed)
    if (type === 'quadCenter' && (index === 0 || index === 4)) {
        const arc = quadCircleArcs[index];
        savedQuadEndpoint = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);
    } else {
        savedQuadEndpoint = null;
    }

    // Save P4S/P8S at drag start for P4/P8 center drags (P4S/P8S stays fixed)
    if (type === 'quadCenter' && (index === 3 || index === 7)) {
        const arc = quadCircleArcs[index];
        savedQuadStartpoint = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
    } else {
        savedQuadStartpoint = null;
    }

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

    // ---- Circular mode drag ----
    if (dragType === 'circularP1') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);

        const p2sy = circularArcs.outer.cy + circularArcs.outer.r;
        const p2ey = circularArcs.outer.cy - circularArcs.outer.r;

        let maxY = p2sy - circularArcs.inner.r - minTt - 0.0001;
        let minY = p2ey + circularArcs.inner.r + minTb + 0.0001;

        if (maxY < minY) {
            circularArcs.inner.cy = (minY + maxY) / 2;
        } else {
            circularArcs.inner.cy = Math.max(minY, Math.min(my, maxY));
        }

        drawSystem();
        return;
    }
    if (dragType === 'circularP1S') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        let newR = Math.abs(my - circularArcs.inner.cy);

        const p2sy = circularArcs.outer.cy + circularArcs.outer.r;
        const p2ey = circularArcs.outer.cy - circularArcs.outer.r;

        const limitR1 = p2sy - circularArcs.inner.cy - minTt;
        const limitR2 = circularArcs.inner.cy - p2ey - minTb;
        const maxR = Math.min(limitR1, limitR2);

        newR = Math.max(0.01, Math.min(newR, maxR));
        circularArcs.inner.r = parseFloat(newR.toFixed(4));
        drawSystem();
        return;
    }
    if (dragType === 'circularP2') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);

        const p1sy = circularArcs.inner.cy + circularArcs.inner.r;
        const p1ey = circularArcs.inner.cy - circularArcs.inner.r;

        let minY = p1sy - circularArcs.outer.r + minTt + 0.0001;
        let maxY = p1ey + circularArcs.outer.r - minTb - 0.0001;

        if (maxY < minY) {
            circularArcs.outer.cy = (minY + maxY) / 2;
        } else {
            circularArcs.outer.cy = Math.max(minY, Math.min(my, maxY));
        }

        drawSystem();
        return;
    }
    if (dragType === 'circularP2S') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        let newR = Math.abs(my - circularArcs.outer.cy);

        const p1sy = circularArcs.inner.cy + circularArcs.inner.r;
        const p1ey = circularArcs.inner.cy - circularArcs.inner.r;

        const minR1 = p1sy + minTt - circularArcs.outer.cy;
        const minR2 = circularArcs.outer.cy + minTb - p1ey;
        const minR = Math.max(0.01, minR1, minR2);

        newR = Math.max(newR, minR);
        circularArcs.outer.r = parseFloat(newR.toFixed(4));
        drawSystem();
        return;
    }

    // ---- Horseshoe mode drag ----
    if (dragType === 'horseshoeP1') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.2);
        const p4sy = horseshoeArcs.outer.cy + horseshoeArcs.outer.r;
        const maxP1Sy = p4sy - minTt - 0.0001;
        const limitY = maxP1Sy - horseshoeArcs.inner.r;
        horseshoeArcs.inner.cy = Math.min(my, limitY);

        // Dynamic Update: Maintain P3S.x >= P1E.x
        const p1e = getPointOnCircle(horseshoeArcs.inner.cx, horseshoeArcs.inner.cy, horseshoeArcs.inner.r, horseshoeArcs.inner.endAngle);
        if (horseshoeArcs.inner.p2e.x < p1e.x) {
            horseshoeArcs.inner.p2e.x = p1e.x;
        }

        drawSystem(); return;
    }
    if (dragType === 'horseshoeP1S') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.2);
        const maxR = (horseshoeArcs.outer.cy + horseshoeArcs.outer.r) - horseshoeArcs.inner.cy - minTt;
        horseshoeArcs.inner.r = Math.min(maxR, Math.max(0.1, Math.abs(my - horseshoeArcs.inner.cy)));

        // Dynamic Update: Maintain P3S.x >= P1E.x
        const p1e = getPointOnCircle(horseshoeArcs.inner.cx, horseshoeArcs.inner.cy, horseshoeArcs.inner.r, horseshoeArcs.inner.endAngle);
        if (horseshoeArcs.inner.p2e.x < p1e.x) {
            horseshoeArcs.inner.p2e.x = p1e.x;
        }

        drawSystem(); return;
    }
    if (dragType === 'horseshoeP1E') {
        const dx = mx - horseshoeArcs.inner.cx;
        const dy = my - horseshoeArcs.inner.cy;
        let ang = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
        if (ang < 90) ang = 90;
        if (ang > 269.9) ang = 269.9;
        horseshoeArcs.inner.endAngle = ang;

        // Maintain P3S.x >= P1E.x
        const p1e = getPointOnCircle(horseshoeArcs.inner.cx, horseshoeArcs.inner.cy, horseshoeArcs.inner.r, horseshoeArcs.inner.endAngle);
        if (horseshoeArcs.inner.p2e.x < p1e.x) {
            horseshoeArcs.inner.p2e.x = p1e.x;
        }

        drawSystem(); return;
    }
    if (dragType === 'horseshoeP3S') {
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.2);
        const limitY = horseshoeArcs.outer.p6e.y + minTb + 0.0001;

        const p1e = getPointOnCircle(horseshoeArcs.inner.cx, horseshoeArcs.inner.cy, horseshoeArcs.inner.r, horseshoeArcs.inner.endAngle);

        // P3S.x < P3E.x (0), P3S.x - P6S.x >= minThicknessBottom, and P3S.x >= P1E.x
        const limitX_Right = -0.001;
        const limitX_Left = Math.max(horseshoeArcs.outer.p5e.x + minTb, p1e.x);

        horseshoeArcs.inner.p2e.x = Math.max(limitX_Left, Math.min(limitX_Right, mx));
        horseshoeArcs.inner.p2e.y = Math.max(limitY, my);
        horseshoeArcs.inner.p3e.y = horseshoeArcs.inner.p2e.y; // Sync Y
        drawSystem(); return;
    }
    if (dragType === 'horseshoeP3E') {
        horseshoeArcs.inner.p3e.y = my;
        drawSystem(); return;
    }
    if (dragType === 'horseshoeP4') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.2);
        const p1sy = horseshoeArcs.inner.cy + horseshoeArcs.inner.r;
        const minP4Sy = p1sy + minTt + 0.0001;
        const limitY = minP4Sy - horseshoeArcs.outer.r;
        horseshoeArcs.outer.cy = Math.max(my, limitY);

        // Dynamic Update: Maintain P6S.x >= P4E.x
        const p4e = getPointOnCircle(horseshoeArcs.outer.cx, horseshoeArcs.outer.cy, horseshoeArcs.outer.r, horseshoeArcs.outer.endAngle);
        if (horseshoeArcs.outer.p5e.x < p4e.x) {
            horseshoeArcs.outer.p5e.x = p4e.x;
        }

        drawSystem(); return;
    }
    if (dragType === 'horseshoeP4S') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.2);
        const minR = (horseshoeArcs.inner.cy + horseshoeArcs.inner.r) - horseshoeArcs.outer.cy + minTt;
        horseshoeArcs.outer.r = Math.max(minR, Math.max(0.1, Math.abs(my - horseshoeArcs.outer.cy)));

        // Dynamic Update: Maintain P6S.x >= P4E.x
        const p4e = getPointOnCircle(horseshoeArcs.outer.cx, horseshoeArcs.outer.cy, horseshoeArcs.outer.r, horseshoeArcs.outer.endAngle);
        if (horseshoeArcs.outer.p5e.x < p4e.x) {
            horseshoeArcs.outer.p5e.x = p4e.x;
        }

        drawSystem(); return;
    }
    if (dragType === 'horseshoeP4E') {
        const dx = mx - horseshoeArcs.outer.cx;
        const dy = my - horseshoeArcs.outer.cy;
        let ang = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
        if (ang < 90) ang = 90;
        if (ang > 269.9) ang = 269.9;
        horseshoeArcs.outer.endAngle = ang;

        // Maintain P6S.x >= P4E.x
        const p4e = getPointOnCircle(horseshoeArcs.outer.cx, horseshoeArcs.outer.cy, horseshoeArcs.outer.r, horseshoeArcs.outer.endAngle);
        if (horseshoeArcs.outer.p5e.x < p4e.x) {
            horseshoeArcs.outer.p5e.x = p4e.x;
        }

        drawSystem(); return;
    }
    if (dragType === 'horseshoeP6S') {
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.2);
        const limitY = horseshoeArcs.inner.p3e.y - minTb - 0.0001;

        const p4e = getPointOnCircle(horseshoeArcs.outer.cx, horseshoeArcs.outer.cy, horseshoeArcs.outer.r, horseshoeArcs.outer.endAngle);

        // P6S.x < P6E.x (0), P3S.x - P6S.x >= minThicknessBottom, and P6S.x >= P4E.x
        const limitX_Right = horseshoeArcs.inner.p2e.x - minTb;
        const limitX_Left = p4e.x;

        horseshoeArcs.outer.p5e.x = Math.max(limitX_Left, Math.min(limitX_Right, mx));
        horseshoeArcs.outer.p5e.y = Math.min(limitY, my);
        horseshoeArcs.outer.p6e.y = horseshoeArcs.outer.p5e.y; // Sync Y
        drawSystem(); return;
    }
    if (dragType === 'horseshoeP6E') {
        horseshoeArcs.outer.p6e.y = my;
        drawSystem(); return;
    }

    // ---- Double Circle mode drag ----
    if (dragType === 'doubleCircleP1') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const p4sy = doubleCircleArcs.outer.p4.cy + doubleCircleArcs.outer.p4.r;
        const limitY = p4sy - minTt - 0.0001 - doubleCircleArcs.inner.p1.r;
        doubleCircleArcs.inner.p1.cy = Math.min(my, limitY);
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP1S') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const p4sy = doubleCircleArcs.outer.p4.cy + doubleCircleArcs.outer.p4.r;
        const limitY = p4sy - minTt;
        const newY = Math.min(limitY, my);
        doubleCircleArcs.inner.p1.r = Math.max(0.1, Math.abs(newY - doubleCircleArcs.inner.p1.cy));
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP1E') {
        const dx = mx - doubleCircleArcs.inner.p1.cx;
        const dy = my - doubleCircleArcs.inner.p1.cy;
        let ang = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
        if (ang < 90) ang = 90;
        if (ang > 269.9) ang = 269.9;
        doubleCircleArcs.inner.p1.endAngle = ang;
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP3') {
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        const p6ey = doubleCircleArcs.outer.p6.cy - doubleCircleArcs.outer.p6.r;
        const limitY = p6ey + minTb + 0.0001 + doubleCircleArcs.inner.p3.r;
        doubleCircleArcs.inner.p3.cy = Math.max(my, limitY);
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP3S') {
        const dx = mx - doubleCircleArcs.inner.p3.cx;
        const dy = my - doubleCircleArcs.inner.p3.cy;
        let ang = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;

        // 1. startAngle > 90.1 and endAngle < 270 is implied by P3E, but let's be safe
        if (ang < 90.1) ang = 90.1;
        if (ang > 270) ang = 270;

        // 2. Horizontal thickness constraint: P3S.x - P6S.x >= minTb
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        const p6s_pt = getPointOnCircle(doubleCircleArcs.outer.p6.cx, doubleCircleArcs.outer.p6.cy, doubleCircleArcs.outer.p6.r, doubleCircleArcs.outer.p6.startAngle);
        const limitX = Math.min(-0.001, p6s_pt.x + minTb);

        const p3 = doubleCircleArcs.inner.p3;
        const curX = p3.cx + p3.r * Math.cos(ang * Math.PI / 180);
        if (curX < limitX) {
            const cosVal = (limitX - p3.cx) / p3.r;
            if (Math.abs(cosVal) <= 1) {
                ang = 360 - Math.acos(cosVal) * 180 / Math.PI;
            }
        }

        doubleCircleArcs.inner.p3.startAngle = ang;
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP3E') {
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        const p6ey = doubleCircleArcs.outer.p6.cy - doubleCircleArcs.outer.p6.r;
        const limitY = p6ey + minTb;
        const newY = Math.max(limitY, my);
        doubleCircleArcs.inner.p3.r = Math.max(0.1, Math.abs(newY - doubleCircleArcs.inner.p3.cy));
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP4') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const p1sy = doubleCircleArcs.inner.p1.cy + doubleCircleArcs.inner.p1.r;
        const limitY = p1sy + minTt + 0.0001 - doubleCircleArcs.outer.p4.r;
        doubleCircleArcs.outer.p4.cy = Math.max(my, limitY);
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP4S') {
        const minTt = parseFloat(document.getElementById('minThicknessTop')?.value || 0.3);
        const p1sy = doubleCircleArcs.inner.p1.cy + doubleCircleArcs.inner.p1.r;
        const limitY = p1sy + minTt;
        const newY = Math.max(limitY, my);
        doubleCircleArcs.outer.p4.r = Math.max(0.1, Math.abs(newY - doubleCircleArcs.outer.p4.cy));
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP4E') {
        const dx = mx - doubleCircleArcs.outer.p4.cx;
        const dy = my - doubleCircleArcs.outer.p4.cy;
        let ang = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
        if (ang < 90) ang = 90;
        if (ang > 269.9) ang = 269.9;
        doubleCircleArcs.outer.p4.endAngle = ang;
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP6') {
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        const p3ey = doubleCircleArcs.inner.p3.cy - doubleCircleArcs.inner.p3.r;
        const limitY = p3ey - minTb - 0.0001 + doubleCircleArcs.outer.p6.r;
        doubleCircleArcs.outer.p6.cy = Math.min(my, limitY);
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP6S') {
        const dx = mx - doubleCircleArcs.outer.p6.cx;
        const dy = my - doubleCircleArcs.outer.p6.cy;
        let ang = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;

        if (ang < 90.1) ang = 90.1;
        if (ang > 270) ang = 270;

        // 2. Horizontal thickness constraint: P3S.x - P6S.x >= minTb -> P6S.x <= P3S.x - minTb
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        const p3s_pt = getPointOnCircle(doubleCircleArcs.inner.p3.cx, doubleCircleArcs.inner.p3.cy, doubleCircleArcs.inner.p3.r, doubleCircleArcs.inner.p3.startAngle);
        const limitX = p3s_pt.x - minTb;

        const p6 = doubleCircleArcs.outer.p6;
        const curX = p6.cx + p6.r * Math.cos(ang * Math.PI / 180);
        if (curX > limitX) {
            const cosVal = (limitX - p6.cx) / p6.r;
            if (Math.abs(cosVal) <= 1) {
                ang = 360 - Math.acos(cosVal) * 180 / Math.PI;
            }
        }

        doubleCircleArcs.outer.p6.startAngle = ang;
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }
    if (dragType === 'doubleCircleP6E') {
        const minTb = parseFloat(document.getElementById('minThicknessBottom')?.value || 0.3);
        const p3ey = doubleCircleArcs.inner.p3.cy - doubleCircleArcs.inner.p3.r;
        const limitY = p3ey - minTb;
        const newY = Math.min(limitY, my);
        doubleCircleArcs.outer.p6.r = Math.max(0.1, Math.abs(newY - doubleCircleArcs.outer.p6.cy));
        updateDoubleCircleGeometry();
        drawSystem(); return;
    }

    if (dragType === 'quadCenter') {
        const arc = quadCircleArcs[activeDragIndex];
        if (activeDragIndex === 0 || activeDragIndex === 3 || activeDragIndex === 4 || activeDragIndex === 7) {
            arc.cx = 0; arc.cy = my;
        } else {
            arc.cx = Math.min(-0.0001, mx); arc.cy = my;
        }
        const side = activeDragIndex < 4 ? 'inner' : 'outer';
        updateQuadCircleArcsConnectorGeometry(side);
        drawSystem();
        checkClearance();
        return;
    }
    if (dragType === 'quadP1S') {
        const p1 = quadCircleArcs[0];
        p1.r = Math.sqrt(Math.pow(mx - p1.cx, 2) + Math.pow(my - p1.cy, 2));
        updateQuadCircleArcsConnectorGeometry('inner', 'p1s');
        drawSystem();
        checkClearance();
        return;
    }
    if (dragType === 'quadP1E') {
        const p1 = quadCircleArcs[0];
        // p1.r = Math.sqrt(Math.pow(mx - p1.cx, 2) + Math.pow(my - p1.cy, 2)); // Locked
        let ea = Math.atan2(my - p1.cy, mx - p1.cx) * 180 / Math.PI;
        while (ea < 90.001) ea += 360;
        if (ea > 270) ea = 270;
        p1.endAngle = ea;
        updateQuadCircleArcsConnectorGeometry('inner');
        drawSystem();
        checkClearance();
        return;
    }
    if (dragType === 'quadP4S') {
        const p3 = quadCircleArcs[2];
        const p4 = quadCircleArcs[3];
        // Tangency: center p4 must lie on the line through p3 center and junction(mouse)
        // Line through (p3.cx, p3.cy) and (mx, my): (y - p3.cy) = m * (x - p3.cx)
        // where m = (my - p3.cy) / (mx - p3.cx)
        // Find cy when x = 0
        if (Math.abs(mx - p3.cx) > 0.0001) {
            const m = (my - p3.cy) / (mx - p3.cx);
            p4.cy = p3.cy - m * p3.cx;
        } else {
            p4.cy = my;
        }
        updateQuadCircleArcsConnectorGeometry('inner');
        drawSystem();
        checkClearance();
        return;
    }
    if (dragType === 'quadP5S') {
        const p5 = quadCircleArcs[4];
        p5.r = Math.sqrt(Math.pow(mx - p5.cx, 2) + Math.pow(my - p5.cy, 2));
        updateQuadCircleArcsConnectorGeometry('outer', 'p5s');
        drawSystem();
        checkClearance();
        return;
    }
    if (dragType === 'quadP5E') {
        const p5 = quadCircleArcs[4];
        // p5.r = Math.sqrt(Math.pow(mx - p5.cx, 2) + Math.pow(my - p5.cy, 2)); // Locked
        let ea = Math.atan2(my - p5.cy, mx - p5.cx) * 180 / Math.PI;
        while (ea < 90.001) ea += 360;
        if (ea > 270) ea = 270;
        p5.endAngle = ea;
        updateQuadCircleArcsConnectorGeometry('outer');
        drawSystem();
        checkClearance();
        return;
    }
    if (dragType === 'quadP8S') {
        const p7 = quadCircleArcs[6];
        const p8 = quadCircleArcs[7];
        if (Math.abs(mx - p7.cx) > 0.0001) {
            const m = (my - p7.cy) / (mx - p7.cx);
            p8.cy = p7.cy - m * p7.cx;
        } else {
            p8.cy = my;
        }
        updateQuadCircleArcsConnectorGeometry('outer');
        drawSystem();
        checkClearance();
        return;
    }

    const arc = tripleCircleArcs[activeDragIndex];


    if (activeDragIndex === 0 || activeDragIndex === 1 || activeDragIndex === 2) {
        if (dragType === 'center') {
            if (activeDragIndex === 0 || activeDragIndex === 2) { // Arc 1LI, 3L: Y-Axis Constrained
                arc.cx = 0;
                arc.cy = my;
            } else if (activeDragIndex === 1) { // Arc 2LI: Constrained to X <= 0
                arc.cx = Math.min(0, mx);
                arc.cy = my;
            }
            updateTripleCircleArcsConnectorGeometry('inner', 'p2');

        } else if (dragType === 'startAngle' || dragType === 'endAngle') {
            const isArc1End = (activeDragIndex === 0 && dragType === 'endAngle');
            const isP1S = (activeDragIndex === 0 && dragType === 'startAngle');

            let targetX = mx, targetY = my;

            if (isP1S) { // P1S.y > P1.y (SVG y < cy)
                targetX = 0;
                if (targetY <= tripleCircleArcs[0].cy) targetY = tripleCircleArcs[0].cy + 0.001;
            }

            const rawAngle = Math.atan2(targetY - arc.cy, targetX - arc.cx) * 180 / Math.PI;
            let r = Math.sqrt(Math.pow(targetX - arc.cx, 2) + Math.pow(targetY - arc.cy, 2));

            if (isArc1End) {
                // arc.r is no longer adjusted by dragging P1E
                let diffE = rawAngle - arc.startAngle;
                while (diffE < 0) diffE += 360;
                while (diffE >= 360) diffE -= 360;
                let ang = arc.startAngle + diffE;
                if (ang < 90) ang = 90;
                if (diffE >= 270 - arc.startAngle) diffE = 270 - arc.startAngle;
                arc.endAngle = ang;
            } else if (isP1S) {
                arc.r = r;
                arc.startAngle = rawAngle;
            }

            const movingPoint = isArc1End ? 'p1e' : null;
            updateTripleCircleArcsConnectorGeometry('inner', movingPoint);
        }
    } else if (activeDragIndex === 3 || activeDragIndex === 4 || activeDragIndex === 5) {
        // Arc 4/5/6 drag handling (mirrors Arc 1/2/3)
        if (dragType === 'center') {
            if (activeDragIndex === 3 || activeDragIndex === 5) { // P4, P6: Y-Axis Constrained
                arc.cx = 0;
                arc.cy = my;
            } else if (activeDragIndex === 4) { // P5: Constrained to X <= 0
                arc.cx = Math.min(0, mx);
                arc.cy = my;
            }
            updateTripleCircleArcsConnectorGeometry('outer', 'p5');

        } else if (dragType === 'startAngle' || dragType === 'endAngle') {
            const isArc4End = (activeDragIndex === 3 && dragType === 'endAngle');
            const isP4S = (activeDragIndex === 3 && dragType === 'startAngle');

            let targetX = mx, targetY = my;
            if (isP4S) {
                targetX = 0;
                if (targetY <= tripleCircleArcs[3].cy) targetY = tripleCircleArcs[3].cy + 0.001;
            }

            const rawAngle = Math.atan2(targetY - arc.cy, targetX - arc.cx) * 180 / Math.PI;
            let r = Math.sqrt(Math.pow(targetX - arc.cx, 2) + Math.pow(targetY - arc.cy, 2));

            if (isArc4End) {
                // arc.r is no longer adjusted by dragging P4E
                let diffE4 = rawAngle - arc.startAngle;
                while (diffE4 < 0) diffE4 += 360;
                while (diffE4 >= 360) diffE4 -= 360;
                let ang = arc.startAngle + diffE4;
                if (ang < 90) ang = 90;
                if (diffE4 >= 270 - arc.startAngle) diffE4 = 270 - arc.startAngle;
                arc.endAngle = ang;
            } else if (isP4S) {
                arc.r = r;
                arc.startAngle = rawAngle;
            }

            const movingPoint = isArc4End ? 'p4e' : null;
            updateTripleCircleArcsConnectorGeometry('outer', movingPoint);
        }
    }

    drawSystem();
    checkClearance(); // Don't alert during drag, only at the end
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
    violatedPointIndices = [];
    const mode = getCurrentMode();

    // 1. Pre-calculate junction angles and cached arc parameters once per frame
    let junctions = [];
    let arcCaches = [];

    if (mode === 'quad') {
        const arcs = quadCircleArcs.slice(0, 4);
        arcs.forEach((a, i) => {
            arcCaches.push({ cx: a.cx, cy: a.cy, r2: (a.r + 0.001) * (a.r + 0.001) });
            if (i < 3) {
                const p = getPointOnCircle(a.cx, a.cy, a.r, a.endAngle);
                junctions.push((Math.atan2(p.y, p.x) * 180 / Math.PI + 360) % 360);
            }
        });
    } else if (mode === 'triple' || mode === 'circular') {
        const a1 = (mode === 'circular') ? circularArcs.inner : tripleCircleArcs[0];
        arcCaches.push({ cx: a1.cx, cy: a1.cy, r2: (a1.r + 0.001) * (a1.r + 0.001) });
        if (mode === 'triple') {
            const a2 = tripleCircleArcs[1], a3 = tripleCircleArcs[2];
            arcCaches.push({ cx: a2.cx, cy: a2.cy, r2: (a2.r + 0.001) * (a2.r + 0.001) });
            arcCaches.push({ cx: a3.cx, cy: a3.cy, r2: (a3.r + 0.001) * (a3.r + 0.001) });

            const j12 = getPointOnCircle(a1.cx, a1.cy, a1.r, a1.endAngle);
            const j23 = getPointOnCircle(a2.cx, a2.cy, a2.r, a2.endAngle);
            junctions.push((Math.atan2(j12.y, j12.x) * 180 / Math.PI + 360) % 360);
            junctions.push((Math.atan2(j23.y, j23.x) * 180 / Math.PI + 360) % 360);
        }
    } else if (mode === 'horseshoe') {
        const inner = horseshoeArcs.inner;
        const p1e = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
        junctions = [p1e.y, inner.p2e.y, inner.p3e.y, p1e.x, inner.p2e.x]; // Using y as junction markers
        arcCaches = [{ cx: inner.cx, cy: inner.cy, r2: (inner.r + 0.001) * (inner.r + 0.001) }];
    } else if (mode === 'double_circle') {
        const inner = doubleCircleArcs.inner;
        const p1e = getPointOnCircle(inner.p1.cx, inner.p1.cy, inner.p1.r, inner.p1.endAngle);
        const p3s = getPointOnCircle(inner.p3.cx, inner.p3.cy, inner.p3.r, inner.p3.startAngle);
        junctions = [p1e.y, p3s.y, Math.abs(inner.line2.ps.x)];
        arcCaches = [
            { cx: inner.p1.cx, cy: inner.p1.cy, r2: (inner.p1.r + 0.001) * (inner.p1.r + 0.001) },
            { cx: inner.p3.cx, cy: inner.p3.cy, r2: (inner.p3.r + 0.001) * (inner.p3.r + 0.001) }
        ];
    }

    // 2. Main Inspection Loop
    envelopes.forEach((env, envIdx) => {
        violatedPointIndices[envIdx] = [];
        if (!env.visible) return;

        env.points.forEach((p, pIdx) => {
            const absX = Math.abs(p.x);
            const testX = -absX;
            const testY = p.y;

            if (mode === 'quad') {
                const theta = (Math.atan2(testY, testX) * 180 / Math.PI + 360) % 360;
                let target;
                if (theta >= 90 && theta < junctions[0]) target = arcCaches[0];
                else if (theta >= junctions[0] && theta < junctions[1]) target = arcCaches[1];
                else if (theta >= junctions[1] && theta < junctions[2]) target = arcCaches[2];
                else target = arcCaches[3];

                const dx = testX - target.cx, dy = testY - target.cy;
                if (dx * dx + dy * dy > target.r2) violatedPointIndices[envIdx].push(pIdx);

            } else if (mode === 'triple' || mode === 'circular') {
                if (mode === 'circular') {
                    const target = arcCaches[0];
                    const dx = testX - target.cx, dy = testY - target.cy;
                    if (dx * dx + dy * dy > target.r2) violatedPointIndices[envIdx].push(pIdx);
                } else {
                    const theta = (Math.atan2(testY, testX) * 180 / Math.PI + 360) % 360;
                    let target;
                    if (theta >= 90 && theta < junctions[0]) target = arcCaches[0];
                    else if (theta >= junctions[0] && theta < junctions[1]) target = arcCaches[1];
                    else target = arcCaches[2];

                    const dx = testX - target.cx, dy = testY - target.cy;
                    if (dx * dx + dy * dy > target.r2) violatedPointIndices[envIdx].push(pIdx);
                }
            } else if (mode === 'horseshoe') {
                const [p1e_y, p2e_y, p3e_y, p1e_x, p2e_x] = junctions;
                if (testY >= p1e_y) {
                    const target = arcCaches[0];
                    const dx = testX - target.cx, dy = testY - target.cy;
                    if (dx * dx + dy * dy > target.r2) violatedPointIndices[envIdx].push(pIdx);
                } else if (testY >= p2e_y) {
                    const tx = p1e_x + (p2e_x - p1e_x) * (testY - p1e_y) / (p2e_y - p1e_y || 1e-6);
                    if (testX < tx - 0.001) violatedPointIndices[envIdx].push(pIdx);
                } else {
                    if (testY < p3e_y - 0.001) violatedPointIndices[envIdx].push(pIdx);
                }
            } else if (mode === 'double_circle') {
                const [p1e_y, p3s_y, lineX] = junctions;
                if (testY >= p1e_y) {
                    const target = arcCaches[0];
                    const dx = testX - target.cx, dy = testY - target.cy;
                    if (dx * dx + dy * dy > target.r2) violatedPointIndices[envIdx].push(pIdx);
                } else if (testY >= p3s_y) {
                    if (absX > lineX + 0.001) violatedPointIndices[envIdx].push(pIdx);
                } else {
                    const target = arcCaches[1];
                    const dx = testX - target.cx, dy = testY - target.cy;
                    if (dx * dx + dy * dy > target.r2) violatedPointIndices[envIdx].push(pIdx);
                }
            }
        });
    });

    drawSystem();
}

function endDrag() {
    activeDragIndex = null;
    dragType = null;
    document.body.removeAttribute('data-active-drag-name');
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

    // Utilize the universal getAllArcs() helper which handles all modes
    const allArcs = getAllArcs();

    allArcs.forEach(a => {
        // Sample start and end points
        minX = Math.min(minX, a.startX, a.endX);
        maxX = Math.max(maxX, a.startX, a.endX);
        minY = Math.min(minY, a.startY, a.endY);
        maxY = Math.max(maxY, a.startY, a.endY);

        // If it's an arc (radius > 0), check extreme angles
        if (a.r > 0) {
            [0, 90, 180, 270].forEach(ang => {
                if (isAngleInRange(ang, a.startAngle, a.endAngle)) {
                    const p = getPointOnCircle(a.cx, a.cy, a.r, ang);
                    minX = Math.min(minX, p.x);
                    maxX = Math.max(maxX, p.x);
                    minY = Math.min(minY, p.y);
                    maxY = Math.max(maxY, p.y);
                }
            });
        }
    });

    // Also include all clearance envelope points
    envelopes.forEach(env => {
        env.points.forEach(p => {
            minX = Math.min(minX, p.x);
            maxX = Math.max(maxX, p.x);
            minY = Math.min(minY, p.y);
            maxY = Math.max(maxY, p.y);
        });
    });

    const mode = getCurrentMode();
    let maxR = 5; // Default fallback

    if (mode === 'circular') {
        const p2s = getPointOnCircle(circularArcs.outer.cx, circularArcs.outer.cy, circularArcs.outer.r, circularArcs.outer.startAngle);
        maxR = Math.sqrt(p2s.x * p2s.x + p2s.y * p2s.y) + 1;
    } else if (mode === 'horseshoe') {
        const outer = horseshoeArcs.outer;
        const p4s = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.startAngle);
        const p4e = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);
        maxR = Math.max(
            Math.sqrt(p4s.x * p4s.x + p4s.y * p4s.y),
            Math.sqrt(p4e.x * p4e.x + p4e.y * p4e.y)
        ) + 1;
    } else if (mode === 'double_circle') {
        const outer = doubleCircleArcs.outer;
        const p4s = getPointOnCircle(outer.p4.cx, outer.p4.cy, outer.p4.r, outer.p4.startAngle);
        const p6e = getPointOnCircle(outer.p6.cx, outer.p6.cy, outer.p6.r, outer.p6.endAngle);
        maxR = Math.max(
            Math.sqrt(p4s.x * p4s.x + p4s.y * p4s.y),
            Math.sqrt(p6e.x * p6e.x + p6e.y * p6e.y)
        ) + 1;
    } else if (mode === 'triple') {
        const p4 = tripleCircleArcs[3]; // Outer Top
        const p6 = tripleCircleArcs[5]; // Outer Bottom
        const p4s = getPointOnCircle(p4.cx, p4.cy, p4.r, p4.startAngle);
        const p6e = getPointOnCircle(p6.cx, p6.cy, p6.r, p6.endAngle);
        maxR = Math.max(
            Math.sqrt(p4s.x * p4s.x + p4s.y * p4s.y),
            Math.sqrt(p6e.x * p6e.x + p6e.y * p6e.y)
        ) + 1;
    } else if (mode === 'quad') {
        const p5 = quadCircleArcs[4]; // Outer Top
        const p6 = quadCircleArcs[5]; // Outer Mid-Upper
        const p8 = quadCircleArcs[7]; // Outer Bottom
        const p5s = getPointOnCircle(p5.cx, p5.cy, p5.r, p5.startAngle);
        const p8e = getPointOnCircle(p8.cx, p8.cy, p8.r, p8.endAngle);
        maxR = Math.max(
            Math.sqrt(p5s.x * p5s.x + p5s.y * p5s.y),
            Math.sqrt(p8e.x * p8e.x + p8e.y * p8e.y),
            Math.abs(p6.cx) + p6.r
        ) + 1;
    }

    viewBoxState.x = -maxR;
    viewBoxState.y = -maxR;
    viewBoxState.w = 2 * maxR;
    viewBoxState.h = 2 * maxR;

    updateCanvasViewBox();
}

function updateCanvasViewBox() {
    const canvas = document.getElementById('canvas');
    if (canvas) {
        canvas.setAttribute('viewBox', `${viewBoxState.x} ${viewBoxState.y} ${viewBoxState.w} ${viewBoxState.h} `);
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
    if (!resultsContainer) return;

    if (getCurrentMode() === 'circular') {
        updateCircularInfoPanel(resultsContainer, areaResultsContainer);
        return;
    }
    if (getCurrentMode() === 'horseshoe') {
        updateHorseshoeInfoPanel(resultsContainer, areaResultsContainer);
        return;
    }
    if (getCurrentMode() === 'double_circle') {
        updateDoubleCircleInfoPanel(resultsContainer, areaResultsContainer);
        return;
    }
    if (getCurrentMode() === 'quad') {
        updateQuadInfoPanel(resultsContainer, areaResultsContainer);
        return;
    }

    // Default: Triple Mode
    updateTripleInfoPanel(resultsContainer, areaResultsContainer);
}

function updateHorseshoeInfoPanel(resultsContainer, areaResultsContainer) {
    const inner = horseshoeArcs.inner;
    const outer = horseshoeArcs.outer;

    function getPolyArea(points) {
        let a = 0;
        for (let i = 0; i < points.length; i++) {
            a += (points[i].x * points[(i + 1) % points.length].y - points[(i + 1) % points.length].x * points[i].y);
        }
        return Math.abs(0.5 * a);
    }

    const thetaInner = Math.abs(inner.endAngle - inner.startAngle) * Math.PI / 180;
    const sectorInner = 0.5 * inner.r * inner.r * thetaInner;
    const p1e = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
    const polyInner = [
        { x: inner.cx, y: inner.cy },
        { x: p1e.x, y: p1e.y },
        { x: inner.p2e.x, y: inner.p2e.y },
        { x: inner.p3e.x, y: inner.p3e.y }
    ];
    const innerAreaSingle = sectorInner + getPolyArea(polyInner);
    const innerArea = 2 * innerAreaSingle;

    const thetaOuter = Math.abs(outer.endAngle - outer.startAngle) * Math.PI / 180;
    const sectorOuter = 0.5 * outer.r * outer.r * thetaOuter;
    const p4e = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);
    const polyOuter = [
        { x: outer.cx, y: outer.cy },
        { x: p4e.x, y: p4e.y },
        { x: outer.p5e.x, y: outer.p5e.y },
        { x: outer.p6e.x, y: outer.p6e.y }
    ];
    const outerAreaSingle = sectorOuter + getPolyArea(polyOuter);
    const outerArea = 2 * outerAreaSingle;

    const liningArea = outerArea - innerArea;
    const t_val = Math.max(0, parseFloat(document.getElementById('excavationThickness')?.value || 0.2));

    const arcLen4L = outer.r * thetaOuter;
    const line5LLen = Math.sqrt((outer.p5e.x - p4e.x) ** 2 + (outer.p5e.y - p4e.y) ** 2);
    const line6LLen = Math.sqrt((outer.p6e.x - outer.p5e.x) ** 2 + (outer.p6e.y - outer.p5e.y) ** 2);
    const excavationArea = 2 * ((arcLen4L + line5LLen + line6LLen) * t_val) + outerArea;

    const areaHtml = `
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #fae1e1ff; border: 2px solid #f37171ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #ca2222ff; font-weight: bold;">預估開挖面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #ca2222ff; font-family: 'Courier New', monospace;"> ${excavationArea.toFixed(2)} m²</span>
            </div>
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #ffddaaff; border: 2px solid #f3a566ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #fd7200ff; font-weight: bold;">襯砌外廓面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #fd7200ff; font-family: 'Courier New', monospace;"> ${outerArea.toFixed(2)} m²</span>
            </div>
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e8f5e9; border: 2px solid #68ac6dff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #1b5e20; font-weight: bold;">襯砌內廓面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #1b5e20; font-family: 'Courier New', monospace;"> ${innerArea.toFixed(2)} m²</span>
            </div>
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #1565c0; font-weight: bold;">襯砌斷面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #0d47a1; font-family: 'Courier New', monospace;">${liningArea.toFixed(2)} m²</span>
            </div>
        </div>`;

    if (areaResultsContainer) areaResultsContainer.innerHTML = areaHtml;

    // Use arc identifiers for calculation consistency
    const p1e_pt = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
    const p1er_pt = { x: -p1e_pt.x, y: p1e_pt.y };
    const p4e_pt = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);
    const p4er_pt = { x: -p4e_pt.x, y: p4e_pt.y };

    const arcData = [
        { name: 'Arc 1L', cx: inner.cx, cy: inner.cy, r: inner.r, sa: inner.startAngle, ea: inner.endAngle, color: inner.color },
        { name: 'Arc 1R', cx: -inner.cx, cy: inner.cy, r: inner.r, sa: 180 - inner.startAngle, ea: 180 - inner.endAngle, color: inner.color },
        { name: 'Arc 4L', cx: outer.cx, cy: outer.cy, r: outer.r, sa: outer.startAngle, ea: outer.endAngle, color: outer.color },
        { name: 'Arc 4R', cx: -outer.cx, cy: outer.cy, r: outer.r, sa: 180 - outer.startAngle, ea: 180 - outer.endAngle, color: outer.color }
    ];

    const color2 = '#28a745'; const color3 = '#007bff';
    const color5 = '#1e7e34'; const color6 = '#0056b3';

    const lineData = [
        { name: 'Line 2L', ps: p1e_pt, pe: inner.p2e, color: color2 },
        { name: 'Line 2R', ps: p1er_pt, pe: { x: -inner.p2e.x, y: inner.p2e.y }, color: color2 },
        { name: 'Line 5L', ps: p4e_pt, pe: outer.p5e, color: color5 },
        { name: 'Line 5R', ps: p4er_pt, pe: { x: -outer.p5e.x, y: outer.p5e.y }, color: color5 },
        { name: 'Line 3L', ps: inner.p2e, pe: inner.p3e, color: color3 },
        { name: 'Line 3R', ps: { x: -inner.p2e.x, y: inner.p2e.y }, pe: { x: -inner.p3e.x, y: inner.p3e.y }, color: color3 },
        { name: 'Line 6L', ps: outer.p5e, pe: outer.p6e, color: color6 },
        { name: 'Line 6R', ps: { x: -outer.p5e.x, y: outer.p5e.y }, pe: { x: -outer.p6e.x, y: outer.p6e.y }, color: color6 }
    ];

    let html = `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">`;

    arcData.forEach(d => {
        const pS = getPointOnCircle(d.cx, d.cy, d.r, d.sa);
        const pE = getPointOnCircle(d.cx, d.cy, d.r, d.ea);
        const len = d.r * Math.abs(d.ea - d.sa) * Math.PI / 180;
        html += `
            <div class="result-item" style="border-left: 6px solid ${d.color}; background: #f8f9fa; padding: 12px; border-radius: 4px;">
                <h4 style="margin:0 0 8px 0; color: ${d.color};">圓弧 ${d.name}</h4>
                <div style="font-size: 0.75em;">
                    <div><strong>圓弧圓心 P:</strong> (${d.cx.toFixed(4)}, ${d.cy.toFixed(4)})</div>
                    <div><strong>圓弧半徑 R:</strong> ${d.r.toFixed(4)}</div>
                    <div><strong>起始弧角 θs:</strong> ${toDMS(d.sa - 90)}</div>
                    <div><strong>結束弧角 θe:</strong> ${toDMS(d.ea - 90)}</div>                
                    <div><strong>圓弧起點 Ps:</strong> (${pS.x.toFixed(4)}, ${pS.y.toFixed(4)})</div>
                    <div><strong>圓弧終點 Pe:</strong> (${pE.x.toFixed(4)}, ${pE.y.toFixed(4)})</div>
                    <div><strong>圓弧長度 S:</strong> ${len.toFixed(4)}</div>
                </div>
            </div>`;
    });
    lineData.forEach(d => {
        const len = Math.sqrt((d.pe.x - d.ps.x) ** 2 + (d.pe.y - d.ps.y) ** 2);
        html += `
            <div class="result-item" style="border-left: 6px solid ${d.color}; background: #f8f9fa; padding: 12px; border-radius: 4px;">
                <h4 style="margin:0 0 8px 0; color: ${d.color};">線段 ${d.name}</h4>
                <div style="font-size: 0.8em;">                
                    <div><strong>線段起點 Ps:</strong> (${d.ps.x.toFixed(4)}, ${d.ps.y.toFixed(4)})</div>
                    <div><strong>線段終點 Pe:</strong> (${d.pe.x.toFixed(4)}, ${d.pe.y.toFixed(4)})</div>
                    <div><strong>線段長度 L:</strong> ${len.toFixed(4)}</div>
                </div>
            </div>`;
    });
    html += `</div>`;
    resultsContainer.innerHTML = html;
    document.getElementById('resultsCard').style.display = 'block';
}

function updateDoubleCircleInfoPanel(resultsContainer, areaResultsContainer) {
    const inner = doubleCircleArcs.inner;
    const outer = doubleCircleArcs.outer;
    const t_val = Math.max(0, parseFloat(document.getElementById('excavationThickness')?.value || 0.2));

    const theta1 = Math.abs(inner.p1.endAngle - inner.p1.startAngle) * Math.PI / 180;
    const theta3 = Math.abs(inner.p3.endAngle - inner.p3.startAngle) * Math.PI / 180;
    const theta4 = Math.abs(outer.p4.endAngle - outer.p4.startAngle) * Math.PI / 180;
    const theta6 = Math.abs(outer.p6.endAngle - outer.p6.startAngle) * Math.PI / 180;

    function getPolyArea(pts) {
        let area = 0;
        for (let i = 0; i < pts.length; i++) {
            let j = (i + 1) % pts.length;
            area += pts[i].x * pts[j].y;
            area -= pts[j].x * pts[i].y;
        }
        return Math.abs(area / 2);
    }

    const p1e = getPointOnCircle(inner.p1.cx, inner.p1.cy, inner.p1.r, inner.p1.endAngle);
    const p3s = getPointOnCircle(inner.p3.cx, inner.p3.cy, inner.p3.r, inner.p3.startAngle);
    const innerPolyArea = getPolyArea([{ x: inner.p1.cx, y: inner.p1.cy }, p1e, p3s, { x: inner.p3.cx, y: inner.p3.cy }]);

    const p4e = getPointOnCircle(outer.p4.cx, outer.p4.cy, outer.p4.r, outer.p4.endAngle);
    const p6s = getPointOnCircle(outer.p6.cx, outer.p6.cy, outer.p6.r, outer.p6.startAngle);
    const outerPolyArea = getPolyArea([{ x: outer.p4.cx, y: outer.p4.cy }, p4e, p6s, { x: outer.p6.cx, y: outer.p6.cy }]);

    const innerArea = 2 * (0.5 * inner.p1.r ** 2 * theta1 + 0.5 * inner.p3.r ** 2 * theta3 + innerPolyArea);
    const outerArea = 2 * (0.5 * outer.p4.r ** 2 * theta4 + 0.5 * outer.p6.r ** 2 * theta6 + outerPolyArea);
    const liningArea = outerArea - innerArea;

    const arc4Len = outer.p4.r * theta4;
    const line5Len = Math.sqrt((outer.line5.pe.x - outer.line5.ps.x) ** 2 + (outer.line5.pe.y - outer.line5.ps.y) ** 2);
    const arc6Len = outer.p6.r * theta6;
    const excavationArea = 2 * (arc4Len + line5Len + arc6Len) * t_val + outerArea;

    const areaHtml = `
    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin: 0 auto 15px auto; width: 100%;">
        <div style="flex: 0 1 180px; padding: 10px 12px; background: #fae1e1ff; border: 2px solid #f37171ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #ca2222ff; font-weight: bold;">預估開挖面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #ca2222ff; font-family: 'Courier New', monospace;"> ${excavationArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 0 1 180px; padding: 10px 12px; background: #ffddaaff; border: 2px solid #f3a566ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #fd7200ff; font-weight: bold;">襯砌外廓面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #fd7200ff; font-family: 'Courier New', monospace;"> ${outerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 0 1 180px; padding: 10px 12px; background: #e8f5e9; border: 2px solid #68ac6dff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #1b5e20; font-weight: bold;">襯砌內廓面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #1b5e20; font-family: 'Courier New', monospace;"> ${innerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 0 1 180px; padding: 10px 12px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #1565c0; font-weight: bold;">襯砌斷面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #0d47a1; font-family: 'Courier New', monospace;">${liningArea.toFixed(2)} m²</span>
        </div>
    </div>`;

    if (areaResultsContainer) areaResultsContainer.innerHTML = areaHtml;

    const itemsToDisplay = [
        { type: 'arc', name: 'Arc 1L', a: inner.p1, isMirror: false },
        { type: 'arc', name: 'Arc 1R', a: inner.p1, isMirror: true },
        { type: 'arc', name: 'Arc 4L', a: outer.p4, isMirror: false },
        { type: 'arc', name: 'Arc 4R', a: outer.p4, isMirror: true },
        { type: 'line', name: 'Line 2L', l: inner.line2, isMirror: false },
        { type: 'line', name: 'Line 2R', l: inner.line2, isMirror: true },
        { type: 'line', name: 'Line 5L', l: outer.line5, isMirror: false },
        { type: 'line', name: 'Line 5R', l: outer.line5, isMirror: true },
        { type: 'arc', name: 'Arc 3L', a: inner.p3, isMirror: false },
        { type: 'arc', name: 'Arc 3R', a: inner.p3, isMirror: true },
        { type: 'arc', name: 'Arc 6L', a: outer.p6, isMirror: false },
        { type: 'arc', name: 'Arc 6R', a: outer.p6, isMirror: true }
    ];

    let html = `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">`;
    itemsToDisplay.forEach(item => {
        if (item.type === 'arc') {
            const a = item.a;
            const sa = item.isMirror ? 180 - a.startAngle : a.startAngle;
            const ea = item.isMirror ? 180 - a.endAngle : a.endAngle;
            const cx = item.isMirror ? -a.cx : a.cx;
            const ps = getPointOnCircle(cx, a.cy, a.r, sa);
            const pe = getPointOnCircle(cx, a.cy, a.r, ea);
            const len = a.r * Math.abs(ea - sa) * Math.PI / 180;

            html += `
                <div class="result-item" style="border-left: 6px solid ${a.color}; background: #f8f9fa; padding: 12px; border-radius: 4px;">
                    <h4 style="margin:0 0 8px 0; color: ${a.color};">圓弧 ${item.name}</h4>
                    <div style="font-size: 0.75em;">
                        <div><strong>圓弧圓心 P:</strong> (${cx.toFixed(4)}, ${a.cy.toFixed(4)})</div>
                        <div><strong>圓弧半徑 R:</strong> ${a.r.toFixed(4)}</div>
                        <div><strong>起始弧角 θs:</strong> ${toDMS(sa - 90)}</div>
                        <div><strong>結束弧角 θe:</strong> ${toDMS(ea - 90)}</div>
                        <div><strong>圓弧長度 S:</strong> ${len.toFixed(4)}</div>
                        <div><strong>圓弧起點 Ps:</strong> (${ps.x.toFixed(4)}, ${ps.y.toFixed(4)})</div>
                        <div><strong>圓弧終點 Pe:</strong> (${pe.x.toFixed(4)}, ${pe.y.toFixed(4)})</div>
                    </div>
                </div>`;
        } else if (item.type === 'line') {
            const l = item.l;
            const ps = item.isMirror ? { x: -l.ps.x, y: l.ps.y } : l.ps;
            const pe = item.isMirror ? { x: -l.pe.x, y: l.pe.y } : l.pe;
            const len = Math.sqrt((pe.x - ps.x) ** 2 + (pe.y - ps.y) ** 2);
            html += `
                <div class="result-item" style="border-left: 6px solid ${l.color}; background: #f8f9fa; padding: 12px; border-radius: 4px;">
                    <h4 style="margin:0 0 8px 0; color: ${l.color};">線段 ${item.name}</h4>
                    <div style="font-size: 0.80em;">
                        <div><strong>線段長度 L:</strong> ${len.toFixed(4)}</div>
                        <div><strong>線段起點 Ps:</strong> (${ps.x.toFixed(4)}, ${ps.y.toFixed(4)})</div>
                        <div><strong>線段終點 Pe:</strong> (${pe.x.toFixed(4)}, ${pe.y.toFixed(4)})</div>
                    </div>
                </div>`;
        }
    });
    html += `</div>`;
    resultsContainer.innerHTML = html;
    document.getElementById('resultsCard').style.display = 'block';
}

// ---- 四心圓 Info Panel ----
function updateQuadInfoPanel(resultsContainer, areaResultsContainer) {
    const p1 = quadCircleArcs[0], p2 = quadCircleArcs[1], p3 = quadCircleArcs[2], p4 = quadCircleArcs[3];
    const p5 = quadCircleArcs[4], p6 = quadCircleArcs[5], p7 = quadCircleArcs[6], p8 = quadCircleArcs[7];

    // Sector area helper
    function sectorArea(arc) {
        return 0.5 * arc.r * arc.r * Math.abs(arc.endAngle - arc.startAngle) * Math.PI / 180;
    }
    // Triangle area helper
    function triArea(a, b, c) {
        return Math.abs(0.5 * (a.cx * (b.cy - c.cy) + b.cx * (c.cy - a.cy) + c.cx * (a.cy - b.cy)));
    }
    // Arc length helper
    function arcLen(arc) {
        return arc.r * Math.abs(arc.endAngle - arc.startAngle) * Math.PI / 180;
    }

    // 襯砌外廓面積 = 2*(sector5 + sector6 + sector7 + sector8 - tri(P5,P7,P8) + tri(P5,P6,P7))
    const outerArea = 2 * (sectorArea(p5) + sectorArea(p6) + sectorArea(p7) + sectorArea(p8)
        - triArea(p5, p7, p8) + triArea(p5, p6, p7));

    // 襯砌內廓面積 = 2*(sector1 + sector2 + sector3 + sector4 - tri(P1,P3,P4) + tri(P1,P2,P3))
    const innerArea = 2 * (sectorArea(p1) + sectorArea(p2) + sectorArea(p3) + sectorArea(p4)
        - triArea(p1, p3, p4) + triArea(p1, p2, p3));

    const liningArea = outerArea - innerArea;
    const t_val = Math.max(0, parseFloat(document.getElementById('excavationThickness')?.value || 0.2));

    // 預估開挖面積 = 2*(L5+L6+L7+L8)*t + outerArea
    const excavationArea = 2 * (arcLen(p5) + arcLen(p6) + arcLen(p7) + arcLen(p8)) * t_val + outerArea;

    const allArcs = getAllArcs();

    // 1. Area Results HTML
    let areaHtml = `
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #fae1e1ff; border: 2px solid #f37171ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #ca2222ff; font-weight: bold; font-size: 0.95rem;">預估開挖面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #ca2222ff; font-family: 'Courier New', monospace;"> ${excavationArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #ffddaaff; border: 2px solid #f3a566ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #fd7200ff; font-weight: bold; font-size: 0.95rem;">襯砌外廓面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #fd7200ff; font-family: 'Courier New', monospace;"> ${outerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e8f5e9; border: 2px solid #68ac6dff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #1b5e20; font-weight: bold; font-size: 0.95rem;">襯砌內廓面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #1b5e20; font-family: 'Courier New', monospace;"> ${innerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #1565c0; font-weight: bold; font-size: 0.95rem;">襯砌斷面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #0d47a1; font-family: 'Courier New', monospace;">${liningArea.toFixed(2)} m²</span>
        </div>
    </div>
    `;
    if (areaResultsContainer) areaResultsContainer.innerHTML = areaHtml;

    // 2. Arc Results HTML - display order per user spec:
    // Arc1L, Arc1R, Arc5L, Arc5R, Arc2L, Arc2R, Arc6L, Arc6R,
    // Arc3L, Arc3R, Arc7L, Arc7R, Arc4L, Arc4R, Arc8L, Arc8R
    let arcHtml = `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">`;
    const displayOrder = [0, 8, 4, 12, 1, 9, 5, 13, 2, 10, 6, 14, 3, 11, 7, 15];
    displayOrder.forEach((idx) => {
        const a = allArcs[idx];
        if (!a) return;
        arcHtml += `
        <div class="result-item" style="border-left: 6px solid ${a.color}; margin-bottom: 0px; padding: 12px; background: #f8f9fa; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h4 style="margin:0 0 8px 0; color: ${a.color}; border-bottom: 1px solid #eee; padding-bottom: 4px;">圓弧 ${a.name}</h4>
            <div style="font-size: 0.75em; line-height: 1.6;">
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

function updateTripleInfoPanel(resultsContainer, areaResultsContainer) {
    const outerArea = calculateTotalArea(tripleCircleArcs[3], tripleCircleArcs[4], tripleCircleArcs[5]);
    const innerArea = calculateTotalArea(tripleCircleArcs[0], tripleCircleArcs[1], tripleCircleArcs[2]);
    const liningArea = outerArea - innerArea;
    const t_val = Math.max(0, parseFloat(document.getElementById('excavationThickness')?.value || 0.2));
    const excavationArea = outerArea + calculateExcavationArea(tripleCircleArcs[3], tripleCircleArcs[4], tripleCircleArcs[5], t_val);

    const allArcs = getAllArcs();

    // 1. Area Results HTML (Summary boxes below SVG)
    let areaHtml = `
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #fae1e1ff; border: 2px solid #f37171ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #ca2222ff; font-weight: bold; font-size: 0.95rem;">預估開挖面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #ca2222ff; font-family: 'Courier New', monospace;"> ${excavationArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #ffddaaff; border: 2px solid #f3a566ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #fd7200ff; font-weight: bold; font-size: 0.95rem;">襯砌外廓面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #fd7200ff; font-family: 'Courier New', monospace;"> ${outerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e8f5e9; border: 2px solid #68ac6dff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #1b5e20; font-weight: bold; font-size: 0.95rem;">襯砌內廓面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #1b5e20; font-family: 'Courier New', monospace;"> ${innerArea.toFixed(2)} m²</span>
        </div>
        <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
            <span style="color: #1565c0; font-weight: bold; font-size: 0.95rem;">襯砌斷面積:</span>
            <span style="font-size: 1.1rem; font-weight: bold; color: #0d47a1; font-family: 'Courier New', monospace;">${liningArea.toFixed(2)} m²</span>
        </div>
    </div>
    `;
    if (areaResultsContainer) areaResultsContainer.innerHTML = areaHtml;

    // 2. Arc Results HTML (Detailed results panel further down)
    let arcHtml = `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;"> `;
    const displayOrder = [0, 6, 3, 9, 1, 7, 4, 10, 2, 8, 5, 11];
    displayOrder.forEach((idx) => {
        const a = allArcs[idx];
        if (!a) return;

        arcHtml += `
        <div class="result-item" style="border-left: 6px solid ${a.color}; margin-bottom: 0px; padding: 12px; background: #f8f9fa; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h4 style="margin:0 0 8px 0; color: ${a.color}; border-bottom: 1px solid #eee; padding-bottom: 4px;">圓弧 ${a.name}</h4>
            <div style="font-size: 0.75em; line-height: 1.6;">
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
    arcHtml += `</div> `;

    resultsContainer.innerHTML = arcHtml;
    document.getElementById('resultsCard').style.display = 'block';
}

// ---- 正圓形 Info Panel ----
function updateCircularInfoPanel(resultsContainer, areaResultsContainer) {
    const inner = circularArcs.inner;
    const outer = circularArcs.outer;
    const t_val = Math.max(0, parseFloat(document.getElementById('excavationThickness')?.value || 0.2));

    const thetaInner = Math.abs(inner.endAngle - inner.startAngle) * Math.PI / 180;
    const thetaOuter = Math.abs(outer.endAngle - outer.startAngle) * Math.PI / 180;

    const sectorArea1L = 0.5 * inner.r * inner.r * thetaInner;
    const sectorArea1R = sectorArea1L;
    const sectorArea2L = 0.5 * outer.r * outer.r * thetaOuter;
    const sectorArea2R = sectorArea2L;

    const arcLen2L = outer.r * thetaOuter;
    const arcLen2R = arcLen2L;

    const innerArea = sectorArea1L + sectorArea1R;
    const outerArea = sectorArea2L + sectorArea2R;
    const liningArea = outerArea - innerArea;
    const excavationArea = (arcLen2L + arcLen2R) * t_val + outerArea;

    const areaHtml = `
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #fae1e1ff; border: 2px solid #f37171ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #ca2222ff; font-weight: bold;">預估開挖面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #ca2222ff; font-family: 'Courier New', monospace;"> ${excavationArea.toFixed(2)} m²</span>
            </div>
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #ffddaaff; border: 2px solid #f3a566ff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #fd7200ff; font-weight: bold;">襯砌外廓面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #fd7200ff; font-family: 'Courier New', monospace;"> ${outerArea.toFixed(2)} m²</span>
            </div>
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e8f5e9; border: 2px solid #68ac6dff; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #1b5e20; font-weight: bold;">襯砌內廓面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #1b5e20; font-family: 'Courier New', monospace;"> ${innerArea.toFixed(2)} m²</span>
            </div>
            <div style="flex: 1; min-width: 180px; padding: 10px 12px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center;">
                <span style="color: #1565c0; font-weight: bold;">襯砌斷面積:</span> <span style="font-size: 1.1rem; font-weight: bold; color: #0d47a1; font-family: 'Courier New', monospace;">${liningArea.toFixed(2)} m²</span>
            </div>
        </div>`;

    if (areaResultsContainer) areaResultsContainer.innerHTML = areaHtml;

    let html = `<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">`;

    const circArcs = getCircularArcs();
    circArcs.forEach(a => {
        html += `
            <div class="result-item" style="border-left: 6px solid ${a.color}; background: #f8f9fa; padding: 12px; border-radius: 4px;">
                <h4 style="margin:0 0 8px 0; color: ${a.color};">圓弧 ${a.name}</h4>
                <div style="font-size: 0.75em;">
                    <div><strong>圓弧圓心 P:</strong> (${a.cx.toFixed(4)}, ${a.cy.toFixed(4)})</div>
                    <div><strong>圓弧半徑 R:</strong> ${a.r.toFixed(4)}</div>
                    <div><strong>起始弧角 θs:</strong> ${toDMS(a.startAngle - 90)}</div>
                    <div><strong>結束弧角 θe:</strong> ${toDMS(a.endAngle - 90)}</div>
                    <div><strong>圓弧長度 S:</strong> ${a.length.toFixed(4)}</div>
                    <div><strong>圓弧起點 Ps:</strong> (${a.startX.toFixed(4)}, ${a.startY.toFixed(4)})</div>
                    <div><strong>圓弧終點 Pe:</strong> (${a.endX.toFixed(4)}, ${a.endY.toFixed(4)})</div>
                </div>
            </div>`;
    });
    html += `</div>`;
    resultsContainer.innerHTML = html;
    document.getElementById('resultsCard').style.display = 'block';
}

// ---- Returns 4 arc objects for circular mode (1L, 1R, 2L, 2R) ----
function getCircularArcs() {
    const inner = circularArcs.inner;
    const outer = circularArcs.outer;
    const result = [];

    // Arc 1L (inner left)
    const p1LS = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.startAngle);
    const p1LE = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
    const theta1L = Math.abs(inner.endAngle - inner.startAngle) * Math.PI / 180;
    result.push({
        name: 'Arc 1L', cx: inner.cx, cy: inner.cy, r: inner.r,
        startAngle: inner.startAngle, endAngle: inner.endAngle,
        length: inner.r * theta1L, startX: p1LS.x, startY: p1LS.y, endX: p1LE.x, endY: p1LE.y,
        color: inner.color
    });

    // Arc 1R (inner right, mirror)
    const sa1R = 180 - inner.startAngle;
    const ea1R = 180 - inner.endAngle;
    const p1RS = getPointOnCircle(-inner.cx, inner.cy, inner.r, sa1R);
    const p1RE = getPointOnCircle(-inner.cx, inner.cy, inner.r, ea1R);
    const theta1R = Math.abs(ea1R - sa1R) * Math.PI / 180;
    result.push({
        name: 'Arc 1R', cx: -inner.cx, cy: inner.cy, r: inner.r,
        startAngle: sa1R, endAngle: ea1R,
        length: inner.r * Math.abs(theta1R), startX: p1RS.x, startY: p1RS.y, endX: p1RE.x, endY: p1RE.y,
        color: inner.color
    });

    // Arc 2L (outer left)
    const p2LS = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.startAngle);
    const p2LE = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);
    const theta2L = Math.abs(outer.endAngle - outer.startAngle) * Math.PI / 180;
    result.push({
        name: 'Arc 2L', cx: outer.cx, cy: outer.cy, r: outer.r,
        startAngle: outer.startAngle, endAngle: outer.endAngle,
        length: outer.r * theta2L, startX: p2LS.x, startY: p2LS.y, endX: p2LE.x, endY: p2LE.y,
        color: outer.color
    });

    // Arc 2R (outer right, mirror)
    const sa2R = 180 - outer.startAngle;
    const ea2R = 180 - outer.endAngle;
    const p2RS = getPointOnCircle(-outer.cx, outer.cy, outer.r, sa2R);
    const p2RE = getPointOnCircle(-outer.cx, outer.cy, outer.r, ea2R);
    const theta2R = Math.abs(ea2R - sa2R) * Math.PI / 180;
    result.push({
        name: 'Arc 2R', cx: -outer.cx, cy: outer.cy, r: outer.r,
        startAngle: sa2R, endAngle: ea2R,
        length: outer.r * Math.abs(theta2R), startX: p2RS.x, startY: p2RS.y, endX: p2RE.x, endY: p2RE.y,
        color: outer.color
    });

    return result;
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
    const fontSize = (0.9 * scale).toFixed(3);
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
    const mode = getCurrentMode();
    const allArcs = [];

    if (mode === 'circular') {
        const inner = circularArcs.inner;
        const outer = circularArcs.outer;
        const pairs = [
            { a: inner, name: 'Arc 1', suffix: 'L', isMirror: false },
            { a: inner, name: 'Arc 1', suffix: 'R', isMirror: true },
            { a: outer, name: 'Arc 2', suffix: 'L', isMirror: false },
            { a: outer, name: 'Arc 2', suffix: 'R', isMirror: true }
        ];
        pairs.forEach(p => {
            const sa = p.isMirror ? 180 - p.a.startAngle : p.a.startAngle;
            const ea = p.isMirror ? 180 - p.a.endAngle : p.a.endAngle;
            const cx = p.isMirror ? -p.a.cx : p.a.cx;
            const ps = getPointOnCircle(cx, p.a.cy, p.a.r, sa);
            const pe = getPointOnCircle(cx, p.a.cy, p.a.r, ea);
            allArcs.push({
                name: p.name + p.suffix, cx, cy: p.a.cy, r: p.a.r, startAngle: sa, endAngle: ea,
                length: p.a.r * Math.abs(ea - sa) * Math.PI / 180,
                startX: ps.x, startY: ps.y, endX: pe.x, endY: pe.y, color: p.a.color
            });
        });
        return allArcs;
    }

    if (mode === 'double_circle') {
        const inner = doubleCircleArcs.inner;
        const outer = doubleCircleArcs.outer;
        const items = [
            { type: 'arc', a: inner.p1, name: 'Arc 1L', isMirror: false },
            { type: 'arc', a: inner.p1, name: 'Arc 1R', isMirror: true },
            { type: 'arc', a: outer.p4, name: 'Arc 4L', isMirror: false },
            { type: 'arc', a: outer.p4, name: 'Arc 4R', isMirror: true },
            { type: 'line', l: inner.line2, name: 'Line 2L', isMirror: false },
            { type: 'line', l: inner.line2, name: 'Line 2R', isMirror: true },
            { type: 'line', l: outer.line5, name: 'Line 5L', isMirror: false },
            { type: 'line', l: outer.line5, name: 'Line 5R', isMirror: true },
            { type: 'arc', a: inner.p3, name: 'Arc 3L', isMirror: false },
            { type: 'arc', a: inner.p3, name: 'Arc 3R', isMirror: true },
            { type: 'arc', a: outer.p6, name: 'Arc 6L', isMirror: false },
            { type: 'arc', a: outer.p6, name: 'Arc 6R', isMirror: true }
        ];
        items.forEach(item => {
            if (item.type === 'arc') {
                const a = item.a;
                const sa = item.isMirror ? 180 - a.startAngle : a.startAngle;
                const ea = item.isMirror ? 180 - a.endAngle : a.endAngle;
                const cx = item.isMirror ? -a.cx : a.cx;
                const pStart = getPointOnCircle(cx, a.cy, a.r, sa);
                const pEnd = getPointOnCircle(cx, a.cy, a.r, ea);
                allArcs.push({
                    name: item.name, cx, cy: a.cy, r: a.r, startAngle: sa, endAngle: ea,
                    length: a.r * Math.abs(ea - sa) * Math.PI / 180,
                    startX: pStart.x, startY: pStart.y, endX: pEnd.x, endY: pEnd.y, color: a.color
                });
            } else if (item.type === 'line') {
                const l = item.l;
                const ps = item.isMirror ? { x: -l.ps.x, y: l.ps.y } : l.ps;
                const pe = item.isMirror ? { x: -l.pe.x, y: l.pe.y } : l.pe;
                allArcs.push({
                    name: item.name, cx: 0, cy: 0, r: 0, startAngle: 0, endAngle: 0,
                    length: Math.sqrt((pe.x - ps.x) ** 2 + (pe.y - ps.y) ** 2),
                    startX: ps.x, startY: ps.y, endX: pe.x, endY: pe.y, color: l.color
                });
            }
        });
        return allArcs;
    }

    if (mode === 'horseshoe') {
        const inner = horseshoeArcs.inner;
        const outer = horseshoeArcs.outer;
        const color2 = '#28a745'; const color3 = '#007bff'; const color5 = '#1e7e34'; const color6 = '#0056b3';
        const items = [
            { a: inner, name: 'Arc 1L', isMirror: false }, { a: inner, name: 'Arc 1R', isMirror: true },
            { a: outer, name: 'Arc 4L', isMirror: false }, { a: outer, name: 'Arc 4R', isMirror: true }
        ];
        items.forEach(item => {
            const a = item.a;
            const sa = item.isMirror ? 180 - a.startAngle : a.startAngle;
            const ea = item.isMirror ? 180 - a.endAngle : a.endAngle;
            const cx = item.isMirror ? -a.cx : a.cx;
            const ps = getPointOnCircle(cx, a.cy, a.r, sa);
            const pe = getPointOnCircle(cx, a.cy, a.r, ea);
            allArcs.push({
                name: item.name, cx, cy: a.cy, r: a.r, startAngle: sa, endAngle: ea,
                length: a.r * Math.abs(ea - sa) * Math.PI / 180,
                startX: ps.x, startY: ps.y, endX: pe.x, endY: pe.y, color: a.color
            });
        });
        const p1e = getPointOnCircle(inner.cx, inner.cy, inner.r, inner.endAngle);
        const p4e = getPointOnCircle(outer.cx, outer.cy, outer.r, outer.endAngle);
        const lines = [
            { ps: p1e, pe: inner.p2e, name: 'Line 2L', color: color2, isMirror: false },
            { ps: { x: -p1e.x, y: p1e.y }, pe: { x: -inner.p2e.x, y: inner.p2e.y }, name: 'Line 2R', color: color2, isMirror: true },
            { ps: inner.p2e, pe: inner.p3e, name: 'Line 3L', color: color3, isMirror: false },
            { ps: { x: -inner.p2e.x, y: inner.p2e.y }, pe: { x: -inner.p3e.x, y: inner.p3e.y }, name: 'Line 3R', color: color3, isMirror: true },
            { ps: p4e, pe: outer.p5e, name: 'Line 5L', color: color5, isMirror: false },
            { ps: { x: -p4e.x, y: p4e.y }, pe: { x: -outer.p5e.x, y: outer.p5e.y }, name: 'Line 5R', color: color5, isMirror: true },
            { ps: outer.p5e, pe: outer.p6e, name: 'Line 6L', color: color6, isMirror: false },
            { ps: { x: -outer.p5e.x, y: outer.p5e.y }, pe: { x: -outer.p6e.x, y: outer.p6e.y }, name: 'Line 6R', color: color6, isMirror: true }
        ];
        lines.forEach(item => {
            allArcs.push({
                name: item.name, cx: 0, cy: 0, r: 0, startAngle: 0, endAngle: 0,
                length: Math.sqrt((item.pe.x - item.ps.x) ** 2 + (item.pe.y - item.ps.y) ** 2),
                startX: item.ps.x, startY: item.ps.y, endX: item.pe.x, endY: item.pe.y, color: item.color
            });
        });
        return allArcs;
    }

    if (mode === 'quad') {
        // 8 left arcs, then 8 right (mirrored) arcs
        quadCircleArcs.forEach((arc, i) => {
            const no = i + 1;
            const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
            const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);
            const theta = (arc.endAngle - arc.startAngle) * Math.PI / 180;
            allArcs.push({
                name: `Arc ${no}L`, cx: arc.cx, cy: arc.cy, r: arc.r,
                startAngle: arc.startAngle, endAngle: arc.endAngle,
                length: Math.abs(arc.r * theta), startX: pStart.x, startY: pStart.y, endX: pEnd.x, endY: pEnd.y, color: arc.color
            });
        });
        quadCircleArcs.forEach((arc, i) => {
            const no = i + 1;
            const startA = 180 - arc.startAngle; const endA = 180 - arc.endAngle;
            const pStart = getPointOnCircle(-arc.cx, arc.cy, arc.r, startA);
            const pEnd = getPointOnCircle(-arc.cx, arc.cy, arc.r, endA);
            const theta = (endA - startA) * Math.PI / 180;
            allArcs.push({
                name: `Arc ${no}R`, cx: -arc.cx, cy: arc.cy, r: arc.r, startAngle: startA, endAngle: endA,
                length: Math.abs(arc.r * theta), startX: pStart.x, startY: pStart.y, endX: pEnd.x, endY: pEnd.y, color: arc.color
            });
        });
        return allArcs;
    }

    // Default: Triple Mode
    tripleCircleArcs.forEach((arc, i) => {
        const no = i + 1;
        const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
        const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);
        const theta = (arc.endAngle - arc.startAngle) * Math.PI / 180;
        allArcs.push({
            name: `Arc ${no}L`, cx: arc.cx, cy: arc.cy, r: arc.r,
            startAngle: arc.startAngle, endAngle: arc.endAngle,
            length: Math.abs(arc.r * theta), startX: pStart.x, startY: pStart.y, endX: pEnd.x, endY: pEnd.y, color: arc.color
        });
    });
    tripleCircleArcs.forEach((arc, i) => {
        const no = i + 1;
        const startA = 180 - arc.startAngle; const endA = 180 - arc.endAngle;
        const pStart = getPointOnCircle(-arc.cx, arc.cy, arc.r, startA);
        const pEnd = getPointOnCircle(-arc.cx, arc.cy, arc.r, endA);
        const theta = (endA - startA) * Math.PI / 180;
        allArcs.push({
            name: `Arc ${no}R`, cx: -arc.cx, cy: arc.cy, r: arc.r, startAngle: startA, endAngle: endA,
            length: Math.abs(arc.r * theta), startX: pStart.x, startY: pStart.y, endX: pEnd.x, endY: pEnd.y, color: arc.color
        });
    });
    return allArcs;
}


async function saveAsDXF() {
    const projectNumber = document.getElementById('projectNumber')?.value.trim() || '';
    const projectName = document.getElementById('projectName')?.value.trim() || '';
    const tunnelName = document.getElementById('tunnelName')?.value.trim() || '';
    const tunnelTypeSelect = document.getElementById('tunnelType');
    const tunnelTypeText = tunnelTypeSelect ? tunnelTypeSelect.options[tunnelTypeSelect.selectedIndex].text : '';

    // 將非 ASCII 字元(如中文)轉為 \U+XXXX 格式以避免亂碼
    const escapeCAD = (str) => {
        if (!str) return "";
        return str.split("").map(char => {
            const code = char.charCodeAt(0);
            return code > 127 ? `\\U+${code.toString(16).toUpperCase().padStart(4, "0")}` : char;
        }).join("");
    };

    const geometries = getAllArcs();
    if (!geometries || geometries.length === 0) {
        alert("No geometry to export.");
        return;
    }

    let dxf = "";
    // fmt: 4位精度，無條件進位 (Strict Ceil)
    const fmt = (val) => {
        const factor = 10000;
        const v = Math.ceil(val * factor) / factor;
        return v.toFixed(4);
    };

    // 1. HEADER
    dxf += "0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$DWGCODEPAGE\n3\nUTF-8\n0\nENDSEC\n";

    // 2. TABLES
    dxf += "0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLTYPE\n70\n4\n";
    dxf += "0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid\n72\n65\n73\n0\n40\n0.0\n";
    dxf += "0\nLTYPE\n2\nDASHED\n70\n0\n3\nDashed\n72\n65\n73\n2\n40\n0.5\n49\n0.3\n49\n-0.2\n";
    dxf += "0\nLTYPE\n2\nDASHDOT\n70\n0\n3\nDashDot\n72\n65\n73\n4\n40\n0.6\n49\n0.3\n49\n-0.1\n49\n0.05\n49\n-0.1\n";
    dxf += "0\nLTYPE\n2\nCENTER\n70\n0\n3\nCenter\n72\n65\n73\n4\n40\n2.0\n49\n1.25\n49\n-0.25\n49\n0.25\n49\n-0.25\n";
    dxf += "0\nENDTAB\n";

    dxf += "0\nTABLE\n2\nLAYER\n70\n5\n";
    const layers = [
        { name: "01_Tunnel", color: 7, ltype: "CONTINUOUS" },
        { name: "02_Radial", color: 8, ltype: "DASHED" },
        { name: "03_Clearance", color: 4, ltype: "DASHDOT" },
        { name: "04_Center", color: 1, ltype: "CENTER" },
        { name: "05_Text", color: 7, ltype: "CONTINUOUS" },
        { name: "03_ControlPoints", color: 2, ltype: "CONTINUOUS" }
    ];
    layers.forEach(l => {
        dxf += `0\nLAYER\n2\n${l.name}\n70\n0\n62\n${l.color}\n6\n${l.ltype}\n`;
    });
    dxf += "0\nENDTAB\n";

    dxf += "0\nTABLE\n2\nSTYLE\n70\n1\n";
    dxf += "0\nSTYLE\n2\nStandard\n70\n0\n40\n0.0\n41\n1.0\n50\n0.0\n71\n0\n42\n0.2\n3\narial.ttf\n4\n\n";
    dxf += "0\nENDTAB\n0\nENDSEC\n";

    // 3. ENTITIES
    dxf += "0\nSECTION\n2\nENTITIES\n";

    const refR = geometries.find(g => g.r > 0)?.r || 4.125;
    // 使用者指定固定文字大小為 0.2
    const textHeight = 0.2;
    const clRange = 1.2 * refR;

    const normalizeRotation = (angle) => {
        let a = angle % 360;
        if (a < 0) a += 360;
        if (a > 90 && a < 270) return (a + 180) % 360;
        return a;
    };

    let minY = 0;
    geometries.forEach(geo => {
        if (geo.startY < minY) minY = geo.startY;
        if (geo.endY < minY) minY = geo.endY;
        if (geo.cy - geo.r < minY && geo.r > 0) minY = geo.cy - geo.r;
    });

    geometries.forEach(geo => {
        if (geo.r > 0) {
            // 使用 POLYLINE (R12 格式) 配合 Vertex Bulge 繪製圓弧，解決座標共點問題且確保相容性
            // Bulge = tan(centralAngle / 4)
            let centralAngle = geo.endAngle - geo.startAngle;
            while (centralAngle > 180) centralAngle -= 360;
            while (centralAngle < -180) centralAngle += 360;
            const bulge = Math.tan((centralAngle * Math.PI / 180) / 4);

            dxf += "0\nPOLYLINE\n8\n01_Tunnel\n66\n1\n70\n0\n";
            // Vertex 1
            dxf += "0\nVERTEX\n8\n01_Tunnel\n";
            dxf += `10\n${fmt(geo.startX)}\n20\n${fmt(geo.startY)}\n30\n0.0\n`;
            dxf += `42\n${fmt(bulge)}\n`;
            // Vertex 2
            dxf += "0\nVERTEX\n8\n01_Tunnel\n";
            dxf += `10\n${fmt(geo.endX)}\n20\n${fmt(geo.endY)}\n30\n0.0\n`;
            // End Polyline
            dxf += "0\nSEQEND\n8\n01_Tunnel\n";

            // 只標註左側(L)或預設未分左右的圓弧，排除右側(R)
            if (geo.name.includes('Arc') && (geo.name.endsWith('L') || !geo.name.includes('R'))) {
                const noMatch = geo.name.match(/\d+/);
                const no = noMatch ? parseInt(noMatch[0]) : 1;

                let isInner = true;
                const mode = getCurrentMode();
                if (mode === 'circular') isInner = (no === 1);
                else if (mode === 'horseshoe' || mode === 'double_circle') isInner = (no <= 3);
                else if (mode === 'quad') isInner = (no <= 4);
                else if (mode === 'triple') isInner = (no <= 3);

                // --- 標註徑向控制線與中心點，移除 PxS, PxE 標註文字 ---
                [{ x: geo.startX, y: geo.startY }, { x: geo.endX, y: geo.endY }].forEach((p) => {
                    // 控制線段
                    dxf += "0\nLINE\n8\n02_Radial\n";
                    dxf += `10\n${fmt(geo.cx)}\n20\n${fmt(geo.cy)}\n30\n0.0\n`;
                    dxf += `11\n${fmt(p.x)}\n21\n${fmt(p.y)}\n31\n0.0\n`;

                    // 點位 (POINT)
                    dxf += "0\nPOINT\n8\n03_ControlPoints\n";
                    dxf += `10\n${fmt(p.x)}\n20\n${fmt(p.y)}\n30\n0.0\n`;
                });

                // --- P (Center Point, with Coordinates) ---
                dxf += "0\nPOINT\n8\n03_ControlPoints\n";
                dxf += `10\n${fmt(geo.cx)}\n20\n${fmt(geo.cy)}\n30\n0.0\n`;

                const labelX = geo.cx + textHeight * 0.5;
                const labelY = isInner ? (geo.cy + textHeight * 0.5) : (geo.cy - textHeight * 0.5);
                const vAlign = isInner ? 1 : 3; // 1=Bottom, 3=Top

                dxf += "0\nTEXT\n8\n05_Text\n7\nStandard\n";
                dxf += `10\n${fmt(labelX)}\n20\n${fmt(labelY)}\n30\n0.0\n`;
                dxf += `11\n${fmt(labelX)}\n21\n${fmt(labelY)}\n31\n0.0\n`;
                dxf += `40\n${fmt(textHeight)}\n72\n0\n73\n${vAlign}\n`;
                dxf += `1\nP${no}(${fmt(geo.cx)},${fmt(geo.cy)})\n`;

                // --- R (Radius) ---
                const radiusLabelFactor = 0.5;
                let refX = geo.startX;
                let refY = geo.startY;
                let rotRadius = normalizeRotation(geo.startAngle);

                // 三心圓之R5標註位置改到P5~P5E，四心圓之R7標註位置改到P7~P7E
                if ((mode === 'triple' && no === 5) || (mode === 'quad' && no === 7)) {
                    refX = geo.endX;
                    refY = geo.endY;
                    rotRadius = normalizeRotation(geo.endAngle);
                }

                const midRX = geo.cx + (refX - geo.cx) * radiusLabelFactor;
                const midRY = geo.cy + (refY - geo.cy) * radiusLabelFactor;

                let perpAngle = rotRadius + 90;
                let isUpsideDown = (rotRadius > 90 && rotRadius < 270);
                if (isUpsideDown) {
                    perpAngle = rotRadius - 90;
                }

                let direction = isInner ? 1 : -1;
                if (isUpsideDown) direction = -direction;

                const radOffset = textHeight * 0.6 * direction;
                const rTextX = midRX + radOffset * Math.cos(perpAngle * Math.PI / 180);
                const rTextY = midRY + radOffset * Math.sin(perpAngle * Math.PI / 180);

                dxf += "0\nTEXT\n8\n05_Text\n7\nStandard\n";
                dxf += `10\n${fmt(rTextX)}\n20\n${fmt(rTextY)}\n30\n0.0\n11\n${fmt(rTextX)}\n21\n${fmt(rTextY)}\n31\n0.0\n`;
                dxf += `40\n${fmt(textHeight)}\n50\n${fmt(rotRadius)}\n72\n1\n73\n2\n`;
                dxf += `1\nR${no}=${fmt(geo.r)}\n`;

                // --- Theta (Arc Angle) ---
                const midAngle = (geo.startAngle + geo.endAngle) / 2;
                const thetaOffset = isInner ? -textHeight * 1.5 : textHeight * 1.5;
                const midArcPos = getPointOnCircle(geo.cx, geo.cy, geo.r + thetaOffset, midAngle);

                let rotTheta = normalizeRotation(midAngle + 90);

                const arcAngle = Math.abs(geo.endAngle - geo.startAngle);
                dxf += "0\nTEXT\n8\n05_Text\n7\nStandard\n";
                dxf += `10\n${fmt(midArcPos.x)}\n20\n${fmt(midArcPos.y)}\n30\n0.0\n11\n${fmt(midArcPos.x)}\n21\n${fmt(midArcPos.y)}\n31\n0.0\n`;
                dxf += `40\n${fmt(textHeight)}\n50\n${fmt(rotTheta)}\n72\n1\n73\n2\n`;
                let dmsString = toDMS(arcAngle).replace('°', '%%d');
                dxf += `1\n\\U+03B8${no}=${dmsString}\n`;
            }
        } else {
            // LINE
            dxf += "0\nLINE\n8\n01_Tunnel\n";
            dxf += `10\n${fmt(geo.startX)}\n20\n${fmt(geo.startY)}\n30\n0.0\n`;
            dxf += `11\n${fmt(geo.endX)}\n21\n${fmt(geo.endY)}\n31\n0.0\n`;

            if (geo.name.includes('Line') && (geo.name.endsWith('L') || !geo.name.includes('R'))) {
                // 增加控制點 (POINT)
                dxf += "0\nPOINT\n8\n03_ControlPoints\n";
                dxf += `10\n${fmt(geo.startX)}\n20\n${fmt(geo.startY)}\n30\n0.0\n`;
                dxf += "0\nPOINT\n8\n03_ControlPoints\n";
                dxf += `10\n${fmt(geo.endX)}\n20\n${fmt(geo.endY)}\n30\n0.0\n`;

                const noMatch = geo.name.match(/\d+/);
                const no = noMatch ? parseInt(noMatch[0]) : "";

                if (no) {
                    let isInner = true;
                    const mode = getCurrentMode();
                    if (mode === 'horseshoe' || mode === 'double_circle') isInner = (no <= 3);

                    const midX = (geo.startX + geo.endX) / 2;
                    const midY = (geo.startY + geo.endY) / 2;

                    let dx = geo.endX - geo.startX;
                    let dy = geo.endY - geo.startY;
                    let angleRad = Math.atan2(dy, dx);
                    let angleDeg = angleRad * 180 / Math.PI;

                    let textAngle = angleDeg;
                    if (textAngle > 90 || textAngle < -90) {
                        textAngle += 180;
                        if (textAngle > 360) textAngle -= 360;
                    }

                    let perpAngle = textAngle + 90;
                    let outVecAngle = Math.atan2(midY, midX) * 180 / Math.PI;
                    let angleDiff = Math.abs((perpAngle - outVecAngle + 540) % 360 - 180);
                    let pointsOut = angleDiff < 90;

                    let direction = isInner ? -1 : 1;
                    if (!pointsOut) direction = -direction;

                    const lineOffset = textHeight * 0.8 * direction;
                    const textX = midX + lineOffset * Math.cos(perpAngle * Math.PI / 180);
                    const textY = midY + lineOffset * Math.sin(perpAngle * Math.PI / 180);

                    dxf += "0\nTEXT\n8\n05_Text\n7\nStandard\n";
                    dxf += `10\n${fmt(textX)}\n20\n${fmt(textY)}\n30\n0.0\n11\n${fmt(textX)}\n21\n${fmt(textY)}\n31\n0.0\n`;
                    dxf += `40\n${fmt(textHeight)}\n50\n${fmt(textAngle)}\n72\n1\n73\n2\n`;
                    dxf += `1\nL${no}=${fmt(geo.length)}\n`;
                }
            }
        }
    });

    // --- 隧道名稱標題 (置中於斷面下方) ---
    const sectionTitle = escapeCAD(`${tunnelName}(${tunnelTypeText})`);

    // 放在最低點下方約 1.2 倍的 clRange 或是固定距離
    const titleY = minY - (textHeight * 5); // 稍微拉開距離
    dxf += "0\nTEXT\n8\n05_Text\n7\nStandard\n";
    dxf += `10\n0.0\n20\n${fmt(titleY)}\n30\n0.0\n`;
    dxf += `11\n0.0\n21\n${fmt(titleY)}\n31\n0.0\n`;
    dxf += `40\n${fmt(textHeight * 2.0)}\n72\n1\n73\n2\n`; // 字體稍微放大一點
    dxf += `1\n${sectionTitle}\n`;

    // 中心線
    dxf += "0\nLINE\n8\n04_Center\n";
    dxf += `10\n${fmt(-clRange)}\n20\n0\n30\n0\n11\n${fmt(clRange)}\n21\n0\n31\n0\n`;


    dxf += "0\nLINE\n8\n04_Center\n";
    dxf += `10\n0\n20\n${fmt(-clRange)} \n30\n0\n`;
    dxf += `11\n0\n21\n${fmt(clRange)} \n31\n0\n`;

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
                    dxf += `10\n${fmt(pt.x)} \n20\n${fmt(pt.y)} \n30\n0.0\n`;
                });

                dxf += "0\nSEQEND\n";
            }
        });
    }

    dxf += "0\nENDSEC\n0\nEOF\n";

    // =====================================================
    // 下載
    // =====================================================
    const blob = new Blob([dxf], { type: 'application/dxf' });
    const fullFilename = [projectNumber, projectName, tunnelName, tunnelTypeText]
        .filter(Boolean)
        .join('_')
        .replace(/\s+/g, '_') || 'Tunnel_Design';
    const fileName = `${fullFilename}.dxf`;

    if (window.showSaveFilePicker) {
        try {
            const handle = await window.showSaveFilePicker({
                suggestedName: fileName,
                types: [{
                    description: 'DXF File',
                    accept: { 'application/dxf': ['.dxf'] },
                }],
            });
            const writable = await handle.createWritable();
            await writable.write(blob);
            await writable.close();
            alert('已成功匯出 DXF 檔案！');
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error saving file:', err);
                traditionalDownloadBlob(blob, fileName);
            }
        }
    } else {
        traditionalDownloadBlob(blob, fileName);
    }
}

function traditionalDownloadBlob(blob, fileName) {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(link.href);
}


async function openProject() {
    if (window.showOpenFilePicker) {
        try {
            const [fileHandle] = await window.showOpenFilePicker({
                types: [{
                    description: 'SinoNATM Project File',
                    accept: { 'application/x-sinonatm': ['.spf'] }
                }],
                multiple: false
            });
            const file = await fileHandle.getFile();
            const text = await file.text();
            loadProjectFromText(text);
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error("Error opening file:", err);
                traditionalOpenProject();
            }
        }
    } else {
        traditionalOpenProject();
    }
}

function traditionalOpenProject() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.spf,.txt';

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
            tripleCircleArcs = data.arcs;
        }
        if (data.circularArcs) {
            circularArcs = data.circularArcs;
        }
        if (data.horseshoeArcs) {
            horseshoeArcs = data.horseshoeArcs;
        }
        if (data.doubleCircleArcs) {
            doubleCircleArcs = data.doubleCircleArcs;
        }
        if (data.quadCircleArcs) {
            quadCircleArcs = data.quadCircleArcs;
        }

        if (data.currentMode) {
            const selector = document.getElementById('tunnelType');
            if (selector) {
                selector.value = data.currentMode;
            }
        }

        if (data.envelopes) {
            envelopes = data.envelopes;
        }

        renderEnvelopeControls();
        updateTripleCircleArcsConnectorGeometry();
        if (data.currentMode === 'quad') updateQuadCircleArcsConnectorGeometry();
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

    const currentMode = getCurrentMode();
    const projectData = {
        projectNumber,
        projectName,
        tunnelName,
        currentMode,
        envelopes
    };

    // Only save the arcs for the current mode
    if (currentMode === 'triple') projectData.arcs = tripleCircleArcs;
    if (currentMode === 'circular') projectData.circularArcs = circularArcs;
    if (currentMode === 'horseshoe') projectData.horseshoeArcs = horseshoeArcs;
    if (currentMode === 'double_circle') projectData.doubleCircleArcs = doubleCircleArcs;
    if (currentMode === 'quad') projectData.quadCircleArcs = quadCircleArcs;

    // Add SavedTime at the very end
    projectData.SavedTime = new Date().toISOString();

    const text = JSON.stringify(projectData, null, 2);
    const fileName = `${projectNumber}${projectName}${tunnelName}.spf`;

    if (window.showSaveFilePicker) {
        try {
            const handle = await window.showSaveFilePicker({
                suggestedName: fileName,
                excludeAcceptAllOption: true,
                types: [
                    {
                        description: 'SinoNATM Project File',
                        accept: {
                            'application/x-sinonatm': ['.spf']
                        }
                    }
                ]
            });
            const writable = await handle.createWritable();
            await writable.write(text);
            await writable.close();
            alert(`專案已儲存成功！`);
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

async function saveNewSection() {
    const sectionData = {
        mode: getCurrentMode(),
        arcs: JSON.parse(JSON.stringify(tripleCircleArcs)),
        quadCircleArcs: JSON.parse(JSON.stringify(quadCircleArcs)),
        circularArcs: JSON.parse(JSON.stringify(circularArcs)),
        horseshoeArcs: JSON.parse(JSON.stringify(horseshoeArcs)),
        doubleCircleArcs: JSON.parse(JSON.stringify(doubleCircleArcs)),
        envelopes: JSON.parse(JSON.stringify(envelopes)),
        timestamp: new Date().toISOString()
    };
    await saveToDB('latest_section', sectionData);
    //alert('斷面已重新設定！');
}


async function saveSectionTemp() {
    const sectionData = {
        mode: getCurrentMode(),
        arcs: JSON.parse(JSON.stringify(tripleCircleArcs)),
        quadCircleArcs: JSON.parse(JSON.stringify(quadCircleArcs)),
        circularArcs: JSON.parse(JSON.stringify(circularArcs)),
        horseshoeArcs: JSON.parse(JSON.stringify(horseshoeArcs)),
        doubleCircleArcs: JSON.parse(JSON.stringify(doubleCircleArcs)),
        envelopes: JSON.parse(JSON.stringify(envelopes)),
        timestamp: new Date().toISOString()
    };
    await saveToDB('latest_section', sectionData);
    alert('斷面已儲存！');
}

async function restoreSectionFromDB() {
    const data = await getFromDB('latest_section');
    if (data && data.arcs) {
        tripleCircleArcs = data.arcs;
        if (data.quadCircleArcs) quadCircleArcs = data.quadCircleArcs;
        if (data.circularArcs) circularArcs = data.circularArcs;
        if (data.horseshoeArcs) horseshoeArcs = data.horseshoeArcs;
        if (data.doubleCircleArcs) doubleCircleArcs = data.doubleCircleArcs;
        if (data.envelopes) envelopes = data.envelopes;
        updateTripleCircleArcsConnectorGeometry();
        if (getCurrentMode() === 'quad') updateQuadCircleArcsConnectorGeometry();
        renderEnvelopeControls();
        drawSystem();
        autoFitViewBox();
        updateInfoPanel();
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
        const tunnelTypeSelect = document.getElementById('tunnelType');
        const tunnelType = tunnelTypeSelect ? tunnelTypeSelect.options[tunnelTypeSelect.selectedIndex].text : '';
        const fullFilename = [projectNumber, projectName, tunnelName, tunnelType]
            .filter(Boolean)
            .join('_')
            .replace(/\s+/g, '_') || 'Tunnel_Design';
        const fileName = `${fullFilename}.csv`;

        if (window.showSaveFilePicker) {
            try {
                const handle = await window.showSaveFilePicker({
                    suggestedName: fileName,
                    types: [{
                        description: 'CSV File',
                        accept: { 'text/csv': ['.csv'] },
                    }],
                });
                const writable = await handle.createWritable();
                await writable.write(blob);
                await writable.close();
                alert('已成功匯出 CSV 檔案！');
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error('Error saving file:', err);
                    traditionalDownloadBlob(blob, fileName);
                    alert('已成功匯出 CSV 檔案！');
                }
            }
        } else {
            traditionalDownloadBlob(blob, fileName);
            alert('已成功匯出 CSV 檔案！');
        }
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


function toggleTemplateMenu(envIdx) {
    const menu = document.getElementById(`template-menu-${envIdx}`);
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}


/**
 * Finds the intersection point of two circles.
 * c1, c2: {x, y}
 * r1, r2: radius
 * returnLeft: preference for the intersection point.
 */
function getCircleIntersection(c1, r1, c2, r2, returnLeft = false) {
    const dx = c2.x - c1.x;
    const dy = c2.y - c1.y;
    const d = Math.sqrt(dx * dx + dy * dy);

    if (d > r1 + r2 || d < Math.abs(r1 - r2) || d === 0) return null;

    const a = (r1 * r1 - r2 * r2 + d * d) / (2 * d);
    const h = Math.sqrt(Math.max(0, r1 * r1 - a * a));

    const x2 = c1.x + a * dx / d;
    const y2 = c1.y + a * dy / d;

    const pa = { x: x2 + h * dy / d, y: y2 - h * dx / d };
    const pb = { x: x2 - h * dy / d, y: y2 + h * dx / d };

    // Default to the one that maintains the tunnel shape (smaller X for left side)
    return (pa.x < pb.x) ? pa : pb;
}


// ------------------------------------------------------------
// Custom Floating Tooltip Logic
// ------------------------------------------------------------
let customTooltip = null;

function initCustomTooltip() {
    if (!document.getElementById('custom-handle-tooltip')) {
        customTooltip = document.createElement('div');
        customTooltip.id = 'custom-handle-tooltip';
        customTooltip.innerHTML = '<span class="tooltip-icon"></span><span class="tooltip-text"></span>';
        document.body.appendChild(customTooltip);
    } else {
        customTooltip = document.getElementById('custom-handle-tooltip');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initCustomTooltip();

    // Attach global mouse handlers for tooltip
    document.addEventListener('mousemove', (e) => {
        if (!customTooltip) return;

        let shouldShow = false;
        let tooltipName = '';
        let cursorIcon = '';

        if (activeDragIndex !== null && dragType) {
            // We are dragging
            shouldShow = true;
            tooltipName = document.body.getAttribute('data-active-drag-name') || dragType;
            cursorIcon = '👆'; // Active drag icon
        } else {
            // Hovering
            const target = e.target;
            // Check if it's an SVG element with class interactive-handle and data-name
            if (target && target.classList && target.classList.contains('interactive-handle') && target.getAttribute('data-name')) {
                shouldShow = true;
                tooltipName = target.getAttribute('data-name');
                cursorIcon = '🤚'; // Hover icon
            }
        }

        if (shouldShow) {
            customTooltip.querySelector('.tooltip-icon').textContent = cursorIcon;
            customTooltip.querySelector('.tooltip-text').textContent = tooltipName;

            // Position near cursor
            let x = e.clientX + 15;
            let y = e.clientY + 15;

            // Keep within window bounds
            const rect = customTooltip.getBoundingClientRect();
            if (x + rect.width > window.innerWidth) x = window.innerWidth - rect.width - 5;
            if (y + rect.height > window.innerHeight) y = window.innerHeight - rect.height - 5;

            customTooltip.style.left = x + 'px';
            customTooltip.style.top = y + 'px';
            customTooltip.style.opacity = '1';
        } else {
            customTooltip.style.opacity = '0';
        }
    });

    // Hide if mouse leaves document area
    document.addEventListener('mouseleave', () => {
        if (customTooltip) customTooltip.style.opacity = '0';
    });
});
