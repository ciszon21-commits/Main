// 重力管水理計算器 JavaScript
// Gravity Pipe Hydraulic Calculator JavaScript

let currentCalcType = null;

// 管材粗糙係數選項
const PIPE_MATERIALS = [
    { value: '0.013', label: '塑化管/鋼管/平滑混凝土' },
    { value: '0.015', label: '一般混凝土管' },
    { value: '0.012', label: '內襯/玻璃纖維管' },
    { value: '0.011', label: '極平滑PE/PVC' }
];

// 各計算類型的輸入欄位配置
const CALC_CONFIGS = {
    1: {
        title: '類型一：管線輸送流量表',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'slope', label: '坡度 (m/m)', type: 'number', step: '0.0001', required: true, hint: '例: 0.01' }
        ]
    },
    2: {
        title: '類型二：特定水深下的輸送容量',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'slope', label: '坡度 (m/m)', type: 'number', step: '0.0001', required: true, hint: '例: 0.01' },
            { name: 'depth_ratio', label: '水深比 (d/D)', type: 'number', step: '0.01', min: '0.01', max: '1.0', required: true, hint: '範圍: 0.01-1.0' }
        ]
    },
    3: {
        title: '類型三：水深與流速',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'slope', label: '坡度 (m/m)', type: 'number', step: '0.0001', required: true, hint: '例: 0.01' },
            { name: 'flow_rate', label: '流量 (CMD)', type: 'number', step: '1', required: true, hint: '例: 43200' }
        ]
    },
    4: {
        title: '類型四：維持流速之坡降表',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'velocity', label: '流速 (m/s)', type: 'number', step: '0.01', required: true, hint: '例: 2.0' }
        ]
    },
    5: {
        title: '類型五：維持流速之坡降',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'velocity', label: '流速 (m/s)', type: 'number', step: '0.01', required: true, hint: '例: 2.0' },
            { name: 'flow_rate', label: '流量 (CMD)', type: 'number', step: '1', required: true, hint: '例: 43200' }
        ]
    },
    6: {
        title: '類型六：輸送流量之坡降表',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'flow_rate', label: '流量 (CMD)', type: 'number', step: '1', required: true, hint: '例: 43200' }
        ]
    },
    7: {
        title: '類型七：輸送流量之坡降',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'diameter', label: '管徑 (mm)', type: 'number', step: '1', required: true, hint: '例: 1000' },
            { name: 'flow_rate', label: '流量 (CMD)', type: 'number', step: '1', required: true, hint: '例: 43200' },
            { name: 'depth_ratio', label: '水深比 (d/D)', type: 'number', step: '0.01', min: '0.01', max: '1.0', required: true, hint: '範圍: 0.01-1.0' }
        ]
    },
    8: {
        title: '類型八：建議管徑',
        fields: [
            { name: 'roughness', label: '粗糙係數 (n)', type: 'select', required: true },
            { name: 'velocity', label: '流速 (m/s)', type: 'number', step: '0.01', required: true, hint: '例: 2.0' },
            { name: 'flow_rate', label: '流量 (CMD)', type: 'number', step: '1', required: true, hint: '例: 43200' },
            { name: 'depth_ratio', label: '水深比 (d/D)', type: 'number', step: '0.01', min: '0.01', max: '1.0', required: true, hint: '範圍: 0.01-1.0' }
        ]
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', function () {
    initCalcTypeSelector();
});

// 初始化計算類型選擇器
function initCalcTypeSelector() {
    const cards = document.querySelectorAll('.calc-card');
    cards.forEach(card => {
        card.addEventListener('click', function () {
            const type = parseInt(this.dataset.type);
            selectCalcType(type);
        });
    });
}

// 選擇計算類型
function selectCalcType(type) {
    currentCalcType = type;
    const config = CALC_CONFIGS[type];

    // 隱藏選擇區，顯示輸入區
    document.getElementById('calcTypeSelector').classList.add('d-none');
    document.getElementById('calcInputSection').classList.remove('d-none');

    // 設置標題
    document.getElementById('calcTitle').textContent = config.title;

    // 生成表單欄位
    generateFormFields(config.fields);
}

// 生成表單欄位
function generateFormFields(fields) {
    const container = document.getElementById('formFields');
    container.innerHTML = '';

    fields.forEach(field => {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';

        const label = document.createElement('label');
        label.textContent = field.label;
        if (field.required) {
            label.innerHTML += ' <span style="color: red;">*</span>';
        }
        formGroup.appendChild(label);

        let input;
        if (field.type === 'select') {
            input = document.createElement('select');
            input.className = 'form-control';
            input.name = field.name;
            input.required = field.required;

            // 添加選項
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '請選擇管材類型';
            input.appendChild(defaultOption);

            PIPE_MATERIALS.forEach(material => {
                const option = document.createElement('option');
                option.value = material.value;
                option.textContent = `${material.label} (n=${material.value})`;
                input.appendChild(option);
            });
        } else {
            input = document.createElement('input');
            input.type = field.type;
            input.name = field.name;
            input.className = 'form-control';
            input.required = field.required;
            if (field.step) input.step = field.step;
            if (field.min) input.min = field.min;
            if (field.max) input.max = field.max;
        }

        formGroup.appendChild(input);

        if (field.hint) {
            const hint = document.createElement('small');
            hint.textContent = field.hint;
            formGroup.appendChild(hint);
        }

        container.appendChild(formGroup);
    });
}

