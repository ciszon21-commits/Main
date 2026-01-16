/**
 * 排洪演算平台 - 步驟1 水庫庫容管理模組
 */
class Step1Manager {
    constructor() {
        // 依賴模組
        this.api = window.fdAPI;
        this.utils = window.fdUtils;
        this.tables = window.fdTables;
        this.charts = window.fdCharts;

        // 檢查依賴是否載入
        if (!this.api) console.warn('fdAPI 未載入');
        if (!this.utils) console.warn('fdUtils 未載入');
        if (!this.tables) console.warn('fdTables 未載入');
        if (!this.charts) console.warn('fdCharts 未載入');

        // 步驟1的數據
        this.reservoirData = null;

        // console.log('Step1Manager 構造函數執行完成');
    }

    /**
     * 初始化步驟1
     */
    init() {
        // console.log('步驟1 init() 方法被調用');

        // 清空表格
        const reservoirTable = document.getElementById('reservoir-data-table');
        if (reservoirTable) reservoirTable.innerHTML = '';

        // console.log('步驟1管理器已初始化');
    }

    /**
     * 載入步驟數據
     */
    loadStepData() {
        // console.log('步驟1 loadStepData() 方法被調用');

        const hasUploaded = sessionStorage.getItem('step1_uploaded');
        if (!hasUploaded) {
            // console.log('步驟1 無上傳記錄，清空數據');
            this.clearStepData();
            return;
        }

        // 從 sessionStorage 恢復數據
        const savedData = sessionStorage.getItem('step1_reservoirData');
        if (savedData) {
            try {
                this.reservoirData = JSON.parse(savedData);

                // ✅ 確保全局數據同步
                window.currentTableData = this.reservoirData;

                // console.log('從 sessionStorage 恢復水庫庫容數據:', this.reservoirData);
                // console.log('全局數據已同步:', window.currentTableData);

                // 重新渲染表格
                this.renderTable();

                // 顯示恢復訊息
                if (this.utils) {
                    this.utils.showMessage('info', '已恢復水庫庫容數據');
                }

                // 自動繪圖
                if (this.reservoirData && this.reservoirData.length > 0) {
                    this.drawChart();
                }

            } catch (error) {
                console.error('恢復水庫庫容數據失敗:', error);
                // 數據損壞，清除所有狀態
                this.clearAllSessionData();
                if (this.utils) {
                    this.utils.showMessage('warning', '數據恢復失敗，請重新上傳檔案');
                }
                this.clearStepData();
            }
        } else {
            // sessionStorage 中沒有數據，但有上傳標記，表示數據丟失
            // console.log('水庫庫容數據丟失，清除狀態');
            this.clearAllSessionData();
            if (this.utils) {
                this.utils.showMessage('warning', '水庫庫容數據已丟失，請重新上傳檔案');
            }
            this.clearStepData();
        }
    }

