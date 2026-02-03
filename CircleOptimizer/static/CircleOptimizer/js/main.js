/**
 * Circle Optimizer - Main JavaScript
 * Updated for Manual 4-Arc Mode with Symmetry and Constrained Connections
 */

// Global State
let viewBoxState = { x: -50, y: -50, w: 100, h: 100 };
let isPanning = false;
let startPan = { x: 0, y: 0 };
let activeDragIndex = null;
let dragType = null; // 'center', 'radius', 'startAngle', 'endAngle'

// Main Data Structure for 4 Arcs
// Arc 1 & 2: Main arcs (Top/Bottom)
// Arc 3 & 4: Connector arcs (Left/Right)
// We store state for all, but Arc 3/4 are heavily constrained.
let arcs = [
    { id: 1, cx: 0, cy: 5, r: 30, startAngle: 10, endAngle: 170, color: '#007bff' },      // Top
    { id: 2, cx: 0, cy: 60, r: 70, startAngle: -110, endAngle: -70, color: '#dc3545' },   // Bottom
    { id: 3, cx: -35, cy: 10, r: 20, startAngle: 0, endAngle: 0, color: '#28a745' },      // Left (Connector)
    { id: 4, cx: 35, cy: 10, r: 20, startAngle: 0, endAngle: 0, color: '#fd7e14' }        // Right (Connector)
];

// Helper: Get point on circle
function getPointOnCircle(cx, cy, r, angleDeg) {
    const rad = angleDeg * Math.PI / 180;
    return {
        x: cx + r * Math.cos(rad),
        y: cy + r * Math.sin(rad)
    };
}

// Helper: Setup initial positions for connector arcs if needed
function initConnectors() {
    updateConnectorGeometry();
}

document.addEventListener('DOMContentLoaded', () => {
    bindZoomPanEvents();

    // Bind Inputs for Polygon Update
    document.querySelectorAll('.point-input input').forEach(input => {
        input.addEventListener('change', drawSystem);
    });

    initConnectors(); // Calc initial geometry
    drawSystem();
    autoFitViewBox();

    // Resize observer or initial fit
    setTimeout(autoFitViewBox, 100);
});


// ------------------------------------------------------------
// Geometry & Constraints
// ------------------------------------------------------------

function updateConnectorGeometry(masterConnectorIndex = null) {
    // Arc 1 (Top) & Arc 2 (Bottom) are masters for endpoints.

    // Arc 3 (Left): Connects Arc 1 End -> Arc 2 Start
    const p1_end = getPointOnCircle(arcs[0].cx, arcs[0].cy, arcs[0].r, arcs[0].endAngle);
    const p2_start = getPointOnCircle(arcs[1].cx, arcs[1].cy, arcs[1].r, arcs[1].startAngle);

    // Arc 4 (Right): Connects Arc 2 End -> Arc 1 Start
    const p1_start = getPointOnCircle(arcs[0].cx, arcs[0].cy, arcs[0].r, arcs[0].startAngle);
    const p2_end = getPointOnCircle(arcs[1].cx, arcs[1].cy, arcs[1].r, arcs[1].endAngle);

    // Symmetry Logic:
    if (masterConnectorIndex === 4) {
        // Update 4, then mirror 3
        updateConnector(arcs[3], p2_end, p1_start);

        // Mirror 3 from 4
        arcs[2].cx = -arcs[3].cx;
        arcs[2].cy = arcs[3].cy;
        // Re-calc 3 angles/radius based on endpoints + mirrored center
        updateConnector(arcs[2], p1_end, p2_start);
    } else {
        // Update 3, then mirror 4
        updateConnector(arcs[2], p1_end, p2_start);

        // Mirror 4 from 3
        arcs[3].cx = -arcs[2].cx;
        arcs[3].cy = arcs[2].cy;
        // Re-calc 4 angles/radius based on endpoints + mirrored center
        updateConnector(arcs[3], p2_end, p1_start);
    }
}

