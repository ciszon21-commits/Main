// 重力管水理計算器專業版 JavaScript
// Professional Gravity Pipe Hydraulic Calculator

let currentMode = 1;

// 計算類型配置
const modes = {
    1: {
        title: "類型一：管線輸送流量表",
        inputs: ["roughness", "diameter", "slope"],
        btn: "產出流量表"
    },
    2: {
        title: "類型二：特定水深下的輸送容量",
        inputs: ["roughness", "diameter", "slope", "depth_ratio"],
        btn: "計算流速流量"
    },
    3: {
        title: "類型三：給定流量求水深與流速",
        inputs: ["roughness", "diameter", "slope", "flow_rate"],
        btn: "反算水深"
    },
    4: {
        title: "類型四：維持流速之坡降表",
        inputs: ["roughness", "diameter", "velocity"],
        btn: "產出坡降表"
    },
    5: {
        title: "類型五：維持流速與流量之坡降",
        inputs: ["roughness", "diameter", "velocity", "flow_rate"],
        btn: "計算設計坡降"
    },
    6: {
        title: "類型六：輸送流量之坡降表",
        inputs: ["roughness", "diameter", "flow_rate"],
        btn: "產出坡降表"
    },
    7: {
        title: "類型七：輸送流量與水深比求坡降",
        inputs: ["roughness", "diameter", "flow_rate", "depth_ratio"],
        btn: "計算所需坡降"
    },
    8: {
        title: "類型八：建議管徑計算",
        inputs: ["roughness", "velocity", "flow_rate", "depth_ratio"],
        btn: "自動選徑與計算"
    }
};

// 管材粗糙係數選項
const manningOptions = [
    { label: "0.013 (塑化管/鋼管/平滑混凝土)", value: "0.013" },
    { label: "0.015 (一般混凝土管)", value: "0.015" },
    { label: "0.012 (內襯/玻璃纖維管)", value: "0.012" },
    { label: "0.011 (極平滑PE/PVC)", value: "0.011" }
];

// 初始化
document.addEventListener('DOMContentLoaded', function () {
    initMenu();
    switchMode(1);
});

// 初始化側邊欄菜單
function initMenu() {
    const menuButtons = document.querySelectorAll('.mode-btn');
    menuButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const mode = parseInt(this.dataset.mode);
            switchMode(mode);
        });
    });
}

