/**
 * 排洪演算平台 - 步驟3：排洪率定曲線管理
 */
class Step3Manager {
    constructor() {
        this.step = 3;
        this.api = window.fdAPI;
        this.charts = window.fdCharts;
        this.utils = window.fdUtils;
        this.tables = window.fdTables;

        // 數據狀態
        this.facilitiesData = null;        // 所有設施數據
        this.currentFacilityId = null;     // 當前選中的設施ID
        this.currentFacilityData = null;   // 當前設施的數據

        this.init();
    }

    /**
     * 初始化步驟3管理器
     */
    init() {
        // console.log('初始化步驟3管理器');

        // 綁定事件
        this.bindEvents();
    }

    /**
     * 綁定事件監聽器
     */
    bindEvents() {
        // 設施選擇事件
        const facilitySelect = document.getElementById('facility-select');
        if (facilitySelect) {
            facilitySelect.addEventListener('change', (e) => this.handleFacilityChange(e.target.value));
        }

        // 操作按鈕事件
        const dataInputBtn = document.querySelector('#step-3 .data-input-btn');
        const drawBtn = document.querySelector('#step-3 .draw-btn');
        const exportBtn = document.querySelector('#step-3 .export-btn');

        if (dataInputBtn) {
            dataInputBtn.addEventListener('click', () => this.triggerFileUpload());
        }

        if (drawBtn) {
            drawBtn.addEventListener('click', () => this.drawChart());
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportChart());
        }
    }

    /**
     * 載入步驟數據
     */
    loadStepData() {
        // console.log('步驟3 loadStepData() 方法被調用');

        const hasUploaded = sessionStorage.getItem('step3_uploaded');
        if (!hasUploaded) {
            // console.log('步驟3 無上傳記錄，清空數據');
            this.clearStepData();
            return;
        }

        // 從 sessionStorage 恢復數據
        const savedData = sessionStorage.getItem('step3_facilitiesData');
        const savedCurrentId = sessionStorage.getItem('step3_currentFacilityId');

        if (savedData) {
            try {
                this.facilitiesData = JSON.parse(savedData);
                // console.log('從 sessionStorage 恢復排洪設施數據');

                // 恢復設施選單
                this.updateFacilitySelect();

                // 恢復當前選中設施
                if (savedCurrentId) {
                    this.currentFacilityId = savedCurrentId;
                    this.handleFacilityChange(savedCurrentId, false); // false 表示不觸發額外的保存
                }

                const q_power = sessionStorage.getItem('step3_q_power');
                const q_start = sessionStorage.getItem('step3_q_start');
                const q_end = sessionStorage.getItem('step3_q_end');
                if (q_power !== null && q_start !== null && q_end !== null) {
                    this.utils.showMessage(
                        'info',
                        `已恢復排洪設施數據<br>q_power: ${q_power}, q_start: ${q_start}, q_end: ${q_end}`
                    );
                } else {
                    this.utils.showMessage('info', '已恢復排洪設施數據');
                }

            } catch (error) {
                console.error('恢復排洪設施數據失敗:', error);
                this.clearAllSessionData();
                this.utils.showMessage('warning', '排洪設施數據恢復失敗，請重新上傳檔案');
                this.clearStepData();
            }
        } else {
            // console.log('排洪設施數據丟失，清除狀態');
            this.clearAllSessionData();
            this.utils.showMessage('warning', '排洪設施數據已丟失，請重新上傳檔案');
            this.clearStepData();
        }

        // 自動繪圖
        if (this.currentFacilityId && this.currentFacilityData && this.currentFacilityData.openings?.length > 0) {
            this.drawChart();
        }
    }

    /**
     * 清空步驟數據
     */
    clearStepData() {
        // console.log('步驟3 clearStepData() 方法被調用');

        // 🔧 修改：清空表格並顯示預設訊息
        this.clearDataTable();

        // 清空設施選單
        const facilitySelect = document.getElementById('facility-select');
        if (facilitySelect) {
            facilitySelect.innerHTML = '<option value="">請選擇設施</option>';
        }

        // 重置數據
        this.facilitiesData = null;
        this.currentFacilityId = null;
        this.currentFacilityData = null;
    }

    /**
     * 處理檔案上傳
     */
    async handleUpload(file) {
        try {
            this.utils.showLoading(3, 'upload');

            const result = await this.api.upload(3, file);

            if (result.success) {
                // 更新數據
                this.facilitiesData = result.data.facilities;

                // 更新設施選單
                this.updateFacilitySelect();

                // 🔧 修復：自動選擇第一個設施並同步下拉選單
                if (this.facilitiesData && this.facilitiesData.length > 0) {
                    this.currentFacilityId = this.facilitiesData[0].id;

                    // 🆕 添加：同步下拉選單的選中狀態
                    const facilitySelect = document.getElementById('facility-select');
                    if (facilitySelect) {
                        facilitySelect.value = this.currentFacilityId;
                    }

                    // 處理設施變更（更新表格等）
                    this.handleFacilityChange(this.currentFacilityId);
                }

                // 保存數據到 sessionStorage
                sessionStorage.setItem('step3_facilitiesData', JSON.stringify(this.facilitiesData));
                sessionStorage.setItem('step3_uploaded', 'true');

                this.utils.showMessage('success', result.message || '排洪設施數據上傳成功！');

                if (result.data && typeof result.q_power !== 'undefined') {
                    sessionStorage.setItem('step3_q_power', result.q_power);
                    sessionStorage.setItem('step3_q_start', result.q_start);
                    sessionStorage.setItem('step3_q_end', result.q_end);
                }
            } else {
                throw new Error(result.message || '上傳失敗');
            }
        } catch (error) {
            this.utils.showMessage('error', '排洪設施數據上傳失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(3, 'upload');
        }
    }

    /**
     * 🔧 修改：更新設施選單 - 顯示開度數量
     */
    updateFacilitySelect() {
        const facilitySelect = document.getElementById('facility-select');
        if (!facilitySelect || !this.facilitiesData) return;

        // 清空現有選項
        facilitySelect.innerHTML = '<option value="">請選擇設施</option>';

        // 添加設施選項，顯示開度數量
        this.facilitiesData.forEach(facility => {
            const option = document.createElement('option');
            option.value = facility.id;
            option.textContent = `${facility.name} (${facility.openings?.length || 0}個開度)`;
            facilitySelect.appendChild(option);
        });

        // 🔧 修復：確保下拉選單與當前設施ID同步
        if (this.currentFacilityId) {
            facilitySelect.value = this.currentFacilityId;
            // console.log(`下拉選單已同步到設施ID: ${this.currentFacilityId}`);
        }
    }

    /**
     * 處理設施變更
     */
    handleFacilityChange(facilityId, shouldSave = true) {
        if (!facilityId || !this.facilitiesData) {
            this.currentFacilityId = null;
            this.currentFacilityData = null;
            this.clearDataTable();

            // 🆕 添加：確保下拉選單也重置
            const facilitySelect = document.getElementById('facility-select');
            if (facilitySelect) {
                facilitySelect.value = '';
            }
            return;
        }

        // 查找選中的設施
        const facility = this.facilitiesData.find(f => f.id == facilityId);
        if (!facility) {
            this.utils.showMessage('error', '找不到指定的設施');
            return;
        }

        this.currentFacilityId = facilityId;
        this.currentFacilityData = facility;

        // 🆕 添加：確保下拉選單與當前選擇同步
        const facilitySelect = document.getElementById('facility-select');
        if (facilitySelect && facilitySelect.value != facilityId) {
            facilitySelect.value = facilityId;
            // console.log(`下拉選單已同步到設施: ${facility.name}`);
        }

        // 🔧 修改：更新為唯讀表格
        this.updateDataTable();

        // 🔧 移除：不再自動更新圖表
        // this.updateChart();  ← 註解掉這一行

        // 保存當前選擇
        if (shouldSave) {
            sessionStorage.setItem('step3_currentFacilityId', facilityId);
        }

        // console.log(`切換到設施: ${facility.name}，開度數量: ${facility.openings?.length || 0}`);
    }

    /**
     * 🔧 修改：更新數據表格 - 支援多開度橫向展示
     */
    updateDataTable() {
        const table = document.getElementById('drainage-data-table');
        const openingHeaderRow = document.getElementById('opening-header-row');
        const dataHeaderRow = document.getElementById('data-header-row');
        const tableBody = document.querySelector('#drainage-data-table tbody');

        if (!table || !openingHeaderRow || !dataHeaderRow || !tableBody) return;

        if (!this.currentFacilityData || !this.currentFacilityData.openings) {
            this.clearDataTable();
            return;
        }

        const openings = this.currentFacilityData.openings;

        if (openings.length === 0) {
            this.clearDataTable();
            return;
        }

        // 🔧 修改：重建表頭結構
        this.buildTableHeaders(openings, openingHeaderRow, dataHeaderRow);

        // 🔧 修改：重建表格內容
        this.buildTableBody(openings, tableBody);

        // console.log(`表格已更新，設施: ${this.currentFacilityData.name}, 開度數: ${openings.length}`);
    }

    /**
     * 🆕 建立表格標頭
     */
    buildTableHeaders(openings, openingHeaderRow, dataHeaderRow) {
        // 清空現有標頭
        openingHeaderRow.innerHTML = '';
        dataHeaderRow.innerHTML = '';

        // 為每個開度創建兩欄（水位、流量）
        openings.forEach((opening) => {
            // 🔧 修改：處理「全開」的顯示
            const openingDisplay = opening.opening === "全開" ? "全開" : `${opening.opening}m`;

            // 開度標頭（跨兩欄）
            const openingHeader = document.createElement('th');
            openingHeader.colSpan = 2;
            openingHeader.className = 'text-center table-primary';
            openingHeader.innerHTML = `<strong>開度 ${openingDisplay}</strong>`;
            openingHeaderRow.appendChild(openingHeader);

            // 水位欄標頭
            const waterLevelHeader = document.createElement('th');
            waterLevelHeader.className = 'text-center';
            waterLevelHeader.textContent = '水位(m)';
            dataHeaderRow.appendChild(waterLevelHeader);

            // 流量欄標頭
            const flowHeader = document.createElement('th');
            flowHeader.className = 'text-center';
            flowHeader.textContent = '流量(cms)';
            dataHeaderRow.appendChild(flowHeader);
        });
    }

    /**
     * 🆕 建立表格內容
     */
    buildTableBody(openings, tableBody) {
        // 清空表格內容
        tableBody.innerHTML = '';

        // 🔧 找出最大數據點數，決定表格行數
        const maxDataLength = Math.max(...openings.map(opening => opening.data?.length || 0));

        if (maxDataLength === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="${openings.length * 2}" class="text-center text-muted p-4">
                        該設施沒有有效數據
                    </td>
                </tr>
            `;
            return;
        }

        // 🔧 修改：為每一行數據創建表格行，文字置中並添加顏色樣式
        for (let rowIndex = 0; rowIndex < maxDataLength; rowIndex++) {
            const row = document.createElement('tr');
            row.className = 'new-data'; // 新增動畫 class

            // 直接為每個開度添加水位和流量欄位
            openings.forEach((opening, openingIndex) => {
                const data = opening.data || [];
                const point = data[rowIndex]; // 可能為 undefined

                // 🎨 計算欄位索引來決定顏色
                const waterLevelColumnIndex = openingIndex * 2;      // 水位欄位索引
                const flowColumnIndex = openingIndex * 2 + 1;        // 流量欄位索引

                // 水位欄位
                const waterLevelCell = document.createElement('td');
                waterLevelCell.className = 'text-center'; // 🔧 修改：改為置中

                if (point && typeof point.water_level === 'number') {
                    waterLevelCell.textContent = point.water_level.toFixed(2);
                    // 🎨 添加藍紫色、藍綠色相間樣式
                    if (waterLevelColumnIndex % 2 === 0) {
                        waterLevelCell.style.color = 'rgb(81, 75, 162)'; // 藍紫色 (Bootstrap purple)
                    } else {
                        waterLevelCell.style.color = 'rgb(75, 127, 162)'; // 藍綠色 (Bootstrap teal)
                    }
                } else {
                    waterLevelCell.textContent = '-';
                    waterLevelCell.className += ' text-muted';
                }
                row.appendChild(waterLevelCell);

                // 流量欄位
                const flowCell = document.createElement('td');
                flowCell.className = 'text-center'; // 🔧 修改：改為置中

                if (point && typeof point.flow === 'number') {
                    flowCell.textContent = point.flow.toFixed(3);
                    // 🎨 添加藍紫色、藍綠色相間樣式
                    if (flowColumnIndex % 2 === 0) {
                        flowCell.style.color = 'rgb(81, 75, 162)'; // 藍紫色 (Bootstrap purple)
                    } else {
                        flowCell.style.color = 'rgb(75, 127, 162)'; // 藍綠色 (Bootstrap teal)
                    }
                } else {
                    flowCell.textContent = '-';
                    flowCell.className += ' text-muted';
                }
                row.appendChild(flowCell);
            });

            tableBody.appendChild(row);

            // 新增動畫效果
            row.style.opacity = '0';
            row.style.transform = 'translateY(20px)';
            setTimeout(() => {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, rowIndex * 30);
        }
        // 移除高亮效果
        setTimeout(() => {
            tableBody.querySelectorAll('tr.new-data').forEach(tr => {
                tr.classList.remove('new-data');
            });
        }, 2000);
    }

    /**
     * 🔧 修改：清空數據表格 - 顯示預設訊息
     */
    clearDataTable() {
        const openingHeaderRow = document.getElementById('opening-header-row');
        const dataHeaderRow = document.getElementById('data-header-row');
        const tableBody = document.querySelector('#drainage-data-table tbody');

        // 🔧 修改：重置表頭為空狀態（不保留序號欄）
        if (openingHeaderRow) {
            openingHeaderRow.innerHTML = '';
        }

        if (dataHeaderRow) {
            dataHeaderRow.innerHTML = '';
        }

        // 重置表格內容
        if (tableBody) {
            tableBody.innerHTML = `
            `;
        }
    }

    /**
     * 更新圖表
     */
    updateChart() {
        if (!this.currentFacilityData || !this.currentFacilityData.openings) return;

        try {
            // 準備圖表數據
            const chartData = this.prepareChartData();

            // 創建圖表
            const success = this.charts.createChart(3, chartData);

            if (!success) {
                console.warn('圖表更新失敗');
            }
        } catch (error) {
            console.error('圖表更新錯誤:', error);
        }
    }

    /**
     * 🔧 修改：準備圖表數據 - 支援多開度
     */
    prepareChartData() {
        if (!this.currentFacilityData || !this.currentFacilityData.openings) return null;

        const datasets = [];
        // 🔧 修改：統一使用相同顏色，透過標籤區分
        const mainColor = '#9966FF'; // 紫色

        this.currentFacilityData.openings.forEach((opening, index) => {
            const data = opening.data || [];

            if (data.length > 0) {
                // 🔧 修改：處理「全開」的標籤顯示
                const openingDisplay = opening.opening === "全開" ? "全開" : `${opening.opening}m`;

                datasets.push({
                    label: `開度 ${openingDisplay}`,
                    data: data.map(point => ({
                        x: point.flow,
                        y: point.water_level
                    })),
                    borderColor: mainColor,
                    backgroundColor: mainColor + '20',
                    fill: false,
                    tension: 0.1,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointStyle: 'circle',
                    borderWidth: 2
                });
            }
        });

        return {
            type: 'line',
            datasets: datasets,
            facilityName: this.currentFacilityData.name || '未知設施'
        };
    }

    /**
     * 繪製圖表
     */
    drawChart() {
        const hasUploaded = sessionStorage.getItem('step3_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳排洪設施數據');
            return;
        }

        if (!this.currentFacilityId) {
            this.utils.showMessage('error', '請先選擇設施');
            return;
        }

        try {
            this.utils.showLoading(3, 'draw');

            this.updateChart();

            const facilityName = this.currentFacilityData?.name || '未知設施';
            this.utils.showMessage('success', `${facilityName} 排洪率定曲線繪製成功！`);

        } catch (error) {
            this.utils.showMessage('error', '排洪率定曲線繪製失敗: ' + error.message);
        } finally {
            this.utils.hideLoading(3, 'draw');
        }
    }

    /**
     * 🆕 儲存原始數據
     */
    async saveOriginalData() {
        // console.log('開始保存原始排洪設施數據...');

        // 檢查是否有上傳的數據
        const hasUploaded = sessionStorage.getItem('step3_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳排洪設施數據');
            return;
        }

        // 檢查本地數據是否存在
        if (!this.facilitiesData || this.facilitiesData.length === 0) {
            this.utils.showMessage('error', '沒有排洪設施數據可以下載');
            console.warn('本地原始數據為空:', this.facilitiesData);
            return;
        }

        try {
            this.utils.showLoading(3, 'save');
            // console.log('正在請求後端下載原始數據...');

            // 🔧 調用 API 獲取下載檔案 - 直接獲取 blob
            const fileBlob = await this.api.save(3, 'original');
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
            const filename = `步驟3_排洪設施數據_${timestamp}.xlsx`;

            // 🔧 直接傳遞 blob 給 handleFileDownload
            const downloadedFilename = this.api.handleFileDownload(fileBlob, filename);

            // console.log('檔案已下載:', downloadedFilename);
            this.utils.showMessage('success', `排洪設施數據下載成功！檔案: ${downloadedFilename}`);

        } catch (error) {
            console.error('原始數據下載失敗:', error);
            this.utils.showMessage('error', '排洪設施數據下載失敗: ' + error.message);

        } finally {
            this.utils.hideLoading(3, 'save');
        }
    }

    /**
     * 匯出圖表
     */
    async exportChart() {
        const hasUploaded = sessionStorage.getItem('step3_uploaded');
        if (!hasUploaded) {
            this.utils.showMessage('error', '請先上傳排洪設施數據');
            return;
        }

        if (!this.charts.hasChart(3)) {
            this.utils.showMessage('error', '請先點擊「繪圖」按鈕繪製排洪率定曲線');
            return;
        }

        if (!this.currentFacilityId) {
            this.utils.showMessage('error', '請先選擇設施');
            return;
        }

        try {
            this.utils.showLoading(3, 'export');
            // console.log('開始匯出步驟3圖表，設施ID:', this.currentFacilityId);

            // 🔧 修復：正確傳遞設施ID給API
            const imageBlob = await this.api.exportChart(3, this.currentFacilityId);
            // console.log('接收到圖片 blob:', imageBlob.size, 'bytes');

            // 生成統一格式的檔案名稱
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const facilityName = this.currentFacilityData?.name || '設施';
            const filename = `步驟3_排洪率定曲線_${facilityName}_${timestamp}.png`;

            // 處理檔案下載
            const downloadedFilename = this.api.handleFileDownload(imageBlob, filename);

            this.utils.showMessage('success', `排洪率定曲線圖表匯出成功！檔案: ${downloadedFilename}`);
            // console.log('步驟3圖表匯出完成');

        } catch (error) {
            console.error('圖表匯出失敗:', error);
            this.utils.showMessage('error', `排洪率定曲線圖表匯出失敗: ${error.message}`);
        } finally {
            this.utils.hideLoading(3, 'export');
        }
    }

    /**
     * 觸發檔案上傳
     */
    triggerFileUpload() {
        // 創建隱藏的檔案輸入元素
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.xlsx,.xls,.xlsm';
        fileInput.style.display = 'none';

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleUpload(file);
            }
        });

        document.body.appendChild(fileInput);
        fileInput.click();
        document.body.removeChild(fileInput);
    }

    /**
     * 深度複製對象
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    /**
     * 清除所有 sessionStorage 數據
     */
    clearAllSessionData() {
        sessionStorage.removeItem('step3_uploaded');
        sessionStorage.removeItem('step3_facilitiesData');
        sessionStorage.removeItem('step3_currentFacilityId');
        sessionStorage.removeItem('step3_q_power');
        sessionStorage.removeItem('step3_q_start');
        sessionStorage.removeItem('step3_q_end');
    }

    // ==================== 公用方法 ====================

    /**
     * 檢查是否有數據
     */
    hasData() {
        return !!(this.facilitiesData && this.facilitiesData.length > 0);
    }

    /**
     * 獲取當前數據狀態
     */
    getDataStatus() {
        return {
            hasData: this.hasData(),
            facilitiesCount: this.facilitiesData?.length || 0,
            currentFacilityId: this.currentFacilityId,
            currentFacilityName: this.currentFacilityData?.name || null,
            openingsCount: this.currentFacilityData?.openings?.length || 0
        };
    }
}

// 🔧 添加：排序函數 - 供 HTML 模板調用
function sortDrainageTable(column, direction) {
    // console.log('步驟3表格排序:', column, direction);

    if (window.fdStep3 && window.fdStep3.utils) {
        window.fdStep3.utils.showMessage('info', '排洪設施數據保持原始順序顯示');
    }
}

// 創建全局實例
window.fdStep3 = new Step3Manager();