    /**
     * 處理檔案上傳
     */
    async handleUpload(file) {
        try {
            this.utils.showLoading(1, 'upload');

            const result = await this.api.upload(1, file);
            // console.log('API 回傳結果:', result);

            if (result.success) {
                // 標準化數據格式
                // console.log('開始標準化數據...');
                this.reservoirData = this.normalizeReservoirData(result.data);
                window.currentTableData = this.reservoirData; // 更新全局變數以保持兼容性

                // console.log('標準化後的數據:', this.reservoirData);

                // 保存數據到 sessionStorage
                sessionStorage.setItem('step1_reservoirData', JSON.stringify(this.reservoirData));

                this.renderTable();
                this.utils.showMessage('success', result.message || '水庫庫容數據上傳成功！');
                sessionStorage.setItem('step1_uploaded', 'true');

                // console.log('水庫庫容數據已保存到 sessionStorage');
            } else {
                throw new Error(result.message || '上傳失敗');
            }
        } catch (error) {
            console.error('上傳過程發生錯誤:', error);
            this.utils.showMessage('error', '水庫庫容數據上傳失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(1, 'upload');
        }
    }

    /**
     * 渲染數據表格
     */
    renderTable() {
        if (!this.reservoirData) {
            // console.log('步驟1沒有數據可渲染');
            return;
        }

        // console.log('渲染步驟1表格，數據:', this.reservoirData);

        const tableBody = document.getElementById('reservoir-data-table');
        if (tableBody && this.tables) {
            this.tables.renderTable(
                tableBody,
                this.reservoirData,
                this.tables.getStep1RowRenderer()
            );
        } else {
            console.error('表格元素或 fdTables 模組不存在');
        }
    }

    /**
     * 獲取字段值（支援多種字段名稱）
     */
    getFieldValue(row, fieldNames) {
        for (const fieldName of fieldNames) {
            if (row.hasOwnProperty(fieldName) && row[fieldName] !== undefined && row[fieldName] !== null) {
                return row[fieldName];
            }
        }
        return '';
    }

    /**
     * 格式化數字顯示
     */
    formatNumber(value) {
        if (value === null || value === undefined || value === '' || value === 'undefined') {
            return '-';
        }

        const num = parseFloat(value);
        if (isNaN(num)) {
            return value.toString();
        }

        // 根據數值大小決定小數位數
        if (Math.abs(num) >= 1000000) {
            return num.toLocaleString('zh-TW', { maximumFractionDigits: 0 });
        } else if (Math.abs(num) >= 1000) {
            return num.toLocaleString('zh-TW', { maximumFractionDigits: 2 });
        } else {
            return num.toLocaleString('zh-TW', { maximumFractionDigits: 3 });
        }
    }

    /**
     * 標準化水庫數據格式
     */
    normalizeReservoirData(data) {
        if (!Array.isArray(data)) {
            console.error('數據不是陣列格式:', data);
            return [];
        }

        // console.log('原始數據樣例:', data[0]);

        return data.map((row, index) => {
            const normalized = {
                level: this.getFieldValue(row, ['level', 'Level', '水位, H (m)', '水位']),
                area: this.getFieldValue(row, ['area', 'Area', '面積, A (m²)', '面積']),
                volume: this.getFieldValue(row, ['volume', 'Volume', '容量, V (m³)', '容量'])
            };

            // console.log(`第${index + 1}筆水庫數據標準化:`, normalized);
            return normalized;
        });
    }

    /**
     * 保存原始數據
     */
    async saveOriginalData() {
        // console.log('開始保存原始水庫庫容數據...');

        // 檢查是否有上傳的數據
        const hasUploaded = sessionStorage.getItem('step1_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳水庫庫容數據');
            return;
        }

        // 檢查本地數據是否存在
        if (!this.reservoirData || this.reservoirData.length === 0) {
            this.utils.showMessage('error', '沒有原始水庫庫容數據可以下載');
            console.warn('本地原始數據為空:', this.reservoirData);
            return;
        }

        try {
            this.utils.showLoading(1, 'save');
            // console.log('正在請求後端下載原始數據...');

            // 🔧 調用 API 獲取下載檔案 - 直接獲取 blob
            const fileBlob = await this.api.save(1, 'original');
            // console.log('後端響應 blob:', fileBlob);

            // 🔧 檢查 blob
            if (!fileBlob || !(fileBlob instanceof Blob)) {
                throw new Error('後端返回的不是有效的檔案格式');
            }

            // 檢查檔案大小
            if (fileBlob.size === 0) {
                throw new Error('下載的檔案為空');
            }

            // console.log('檔案下載成功，大小:', fileBlob.size, 'bytes');

            // 🔧 修復：生成統一格式的檔案名稱
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `步驟1_水庫庫容數據_${timestamp}.xlsx`;

            // 🔧 修復：實際執行檔案下載
            const downloadedFilename = this.api.handleFileDownload(fileBlob, filename);

            // console.log('檔案已下載:', downloadedFilename);
            this.utils.showMessage('success', `水庫庫容數據下載成功！檔案: ${downloadedFilename}`);

        } catch (error) {
            console.error('原始數據下載失敗:', error);
            this.utils.showMessage('error', '水庫庫容數據下載失敗: ' + error.message);

        } finally {
            this.utils.hideLoading(1, 'save');
        }
    }