// 切換計算模式
function switchMode(mode) {
    currentMode = mode;

    // 更新側邊欄按鈕狀態
    document.querySelectorAll('.mode-btn').forEach(btn => {
        if (parseInt(btn.dataset.mode) === mode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // 更新標題
    document.getElementById('mode-title').textContent = modes[mode].title;

    // 渲染輸入欄位
    renderInputs();

    // 清空結果
    clearResults();

    // 更新建議文字
    updateSuggestion();
}

// 渲染輸入欄位
function renderInputs() {
    const config = modes[currentMode];
    const container = document.getElementById('input-form');

    let html = '';

    config.inputs.forEach(fieldName => {
        if (fieldName === 'roughness') {
            html += `
                <div class="input-group">
                    <label class="label-text text-emerald-700 font-bold">粗糙係數 n</label>
                    <select id="input-roughness" class="input-field">
                        ${manningOptions.map(opt =>
                `<option value="${opt.value}">${opt.label}</option>`
            ).join('')}
                    </select>
                </div>
            `;
        } else {
            const labelMap = {
                diameter: "管徑 (mm)",
                slope: "坡度 (m/m)",
                depth_ratio: "水深比 d/D (0.05-1.0)",
                flow_rate: "計畫流量 (CMD)",
                velocity: "設計流速 (m/s)"
            };

            const placeholderMap = {
                diameter: "例: 1000",
                slope: "例: 0.01",
                depth_ratio: "例: 0.5",
                flow_rate: "例: 43200",
                velocity: "例: 2.0"
            };

            html += `
                <div class="input-group">
                    <label class="label-text">${labelMap[fieldName]}</label>
                    <input type="number" id="input-${fieldName}" step="any" 
                           class="input-field" placeholder="${placeholderMap[fieldName]}">
                </div>
            `;
        }
    });

    html += `
        <button onclick="doCalculate()" 
                class="w-full bg-emerald-700 text-white font-bold py-3 rounded-lg shadow hover:bg-emerald-800 transition">
            ${config.btn}
        </button>
    `;

    container.innerHTML = html;
}

// 執行計算
async function doCalculate() {
    // 收集輸入數據
    const formData = {};
    modes[currentMode].inputs.forEach(field => {
        const input = document.getElementById(`input-${field}`);
        if (input) {
            formData[field] = input.value;
        }
    });

    // 驗證輸入
    if (!validateInput(formData)) {
        return;
    }

    // 顯示載入狀態
    showLoading();

    try {
        const url = window.djangoUrls[`type${currentMode}`];
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.status === 'success') {
            displayResults(result);
            updateSuggestion(result, formData);
        } else {
            showError(result.message || '計算失敗，請檢查輸入參數');
        }
    } catch (error) {
        showError('網路錯誤：' + error.message);
    }
}

// 驗證輸入
function validateInput(data) {
    for (let key in data) {
        if (!data[key] || data[key] === '') {
            showError('請填寫所有必填欄位');
            return false;
        }

        const value = parseFloat(data[key]);
        if (isNaN(value) || value <= 0) {
            showError('所有數值必須大於 0');
            return false;
        }

        // 特殊驗證
        if (key === 'depth_ratio' && (value < 0.05 || value > 1.0)) {
            showError('水深比必須在 0.05 到 1.0 之間');
            return false;
        }
    }
    return true;
}

// 顯示載入狀態
function showLoading() {
    document.getElementById('table-body').innerHTML = `
        <tr>
            <td colspan="10" class="p-8 text-center">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-700"></div>
                <p class="mt-2 text-gray-500">計算中...</p>
            </td>
        </tr>
    `;
}

// 顯示錯誤
function showError(message) {
    document.getElementById('suggestion-text').innerHTML = `
        <span class="text-red-600 font-bold">⚠️ ${message}</span>
    `;
}

// 清空結果
function clearResults() {
    document.getElementById('table-head').innerHTML = '<th>請先執行計算</th>';
    document.getElementById('table-body').innerHTML = `
        <tr><td class="p-4 text-center text-gray-400">尚無計算結果</td></tr>
    `;
}

// 顯示結果
function displayResults(result) {
    if (currentMode === 1) {
        displayType1Results(result.data);
    } else if (currentMode === 2 || currentMode === 7) {
        displaySingleResult(result.data);
    } else if (currentMode === 3) {
        displayType3Results(result.data);
    } else if (currentMode === 4 || currentMode === 6) {
        displayTableResults(result.data, currentMode);
    } else if (currentMode === 5) {
        displayType5Results(result.data);
    } else if (currentMode === 8) {
        displayType8Results(result.data);
    }
}

// 類型一：流量表
function displayType1Results(data) {
    let tableHead = `
        <tr>
            <th>水深比 d/D</th>
            <th>流速 V (m/s)</th>
            <th>流量 Q (CMD)</th>
            <th>法規檢核</th>
        </tr>
    `;

    let tableBody = '';
    data.forEach(row => {
        const check = checkVelocity(row.velocity);
        tableBody += `
            <tr class="result-row">
                <td>${row.depth_ratio.toFixed(2)}</td>
                <td>${row.velocity.toFixed(2)}</td>
                <td>${row.flow_rate.toLocaleString()}</td>
                <td>${check}</td>
            </tr>
        `;
    });

    document.getElementById('table-head').innerHTML = tableHead;
    document.getElementById('table-body').innerHTML = tableBody;
}

// 類型二、七：單一結果
function displaySingleResult(data) {
    let tableHead = `<tr><th>計算項目</th><th>結果值</th><th>法規檢核</th></tr>`;
    let tableBody = '';

    if (data.depth_ratio !== undefined) {
        tableBody += `<tr><td>水深比 d/D</td><td>${data.depth_ratio.toFixed(3)}</td><td>-</td></tr>`;
    }
    if (data.velocity !== undefined) {
        const check = checkVelocity(data.velocity);
        tableBody += `<tr><td>流速 V</td><td>${data.velocity.toFixed(2)} m/s</td><td>${check}</td></tr>`;
    }
    if (data.flow_rate !== undefined) {
        tableBody += `<tr><td>流量 Q</td><td>${data.flow_rate.toLocaleString()} CMD</td><td>-</td></tr>`;
    }
    if (data.slope !== undefined) {
        tableBody += `<tr><td>坡度 S</td><td>${data.slope.toFixed(6)} m/m</td><td>-</td></tr>`;
    }

    document.getElementById('table-head').innerHTML = tableHead;
    document.getElementById('table-body').innerHTML = tableBody;
}

// 類型三：水深流速表
function displayType3Results(data) {
    let tableHead = `
        <tr>
            <th>水深比 d/D</th>
            <th>流速 V (m/s)</th>
            <th>法規檢核</th>
            <th>狀態</th>
        </tr>
    `;

    let tableBody = '';
    data.table.forEach(row => {
        const check = checkVelocity(row.velocity);
        const highlight = row.is_target ? 'bg-emerald-100 font-bold' : '';
        tableBody += `
            <tr class="result-row ${highlight}">
                <td>${row.depth_ratio.toFixed(2)}</td>
                <td>${row.velocity.toFixed(2)}</td>
                <td>${check}</td>
                <td>${row.is_target ? '✓ 目標' : ''}</td>
            </tr>
        `;
    });

    document.getElementById('table-head').innerHTML = tableHead;
    document.getElementById('table-body').innerHTML = tableBody;
}

// 類型四、六：坡降表
function displayTableResults(data, type) {
    let tableHead = '';
    let tableBody = '';

    if (type === 4) {
        tableHead = `
            <tr>
                <th>水深比 d/D</th>
                <th>所需坡度 S (m/m)</th>
                <th>對應流量 Q (CMD)</th>
            </tr>
        `;
        data.forEach(row => {
            tableBody += `
                <tr class="result-row">
                    <td>${row.depth_ratio.toFixed(2)}</td>
                    <td>${row.slope.toFixed(6)}</td>
                    <td>${row.flow_rate.toLocaleString()}</td>
                </tr>
            `;
        });
    } else if (type === 6) {
        tableHead = `
            <tr>
                <th>水深比 d/D</th>
                <th>所需坡度 S (m/m)</th>
                <th>流速 V (m/s)</th>
                <th>法規檢核</th>
            </tr>
        `;
        data.forEach(row => {
            const check = checkVelocity(row.velocity);
            tableBody += `
                <tr class="result-row">
                    <td>${row.depth_ratio.toFixed(2)}</td>
                    <td>${row.slope.toFixed(6)}</td>
                    <td>${row.velocity.toFixed(2)}</td>
                    <td>${check}</td>
                </tr>
            `;
        });
    }

    document.getElementById('table-head').innerHTML = tableHead;
    document.getElementById('table-body').innerHTML = tableBody;
}

// 類型五：維持流速流量
function displayType5Results(data) {
    let tableHead = `
        <tr>
            <th>水深比 d/D</th>
            <th>所需坡度 S (m/m)</th>
            <th>實際流量 Q (CMD)</th>
            <th>流量誤差 (%)</th>
            <th>建議</th>
        </tr>
    `;

    let tableBody = '';
    data.table.forEach(row => {
        const isRecommended = row.depth_ratio === data.recommended_depth_ratio;
        const highlight = isRecommended ? 'bg-emerald-100 font-bold' : '';
        tableBody += `
            <tr class="result-row ${highlight}">
                <td>${row.depth_ratio.toFixed(2)}</td>
                <td>${row.slope.toFixed(6)}</td>
                <td>${row.actual_flow.toLocaleString()}</td>
                <td>${row.flow_error_percent.toFixed(2)}</td>
                <td>${isRecommended ? '✓ 建議' : ''}</td>
            </tr>
        `;
    });

    document.getElementById('table-head').innerHTML = tableHead;
    document.getElementById('table-body').innerHTML = tableBody;
}

// 類型八：建議管徑
function displayType8Results(data) {
    if (!data.success) {
        showError(data.message);
        return;
    }

    let tableHead = `<tr><th class="text-left">計算指標</th><th>數值</th></tr>`;
    let tableBody = `
        <tr><td class="text-left">理論所需管徑</td><td>${data.calculated_diameter} mm</td></tr>
        <tr class="bg-emerald-50 font-bold">
            <td class="text-left">建議標準管徑 (D)</td>
            <td class="text-emerald-700">${data.recommended_standard_diameter} mm</td>
        </tr>
        <tr class="bg-emerald-50 font-bold">
            <td class="text-left">設計所需坡度 (S)</td>
            <td class="text-emerald-700">${data.slope.toFixed(6)} m/m</td>
        </tr>
        <tr><td class="text-left">設計流速 (V)</td><td>${data.velocity.toFixed(2)} m/s</td></tr>
        <tr><td class="text-left">設計流量 (Q)</td><td>${data.flow_rate.toLocaleString()} CMD</td></tr>
        <tr><td class="text-left">設計水深比 (d/D)</td><td>${data.depth_ratio.toFixed(2)}</td></tr>
    `;

    document.getElementById('table-head').innerHTML = tableHead;
    document.getElementById('table-body').innerHTML = tableBody;
}

// 檢查流速是否符合法規
function checkVelocity(velocity) {
    if (velocity < 0.6) {
        return '<span class="text-red-500 font-bold">✖ 淤積風險</span>';
    } else if (velocity > 3.0) {
        return '<span class="text-orange-500 font-bold">⚠ 沖蝕風險</span>';
    } else {
        return '<span class="text-emerald-600">✔ 正常</span>';
    }
}

// 更新建議文字
function updateSuggestion(result, formData) {
    const suggestionDiv = document.getElementById('suggestion-text');

    if (!result) {
        suggestionDiv.innerHTML = '請輸入數據後點擊計算，系統將自動比對法規標準。';
        return;
    }

    let suggestion = '';

    switch (currentMode) {
        case 1:
            suggestion = `此管徑在給定坡度下，建議操作水深比為 0.5-0.8，以確保流速在法規範圍內（0.6-3.0 m/s）。`;
            break;
        case 2:
        case 7:
            if (result.data.velocity < 0.6) {
                suggestion = `⚠️ 流速過低（${result.data.velocity.toFixed(2)} m/s），可能造成淤積。建議增加坡度或減小管徑。`;
            } else if (result.data.velocity > 3.0) {
                suggestion = `⚠️ 流速過高（${result.data.velocity.toFixed(2)} m/s），可能造成沖蝕。建議減小坡度或增大管徑。`;
            } else {
                suggestion = `✓ 流速符合法規標準（0.6-3.0 m/s），設計合理。`;
            }
            break;
        case 3:
            suggestion = `目標流量對應的水深比為 ${result.data.target_depth_ratio?.toFixed(2)}，請確認流速是否在合理範圍內。`;
            break;
        case 4:
            suggestion = `維持恆定流速時，坡度需隨水位降低而增加。建議選擇水深比 0.5-0.8 的範圍進行設計。`;
            break;
        case 5:
            suggestion = `建議採用水深比 ${result.data.recommended_depth_ratio.toFixed(2)}，對應坡度 ${result.data.recommended_slope.toFixed(6)} m/m。`;
            break;
        case 6:
            suggestion = `注意：當水深比極低時，為輸送相同流量，所需坡度會呈現指數成長。建議避免低水深比設計。`;
            break;
        case 8:
            if (result.data.recommended_standard_diameter < 200) {
                suggestion = `⚠️ 依設施標準第13條，公共污水管最小管徑應為 200mm。`;
            } else {
                suggestion = `✓ 選徑符合規範。建議標準管徑為 ${result.data.recommended_standard_diameter} mm。`;
            }
            break;
    }

    suggestionDiv.innerHTML = suggestion;
}
