/**
 * 排洪演算平台 - 圖表管理模組
 * 負責創建、管理和配置所有步驟的互動圖表
 */
window.fdFinalMaxLabelsVisible_1 = true;
window.fdFinalMaxLabelsVisible_2 = true;
window.fdFinalMaxLabelsVisible_3 = true;
class ChartManager {
    constructor() {
        this.charts = {};
        this.utils = window.fdUtils;

        // 圖表預設配置
        this.defaultConfigs = {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 800,
                easing: 'easeInOutQuart'
            }
        };
    }

    // ==================== 主要方法 ====================

    /**
     * 創建指定步驟的圖表
     * @param {number} step - 步驟編號 (1, 2, 3, 5)
     * @param {Object} chartData - 圖表數據
     * @returns {boolean} 創建是否成功
     */
    createChart(step, chartData) {
        try {
            // console.log(`開始創建步驟 ${step} 圖表...`);

            // 驗證輸入
            if (!this._validateInput(step, chartData)) {
                return false;
            }

            // 獲取圖表容器
            const ctx = this._getChartContext(step);
            if (!ctx) {
                return false;
            }

            // 銷毀現有圖表
            this.destroyChart(step);

            // 註冊自定義插件
            let plugins = [];
            if (step === 3) {
                plugins = [this._createDrainageLabelsPlugin()];
            }
            if (step === 5) {
                plugins = [this._createFinalMaxLabelsPlugin()];
                const canvas = ctx;
                let lastHoverKey = null;
                if (canvas) {
                    // 滑鼠移動：動態游標
                    canvas.onmousemove = (e) => {
                        const chart = this.getChart(5);
                        if (!chart) return;
                        const { x: xScale, y: yScale, y2: y2Scale } = chart.scales;
                        const { datasets } = chart.data;
                        const rect = canvas.getBoundingClientRect();
                        const mouseX = e.clientX - rect.left;
                        const mouseY = e.clientY - rect.top;
                        const ctx2 = chart.ctx;
                        ctx2.save();
                        ctx2.font = 'bold 13px Arial';
                        ctx2.textAlign = 'left';
                        ctx2.textBaseline = 'bottom';
                        const padding = 6;
                        const height = 40;
                        let hoverKey = null;

                        // hitbox 計算同下方
                        const labelHitboxes = [];
                        // ...（同你原本的 hitbox 計算，key:1/2/3, x, y, w, h）...
                        // 1. 水庫最高水位
                        const wlDs = datasets.find(ds => ds.label && ds.label.includes('水位'));
                        if (wlDs && wlDs.data && wlDs.data.length) {
                            let maxIdx = 0, maxVal = wlDs.data[0].y;
                            wlDs.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                            const pt = wlDs.data[maxIdx];
                            const x = xScale.getPixelForValue(pt.x);
                            const y = y2Scale.getPixelForValue(pt.y);
                            const label1 = '水庫最高水位';
                            const label2 = `EL. ${maxVal.toFixed(3)} m`;
                            const width = Math.max(ctx2.measureText(label1).width, ctx2.measureText(label2).width) + padding * 2;
                            const rectX = x + 8;
                            const rectY = y - 48;
                            labelHitboxes.push({ key: 1, x: rectX, y: rectY, w: width, h: height });
                        }
                        // 2. 最大總入流量
                        const inDs = datasets.find(ds => ds.label && (ds.label.includes('入流') || ds.label.includes('in')));
                        if (inDs && inDs.data && inDs.data.length) {
                            let maxIdx = 0, maxVal = inDs.data[0].y;
                            inDs.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                            const pt = inDs.data[maxIdx];
                            const x = xScale.getPixelForValue(pt.x);
                            const y = yScale.getPixelForValue(pt.y);
                            const label1 = '最大總入流量';
                            const label2 = `Qin,max=${maxVal.toFixed(3)} cms`;
                            const width = Math.max(ctx2.measureText(label1).width, ctx2.measureText(label2).width) + padding * 2;
                            const rectX = x - 164;
                            const rectY = y - 48;
                            labelHitboxes.push({ key: 2, x: rectX, y: rectY, w: width, h: height });
                        }
                        // 3. 最大總出流量
                        const outDs = datasets.find(ds => ds.label && (ds.label.includes('出流') || ds.label.includes('out')));
                        if (outDs && outDs.data && outDs.data.length) {
                            let maxIdx = 0, maxVal = outDs.data[0].y;
                            outDs.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                            const pt = outDs.data[maxIdx];
                            const x = xScale.getPixelForValue(pt.x);
                            const y = yScale.getPixelForValue(pt.y);
                            const label1 = '最大總出流量';
                            const label2 = `Qout,max=${maxVal.toFixed(3)} cms`;
                            const width = Math.max(ctx2.measureText(label1).width, ctx2.measureText(label2).width) + padding * 2;
                            const rectX = x + 8;
                            const rectY = y - 48;
                            labelHitboxes.push({ key: 3, x: rectX, y: rectY, w: width, h: height });
                        }
                        ctx2.restore();

                        for (const box of labelHitboxes) {
                            if (
                                mouseX >= box.x &&
                                mouseX <= box.x + box.w &&
                                mouseY >= box.y &&
                                mouseY <= box.y + box.h
                            ) {
                                hoverKey = box.key;
                                break;
                            }
                        }
                        lastHoverKey = hoverKey;
                        canvas.style.cursor = hoverKey ? 'pointer' : 'default';
                        // 觸發重繪（讓半透明提示顯示）
                        if (chart) chart.update('none');
                    };
                    // 新增：點擊時判斷點到哪個標籤
                    canvas.onclick = (e) => {
                        const chart = this.getChart(5);
                        if (!chart) return;
                        const { x: xScale, y: yScale, y2: y2Scale } = chart.scales;
                        const { datasets } = chart.data;
                        const rect = canvas.getBoundingClientRect();
                        const mouseX = e.clientX - rect.left;
                        const mouseY = e.clientY - rect.top;

                        // 取得 ctx 以便計算文字寬度
                        const ctx2 = chart.ctx;
                        ctx2.save();
                        ctx2.font = 'bold 13px Arial';
                        ctx2.textAlign = 'left';
                        ctx2.textBaseline = 'bottom';
                        const padding = 6;
                        const height = 40;

                        const labelHitboxes = [];

                        // 1. 水庫最高水位
                        const wlDs = datasets.find(ds => ds.label && ds.label.includes('水位'));
                        if (wlDs && wlDs.data && wlDs.data.length) {
                            let maxIdx = 0, maxVal = wlDs.data[0].y;
                            wlDs.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                            const pt = wlDs.data[maxIdx];
                            const x = xScale.getPixelForValue(pt.x);
                            const y = y2Scale.getPixelForValue(pt.y);
                            const label1 = '水庫最高水位';
                            const label2 = `EL. ${maxVal.toFixed(3)} m`;
                            const width = Math.max(ctx2.measureText(label1).width, ctx2.measureText(label2).width) + padding * 2;
                            const rectX = x + 8;
                            const rectY = y - 48;
                            labelHitboxes.push({
                                key: 1,
                                x: rectX,
                                y: rectY,
                                w: width,
                                h: height
                            });
                        }
                        // 2. 最大總入流量
                        const inDs = datasets.find(ds => ds.label && (ds.label.includes('入流') || ds.label.includes('in')));
                        if (inDs && inDs.data && inDs.data.length) {
                            let maxIdx = 0, maxVal = inDs.data[0].y;
                            inDs.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                            const pt = inDs.data[maxIdx];
                            const x = xScale.getPixelForValue(pt.x);
                            const y = yScale.getPixelForValue(pt.y);
                            const label1 = '最大總入流量';
                            const label2 = `Qin,max=${maxVal.toFixed(3)} cms`;
                            const width = Math.max(ctx2.measureText(label1).width, ctx2.measureText(label2).width) + padding * 2;
                            const rectX = x - 164;
                            const rectY = y - 48;
                            labelHitboxes.push({
                                key: 2,
                                x: rectX,
                                y: rectY,
                                w: width,
                                h: height
                            });
                        }
                        // 3. 最大總出流量
                        const outDs = datasets.find(ds => ds.label && (ds.label.includes('出流') || ds.label.includes('out')));
                        if (outDs && outDs.data && outDs.data.length) {
                            let maxIdx = 0, maxVal = outDs.data[0].y;
                            outDs.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                            const pt = outDs.data[maxIdx];
                            const x = xScale.getPixelForValue(pt.x);
                            const y = yScale.getPixelForValue(pt.y);
                            const label1 = '最大總出流量';
                            const label2 = `Qout,max=${maxVal.toFixed(3)} cms`;
                            const width = Math.max(ctx2.measureText(label1).width, ctx2.measureText(label2).width) + padding * 2;
                            const rectX = x + 8;
                            const rectY = y - 48;
                            labelHitboxes.push({
                                key: 3,
                                x: rectX,
                                y: rectY,
                                w: width,
                                h: height
                            });
                        }
                        ctx2.restore();

                        // 檢查是否點到標籤
                        let hit = false;
                        for (const box of labelHitboxes) {
                            if (
                                mouseX >= box.x &&
                                mouseX <= box.x + box.w &&
                                mouseY >= box.y &&
                                mouseY <= box.y + box.h
                            ) {
                                window['fdFinalMaxLabelsVisible_' + box.key] = !window['fdFinalMaxLabelsVisible_' + box.key];
                                hit = true;
                                break;
                            }
                        }
                        if (hit) {
                            chart.update();
                        }
                    };

                    canvas._fdFinalMaxLabelsHoverKey = () => lastHoverKey;
                }
            }

            // 創建新圖表
            this.charts[step] = new Chart(ctx, {
                type: 'line',
                data: this._prepareChartData(step, chartData),
                options: this._createChartOptions(step, chartData),
                plugins: plugins // 🆕 添加插件
            });

            // console.log(`步驟 ${step} 圖表創建成功`);
            return true;

        } catch (error) {
            console.error(`圖表創建失敗:`, error);
            this.utils?.showMessage('error', `圖表創建失敗: ${error.message}`);
            return false;
        }
    }

    /**
     * 銷毀指定步驟的圖表
     * @param {number} step - 步驟編號
     */
    destroyChart(step) {
        if (this.charts[step]) {
            try {
                this.charts[step].destroy();
                // console.log(`步驟 ${step} 圖表已銷毀`);
            } catch (error) {
                console.warn(`圖表銷毀警告:`, error);
            } finally {
                delete this.charts[step];
            }
        }
    }

    /**
     * 獲取圖表實例
     * @param {number} step - 步驟編號
     * @returns {Chart|null} 圖表實例
     */
    getChart(step) {
        return this.charts[step] || null;
    }

    /**
     * 檢查圖表是否存在
     * @param {number} step - 步驟編號
     * @returns {boolean} 圖表是否存在
     */
    hasChart(step) {
        return !!this.charts[step];
    }

    // ==================== 私有方法 - 驗證與初始化 ====================

    /**
     * 驗證輸入參數
     */
    _validateInput(step, chartData) {
        // 支援步驟1,2,3,5
        if (![1, 2, 3, 5].includes(step)) {
            console.error(`不支援的步驟: ${step}`);
            return false;
        }
        if (!chartData || typeof chartData !== 'object') {
            console.error('無效的圖表數據');
            return false;
        }
        return true;
    }

    /**
     * 獲取圖表容器上下文
     */
    _getChartContext(step) {
        let chartId;
        if (step === 1) chartId = 'havChart';
        else if (step === 2) chartId = 'inflowChart';
        else if (step === 3) chartId = 'drainageChart';
        else if (step === 5) chartId = 'finalChart';
        const ctx = document.getElementById(chartId);
        if (!ctx) {
            console.error(`找不到圖表容器 #${chartId}`);
            return null;
        }
        return ctx;
    }

    // ==================== 私有方法 - 數據準備 ====================

    /**
     * 準備圖表數據
     */
    _prepareChartData(step, chartData) {
        return {
            datasets: this._createDatasets(step, chartData)
        };
    }

    /**
     * 創建數據集
     */
    _createDatasets(step, chartData) {
        if (step === 1) return this._createHAVDatasets(chartData);
        else if (step === 2) return this._createInflowDatasets(chartData);
        else if (step === 3) return this._createDrainageDatasets(chartData);
        else if (step === 5) return this._createFinalDatasets(chartData);
        return [];
    }

    /**
     * 創建 HAV 圖表數據集
     */
    _createHAVDatasets(chartData) {
        const { levels, areas, volumes } = chartData;

        return [
            {
                label: '面積 A (m²)',
                data: levels.map((level, index) => ({
                    x: areas[index],
                    y: level
                })),
                borderColor: 'rgb(220, 53, 69)',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                borderWidth: 3,
                fill: false,
                xAxisID: 'x',
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.1
            },
            {
                label: '容量 V (m³)',
                data: levels.map((level, index) => ({
                    x: volumes[index],
                    y: level
                })),
                borderColor: 'rgb(13, 110, 253)',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 3,
                fill: false,
                xAxisID: 'x1',
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.1
            }
        ];
    }

    /**
     * 創建入流圖表數據集
     */
    _createInflowDatasets(chartData) {
        const { times, flows } = chartData;

        return [
            {
                label: '流量 (cms)',
                data: times.map((time, index) => ({
                    x: time,
                    y: flows[index]
                })),
                borderColor: 'rgb(25, 135, 84)',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                borderWidth: 3,
                fill: false,
                yAxisID: 'y',
                pointRadius: 2,
                pointHoverRadius: 4,
                tension: 0.1
            }
        ];
    }

    /**
     * 🆕 創建排洪圖表數據集
     */
    _createDrainageDatasets(chartData) {
        // 如果 chartData 已經包含 datasets，直接使用
        if (chartData.datasets && Array.isArray(chartData.datasets)) {
            return chartData.datasets;
        }

        // 否則返回空陣列
        return [];
    }

    /**
     * 步驟5：排洪演算結果圖 數據集
     * chartData: {
     *   times: [],
     *   inflow: [],
     *   outflow: [],
     *   waterlevel: []
     * }
     */
    _createFinalDatasets(chartData) {
        const { times, inflow, outflow, waterlevel } = chartData;
        return [
            {
                label: '總入流量 (cms)',
                data: times.map((t, i) => ({ x: t, y: inflow[i] })),
                borderColor: 'rgba(231, 137, 29, 1)',
                backgroundColor: 'rgba(231, 137, 29, 0.1)',
                borderWidth: 2,
                fill: false,
                yAxisID: 'y',
                pointRadius: 2,
                pointHoverRadius: 4,
                tension: 0.1,
                order: 2
            },
            {
                label: '總出流量 (cms)',
                data: times.map((t, i) => ({ x: t, y: outflow[i] })),
                borderColor: 'rgba(61, 106, 189, 1)',
                backgroundColor: 'rgba(61, 106, 189, 0.1)',
                borderWidth: 2,
                fill: false,
                yAxisID: 'y',
                pointRadius: 2,
                pointHoverRadius: 4,
                tension: 0.1,
                order: 1
            },
            {
                label: '水庫水位 (m)',
                data: times.map((t, i) => ({ x: t, y: waterlevel[i] })),
                borderColor: 'rgba(41, 136, 84, 1)',
                backgroundColor: 'rgba(41, 136, 84, 0.1)',
                borderWidth: 2,
                fill: false,
                yAxisID: 'y2',
                pointRadius: 2,
                pointHoverRadius: 4,
                tension: 0.1,
                order: 0
            }
        ];
    }

    // ==================== 私有方法 - 圖表選項配置 ====================

    /**
     * 創建圖表選項
     */
    _createChartOptions(step, chartData) {
        if (step === 5) return this._createFinalChartOptions(chartData);
        const baseOptions = {
            ...this.defaultConfigs,
            interaction: {
                mode: 'point',
                intersect: true
            },
            plugins: {
                title: this._createTitleConfig(step, chartData), // 🔧 修改：傳遞 chartData 參數
                legend: this._createLegendConfig(step),
                tooltip: this._createTooltipConfig(step),
                ...(step === 3 ? {
                    drainageLabels: {
                        enabled: true
                    }
                } : {})
            },
            scales: this._createScalesConfig(step, chartData), // 🔧 傳遞 chartData
            onHover: (event, activeElements, chart) => {
                this._handleChartHover(event, activeElements, chart);
            }
        };

        return baseOptions;
    }

    /**
     * 步驟5：排洪演算結果圖 Chart.js options
     */
    _createFinalChartOptions(chartData) {
        return {
            ...this.defaultConfigs,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: '排洪演算結果圖',
                    font: { size: 20, weight: 'bold' },
                    padding: 20,
                    color: '#333'
                },
                legend: {
                    position: 'top',
                    labels: {
                        font: { size: 12 },
                        padding: 20,
                        usePointStyle: true,
                        color: '#666'
                    }
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: (context) => {
                            if (!context?.[0]?.parsed) return '';
                            const t = context[0].parsed.x;
                            return `歷時: ${t} 小時`;
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const y = context.parsed.y;
                            if (label.includes('水位')) {
                                return `${label}: ${y.toFixed(2)} m`;
                            }
                            return `${label}: ${y.toFixed(3)} cms`;
                        }
                    }
                }
            },
            scales: this._createFinalScales(chartData), // 🔧 傳遞 chartData
            onHover: (event, activeElements, chart) => {
                this._handleChartHover(event, activeElements, chart);
            }
        };
    }

    /**
     * 創建標題配置
     */
    _createTitleConfig(step, chartData) { // 🔧 修改：添加 chartData 參數
        let title;

        if (step === 1) {
            title = '水庫庫容關係圖 (HAV)';
        } else if (step === 2) {
            title = '入流流量歷線圖';
        } else if (step === 3) {
            // 🆕 步驟3動態標題，包含設施名稱
            const facilityName = chartData?.facilityName || '排洪設施';
            title = `${facilityName} - 排洪率定曲線`;
        } else {
            title = '圖表';
        }

        return {
            display: true,
            text: title,
            font: {
                size: 20,
                weight: 'bold'
            },
            padding: 20,
            color: '#333'
        };
    }

    /**
     * 創建圖例配置
     */
    _createLegendConfig(step) {
        return {
            position: 'top',
            labels: {
                font: { size: 12 },
                padding: 20,
                usePointStyle: true,
                color: '#666'
            },
            onClick: (event, legendItem, legend) => {
                this._handleLegendClick(event, legendItem, legend, step);
            }
        };
    }

    /**
     * 創建 Tooltip 配置 - 📍 這裡是您要修改的地方
     */
    _createTooltipConfig(step) {
        const baseConfig = {
            enabled: true,
            position: 'nearest',
            backgroundColor: 'rgba(33, 37, 41, 0.95)',
            titleColor: '#ffffff',
            bodyColor: '#e9ecef',
            footerColor: '#adb5bd',
            borderColor: step === 1 ? '#dc3545' : (step === 2 ? '#198754' : '#6f42c1'),
            borderWidth: 2,
            cornerRadius: 8,
            padding: 12,
            displayColors: true,
            usePointStyle: true,
            animation: {
                duration: 200,
                easing: 'easeOutQuart'
            },
            titleFont: {
                size: 14,
                weight: 'bold'
            },
            bodyFont: {
                size: 13
            },
            footerFont: {
                size: 11,
                style: 'italic'
            }
        };

        // 根據步驟設定不同的回調函數
        if (step === 1) {
            return {
                ...baseConfig,
                callbacks: this._getHAVTooltipCallbacks()
            };
        } else if (step === 2) {
            return {
                ...baseConfig,
                callbacks: this._getInflowTooltipCallbacks()
            };
        } else if (step === 3) {
            // 🆕 添加步驟3 tooltip 回調
            return {
                ...baseConfig,
                callbacks: this._getDrainageTooltipCallbacks()
            };
        }

        return baseConfig;
    }

    /**
     * HAV 圖表的 Tooltip 回調函數
     */
    _getHAVTooltipCallbacks() {
        return {
            title: (context) => {
                if (!context?.[0]?.parsed) return '';
                const waterLevel = context[0].parsed.y;
                return `水位: ${waterLevel.toFixed(0)} m`;
            },
            label: (context) => {
                if (!context?.parsed || !context?.dataset) return '';

                const value = context.parsed.x;
                const label = context.dataset.label;

                if (label.includes('面積')) {
                    return `面積: ${value.toLocaleString('zh-TW')} m²`;
                } else if (label.includes('容量')) {
                    return `容量: ${value.toLocaleString('zh-TW')} m³`;
                }

                return `${label}: ${value.toLocaleString('zh-TW')}`;
            }
        };
    }

    /**
     * 入流圖表的 Tooltip 回調函數
     */
    _getInflowTooltipCallbacks() {
        return {
            title: (context) => {
                if (!context?.[0]?.parsed) return '';
                const time = context[0].parsed.x;
                return `歷時: ${time.toFixed(0)} 小時`;
            },
            label: (context) => {
                if (!context?.parsed) return '';
                const flow = context.parsed.y;
                return `流量: ${flow.toFixed(3)} cms`;
            },
        };
    }

    /**
     * 🆕 排洪圖表的 Tooltip 回調函數
     */
    _getDrainageTooltipCallbacks() {
        return {
            title: (context) => {
                if (!context?.[0]?.parsed) return '';
                const waterLevel = context[0].parsed.y;
                return `水位: ${waterLevel.toFixed(2)} m`; // 🔧 修改：以水位作為標題
            },
            label: (context) => {
                if (!context?.parsed) return '';
                const flow = context.parsed.x;
                const opening = context.dataset.label || '未知開度';
                return `${opening} - 流量: ${flow.toFixed(3)} cms`; // 🔧 修改：內容顯示流量
            }
        };
    }

    /**
     * 創建座標軸配置
     */
    _createScalesConfig(step, chartData) { // 🔧 傳遞 chartData
        if (step === 1) return this._createHAVScales();
        else if (step === 2) return this._createInflowScales();
        else if (step === 3) return this._createDrainageScales();
        else if (step === 5) return this._createFinalScales(chartData); // 🔧 傳遞 chartData
        return {};
    }

    /**
     * 創建 HAV 圖表座標軸
     */
    _createHAVScales() {
        return {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: '水位 H (m)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#333',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            },
            x: {
                type: 'linear',
                display: true,
                position: 'bottom',
                reverse: true,
                title: {
                    display: true,
                    text: '面積 A (m²)',
                    color: 'rgb(220, 53, 69)',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    display: false,
                    color: 'rgba(220, 53, 69, 0.3)'
                },
                ticks: {
                    color: 'rgb(220, 53, 69)',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            },
            x1: {
                type: 'linear',
                display: true,
                position: 'top',
                title: {
                    display: true,
                    text: '容量 V (m³)',
                    color: 'rgb(13, 110, 253)',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    display: false,
                    color: 'rgba(13, 110, 253, 0.3)'
                },
                ticks: {
                    color: 'rgb(13, 110, 253)',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            }
        };
    }

    /**
     * 創建入流圖表座標軸
     */
    _createInflowScales() {
        return {
            x: {
                type: 'linear',
                display: true,
                title: {
                    display: true,
                    text: '歷時 (hr)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#333',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            },
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: '流量 (cms)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#333',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            }
        };
    }

    /**
     * 🆕 創建排洪圖表座標軸
     */
    _createDrainageScales() {
        return {
            x: {
                type: 'linear',
                display: true,
                title: {
                    display: true,
                    text: '流量 (cms)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#333',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            },
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: '水位 (m)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    color: '#333',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            }
        };
    }

    /**
     * 步驟5：排洪演算結果圖 雙Y軸
     */
    _createFinalScales(chartData) {
        // 取得水位資料
        const waterlevel = chartData?.waterlevel || [];
        let wlMin = Math.min(...waterlevel.filter(x => typeof x === 'number' && !isNaN(x)));
        let wlMax = Math.max(...waterlevel.filter(x => typeof x === 'number' && !isNaN(x)));
        if (!isFinite(wlMin) || !isFinite(wlMax)) {
            wlMin = 0;
            wlMax = 1;
        }

        // 取得流量最大值
        const inflow = chartData?.inflow || [];
        const outflow = chartData?.outflow || [];
        const maxFlow = Math.max(
            ...inflow.filter(x => typeof x === 'number' && !isNaN(x)),
            ...outflow.filter(x => typeof x === 'number' && !isNaN(x))
        );
        // y1: 0 ~ 500的倍數，tick間距500
        let y1Min = 0;
        let y1Max = 1000;
        if (isFinite(maxFlow)) {
            y1Max = Math.ceil(maxFlow / 333) * 500;
            if (y1Max === maxFlow) y1Max += 500; // 至少多一格
        }
        const y1Step = 500;
        const yTickCount = Math.round((y1Max - y1Min) / y1Step) + 1;

        // y2: tick間距10~100，max比wlMax多一格，min自動外推
        const wlRange = wlMax - wlMin;
        let y2Step = 10;
        if (wlRange > 0) {
            // 進位到最接近的 10, 20, 50, 100, 200, 500, 1000
            const stepCandidates = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000];
            for (let i = 0; i < stepCandidates.length; i++) {
                if (wlRange < stepCandidates[i] * 2) {
                    y2Step = stepCandidates[i];
                    break;
                }
            }
        }
        let y2Max = Math.ceil(wlMax / y2Step) * y2Step + y2Step; // 水位線永遠不會貼頂
        let y2Min = y2Max - y2Step * (yTickCount - 1);

        // 若 wlMin < y2Min，則再往下補一格
        while (wlMin < y2Min) {
            y2Min -= y2Step;
            y2Max -= y2Step;
        }

        return {
            x: {
                type: 'linear',
                display: true,
                title: {
                    display: true,
                    text: '歷時 (hr)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                grid: { color: 'rgba(0,0,0,0.1)' },
                ticks: {
                    color: '#333',
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : '')
                }
            },
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: '流量 (cms)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                min: y1Min,
                max: y1Max,
                grid: { 
                    color: 'rgba(0,0,0,0.1)',
                    drawOnChartArea: true,
                    drawTicks: true
                },
                ticks: {
                    color: '#333',
                    stepSize: y1Step,
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : ''),
                    count: yTickCount
                }
            },
            y2: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: '水位 (m)',
                    color: '#333',
                    font: { size: 14, weight: 'bold' }
                },
                min: y2Min,
                max: y2Max,
                grid: { 
                    drawOnChartArea: true,
                    color: 'rgba(0,0,0,0.1)',
                    drawTicks: true
                },
                afterBuildTicks: function(axis) {
                    // 產生與主y軸一樣數量的tick，且每個tick為10的倍數
                    const ticks = [];
                    for (let i = 0; i < yTickCount; i++) {
                        ticks.push({ value: y2Min + i * y2Step });
                    }
                    axis.ticks = ticks;
                },
                ticks: {
                    color: '#333',
                    stepSize: y2Step,
                    callback: (value) => (typeof value === 'number' && isFinite(value) ? value.toLocaleString('zh-TW') : ''),
                    count: yTickCount
                }
            }
        };
    }

    /**
     * 步驟5：標示最大值插件
     */
    _createFinalMaxLabelsPlugin() {
        return {
            id: 'finalMaxLabels',
            afterDatasetsDraw: (chart, args, options) => {
                const { ctx, data, scales } = chart;
                if (!data || !scales) return;
                const { x: xScale, y: yScale, y2: y2Scale } = scales;
                if (!xScale || !yScale || !y2Scale) return;

                // 取得 hoverKey
                let hoverKey = null;
                if (chart.canvas && typeof chart.canvas._fdFinalMaxLabelsHoverKey === 'function') {
                    hoverKey = chart.canvas._fdFinalMaxLabelsHoverKey();
                }

                ctx.save();
                ctx.font = 'bold 13px Arial';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'bottom';

                // 1. 水庫最高水位
                const wlDs = data.datasets.find(ds => ds.label && ds.label.includes('水位'));
                if (wlDs && wlDs.data && wlDs.data.length && window.fdFinalMaxLabelsVisible_1 === true && !wlDs.hidden) {
                    let maxIdx = 0;
                    let maxVal = wlDs.data[0].y;
                    wlDs.data.forEach((pt, i) => {
                        if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; }
                    });
                    const pt = wlDs.data[maxIdx];
                    const x = xScale.getPixelForValue(pt.x);
                    const y = y2Scale.getPixelForValue(pt.y);

                    const label1 = '水庫最高水位';
                    const label2 = `EL. ${maxVal.toFixed(3)} m`;

                    // --- 標籤底圖 ---
                    ctx.save();
                    ctx.font = 'bold 13px Arial';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'bottom';
                    const padding = 6;
                    const width = Math.max(ctx.measureText(label1).width, ctx.measureText(label2).width) + padding * 2;
                    const height = 40;
                    const rectX = x + 8;
                    const rectY = y - 48;
                    ctx.beginPath();
                    ctx.roundRect(rectX, rectY, width, height, 6);
                    ctx.fillStyle = '#fff';
                    ctx.strokeStyle = '#298854';
                    ctx.lineWidth = 2;
                    ctx.fill();
                    ctx.stroke();
                    ctx.restore();

                    // --- 文字 ---
                    ctx.fillStyle = '#298854';
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 4;
                    ctx.strokeText(label1, x + 12, y - 30);
                    ctx.strokeText(label2, x + 12, y - 12);
                    ctx.fillText(label1, x + 12, y - 30);
                    ctx.fillText(label2, x + 12, y - 12);

                    // --- 圓點 ---
                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2 * Math.PI);
                    ctx.fillStyle = '#298854';
                    ctx.fill();
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }

                // 2. 最大總入流量
                const inDs = data.datasets.find(ds => ds.label && (ds.label.includes('入流') || ds.label.includes('in')));
                if (inDs && inDs.data && inDs.data.length && window.fdFinalMaxLabelsVisible_2 === true && !inDs.hidden) {
                    let maxIdx = 0;
                    let maxVal = inDs.data[0].y;
                    inDs.data.forEach((pt, i) => {
                        if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; }
                    });
                    const pt = inDs.data[maxIdx];
                    const x = xScale.getPixelForValue(pt.x);
                    const y = yScale.getPixelForValue(pt.y);

                    const label1 = '最大總入流量';
                    const label2 = `Qin,max=${maxVal.toFixed(3)} cms`;

                    ctx.save();
                    ctx.font = 'bold 13px Arial';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'bottom';
                    const padding = 6;
                    const width = Math.max(ctx.measureText(label1).width, ctx.measureText(label2).width) + padding * 2;
                    const height = 40;
                    const rectX = x - 164;
                    const rectY = y - 48;
                    ctx.beginPath();
                    ctx.roundRect(rectX, rectY, width, height, 6);
                    ctx.fillStyle = '#fff';
                    ctx.strokeStyle = '#e7891d';
                    ctx.lineWidth = 2;
                    ctx.fill();
                    ctx.stroke();
                    ctx.restore();

                    ctx.fillStyle = '#e7891d';
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 4;
                    ctx.strokeText(label1, x - 160, y - 30);
                    ctx.strokeText(label2, x - 160, y - 12);
                    ctx.fillText(label1, x - 160, y - 30);
                    ctx.fillText(label2, x - 160, y - 12);

                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2 * Math.PI);
                    ctx.fillStyle = '#e7891d';
                    ctx.fill();
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }

                // 3. 最大總出流量
                const outDs = data.datasets.find(ds => ds.label && (ds.label.includes('出流') || ds.label.includes('out')));
                if (outDs && outDs.data && outDs.data.length && window.fdFinalMaxLabelsVisible_3 === true && !outDs.hidden) {
                    let maxIdx = 0;
                    let maxVal = outDs.data[0].y;
                    outDs.data.forEach((pt, i) => {
                        if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; }
                    });
                    const pt = outDs.data[maxIdx];
                    const x = xScale.getPixelForValue(pt.x);
                    const y = yScale.getPixelForValue(pt.y);

                    const label1 = '最大總出流量';
                    const label2 = `Qout,max=${maxVal.toFixed(3)} cms`;

                    ctx.save();
                    ctx.font = 'bold 13px Arial';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'bottom';
                    const padding = 6;
                    const width = Math.max(ctx.measureText(label1).width, ctx.measureText(label2).width) + padding * 2;
                    const height = 40;
                    const rectX = x + 8;
                    const rectY = y - 48;
                    ctx.beginPath();
                    ctx.roundRect(rectX, rectY, width, height, 6);
                    ctx.fillStyle = '#fff';
                    ctx.strokeStyle = '#3d6abd';
                    ctx.lineWidth = 2;
                    ctx.fill();
                    ctx.stroke();
                    ctx.restore();

                    ctx.fillStyle = '#3d6abd';
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 4;
                    ctx.strokeText(label1, x + 12, y - 30);
                    ctx.strokeText(label2, x + 12, y - 12);
                    ctx.fillText(label1, x + 12, y - 30);
                    ctx.fillText(label2, x + 12, y - 12);

                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2 * Math.PI);
                    ctx.fillStyle = '#3d6abd';
                    ctx.fill();
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }

                // 額外：如果標籤是隱藏狀態，且 hover 到該 hitbox，畫半透明提示
                const labelConfigs = [
                    {
                        key: 1,
                        visible: window.fdFinalMaxLabelsVisible_1,
                        ds: data.datasets.find(ds => ds.label && ds.label.includes('水位')),
                        color: '#298854',
                        label1: '水庫最高水位',
                        label2: ds => `EL. ${ds ? Math.max(...ds.data.map(pt => pt.y)).toFixed(3) : ''} m`
                    },
                    {
                        key: 2,
                        visible: window.fdFinalMaxLabelsVisible_2,
                        ds: data.datasets.find(ds => ds.label && (ds.label.includes('入流') || ds.label.includes('in'))),
                        color: '#e7891d',
                        label1: '最大總入流量',
                        label2: ds => `Qin,max=${ds ? Math.max(...ds.data.map(pt => pt.y)).toFixed(3) : ''} cms`
                    },
                    {
                        key: 3,
                        visible: window.fdFinalMaxLabelsVisible_3,
                        ds: data.datasets.find(ds => ds.label && (ds.label.includes('出流') || ds.label.includes('out'))),
                        color: '#3d6abd',
                        label1: '最大總出流量',
                        label2: ds => `Qout,max=${ds ? Math.max(...ds.data.map(pt => pt.y)).toFixed(3) : ''} cms`
                    }
                ];
                const padding = 6, height = 40;
                for (const cfg of labelConfigs) {
                    const ds = cfg.ds;
                    if (!ds || !ds.data || !ds.data.length) continue;
                    let maxIdx = 0, maxVal = ds.data[0].y;
                    ds.data.forEach((pt, i) => { if (pt.y > maxVal) { maxVal = pt.y; maxIdx = i; } });
                    const pt = ds.data[maxIdx];
                    const x = (cfg.key === 1) ? xScale.getPixelForValue(pt.x) : xScale.getPixelForValue(pt.x);
                    const y = (cfg.key === 1) ? y2Scale.getPixelForValue(pt.y) : yScale.getPixelForValue(pt.y);
                    const label1 = cfg.label1;
                    const label2 = typeof cfg.label2 === 'function' ? cfg.label2(ds) : cfg.label2;
                    const width = Math.max(ctx.measureText(label1).width, ctx.measureText(label2).width) + padding * 2;
                    const rectX = (cfg.key === 2) ? x - 164 : x + 8;
                    const rectY = y - 48;

                    // 如果該標籤目前是隱藏且 hover 到，畫半透明提示
                    if (!cfg.visible && hoverKey === cfg.key) {
                        ctx.save();
                        ctx.globalAlpha = 0.5;
                        ctx.beginPath();
                        ctx.roundRect(rectX, rectY, width, height, 6);
                        ctx.fillStyle = '#bbb';
                        ctx.fill();
                        ctx.restore();

                        // 可加提示字
                        ctx.save();
                        ctx.font = 'bold 12px Arial';
                        ctx.fillStyle = '#fff';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText('點擊顯示', rectX + width / 2, rectY + height / 2);
                        ctx.restore();
                    }
                }

                ctx.restore();
            }
        };
    }

    // ==================== 私有方法 - 事件處理 ====================

    /**
     * 處理圖例點擊事件
     */
    _handleLegendClick(event, legendItem, legend, step) {
        const chart = legend.chart;
        const datasetIndex = legendItem.datasetIndex;
        const dataset = chart.data.datasets[datasetIndex];

        // 步驟5：同步標籤顯示狀態（這裡只同步全域變數，不要自己切換 hidden）
        if (step === 5) {
            if (dataset.label && dataset.label.includes('水位')) {
                window.fdFinalMaxLabelsVisible_1 = dataset.hidden; // 點擊前的狀態，點擊後會反轉
            } else if (dataset.label && (dataset.label.includes('入流') || dataset.label.includes('in'))) {
                window.fdFinalMaxLabelsVisible_2 = dataset.hidden;
            } else if (dataset.label && (dataset.label.includes('出流') || dataset.label.includes('out'))) {
                window.fdFinalMaxLabelsVisible_3 = dataset.hidden;
            }
        }

        // 呼叫 Chart.js 預設 legend onClick 行為（會自動切換 hidden 並 update）
        if (Chart.defaults.plugins && Chart.defaults.plugins.legend && typeof Chart.defaults.plugins.legend.onClick === 'function') {
            Chart.defaults.plugins.legend.onClick.call(this, event, legendItem, legend);
        }

        // 顯示提示訊息
        const action = dataset.hidden ? '隱藏' : '顯示';
        this.utils?.showMessage('info', `已${action} ${dataset.label}`);

        // 檢查是否所有數據都被隱藏
        const allHidden = chart.data.datasets.every(ds => ds.hidden);
        if (allHidden) {
            this.utils?.showMessage('warning', '所有數據系列已隱藏，圖表將顯示為空白');
        }
    }

    /**
     * 處理圖表懸停事件
     */
    _handleChartHover(event, activeElements, chart) {
        if (!chart?.canvas) return;

        try {
            const hasActiveElements = activeElements && activeElements.length > 0;
            const hasVisibleData = chart.data.datasets.some(dataset =>
                dataset && !dataset.hidden
            );

            chart.canvas.style.cursor = hasActiveElements && hasVisibleData ? 'pointer' : 'default';
        } catch (error) {
            console.warn('圖表懸停處理錯誤:', error);
            chart.canvas.style.cursor = 'default';
        }
    }

    /**
     * 更新座標軸顯示狀態
     */
    _updateScalesVisibility(chart, step) {
        if (!chart?.options?.scales) return;

        try {
            if (step === 1) {
                const datasets = chart.data.datasets;
                const hasAreaData = datasets[0] && !datasets[0].hidden;
                const hasVolumeData = datasets[1] && !datasets[1].hidden;

                // 更新座標軸顯示
                if (chart.options.scales.x) {
                    chart.options.scales.x.display = hasAreaData;
                }
                if (chart.options.scales.x1) {
                    chart.options.scales.x1.display = hasVolumeData;
                }
            }
        } catch (error) {
            console.warn('座標軸顯示更新錯誤:', error);
        }
    }

    // ==================== 公用工具方法 ====================

    /**
     * 清除所有圖表
     */
    clearAllCharts() {
        Object.keys(this.charts).forEach(step => {
            this.destroyChart(parseInt(step));
        });
        // console.log('所有圖表已清除');
    }

    /**
     * 獲取圖表統計資訊
     */
    getChartStats() {
        const stats = {};
        Object.entries(this.charts).forEach(([step, chart]) => {
            if (chart && chart.data) {
                const datasets = chart.data.datasets || [];
                stats[step] = {
                    datasetsCount: datasets.length,
                    visibleDatasets: datasets.filter(ds => !ds.hidden).length,
                    totalDataPoints: datasets.reduce((sum, ds) => sum + (ds.data?.length || 0), 0)
                };
            }
        });
        return stats;
    }

    /**
     * 🆕 創建排洪圖表標籤插件
     */
    _createDrainageLabelsPlugin() {
        return {
            id: 'drainageLabels',
            afterDatasetsDraw: (chart, args, options) => {
                if (!options.enabled) return;

                const { ctx, data, scales } = chart;
                const { x: xScale, y: yScale } = scales;

                ctx.save();
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                data.datasets.forEach((dataset, datasetIndex) => {
                    if (dataset.hidden) return;

                    const dataPoints = dataset.data;
                    if (!dataPoints || dataPoints.length === 0) return;

                    // 取最後一個數據點
                    const lastPoint = dataPoints[dataPoints.length - 1];
                    if (!lastPoint || typeof lastPoint.x !== 'number' || typeof lastPoint.y !== 'number') return;

                    const x = xScale.getPixelForValue(lastPoint.x);
                    const y = yScale.getPixelForValue(lastPoint.y);

                    // 檢查座標是否在圖表範圍內
                    if (x < xScale.left || x > xScale.right || y < yScale.top || y > yScale.bottom) return;

                    // 🔧 修改：提取開度值，支援「全開」
                    const label = dataset.label || '';
                    let openingValue;

                    if (label.includes('全開')) {
                        openingValue = '全開';
                    } else {
                        const openingMatch = label.match(/開度[：:\s]*(\S+)/);
                        openingValue = openingMatch ? openingMatch[1] : label;
                    }

                    // 設定標籤樣式
                    const backgroundColor = 'rgba(255, 255, 255, 0.9)';
                    const borderColor = dataset.borderColor || '#2563eb';
                    const textColor = '#1e40af';

                    // 測量文字尺寸
                    const metrics = ctx.measureText(openingValue);
                    const textWidth = metrics.width;
                    const textHeight = 12;
                    const padding = 4;

                    // 計算標籤位置（在點的右上方）
                    const labelX = x + 15;
                    const labelY = y - 15;

                    // 繪製背景
                    ctx.fillStyle = backgroundColor;
                    ctx.strokeStyle = borderColor;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.roundRect(
                        labelX - textWidth / 2 - padding,
                        labelY - textHeight / 2 - padding,
                        textWidth + padding * 2,
                        textHeight + padding * 2,
                        3
                    );
                    ctx.fill();
                    ctx.stroke();

                    // 繪製文字
                    ctx.fillStyle = textColor;
                    ctx.fillText(openingValue, labelX, labelY);

                    // 繪製指向線（從標籤到數據點）
                    ctx.strokeStyle = borderColor;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([2, 2]);
                    ctx.beginPath();
                    ctx.moveTo(labelX - 5, labelY + 5);
                    ctx.lineTo(x + 5, y - 5);
                    ctx.stroke();
                    ctx.setLineDash([]);
                });

                ctx.restore();
            }
        };
    }
}

// 創建全局實例
window.fdCharts = new ChartManager();

// 除錯用：在控制台中可以檢查圖表狀態
window.fdCharts.debug = {
    getCharts: () => window.fdCharts.charts,
    getStats: () => window.fdCharts.getChartStats(),
    clearAll: () => window.fdCharts.clearAllCharts()
};