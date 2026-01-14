/**
 * 排洪演算平台 - 步驟2：入流流量歷線管理
 */
class Step2Manager {
    constructor() {
        this.step = 2;
        this.api = window.fdAPI;
        this.charts = window.fdCharts;
        this.utils = window.fdUtils;
        this.tables = window.fdTables;

        // 數據狀態 - 保持原有命名慣例
        this.inflowOriginalData = null;
        this.inflowAdjustedData = null;
        this.initialWL = null;
        this.deltaT = null;
        this.adjustmentSummary = null;

        this.init();
    }

    /**
     * 初始化步驟2管理器
     */
    init() {
        // console.log('初始化步驟2管理器');

        // 綁定事件
        this.bindEvents();
    }

    /**
     * 綁定事件監聽器
     */
    bindEvents() {
        // 時距調整事件
        const adjustBtn = document.querySelector('#step-2 .adjust-btn');
        if (adjustBtn) {
            adjustBtn.addEventListener('click', () => this.handleTimeStepAdjustment());
        }

        // 下載事件
        const downloadOriginalBtn = document.querySelector('#step-2 .download-original-btn');
        const downloadAdjustedBtn = document.querySelector('#step-2 .download-adjusted-btn');

        if (downloadOriginalBtn) {
            downloadOriginalBtn.addEventListener('click', () => this.saveOriginalData());
        }

        if (downloadAdjustedBtn) {
            downloadAdjustedBtn.addEventListener('click', () => this.saveAdjustedData());
        }

        // 繪圖和匯出事件
        const drawBtn = document.querySelector('#step-2 .draw-btn');
        const exportBtn = document.querySelector('#step-2 .export-btn');

        if (drawBtn) {
            drawBtn.addEventListener('click', () => this.drawChart());
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportChart());
        }
    }

    /**
     * 載入步驟數據 - 保持原有邏輯
     */
    loadStepData() {
        // console.log('步驟2 loadStepData() 方法被調用');

        const hasUploaded = sessionStorage.getItem('step2_uploaded');
        if (!hasUploaded) {
            // console.log('步驟2 無上傳記錄，清空數據');
            this.clearStepData();
            return;
        }

        // 從 sessionStorage 恢復原始數據
        const savedOriginalData = sessionStorage.getItem('step2_originalData');
        if (savedOriginalData) {
            try {
                this.inflowOriginalData = JSON.parse(savedOriginalData);
                // console.log('從 sessionStorage 恢復入流數據');

                // 重新渲染原始數據表格
                if (this.tables && typeof this.tables.updateStep2OriginalTable === 'function') {
                    this.tables.updateStep2OriginalTable(this.inflowOriginalData);
                }

                // 恢復入流數據信息
                const savedInitialWL = sessionStorage.getItem('step2_initialWL');
                if (savedInitialWL) {
                    this.initialWL = parseFloat(savedInitialWL);
                    this.utils.showMessage('info', `已恢復入流數據，初始水位: ${savedInitialWL}m`);
                }

                // 檢查是否有調整後的數據
                const hasAdjusted = sessionStorage.getItem('step2_adjusted');
                const savedAdjustedData = sessionStorage.getItem('step2_adjustedData');

                if (hasAdjusted && savedAdjustedData) {
                    try {
                        this.inflowAdjustedData = JSON.parse(savedAdjustedData);
                        // console.log('從 sessionStorage 恢復調整後入流數據');

                        // 重新渲染調整後數據表格
                        if (this.tables && typeof this.tables.updateStep2AdjustedTable === 'function') {
                            this.tables.updateStep2AdjustedTable(this.inflowAdjustedData);
                        }

                        // 恢復 Delta T 值
                        const savedDeltaT = sessionStorage.getItem('step2_deltaT');
                        if (savedDeltaT) {
                            this.deltaT = parseFloat(savedDeltaT);
                            const deltaTInput = document.getElementById('delta-t-input');
                            if (deltaTInput) {
                                deltaTInput.value = savedDeltaT;
                            }
                            this.utils.showMessage('info', `已恢復入流數據時距調整: ${savedDeltaT} 小時`);
                        }

                        // 顯示調整摘要
                        this.showAdjustmentInfo();

                    } catch (error) {
                        console.error('恢復調整後入流數據失敗:', error);
                        sessionStorage.removeItem('step2_adjusted');
                        sessionStorage.removeItem('step2_adjustedData');
                        sessionStorage.removeItem('step2_deltaT');
                    }
                }

                // 自動繪圖
                // 優先用調整後數據，否則用原始數據
                const currentData = this.inflowAdjustedData || this.inflowOriginalData;
                if (currentData && currentData.length > 0) {
                    this.drawChart();
                }

            } catch (error) {
                console.error('恢復入流數據失敗:', error);
                // 數據損壞，清除所有狀態
                this.clearAllSessionData();
                this.utils.showMessage('warning', '入流數據恢復失敗，請重新上傳檔案');
                this.clearStepData();
            }
        } else {
            // sessionStorage 中沒有數據，但有上傳標記，表示數據丟失
            // console.log('入流數據丟失，清除狀態');
            this.clearAllSessionData();
            this.utils.showMessage('warning', '入流數據已丟失，請重新上傳檔案');
            this.clearStepData();
        }
    }

    /**
     * 清空步驟數據 - 保持原有邏輯
     */
    clearStepData() {
        // console.log('步驟2 clearStepData() 方法被調用');

        const originalTable = document.getElementById('inflow-original-table');
        const adjustedTable = document.getElementById('inflow-adjusted-table');

        if (originalTable) originalTable.innerHTML = '';
        if (adjustedTable) adjustedTable.innerHTML = '';

        this.inflowOriginalData = null;
        this.inflowAdjustedData = null;
        this.initialWL = null;
        this.deltaT = null;
        this.adjustmentSummary = null;
    }

    /**
     * 處理檔案上傳 - 保持原有邏輯
     */
    async handleUpload(file) {
        try {
            this.utils.showLoading(2, 'upload');

            const result = await this.api.upload(2, file);

            if (result.success) {
                // 更新數據
                this.inflowOriginalData = result.data;
                this.initialWL = result.initial_wl;

                // 更新表格
                if (this.tables && typeof this.tables.updateStep2OriginalTable === 'function') {
                    this.tables.updateStep2OriginalTable(result.data);
                }

                // 保存數據到 sessionStorage
                sessionStorage.setItem('step2_originalData', JSON.stringify(result.data));

                // 處理初始水位
                if (result.initial_wl !== undefined) {
                    // console.log('入流數據初始水位:', result.initial_wl);
                    sessionStorage.setItem('step2_initialWL', result.initial_wl);
                    this.utils.showMessage('info', `入流數據載入成功，初始水位: ${result.initial_wl}m`);
                }

                this.utils.showMessage('success', result.message || '入流數據上傳成功！');
                sessionStorage.setItem('step2_uploaded', 'true');

                // 清除之前的調整結果
                this.clearAdjustedData();

            } else {
                throw new Error(result.message || '上傳失敗');
            }
        } catch (error) {
            this.utils.showMessage('error', '入流數據上傳失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(2, 'upload');
        }
    }

    /**
     * 時距調整 - 新增使用新的 API
     */
    async handleTimeStepAdjustment() {
        const hasUploaded = sessionStorage.getItem('step2_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳入流數據');
            return;
        }

        const deltaT = this.getDeltaT();
        if (!this.validateDeltaT(deltaT)) {
            return;
        }

        try {
            this.utils.showLoading(2, 'adjust');

            // 使用新的調整 API
            const result = await this.api.adjustInflow(2, deltaT);

            if (result.success) {
                // 更新調整後數據
                this.inflowAdjustedData = result.data.adjusted_data;
                this.deltaT = result.data.delta_t;
                this.adjustmentSummary = result.data.summary;

                // 更新表格
                if (this.tables && typeof this.tables.updateStep2AdjustedTable === 'function') {
                    this.tables.updateStep2AdjustedTable(this.inflowAdjustedData);
                }

                // 保存調整後數據到 sessionStorage
                sessionStorage.setItem('step2_adjustedData', JSON.stringify(this.inflowAdjustedData));
                sessionStorage.setItem('step2_deltaT', deltaT);
                sessionStorage.setItem('step2_adjusted', 'true');

                // 顯示調整摘要
                this.showAdjustmentInfo();

                this.utils.showMessage('success', result.message || `入流數據時距調整完成！調整為 ${deltaT} 小時間距`);

            } else {
                throw new Error(result.message || '入流數據時距調整失敗');
            }
        } catch (error) {
            this.utils.showMessage('error', '入流數據時距調整失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(2, 'adjust');
        }
    }

    /**
     * 獲取 Delta T 值
     */
    getDeltaT() {
        const input = document.getElementById('delta-t-input');
        return input ? parseFloat(input.value) : null;
    }

    /**
     * 驗證 Delta T 值
     */
    validateDeltaT(deltaT) {
        if (!deltaT || deltaT <= 0) {
            this.utils.showMessage('error', '請輸入有效的時距值');
            return false;
        }
        if (deltaT > 24) {
            const confirmed = confirm(`時間間距 ${deltaT} 小時較大，確定要繼續嗎？`);
            if (!confirmed) return false;
        }
        return true;
    }

    /**
     * 顯示調整摘要資訊
     */
    showAdjustmentInfo() {
        if (!this.adjustmentSummary || !this.deltaT) return;

        const summaryContainer = document.querySelector('#step-2 .adjustment-summary');
        if (summaryContainer) {
            const summaryHTML = this.generateAdjustmentSummaryHTML();
            summaryContainer.innerHTML = summaryHTML;
            summaryContainer.style.display = 'block';
        }
    }

    /**
     * 生成調整摘要 HTML
     */
    generateAdjustmentSummaryHTML() {
        if (!this.adjustmentSummary) return '';

        const summary = this.adjustmentSummary;

        return `
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">
                        <i class="bi bi-graph-up"></i> 調整結果摘要
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>數據統計</h6>
                            <ul class="list-unstyled">
                                <li><strong>目標間距:</strong> ${this.deltaT} 小時</li>
                                <li><strong>原始筆數:</strong> ${summary.adjustment_info?.original_points || 'N/A'}</li>
                                <li><strong>調整後筆數:</strong> ${summary.adjustment_info?.adjusted_points || 'N/A'}</li>
                                <li><strong>插值方法:</strong> ${summary.adjustment_info?.interpolation_method || 'N/A'}</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>流量統計</h6>
                            <ul class="list-unstyled">
                                <li><strong>原始平均:</strong> ${summary.flow_statistics?.original?.mean?.toFixed(3) || 'N/A'} m³/s</li>
                                <li><strong>調整後平均:</strong> ${summary.flow_statistics?.adjusted?.mean?.toFixed(3) || 'N/A'} m³/s</li>
                                <li><strong>原始範圍:</strong> ${summary.flow_statistics?.original?.min?.toFixed(3) || 'N/A'} ~ ${summary.flow_statistics?.original?.max?.toFixed(3) || 'N/A'}</li>
                                <li><strong>調整後範圍:</strong> ${summary.flow_statistics?.adjusted?.min?.toFixed(3) || 'N/A'} ~ ${summary.flow_statistics?.adjusted?.max?.toFixed(3) || 'N/A'}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 儲存原始數據 - 保持原有邏輯
     */
    async saveOriginalData() {
        // console.log('開始保存原始入流數據...');

        const hasUploaded = sessionStorage.getItem('step2_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳入流數據');
            return;
        }

        if (!this.inflowOriginalData || this.inflowOriginalData.length === 0) {
            this.utils.showMessage('error', '沒有原始入流數據可以下載');
            return;
        }

        try {
            this.utils.showLoading(2, 'save');

            // 🔧 修復：直接獲取 blob
            const fileBlob = await this.api.save(2, 'original');

            if (!fileBlob || !(fileBlob instanceof Blob)) {
                throw new Error('後端返回的不是有效的檔案格式');
            }

            // 🔧 修復：生成統一格式的檔案名稱
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `步驟2_原始入流數據_${timestamp}.xlsx`;

            // 🔧 修復：直接傳遞 blob
            const downloadedFilename = this.api.handleFileDownload(fileBlob, filename);

            this.utils.showMessage('success', `原始入流數據下載成功！檔案: ${downloadedFilename}`);

        } catch (error) {
            console.error('原始數據下載失敗:', error);
            this.utils.showMessage('error', '入流數據下載失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(2, 'save');
        }
    }

    /**
     * 儲存調整後數據 - 保持原有邏輯並使用新 API
     */
    async saveAdjustedData() {
        const hasAdjusted = sessionStorage.getItem('step2_adjusted');
        if (!hasAdjusted) {
            this.utils.showMessage('error', '請先進行入流數據時距調整');
            return;
        }

        if (!this.inflowAdjustedData || this.inflowAdjustedData.length === 0) {
            this.utils.showMessage('error', '沒有調整後數據可以下載');
            return;
        }

        try {
            this.utils.showLoading(2, 'save-adjusted');

            // 🔧 修復：直接獲取 blob
            const fileBlob = await this.api.save(2, 'adjusted');

            if (!fileBlob || !(fileBlob instanceof Blob)) {
                throw new Error('後端返回的不是有效的檔案格式');
            }

            // 🔧 修復：生成統一格式的檔案名稱
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `步驟2_調整後入流數據_Δt${this.deltaT}hr_${timestamp}.xlsx`;

            // 🔧 修復：直接傳遞 blob
            const downloadedFilename = this.api.handleFileDownload(fileBlob, filename);

            this.utils.showMessage('success', '調整後入流數據下載成功！');

        } catch (error) {
            console.error('調整後數據下載失敗:', error);
            this.utils.showMessage('error', '調整後入流數據下載失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(2, 'save-adjusted');
        }
    }

    /**
     * 繪製圖表 - 保持原有邏輯
     */
    drawChart() {
        const hasUploaded = sessionStorage.getItem('step2_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳入流數據');
            return;
        }

        // 優先使用調整後的數據，如果沒有則使用原始數據
        const currentData = this.inflowAdjustedData || this.inflowOriginalData;

        if (!currentData || currentData.length === 0) {
            this.utils.showMessage('error', '沒有入流數據可以繪圖，請先上傳檔案');
            return;
        }

        try {
            this.utils.showLoading(2, 'draw');

            const chartData = {
                times: currentData.map(row => parseFloat(row.Time)),
                flows: currentData.map(row => parseFloat(row.Flow))
            };

            const success = this.charts.createChart(2, chartData);

            if (success) {
                const dataType = this.inflowAdjustedData ? `調整後數據 (Δt=${this.deltaT}h)` : '原始數據';
                this.utils.showMessage('success', `入流數據圖表繪製成功！(${dataType})`);
            } else {
                throw new Error('入流數據圖表創建失敗');
            }
        } catch (error) {
            this.utils.showMessage('error', '入流數據繪圖失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(2, 'draw');
        }
    }

    /**
     * 匯出圖表 - 確認是否正確實作
     */
    async exportChart() {
        const hasUploaded = sessionStorage.getItem('step2_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳入流數據');
            return;
        }

        if (!this.charts.hasChart(2)) {
            this.utils.showMessage('error', '請先點擊「繪圖」按鈕繪製入流數據圖表');
            return;
        }

        try {
            this.utils.showLoading(2, 'export');
            // console.log('開始匯出步驟2圖表...');

            // 調用 API 匯出圖表
            const imageBlob = await this.api.exportChart(2);
            // console.log('接收到圖片 blob:', imageBlob.size, 'bytes');

            // 🔧 修復：生成統一格式的檔案名稱
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const dataType = this.inflowAdjustedData ? `調整後數據_Δt${this.deltaT}h` : '原始數據';
            const filename = `步驟2_入流流量歷線圖_${dataType}_${timestamp}.png`;

            // 處理檔案下載
            const downloadedFilename = this.api.handleFileDownload(imageBlob, filename);

            this.utils.showMessage('success', `入流數據圖表匯出成功！檔案: ${downloadedFilename}`);
            // console.log('步驟2圖表匯出完成');

        } catch (error) {
            console.error('圖表匯出失敗:', error);
            this.utils.showMessage('error', `入流數據圖表匯出失敗: ${error.message}`);
        } finally {
            this.utils.hideLoading(2, 'export');
        }
    }

    /**
     * 清除所有 sessionStorage 數據
     */
    clearAllSessionData() {
        sessionStorage.removeItem('step2_uploaded');
        sessionStorage.removeItem('step2_adjusted');
        sessionStorage.removeItem('step2_originalData');
        sessionStorage.removeItem('step2_adjustedData');
        sessionStorage.removeItem('step2_initialWL');
        sessionStorage.removeItem('step2_deltaT');
    }

    /**
     * 清除調整後數據
     */
    clearAdjustedData() {
        sessionStorage.removeItem('step2_adjusted');
        sessionStorage.removeItem('step2_adjustedData');
        sessionStorage.removeItem('step2_deltaT');
        this.inflowAdjustedData = null;
        this.deltaT = null;
        this.adjustmentSummary = null;

        const adjustedTableBody = document.getElementById('inflow-adjusted-table');
        if (adjustedTableBody) {
            adjustedTableBody.innerHTML = '';
        }

        // 隱藏調整摘要
        const summaryContainer = document.querySelector('#step-2 .adjustment-summary');
        if (summaryContainer) {
            summaryContainer.style.display = 'none';
        }
    }

    // ==================== 公用方法 ====================

    /**
     * 檢查是否有數據
     */
    hasData() {
        return !!(this.inflowOriginalData && this.inflowOriginalData.length > 0);
    }

    /**
     * 檢查是否有調整後數據
     */
    hasAdjustedData() {
        return !!(this.inflowAdjustedData && this.inflowAdjustedData.length > 0);
    }

    /**
     * 獲取當前數據狀態
     */
    getDataStatus() {
        return {
            hasOriginal: this.hasData(),
            hasAdjusted: this.hasAdjustedData(),
            originalCount: this.inflowOriginalData?.length || 0,
            adjustedCount: this.inflowAdjustedData?.length || 0,
            deltaT: this.deltaT,
            initialWL: this.initialWL
        };
    }

    /**
     * 獲取調整資訊 - 新增方法
     */
    async getAdjustmentInfo() {
        try {
            const info = await this.api.getAdjustmentInfo(2);
            return info;
        } catch (error) {
            console.error('獲取調整資訊失敗:', error);
            return null;
        }
    }
}

// 創建全局實例
window.fdStep2 = new Step2Manager();