function updateConnector(arc, pStart, pEnd) {
    // 1. Calculate Chord Bisector
    // Midpoint
    const mx = (pStart.x + pEnd.x) / 2;
    const my = (pStart.y + pEnd.y) / 2;

    // Vector PStart -> PEnd
    const dx = pEnd.x - pStart.x;
    const dy = pEnd.y - pStart.y;

    // 2. constrain current arc.cx, arc.cy to this line
    // Project current C onto line (Perpendicular bisector)
    // Bisector vector is (-dy, dx)
    // P = M + t * (-dy, dx)

    const dcx = arc.cx - mx;
    const dcy = arc.cy - my;

    const len = Math.sqrt(dx * dx + dy * dy);
    if (len < 0.001) return;

    const ux = -dy / len;
    const uy = dx / len;

    // Project M->C onto U
    const proj = dcx * ux + dcy * uy;

    // New Center
    arc.cx = mx + proj * ux;
    arc.cy = my + proj * uy;

    // 3. Update Radius
    const rx = pStart.x - arc.cx;
    const ry = pStart.y - arc.cy;
    arc.r = Math.sqrt(rx * rx + ry * ry);

    // 4. Update Angles
    // Normal atan2
    const angStart = Math.atan2(pStart.y - arc.cy, pStart.x - arc.cx) * 180 / Math.PI;
    const angEnd = Math.atan2(pEnd.y - arc.cy, pEnd.x - arc.cx) * 180 / Math.PI;

    arc.startAngle = angStart;
    arc.endAngle = angEnd;
}


// ------------------------------------------------------------
// Rendering
// ------------------------------------------------------------

function drawSystem() {
    const canvas = document.getElementById('canvas');
    if (!canvas) return;

    // Clear Groups
    const shapeGroup = document.getElementById('shapeGroup');
    const circlesGroup = document.getElementById('circlesGroup');
    shapeGroup.innerHTML = '';
    circlesGroup.innerHTML = '';

    // 1. Draw Background Polygon (Envelope)
    drawPolygon(shapeGroup);

    // 2. Draw Arcs
    arcs.forEach((arc, i) => {
        drawArc(circlesGroup, arc, i);
    });

    // 3. Draw Info Table
    updateInfoPanel();
}

function drawPolygon(container) {
    const points = [];
    document.querySelectorAll('.point-input').forEach((div, index) => {
        const x = parseFloat(div.querySelector('.coord-x').value);
        const y = parseFloat(div.querySelector('.coord-y').value);
        if (!isNaN(x) && !isNaN(y)) points.push({ x, y, index });
    });

    if (points.length < 3) return;

    const d = points.map((p, i) => (i === 0 ? 'M' : 'L') + ` ${p.x} ${-p.y}`).join(' ') + ' Z';

    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    poly.setAttribute('d', d);
    poly.setAttribute('fill', 'rgba(0, 0, 0, 0.05)'); // Very light grey fill
    poly.setAttribute('stroke', '#000000'); // Black Stroke
    poly.setAttribute('stroke-width', '0.5');
    poly.setAttribute('stroke-dasharray', '2,2');
    container.appendChild(poly);

    // Draw Vertices
    points.forEach(p => {
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('cx', p.x);
        dot.setAttribute('cy', -p.y);
        dot.setAttribute('r', '0.8'); // Smaller size
        dot.setAttribute('fill', '#000000');
        dot.setAttribute('class', 'interactive-handle');
        dot.style.cursor = 'move';
        bindDrag(dot, p.index, 'polygonPoint');
        container.appendChild(dot);
    });
}