// 執行計算
async function performCalculation() {
    const formData = collectFormData();

    if (!validateFormData(formData)) {
        return;
    }

    // 顯示載入狀態
    const button = document.querySelector('.btn-calculate');
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading-spinner"></span> 計算中...';
    button.disabled = true;

    try {
        const url = window.djangoUrls[`type${currentCalcType}`];
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
        } else {
            showError(result.message || '計算失敗，請檢查輸入參數');
        }
    } catch (error) {
        showError('網路錯誤：' + error.message);
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// 收集表單數據
function collectFormData() {
    const formData = {};
    const inputs = document.querySelectorAll('#formFields input, #formFields select');

    inputs.forEach(input => {
        formData[input.name] = input.value;
    });

    return formData;
}

// 驗證表單數據
function validateFormData(data) {
    for (let key in data) {
        if (!data[key] || data[key] === '') {
            showError('請填寫所有必填欄位');
            return false;
        }
    }
    return true;
}

// 顯示結果
function displayResults(result) {
    // 隱藏輸入區，顯示結果區
    document.getElementById('calcInputSection').classList.add('d-none');
    document.getElementById('calcResultsSection').classList.remove('d-none');

    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';

    // 顯示輸入參數摘要
    const summary = createResultSummary(result.input);
    container.appendChild(summary);

    // 根據計算類型顯示不同格式的結果
    if (currentCalcType === 1) {
        displayType1Results(result.data, container);
    } else if (currentCalcType === 2 || currentCalcType === 7) {
        displaySingleResult(result.data, container);
    } else if (currentCalcType === 3) {
        displayType3Results(result.data, container);
    } else if (currentCalcType === 4 || currentCalcType === 6) {
        displayTableResults(result.data, container, currentCalcType);
    } else if (currentCalcType === 5) {
        displayType5Results(result.data, container);
    } else if (currentCalcType === 8) {
        displayType8Results(result.data, container);
    }
}

// 創建結果摘要
function createResultSummary(input) {
    const summary = document.createElement('div');
    summary.className = 'result-summary';

    const title = document.createElement('h3');
    title.textContent = '輸入參數';
    summary.appendChild(title);

    for (let key in input) {
        const p = document.createElement('p');
        const label = getFieldLabel(key);
        p.innerHTML = `<strong>${label}:</strong> ${input[key]}`;
        summary.appendChild(p);
    }

    return summary;
}

// 獲取欄位標籤
function getFieldLabel(fieldName) {
    const labels = {
        'roughness': '粗糙係數',
        'diameter': '管徑 (mm)',
        'slope': '坡度 (m/m)',
        'depth_ratio': '水深比',
        'flow_rate': '流量 (CMD)',
        'velocity': '流速 (m/s)'
    };
    return labels[fieldName] || fieldName;
}

// 顯示類型1結果（流量表）
function displayType1Results(data, container) {
    const table = document.createElement('table');
    table.className = 'result-table';

    table.innerHTML = `
        <thead>
            <tr>
                <th>水深比 (d/D)</th>
                <th>流量 (CMD)</th>
                <th>流速 (m/s)</th>
            </tr>
        </thead>
        <tbody>
            ${data.map(row => `
                <tr>
                    <td>${row.depth_ratio.toFixed(2)}</td>
                    <td>${row.flow_rate}</td>
                    <td>${row.velocity.toFixed(2)}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    container.appendChild(table);
}

// 顯示單一結果
function displaySingleResult(data, container) {
    const resultDiv = document.createElement('div');
    resultDiv.className = 'result-summary';
    resultDiv.style.background = 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)';
    resultDiv.style.borderLeft = '4px solid #10b981';

    resultDiv.innerHTML = `
        <h3>計算結果</h3>
        ${data.depth_ratio ? `<p><strong>水深比:</strong> ${data.depth_ratio.toFixed(3)}</p>` : ''}
        ${data.velocity ? `<p><strong>流速:</strong> ${data.velocity.toFixed(2)} m/s</p>` : ''}
        ${data.flow_rate ? `<p><strong>流量:</strong> ${data.flow_rate} CMD</p>` : ''}
        ${data.slope ? `<p><strong>坡度:</strong> ${data.slope.toFixed(6)} m/m</p>` : ''}
    `;

    container.appendChild(resultDiv);
}

