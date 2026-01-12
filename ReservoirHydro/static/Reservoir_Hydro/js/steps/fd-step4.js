class Step4Manager {
    constructor() {
        // 條件資料陣列
        this.conditions = [];
        // 設施與開度資料
        this.facilities = [];
        // 編輯索引
        this.editingIdx = null;
        // 初始化
        this.init();
    }

    init() {
        this.loadFacilities();
        // 載入已存條件
        const saved = sessionStorage.getItem('step4_conditions');
        if (saved) {
            try {
                this.conditions = JSON.parse(saved);
            } catch (e) {
                this.conditions = [];
            }
        }
        document.getElementById('add-condition-btn').onclick = async () => { await this.addCondition(); };
        document.getElementById('export-condition-btn').onclick = () => this.exportConditions();
        this.renderTable();

        // === 新增：載入時吐司訊息 ===
        if (this.conditions && this.conditions.length > 0) {
            fdUtils.showMessage('info', `已恢復排洪規則設定，共 ${this.conditions.length} 筆`);
        } else {
            fdUtils.showMessage('info', '尚未設定排洪規則，請新增條件');
        }
    }

    loadFacilities() {
        const facilitiesData = sessionStorage.getItem('step3_facilitiesData');
        if (facilitiesData) {
            try {
                this.facilities = JSON.parse(facilitiesData);
            } catch (e) {
                this.facilities = [];
            }
        } else {
            this.facilities = [];
        }
    }

    // 渲染條件設定表格
    renderTable() {
        const container = document.getElementById('step4-condition-table');
        if (!container) return;

        let html = `
        <div class="table-responsive">
        <table class="table table-striped table-bordered align-middle mb-0">
            <colgroup>
                <col style="width: 100px;">
                <col style="width: 50px;">
                <col style="width: 160px;">
                <col style="width: 160px;">
                <col style="width: 160px;">
                <col style="width: 160px;">
                <col style="width: 160px;">
                <col style="width: 150px;">
            </colgroup>
            <thead class="table-primary">
                <tr>
                    <th>設施</th>
                    <th>開度</th>
                    <th>時間控制<br>(hr)</th>
                    <th>流量控制(洪峰前)<br>(cms)</th>
                    <th>流量控制(洪峰後)<br>(cms)</th>
                    <th>水位控制(洪峰前)<br>(m)</th>
                    <th>水位控制(洪峰後)<br>(m)</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
        `;

        if (this.conditions.length === 0) {
            html += `<tr><td colspan="8" class="text-center text-muted">尚未新增任何條件</td></tr>`;
        } else {
            // 依步驟三設施與開度順序組合排序
            let ordered = [];
            let orderedIdxMap = [];
            this.facilities.forEach(fac => {
                (fac.openings || []).forEach(openingObj => {
                    const condIdx = this.conditions.findIndex(
                        c => c.facility === fac.name && c.opening == openingObj.opening
                    );
                    if (condIdx !== -1) {
                        ordered.push(this.conditions[condIdx]);
                        orderedIdxMap.push(condIdx);
                    }
                });
            });
            this.conditions.forEach((c, i) => {
                if (!ordered.includes(c)) {
                    ordered.push(c);
                    orderedIdxMap.push(i);
                }
            });
            ordered.forEach((cond, idx) => {
                if (this.editingIdx === idx) {
                    // 編輯模式
                    html += `
                    <tr>
                        <td>${cond.facility || ''}</td>
                        <td>${cond.opening || ''}</td>
                        <td>
                            <i class="bi bi-power"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.time_control[0] !== undefined ? cond.time_control[0] : ''}"
                                placeholder="起始時間"
                                data-idx="${orderedIdxMap[idx]}" data-type="time_control" data-pos="0"
                                onblur="fdStep4.handleInputChange(event)">
                            <br>
                            <i class="bi bi-stop-circle"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.time_control[1] !== undefined ? cond.time_control[1] : ''}"
                                placeholder="結束時間"
                                data-idx="${orderedIdxMap[idx]}" data-type="time_control" data-pos="1"
                                onblur="fdStep4.handleInputChange(event)">
                        </td>
                        <td>
                            <i class="bi bi-power"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.flow_control_before[0] !== undefined ? cond.flow_control_before[0] : ''}"
                                placeholder="開啟流量"
                                data-idx="${orderedIdxMap[idx]}" data-type="flow_control_before" data-pos="0"
                                onblur="fdStep4.handleInputChange(event)">
                            <br>
                            <i class="bi bi-stop-circle"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.flow_control_before[1] !== undefined ? cond.flow_control_before[1] : ''}"
                                placeholder="關閉流量"
                                data-idx="${orderedIdxMap[idx]}" data-type="flow_control_before" data-pos="1"
                                onblur="fdStep4.handleInputChange(event)">
                        </td>
                        <td>
                            <i class="bi bi-power"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.flow_control_after[0] !== undefined ? cond.flow_control_after[0] : ''}"
                                placeholder="開啟流量"
                                data-idx="${orderedIdxMap[idx]}" data-type="flow_control_after" data-pos="0"
                                onblur="fdStep4.handleInputChange(event)">
                            <br>
                            <i class="bi bi-stop-circle"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.flow_control_after[1] !== undefined ? cond.flow_control_after[1] : ''}"
                                placeholder="關閉流量"
                                data-idx="${orderedIdxMap[idx]}" data-type="flow_control_after" data-pos="1"
                                onblur="fdStep4.handleInputChange(event)">
                        </td>
                        <td>
                            <i class="bi bi-power"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.waterlevel_control_before[0] !== undefined ? cond.waterlevel_control_before[0] : ''}"
                                placeholder="開啟水位"
                                data-idx="${orderedIdxMap[idx]}" data-type="waterlevel_control_before" data-pos="0"
                                onblur="fdStep4.handleInputChange(event)">
                            <br>
                            <i class="bi bi-stop-circle"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.waterlevel_control_before[1] !== undefined ? cond.waterlevel_control_before[1] : ''}"
                                placeholder="關閉水位"
                                data-idx="${orderedIdxMap[idx]}" data-type="waterlevel_control_before" data-pos="1"
                                onblur="fdStep4.handleInputChange(event)">
                        </td>
                        <td>
                            <i class="bi bi-power"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.waterlevel_control_after[0] !== undefined ? cond.waterlevel_control_after[0] : ''}"
                                placeholder="開啟水位"
                                data-idx="${orderedIdxMap[idx]}" data-type="waterlevel_control_after" data-pos="0"
                                onblur="fdStep4.handleInputChange(event)">
                            <br>
                            <i class="bi bi-stop-circle"></i>
                            <input type="text" class="form-control form-control-sm" style="width:90px;display:inline-block"
                                value="${cond.waterlevel_control_after[1] !== undefined ? cond.waterlevel_control_after[1] : ''}"
                                placeholder="關閉水位"
                                data-idx="${orderedIdxMap[idx]}" data-type="waterlevel_control_after" data-pos="1"
                                onblur="fdStep4.handleInputChange(event)">
                        </td>
                        <td>
                            <button class="btn btn-sm btn-success" onclick="fdStep4.saveCondition(${idx})">
                                <i class="bi bi-floppy"></i> 儲存
                            </button>
                            <button class="btn btn-sm btn-secondary ms-1" onclick="fdStep4.cancelEdit()">
                                <i class="bi bi-x-square"></i> 取消
                            </button>
                        </td>
                    </tr>
                    `;
                } else {
                    // 靜態模式
                    html += `
                    <tr>
                        <td>${cond.facility || ''}</td>
                        <td>${cond.opening || ''}</td>
                        <td>
                            ${(cond.time_control?.[0] !== undefined && cond.time_control?.[0] !== '') ||
                            (cond.time_control?.[1] !== undefined && cond.time_control?.[1] !== '')
                            ? `
                                    <i class="bi bi-power"></i> ${(cond.time_control?.[0] !== undefined && cond.time_control?.[0] !== '') ? cond.time_control[0] : '-'}<br>
                                    <i class="bi bi-stop-circle"></i> ${(cond.time_control?.[1] !== undefined && cond.time_control?.[1] !== '') ? cond.time_control[1] : '-'}
                                `
                            : '-'
                        }
                        </td>
                        <td>
                            ${(cond.flow_control_before?.[0] !== undefined && cond.flow_control_before?.[0] !== '') ||
                            (cond.flow_control_before?.[1] !== undefined && cond.flow_control_before?.[1] !== '')
                            ? `
                                    <i class="bi bi-power"></i> ${(cond.flow_control_before?.[0] !== undefined && cond.flow_control_before?.[0] !== '') ? cond.flow_control_before[0] : '-'}<br>
                                    <i class="bi bi-stop-circle"></i> ${(cond.flow_control_before?.[1] !== undefined && cond.flow_control_before?.[1] !== '') ? cond.flow_control_before[1] : '-'}
                                `
                            : '-'
                        }
                        </td>
                        <td>
                            ${(cond.flow_control_after?.[0] !== undefined && cond.flow_control_after?.[0] !== '') ||
                            (cond.flow_control_after?.[1] !== undefined && cond.flow_control_after?.[1] !== '')
                            ? `
                                    <i class="bi bi-power"></i> ${(cond.flow_control_after?.[0] !== undefined && cond.flow_control_after?.[0] !== '') ? cond.flow_control_after[0] : '-'}<br>
                                    <i class="bi bi-stop-circle"></i> ${(cond.flow_control_after?.[1] !== undefined && cond.flow_control_after?.[1] !== '') ? cond.flow_control_after[1] : '-'}
                                `
                            : '-'
                        }
                        </td>
                        <td>
                            ${(cond.waterlevel_control_before?.[0] !== undefined && cond.waterlevel_control_before?.[0] !== '') ||
                            (cond.waterlevel_control_before?.[1] !== undefined && cond.waterlevel_control_before?.[1] !== '')
                            ? `
                                    <i class="bi bi-power"></i> ${(cond.waterlevel_control_before?.[0] !== undefined && cond.waterlevel_control_before?.[0] !== '') ? cond.waterlevel_control_before[0] : '-'}<br>
                                    <i class="bi bi-stop-circle"></i> ${(cond.waterlevel_control_before?.[1] !== undefined && cond.waterlevel_control_before?.[1] !== '') ? cond.waterlevel_control_before[1] : '-'}
                                `
                            : '-'
                        }
                        </td>
                        <td>
                            ${(cond.waterlevel_control_after?.[0] !== undefined && cond.waterlevel_control_after?.[0] !== '') ||
                            (cond.waterlevel_control_after?.[1] !== undefined && cond.waterlevel_control_after?.[1] !== '')
                            ? `
                                    <i class="bi bi-power"></i> ${(cond.waterlevel_control_after?.[0] !== undefined && cond.waterlevel_control_after?.[0] !== '') ? cond.waterlevel_control_after[0] : '-'}<br>
                                    <i class="bi bi-stop-circle"></i> ${(cond.waterlevel_control_after?.[1] !== undefined && cond.waterlevel_control_after?.[1] !== '') ? cond.waterlevel_control_after[1] : '-'}
                                `
                            : '-'
                        }
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="fdStep4.editCondition(${idx})">
                                <i class="bi bi-pencil"></i> 編輯
                            </button>
                            <button class="btn btn-sm btn-danger ms-1" onclick="fdStep4.deleteCondition(${orderedIdxMap[idx]})">
                                <i class="bi bi-trash"></i> 刪除
                            </button>
                        </td>
                    </tr>
                    `;
                }
            });
        }

        html += `</tbody></table></div>`;
        container.innerHTML = html;
    }

    editCondition(idx) {
        this.editingIdx = idx;
        this.renderTable();
    }

    async saveCondition(idx) {
        // 不做格式驗證
        sessionStorage.setItem('step4_conditions', JSON.stringify(this.conditions));
        this.editingIdx = null;
        this.renderTable();
        fdUtils.showMessage('success', '條件已儲存');
        await this.saveToBackend();
    }

    cancelEdit() {
        this.editingIdx = null;
        this.renderTable();
    }

    // 新增條件
    async addCondition() {
        const oldModal = document.getElementById('fd4-modal');
        if (oldModal && oldModal.parentNode) oldModal.parentNode.removeChild(oldModal);
        const oldMask = document.getElementById('fd4-modal-mask');
        if (oldMask && oldMask.parentNode) oldMask.parentNode.removeChild(oldMask);
        this.loadFacilities();
        // console.log('addCondition 讀到的設施資料:', this.facilities);
        // 1. 動態產生設施選單
        if (!this.facilities || this.facilities.length === 0) {
            fdUtils.showMessage('error', '請先完成步驟3的設施資料上傳');
            return;
        }

        // 取得步驟2入流流量曲線的起訖時間
        let startTime = '';
        let endTime = '';
        try {
            const inflowData = sessionStorage.getItem('step2_originalData');
            if (inflowData) {
                const arr = JSON.parse(inflowData);
                if (Array.isArray(arr) && arr.length > 0) {
                    // 假設每筆有 Time 欄位
                    startTime = arr[0].Time !== undefined ? arr[0].Time : '';
                    endTime = arr[arr.length - 1].Time !== undefined ? arr[arr.length - 1].Time : '';
                }
            }
        } catch (e) {
            startTime = '';
            endTime = '';
        }

        // 建立選單HTML
        let facilityOptions = this.facilities.map((f, idx) =>
            `<option value="${idx}">${f.name}</option>`
        ).join('');
        let modalHtml = `
            <div id="fd4-modal-mask" style="position:fixed;z-index:9999;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.2);"></div>
            <div id="fd4-modal" style="position:fixed;z-index:10000;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;padding:24px 32px;border-radius:8px;box-shadow:0 2px 12px #0002;">
                <div class="mb-2"><b>選擇設施與開度</b></div>
                <div class="mb-2">
                    <label>設施：</label>
                    <select id="fd4-facility-select" class="form-select form-select-sm" style="width:180px;display:inline-block;">
                        ${facilityOptions}
                    </select>
                </div>
                <div class="mb-2">
                    <label>開度：</label>
                    <select id="fd4-opening-select" class="form-select form-select-sm" style="width:180px;display:inline-block;">
                    </select>
                </div>
                <div class="text-end mt-3">
                    <button id="fd4-modal-ok" type="button" class="btn btn-primary btn-sm me-2">確定</button>
                    <button id="fd4-modal-cancel" type="button" class="btn btn-secondary btn-sm">取消</button>
                </div>
            </div>
        `;
        // 插入到 body
        let modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);

        // 動態更新開度選單
        const updateOpeningOptions = () => {
            const facilityIdx = Number(document.getElementById('fd4-facility-select').value);
            // console.log('選擇設施idx:', facilityIdx, '設施物件:', this.facilities[facilityIdx]);
            const openings = this.facilities[facilityIdx]?.openings || [];
            // console.log('該設施的 openings:', openings);
            let openingOptions = openings.map((o, i) =>
                `<option value="${o.opening}">${o.opening}</option>`
            ).join('');
            document.getElementById('fd4-opening-select').innerHTML = openingOptions;
        };
        document.getElementById('fd4-facility-select').addEventListener('change', updateOpeningOptions);
        updateOpeningOptions();

        // 綁定確定/取消
        document.getElementById('fd4-modal-ok').onclick = async () => {
            const facilityIdx = document.getElementById('fd4-facility-select').value;
            const openingValue = document.getElementById('fd4-opening-select').value;
            const facilityName = this.facilities[facilityIdx].name;

            // 檢查是否重複
            const isDuplicate = this.conditions.some(
                c => c.facility === facilityName && c.opening === openingValue
            );
            if (isDuplicate) {
                fdUtils.showMessage('error', '已存在相同設施與開度的條件，請勿重複新增');
                return;
            }

            // 新增條件，預設時間帶入
            this.conditions.push({
                facility: facilityName,
                opening: openingValue,
                time_control: [String(startTime), String(endTime)],
                flow_control_before: ['', ''],
                flow_control_after: ['', ''],
                waterlevel_control_before: ['', ''],
                waterlevel_control_after: ['', '']
            });
            fdUtils.showMessage('success', '條件新增成功');
            document.body.removeChild(modalDiv);
            sessionStorage.setItem('step4_conditions', JSON.stringify(this.conditions));
            this.renderTable();
            await this.saveToBackend();
            if (startTime === '' || endTime === '') {
                fdUtils.showMessage('info', '無法取得入流曲線時間，請手動設定起訖條件');
            } else {
                fdUtils.showMessage('info', '已根據入流曲線設定預設起訖條件');
            }
        };
        document.getElementById('fd4-modal-cancel').onclick = () => {
            document.body.removeChild(modalDiv);
        };
    }

    // 刪除條件
    async deleteCondition(idx) {
        this.conditions.splice(idx, 1);
        sessionStorage.setItem('step4_conditions', JSON.stringify(this.conditions));
        this.renderTable();
        await this.saveToBackend();
        fdUtils.showMessage('success', '條件已刪除');
    }

    handleInputChange(event) {
        const idx = event.target.getAttribute('data-idx');
        const type = event.target.getAttribute('data-type');
        const pos = event.target.getAttribute('data-pos');
        let value = event.target.value.trim();

        // 格式驗證
        if (type === 'time_control') {
            if (value && !/^\d+(\.\d{1,2})?$/.test(value)) {
                fdUtils.showMessage('error', '時間請輸入數字，最多小數2位');
                event.target.value = '';
                return;
            }
        } else if (type.startsWith('flow_control')) {
            if (value && !/^\d+(\.\d{1,3})?$/.test(value)) {
                fdUtils.showMessage('error', '流量請輸入數字，最多小數3位');
                event.target.value = '';
                return;
            }
        } else if (type.startsWith('waterlevel_control')) {
            if (value && !/^\d+(\.\d{1,2})?$/.test(value)) {
                fdUtils.showMessage('error', '水位請輸入數字，最多小數2位');
                event.target.value = '';
                return;
            }
        }

        // 更新資料
        this.conditions[idx][type][pos] = value;
    }

    validateCondition(cond) {
        // 五種控制條件
        const fields = [
            { key: 'time_control', name: '時間控制', decimals: 2 },
            { key: 'flow_control_before', name: '洪峰前流量控制', decimals: 3 },
            { key: 'flow_control_after', name: '洪峰後流量控制', decimals: 3 },
            { key: 'waterlevel_control_before', name: '洪峰前水位控制', decimals: 2 },
            { key: 'waterlevel_control_after', name: '洪峰後水位控制', decimals: 2 }
        ];

        // 至少一種有設開啟條件
        let hasOpen = false;
        // 至少一種有設關閉條件
        let hasClose = false;

        for (const field of fields) {
            const arr = cond[field.key] || [];
            // 開啟條件
            const openVal = (arr[0] ?? '').toString().trim();
            if (openVal !== '') hasOpen = true;
            // 關閉條件
            const closeVal = (arr[1] ?? '').toString().trim();
            if (closeVal !== '') hasClose = true;

            // 格式檢查
            for (let i = 0; i < 2; i++) {
                const valStr = (arr[i] ?? '').toString().trim();
                if (valStr !== '') {
                    let regex;
                    if (field.decimals === 2) regex = /^\d+(\.\d{1,2})?$/;
                    else if (field.decimals === 3) regex = /^\d+(\.\d{1,3})?$/;
                    if (!regex.test(valStr)) {
                        return `${field.name}（${i === 0 ? '開啟' : '關閉'}）格式錯誤，請輸入數字，最多小數${field.decimals}位`;
                    }
                }
            }
        }

        if (!hasOpen) return '至少需設定一種開啟條件';
        if (!hasClose) return '至少需設定一種關閉條件';
        return null; // 通過驗證
    }

    // 匯出存檔（下載 Excel）
    async exportConditions() {
        if (!this.conditions || this.conditions.length === 0) {
            fdUtils.showMessage('error', '沒有條件資料可匯出');
            return;
        }
        try {
            fdUtils.showLoading(4, 'save');
            // 呼叫 API 儲存並下載 Excel
            const fileBlob = await fdAPI.save(4, 'download', this.conditions);
            if (!fileBlob || !(fileBlob instanceof Blob)) {
                throw new Error('後端返回的不是有效的檔案格式');
            }
            // 產生檔名
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `步驟4_排洪規則設定_${timestamp}.xlsx`;
            fdAPI.handleFileDownload(fileBlob, filename);
            fdUtils.showMessage('success', '排洪規則設定下載成功！');
        } catch (error) {
            console.error('步驟4匯出失敗:', error);
            fdUtils.showMessage('error', '排洪規則設定下載失敗: ' + error.message);
        } finally {
            fdUtils.hideLoading(4, 'save');
        }
    }

    async saveToBackend() {
        try {
            await fdAPI.save(4, 'original', this.conditions);
        } catch (e) {
            fdUtils.showMessage('error', '同步到後端失敗: ' + (e.message || e));
        }
    }

    clearAllSessionData() {
        sessionStorage.removeItem('step4_conditions');
    }

    clearStepData() {
        this.conditions = [];
        this.renderTable();
    }
}

// 全域實例
window.fdStep4 = new Step4Manager();