function drawArc(container, arc, index) {
    // Arc Path (Thinner Line Width: 0.5)
    const d = describeArc(arc.cx, -arc.cy, arc.r, arc.startAngle, arc.endAngle);
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', arc.color);
    path.setAttribute('stroke-width', '0.5'); // Reduced from 1.5
    container.appendChild(path);

    // Center Handle
    const center = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    center.setAttribute('cx', arc.cx);
    center.setAttribute('cy', -arc.cy);
    center.setAttribute('r', '1.5'); // Slightly smaller handle
    center.setAttribute('fill', arc.color);
    center.setAttribute('class', 'interactive-handle');
    center.style.cursor = 'move';
    bindDrag(center, index, 'center');
    container.appendChild(center);

    // On-Canvas Labels (Center & Radius)
    const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    labelGroup.style.pointerEvents = 'none'; // Don't block clicking

    // Center Label
    const cLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    cLabel.setAttribute('x', arc.cx);
    cLabel.setAttribute('y', -arc.cy + 4); // Offset below center
    cLabel.setAttribute('font-size', '2.5');
    cLabel.setAttribute('fill', arc.color);
    cLabel.setAttribute('text-anchor', 'middle');
    cLabel.textContent = `C(${arc.cx.toFixed(1)}, ${arc.cy.toFixed(1)})`;
    labelGroup.appendChild(cLabel);

    // Radius Label (Positioned at midpoint of arc or near radius handle)
    const midAngle = (arc.startAngle + arc.endAngle) / 2;
    const pMid = getPointOnCircle(arc.cx, arc.cy, arc.r, midAngle);
    // slightly offset outward
    const rLabelPos = getPointOnCircle(arc.cx, arc.cy, arc.r + 3, midAngle);

    const rLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    rLabel.setAttribute('x', rLabelPos.x);
    rLabel.setAttribute('y', -rLabelPos.y);
    rLabel.setAttribute('font-size', '2.5');
    rLabel.setAttribute('fill', arc.color);
    rLabel.setAttribute('text-anchor', 'middle');
    rLabel.textContent = `R:${arc.r.toFixed(1)}`;
    labelGroup.appendChild(rLabel);

    container.appendChild(labelGroup);

    // Handles for Arc 1/2
    if (index < 2) {
        const rHandle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        rHandle.setAttribute('cx', pMid.x);
        rHandle.setAttribute('cy', -pMid.y);
        rHandle.setAttribute('r', '1.2');
        rHandle.setAttribute('fill', 'white');
        rHandle.setAttribute('stroke', arc.color);
        rHandle.setAttribute('stroke-width', '0.5');
        rHandle.style.cursor = 'nwse-resize';
        bindDrag(rHandle, index, 'radius');
        container.appendChild(rHandle);

        const pStart = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.startAngle);
        const pEnd = getPointOnCircle(arc.cx, arc.cy, arc.r, arc.endAngle);

        const sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        sHandle.setAttribute('x', pStart.x - 1.2);
        sHandle.setAttribute('y', -pStart.y - 1.2);
        sHandle.setAttribute('width', '2.4');
        sHandle.setAttribute('height', '2.4');
        sHandle.setAttribute('fill', arc.color);
        sHandle.style.cursor = 'pointer';
        bindDrag(sHandle, index, 'startAngle');
        container.appendChild(sHandle);

        const eHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        eHandle.setAttribute('x', pEnd.x - 1.2);
        eHandle.setAttribute('y', -pEnd.y - 1.2);
        eHandle.setAttribute('width', '2.4');
        eHandle.setAttribute('height', '2.4');
        eHandle.setAttribute('fill', arc.color);
        eHandle.setAttribute('stroke', 'white');
        eHandle.style.cursor = 'pointer';
        bindDrag(eHandle, index, 'endAngle');
        container.appendChild(eHandle);
    }
}

// ------------------------------------------------------------
// Interaction
// ------------------------------------------------------------

function bindDrag(el, index, type) {
    el.addEventListener('mousedown', (e) => startDrag(e, index, type));
    el.addEventListener('touchstart', (e) => startDrag(e, index, type));
}