// 顯示類型3結果
function displayType3Results(data, container) {
    if (data.target_depth_ratio) {
        const info = document.createElement('div');
        info.className = 'result-summary';
        info.innerHTML = `<p><strong>達到目標流量的水深比:</strong> ${data.target_depth_ratio.toFixed(3)}</p>`;
        container.appendChild(info);
    }

    const table = document.createElement('table');
    table.className = 'result-table';

    table.innerHTML = `
        <thead>
            <tr>
                <th>水深比 (d/D)</th>
                <th>流速 (m/s)</th>
            </tr>
        </thead>
        <tbody>
            ${data.table.map(row => `
                <tr class="${row.is_target ? 'highlight' : ''}">
                    <td>${row.depth_ratio.toFixed(2)}</td>
                    <td>${row.velocity.toFixed(2)}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    container.appendChild(table);
}

// 顯示表格結果（類型4、6）
function displayTableResults(data, container, type) {
    const table = document.createElement('table');
    table.className = 'result-table';

    let headers = '<th>水深比 (d/D)</th>';
    let dataTemplate = row => `<td>${row.depth_ratio.toFixed(2)}</td>`;

    if (type === 4) {
        headers += '<th>坡度 (m/m)</th><th>流量 (CMD)</th>';
        dataTemplate = row => `
            <td>${row.depth_ratio.toFixed(2)}</td>
            <td>${row.slope.toFixed(6)}</td>
            <td>${row.flow_rate}</td>
        `;
    } else if (type === 6) {
        headers += '<th>坡度 (m/m)</th><th>流速 (m/s)</th>';
        dataTemplate = row => `
            <td>${row.depth_ratio.toFixed(2)}</td>
            <td>${row.slope.toFixed(6)}</td>
            <td>${row.velocity.toFixed(2)}</td>
        `;
    }

    table.innerHTML = `
        <thead>
            <tr>${headers}</tr>
        </thead>
        <tbody>
            ${data.map(row => `<tr>${dataTemplate(row)}</tr>`).join('')}
        </tbody>
    `;

    container.appendChild(table);
}

// 顯示類型5結果
function displayType5Results(data, container) {
    const recommendation = document.createElement('div');
    recommendation.className = 'result-summary';
    recommendation.innerHTML = `
        <h3>建議值</h3>
        <p><strong>建議水深比:</strong> ${data.recommended_depth_ratio.toFixed(2)}</p>
        <p><strong>建議坡度:</strong> ${data.recommended_slope.toFixed(6)} m/m</p>
    `;
    container.appendChild(recommendation);

    const table = document.createElement('table');
    table.className = 'result-table';

    table.innerHTML = `
        <thead>
            <tr>
                <th>水深比 (d/D)</th>
                <th>坡度 (m/m)</th>
                <th>實際流量 (CMD)</th>
                <th>流量誤差 (%)</th>
            </tr>
        </thead>
        <tbody>
            ${data.table.map(row => `
                <tr class="${row.depth_ratio === data.recommended_depth_ratio ? 'highlight' : ''}">
                    <td>${row.depth_ratio.toFixed(2)}</td>
                    <td>${row.slope.toFixed(6)}</td>
                    <td>${row.actual_flow}</td>
                    <td>${row.flow_error_percent.toFixed(2)}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    container.appendChild(table);
}

// 顯示類型8結果
function displayType8Results(data, container) {
    if (!data.success) {
        showError(data.message);
        return;
    }

    const resultDiv = document.createElement('div');
    resultDiv.className = 'result-summary';
    resultDiv.style.background = 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)';
    resultDiv.style.borderLeft = '4px solid #f59e0b';

    resultDiv.innerHTML = `
        <h3>建議管徑計算結果</h3>
        <p><strong>計算管徑:</strong> ${data.calculated_diameter} mm</p>
        <p><strong>建議標準管徑:</strong> ${data.recommended_standard_diameter} mm</p>
        <p><strong>所需坡度:</strong> ${data.slope.toFixed(6)} m/m</p>
        <p><strong>設計流速:</strong> ${data.velocity.toFixed(2)} m/s</p>
        <p><strong>設計流量:</strong> ${data.flow_rate} CMD</p>
        <p><strong>設計水深比:</strong> ${data.depth_ratio.toFixed(2)}</p>
    `;

    container.appendChild(resultDiv);
}

// 顯示錯誤訊息
function showError(message) {
    const container = document.getElementById('formFields');
    const existingError = container.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);

    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// 返回選擇頁面
function backToSelection() {
    document.getElementById('calcInputSection').classList.add('d-none');
    document.getElementById('calcTypeSelector').classList.remove('d-none');
    currentCalcType = null;
}

// 新計算
function newCalculation() {
    document.getElementById('calcResultsSection').classList.add('d-none');
    document.getElementById('calcTypeSelector').classList.remove('d-none');
    currentCalcType = null;
}
