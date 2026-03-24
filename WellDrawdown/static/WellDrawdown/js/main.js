/**
 * WellDrawdown — 水理分析抽水預測系統 前端邏輯
 */
(function () {
    'use strict';

    // ─────────────────────────────────────────
    // 預設資料
    // ─────────────────────────────────────────
    const DEFAULT_STATION = [
        { x: 80, y: 250 },
        { x: 80, y: 310 },
        { x: 230, y: 310 },
        { x: 230, y: 250 },
    ];

    const DEFAULT_WELLS = [
        { name: 'W1', x: 70, y: 260 },
        { name: 'W2', x: 100, y: 260 },
        { name: 'W3', x: 140, y: 260 },
        { name: 'W4', x: 180, y: 260 },
        { name: 'W5', x: 220, y: 260 },
        { name: 'W6', x: 240, y: 280 },
        { name: 'W7', x: 240, y: 300 },
    ];

    let selectedMethod = 'both';

    // ─────────────────────────────────────────
    // DOM Ready
    // ─────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        initMethodButtons();
        initStationTable(DEFAULT_STATION);
        initWellTable(DEFAULT_WELLS);
        initEventListeners();
    });

    // ─────────────────────────────────────────
    // 方法選擇按鈕
    // ─────────────────────────────────────────
    function initMethodButtons() {
        const buttons = document.querySelectorAll('.method-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMethod = btn.dataset.method;
                toggleNeumanParams();
            });
        });
        toggleNeumanParams();
    }

    function toggleNeumanParams() {
        const panel = document.getElementById('neuman-params');
        if (selectedMethod === 'theis') {
            panel.classList.add('hidden');
        } else {
            panel.classList.remove('hidden');
        }
    }

    // ─────────────────────────────────────────
    // 車站外框座標表格
    // ─────────────────────────────────────────
    function initStationTable(data) {
        const tbody = document.getElementById('station-tbody');
        tbody.innerHTML = '';
        data.forEach((pt, i) => addStationRow(pt.x, pt.y, i + 1));
    }

    function addStationRow(x = 0, y = 0, idx) {
        const tbody = document.getElementById('station-tbody');
        if (!idx) idx = tbody.rows.length + 1;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" class="wd-checkbox station-row-check"></td>
            <td class="station-no text-xs text-gray-500 font-mono">${idx}</td>
            <td><input type="number" value="${x}" step="0.1" class="station-x"></td>
            <td><input type="number" value="${y}" step="0.1" class="station-y"></td>
        `;
        tbody.appendChild(tr);
    }

    function renumberStationRows() {
        const rows = document.querySelectorAll('#station-tbody tr');
        rows.forEach((tr, i) => {
            tr.querySelector('.station-no').textContent = i + 1;
        });
    }

    // ─────────────────────────────────────────
    // 抽水井座標表格
    // ─────────────────────────────────────────
    function initWellTable(data) {
        const tbody = document.getElementById('well-tbody');
        tbody.innerHTML = '';
        data.forEach((w) => addWellRow(w.name, w.x, w.y));
    }

    function addWellRow(name, x = 0, y = 0) {
        const tbody = document.getElementById('well-tbody');
        if (!name) name = `W${tbody.rows.length + 1}`;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" class="wd-checkbox well-row-check"></td>
            <td><input type="text" value="${name}" class="well-name"></td>
            <td><input type="number" value="${x}" step="0.1" class="well-x"></td>
            <td><input type="number" value="${y}" step="0.1" class="well-y"></td>
        `;
        tbody.appendChild(tr);
    }

    // ─────────────────────────────────────────
    // 事件監聽
    // ─────────────────────────────────────────
    function initEventListeners() {
        // 新增/刪除 車站座標
        document.getElementById('btn-add-station').addEventListener('click', () => {
            addStationRow();
            renumberStationRows();
        });
        document.getElementById('btn-del-station').addEventListener('click', () => {
            deleteCheckedRows('station-tbody', 'station-row-check');
            renumberStationRows();
        });
        document.getElementById('station-check-all').addEventListener('change', (e) => {
            toggleAllChecks('station-tbody', 'station-row-check', e.target.checked);
        });

        // 新增/刪除 抽水井
        document.getElementById('btn-add-well').addEventListener('click', () => {
            addWellRow();
        });
        document.getElementById('btn-del-well').addEventListener('click', () => {
            deleteCheckedRows('well-tbody', 'well-row-check');
        });
        document.getElementById('well-check-all').addEventListener('change', (e) => {
            toggleAllChecks('well-tbody', 'well-row-check', e.target.checked);
        });

        // 計算
        document.getElementById('btn-calculate').addEventListener('click', runCalculation);

        // 匯入 txt
        document.getElementById('file-import').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            try {
                const text = await file.text();

                // --- 解析 Station_Coordinate_All ---
                let stationData = [];
                const sIdx = text.indexOf('Station_Coordinate_All');
                const wIdx = text.indexOf('WellCoordinate_1');

                if (sIdx !== -1) {
                    const sText = text.substring(sIdx, wIdx !== -1 ? wIdx : text.length);
                    const arrRegex = /\[([\s0-9.,-]+)\]/g;
                    const matches = [];
                    let m;
                    while ((m = arrRegex.exec(sText)) !== null) matches.push(m[1]);

                    if (matches.length >= 2) {
                        const xs = matches[0].split(',').map(v => parseFloat(v));
                        const ys = matches[1].split(',').map(v => parseFloat(v));
                        for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
                            if (!isNaN(xs[i]) && !isNaN(ys[i])) {
                                stationData.push({ x: xs[i], y: ys[i] });
                            }
                        }
                    }
                }
                if (stationData.length > 0) initStationTable(stationData);

                // --- 解析 WellCoordinate_1 ---
                if (wIdx !== -1) {
                    const wText = text.substring(wIdx);
                    // Match inner arrays with robust regex
                    const arrRegex = /\[([\s0-9.,-]+)\]/g;
                    let wellPairs = [];
                    let m;
                    while ((m = arrRegex.exec(wText)) !== null) {
                        const vals = m[1].split(',').map(v => parseFloat(v));
                        if (vals.length >= 2 && !isNaN(vals[0]) && !isNaN(vals[1])) {
                            wellPairs.push({ name: `W${wellPairs.length + 1}`, x: vals[0], y: vals[1] });
                        }
                    }
                    if (wellPairs.length > 0) initWellTable(wellPairs);
                }
            } catch (err) {
                alert('讀取檔案失敗');
                console.error(err);
            }
            e.target.value = ''; // reset file input
        });
    }

    function deleteCheckedRows(tbodyId, checkClass) {
        const checks = document.querySelectorAll(`#${tbodyId} .${checkClass}`);
        checks.forEach(cb => {
            if (cb.checked) cb.closest('tr').remove();
        });
    }

    function toggleAllChecks(tbodyId, checkClass, checked) {
        const checks = document.querySelectorAll(`#${tbodyId} .${checkClass}`);
        checks.forEach(cb => cb.checked = checked);
    }

    // ─────────────────────────────────────────
    // 蒐集資料 & 呼叫 API
    // ─────────────────────────────────────────
    function collectData() {
        const params = {
            method: selectedMethod,
            excavation_depth: val('excavation_depth'),
            head: val('head'),
            S: val('S'),
            T: val('T'),
            t: val('t'),
        };
        if (selectedMethod !== 'theis') {
            params.Sy = val('Sy');
            params.Kh = val('Kh');
            params.Kv = val('Kv');
            params.b = val('b');
        }

        // 車站座標
        const stationRows = document.querySelectorAll('#station-tbody tr');
        params.station_coords = [];
        stationRows.forEach(tr => {
            params.station_coords.push({
                x: parseFloat(tr.querySelector('.station-x').value) || 0,
                y: parseFloat(tr.querySelector('.station-y').value) || 0,
            });
        });

        // 井位
        const wellRows = document.querySelectorAll('#well-tbody tr');
        params.wells = [];
        wellRows.forEach(tr => {
            params.wells.push({
                name: tr.querySelector('.well-name').value,
                x: parseFloat(tr.querySelector('.well-x').value) || 0,
                y: parseFloat(tr.querySelector('.well-y').value) || 0,
            });
        });

        return params;
    }

    function val(id) {
        return parseFloat(document.getElementById(id).value) || 0;
    }

    async function runCalculation() {
        const data = collectData();

        // 簡易驗證
        if (data.wells.length === 0) {
            alert('至少需要一口抽水井');
            return;
        }
        if (data.station_coords.length < 3) {
            alert('車站外框至少需要 3 個點位');
            return;
        }

        // 顯示 loading
        showLoading(true);

        try {
            const resp = await fetch(window.djangoUrls.calculate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await resp.json();

            if (!resp.ok || result.error) {
                throw new Error(result.error || '伺服器錯誤');
            }

            renderResults(result.data);
        } catch (err) {
            alert('計算失敗：' + err.message);
        } finally {
            showLoading(false);
        }
    }

    // ─────────────────────────────────────────
    // 渲染結果
    // ─────────────────────────────────────────
    function showLoading(show) {
        const status = document.getElementById('calc-status');
        const btn = document.getElementById('btn-calculate');
        if (show) {
            status.classList.remove('hidden');
            btn.disabled = true;
            btn.textContent = '計算中...';
        } else {
            status.classList.add('hidden');
            btn.disabled = false;
            btn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
                開始計算
            `;
        }
    }

    function renderResults(data) {
        document.getElementById('empty-result').classList.add('hidden');
        document.getElementById('result-contours').classList.remove('hidden');
        document.getElementById('result-tables').classList.remove('hidden');

        // Theis
        const theisResult = document.getElementById('theis-result');
        const theisTableSection = document.getElementById('theis-table-section');
        if (data.theis) {
            theisResult.classList.remove('hidden');
            theisTableSection.classList.remove('hidden');
            document.getElementById('theis-contour-img').src = 'data:image/png;base64,' + data.theis.contour;
            renderResultTable('theis-result-tbody', data.theis.table);
            theisResult.classList.add('wd-fade-in');
        } else {
            theisResult.classList.add('hidden');
            theisTableSection.classList.add('hidden');
        }

        // Neuman
        const neumanResult = document.getElementById('neuman-result');
        const neumanTableSection = document.getElementById('neuman-table-section');
        if (data.neuman) {
            neumanResult.classList.remove('hidden');
            neumanTableSection.classList.remove('hidden');
            document.getElementById('neuman-contour-img').src = 'data:image/png;base64,' + data.neuman.contour;
            renderResultTable('neuman-result-tbody', data.neuman.table);
            neumanResult.classList.add('wd-fade-in');
        } else {
            neumanResult.classList.add('hidden');
            neumanTableSection.classList.add('hidden');
        }
    }

    function renderResultTable(tbodyId, tableData) {
        const tbody = document.getElementById(tbodyId);
        tbody.innerHTML = '';
        tableData.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="font-bold text-red-600">${row.name}</td>
                <td>${row.Q_cmd}</td>
                <td>${row.Q_fs_cmd}</td>
                <td>${row.Q_fs_gpm}</td>
                <td>${row.pump_type}</td>
                <td>${row.pump_hp}</td>
                <td>${row.q_list_gpm}</td>
            `;
            tbody.appendChild(tr);
        });
    }

})();