function startDrag(e, index, type) {
    e.preventDefault();
    e.stopPropagation();
    activeDragIndex = index;
    dragType = type;

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

    if (dragType === 'polygonPoint') {
        const div = document.querySelector(`.point-input[data-index="${activeDragIndex}"]`);
        if (div) {
            div.querySelector('.coord-x').value = mx.toFixed(1);
            div.querySelector('.coord-y').value = my.toFixed(1);

            // Auto-update viewbox if needed (optional, or just redraw)
            drawSystem();
            return;
        }
    }

    const arc = arcs[activeDragIndex];
    let master = null;

    if (activeDragIndex < 2) { // Arc 1 or 2
        if (dragType === 'center') {
            arc.cx = 0; // Constrain X
            arc.cy = my;
        } else if (dragType === 'radius') {
            const dx = mx - arc.cx;
            const dy = my - arc.cy;
            arc.r = Math.sqrt(dx * dx + dy * dy);
        } else if (dragType === 'startAngle') {
            const raw = Math.atan2(my - arc.cy, mx - arc.cx) * 180 / Math.PI;
            arc.startAngle = raw;
            // Symmetry: EndAngle = 180 - StartAngle
            let mirror = 180 - raw;
            while (mirror > 180) mirror -= 360;
            while (mirror <= -180) mirror += 360;
            arc.endAngle = mirror;
        } else if (dragType === 'endAngle') {
            const raw = Math.atan2(my - arc.cy, mx - arc.cx) * 180 / Math.PI;
            arc.endAngle = raw;
            // Symmetry: StartAngle = 180 - EndAngle
            let mirror = 180 - raw;
            while (mirror > 180) mirror -= 360;
            while (mirror <= -180) mirror += 360;
            arc.startAngle = mirror;
        }
    } else { // Arc 3 or 4
        // If dragging 3, master=3. If dragging 4, master=4.
        master = activeDragIndex;
        if (dragType === 'center') {
            arc.cx = mx;
            arc.cy = my;
        }
    }

    updateConnectorGeometry(master);
    drawSystem();
}

function endDrag() {
    activeDragIndex = null;
    dragType = null;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', endDrag);
    document.removeEventListener('touchmove', onDrag);
    document.removeEventListener('touchend', endDrag);
}


// ------------------------------------------------------------
// View Control
// ------------------------------------------------------------

function autoFitViewBox() {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    arcs.forEach(a => {
        for (let ang = 0; ang < 360; ang += 45) {
            const p = getPointOnCircle(a.cx, a.cy, a.r, ang);
            minX = Math.min(minX, p.x);
            maxX = Math.max(maxX, p.x);
            minY = Math.min(minY, p.y);
            maxY = Math.max(maxY, p.y);
        }
    });

    document.querySelectorAll('.point-input').forEach(div => {
        const x = parseFloat(div.querySelector('.coord-x').value);
        const y = parseFloat(div.querySelector('.coord-y').value);
        if (!isNaN(x) && !isNaN(y)) {
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
        }
    });

    if (minX === Infinity) return;

    const w = maxX - minX;
    const h = maxY - minY;
    const pad = Math.max(w, h) * 0.2;

    viewBoxState.x = minX - pad;
    viewBoxState.y = -(maxY + pad);
    viewBoxState.w = w + pad * 2;
    viewBoxState.h = h + pad * 2;

    updateCanvasViewBox();
    drawAxisWithTicks();
}