    /**
     * 繪製圖表
     */
    drawChart() {
        const hasUploaded = sessionStorage.getItem('step1_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳水庫庫容數據');
            return;
        }

        if (!this.reservoirData || this.reservoirData.length === 0) {
            this.utils.showMessage('error', '沒有水庫庫容數據可以繪圖，請先上傳檔案');
            return;
        }

        try {
            this.utils.showLoading(1, 'draw');

            const chartData = {
                levels: this.reservoirData.map(row => parseFloat(row.level) || 0),
                areas: this.reservoirData.map(row => parseFloat(row.area) || 0),
                volumes: this.reservoirData.map(row => parseFloat(row.volume) || 0)
            };

            const success = this.charts.createChart(1, chartData);

            if (success) {
                this.utils.showMessage('success', '水庫庫容圖表繪製成功！');
            } else {
                throw new Error('水庫庫容圖表創建失敗');
            }
        } catch (error) {
            this.utils.showMessage('error', '水庫庫容繪圖失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(1, 'draw');
        }
    }

    /**
     * 匯出圖表
     */
    async exportChart() {
        const hasUploaded = sessionStorage.getItem('step1_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳水庫庫容數據');
            return;
        }

        if (!this.charts.hasChart(1)) {
            this.utils.showMessage('error', '請先點擊「繪圖」按鈕繪製圖表');
            return;
        }

        try {
            this.utils.showLoading(1, 'export');
            // console.log('開始匯出步驟1圖表...');

            // 調用 API 匯出圖表
            const imageBlob = await this.api.exportChart(1);
            // console.log('接收到圖片 blob:', imageBlob.size, 'bytes');

            // 🔧 修復：生成統一格式的檔案名稱
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `步驟1_水庫庫容關係圖_${timestamp}.png`;

            // 處理檔案下載
            const downloadedFilename = this.api.handleFileDownload(imageBlob, filename);

            this.utils.showMessage('success', `圖表匯出成功！檔案: ${downloadedFilename}`);
            // console.log('步驟1圖表匯出完成');

        } catch (error) {
            console.error('圖表匯出失敗:', error);
            this.utils.showMessage('error', `水庫庫容圖表匯出失敗: ${error.message}`);
        } finally {
            this.utils.hideLoading(1, 'export');
        }
    }

    /**
     * 清除所有 sessionStorage 數據
     */
    clearAllSessionData() {
        sessionStorage.removeItem('step1_uploaded');
        sessionStorage.removeItem('step1_reservoirData');
        // console.log('步驟1 sessionStorage 數據已清除');
    }

    /**
     * 清空步驟數據
     */
    clearStepData() {
        // console.log('步驟1 clearStepData() 方法被調用');

        const reservoirTable = document.getElementById('reservoir-data-table');
        if (reservoirTable) {
            reservoirTable.innerHTML = '';
        }

        this.reservoirData = null;
        window.currentTableData = []; // 同時清除全局變數
    }
}

// 檢查並創建全局實例
try {
    // console.log('準備創建 fdStep1 實例');
    window.fdStep1 = new Step1Manager();
    // console.log('fdStep1 實例創建成功:', window.fdStep1);
    // console.log('fdStep1 所有方法:', Object.getOwnPropertyNames(Object.getPrototypeOf(window.fdStep1)));
    // console.log('fdStep1.loadStepData 類型:', typeof window.fdStep1.loadStepData);
} catch (error) {
    console.error('創建 fdStep1 實例失敗:', error);
}