function updateCanvasViewBox() {
    const canvas = document.getElementById('canvas');
    if (canvas) {
        canvas.setAttribute('viewBox', `${viewBoxState.x} ${viewBoxState.y} ${viewBoxState.w} ${viewBoxState.h}`);
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
// Utilities
// ------------------------------------------------------------

function describeArc(x, y, radius, startAngle, endAngle) {
    const start = {
        x: x + radius * Math.cos(startAngle * Math.PI / 180),
        y: y - radius * Math.sin(startAngle * Math.PI / 180)
    };
    const end = {
        x: x + radius * Math.cos(endAngle * Math.PI / 180),
        y: y - radius * Math.sin(endAngle * Math.PI / 180)
    };

    let angleDiff = endAngle - startAngle;
    while (angleDiff < 0) angleDiff += 360;

    const largeArcFlag = angleDiff > 180 ? "1" : "0";
    const sweepFlag = "0";

    return [
        "M", start.x, start.y,
        "A", radius, radius, 0, largeArcFlag, sweepFlag, end.x, end.y
    ].join(" ");
}

function updateInfoPanel() {
    const container = document.getElementById('resultsContainer');
    if (!container) return;

    let html = '';
    arcs.forEach((a, i) => {
        const pStart = getPointOnCircle(a.cx, a.cy, a.r, a.startAngle);
        const pEnd = getPointOnCircle(a.cx, a.cy, a.r, a.endAngle);

        html += `
        <div class="result-item" style="border-left: 4px solid ${a.color}; margin-bottom: 10px; padding: 10px; background: #f8f9fa;">
            <h4 style="margin:0 0 5px 0;">圓弧 ${i + 1}</h4>
            <div style="font-size: 0.9em;">
                <div><strong>圓心:</strong> (${a.cx.toFixed(2)}, ${a.cy.toFixed(2)})</div>
                <div><strong>半徑:</strong> ${a.r.toFixed(2)}</div>
                <div><strong>角度:</strong> ${a.startAngle.toFixed(1)}° ~ ${a.endAngle.toFixed(1)}°</div>
                <div style="margin-top:4px; padding-top:4px; border-top:1px dashed #ddd;">
                    Start: (${pStart.x.toFixed(2)}, ${pStart.y.toFixed(2)})<br>
                    End: (${pEnd.x.toFixed(2)}, ${pEnd.y.toFixed(2)})
                </div>
            </div>
        </div>
        `;
    });

    container.innerHTML = html;
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

    // Grid/Tick styling
    const fontSize = Math.min(vb.w, vb.h) * 0.03;
    const tickLen = Math.min(vb.w, vb.h) * 0.015;

    // X Axis
    const xInterval = calculateTickInterval(vb.w);
    const xStart = Math.ceil(minX / xInterval) * xInterval;

    for (let x = xStart; x <= maxX; x += xInterval) {
        const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick.setAttribute('x1', x);
        tick.setAttribute('y1', -tickLen);
        tick.setAttribute('x2', x);
        tick.setAttribute('y2', tickLen);
        tick.setAttribute('stroke', '#bbb');
        tick.setAttribute('stroke-width', '0.5');
        axisGroup.appendChild(tick);

        if (Math.abs(x) > 0.0001) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', tickLen + fontSize);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', fontSize);
            text.setAttribute('fill', '#999');
            text.textContent = parseFloat(x.toFixed(2));
            axisGroup.appendChild(text);
        }
    }

    // Y Axis
    const yInterval = calculateTickInterval(vb.h);
    const yStart = Math.ceil(realMinY / yInterval) * yInterval;

    for (let y = yStart; y <= realMaxY; y += yInterval) {
        const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick.setAttribute('x1', -tickLen);
        tick.setAttribute('y1', -y);
        tick.setAttribute('x2', tickLen);
        tick.setAttribute('y2', -y);
        tick.setAttribute('stroke', '#bbb');
        tick.setAttribute('stroke-width', '0.5');
        axisGroup.appendChild(tick);

        if (Math.abs(y) > 0.0001) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', -tickLen - fontSize * 0.5);
            text.setAttribute('y', -y + fontSize * 0.4);
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
    xAxis.setAttribute('stroke-width', '1');
    axisGroup.appendChild(xAxis);

    const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    yAxis.setAttribute('x1', 0);
    yAxis.setAttribute('y1', minY);
    yAxis.setAttribute('x2', 0);
    yAxis.setAttribute('y2', maxY);
    yAxis.setAttribute('stroke', '#999');
    yAxis.setAttribute('stroke-width', '1');
    axisGroup.appendChild(yAxis);
}
