/**
 * 排洪演算平台 - API 通信管理模組
 */
class APIManager {
    constructor() {
        this.baseURL = '/reservoir-hydro/flood-drainage/api/';
        this.utils = window.fdUtils;
    }

    /**
     * 獲取 CSRF Token
     */
    getCsrfToken() {
        // 方法1：從 meta 標籤獲取
        let token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

        // 方法2：從隱藏表單欄位獲取
        if (!token) {
            token = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        }

        // 方法3：從 cookies 獲取
        if (!token) {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    token = value;
                    break;
                }
            }
        }

        // 除錯資訊
        if (!token) {
            console.warn('⚠️ 無法獲取 CSRF Token');
            // console.log('📋 Meta 標籤:', document.querySelector('meta[name="csrf-token"]'));
            // console.log('📋 表單欄位:', document.querySelector('input[name="csrfmiddlewaretoken"]'));
            // console.log('📋 Cookies:', document.cookie);
        } else {
            // console.log('✅ CSRF Token 獲取成功:', token.substring(0, 10) + '...');
        }

        return token || '';
    }

    /**
     * 通用 API 請求方法
     */
    async makeRequest(endpoint, data, options = {}) {
        try {
            const response = await fetch(this.baseURL + endpoint, {
                method: 'POST',
                body: data,
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 檢查內容類型
            const contentType = response.headers.get('content-type');

            if (options.responseType === 'blob') {
                return {
                    blob: await response.blob(),
                    headers: response.headers
                };
            }

            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('非 JSON 響應:', text);
                throw new Error('服務器返回了非 JSON 格式的響應');
            }

            return await response.json();
        } catch (error) {
            console.error('API 請求錯誤:', error);
            throw error;
        }
    }

    /**
     * 上傳檔案
     */
    async upload(step, file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('step', step.toString());

        // console.log('準備發送上傳請求:', {
        //     step,
        //     fileName: file.name,
        //     fileSize: file.size
        // });

        return this.makeRequest('upload/', formData);
    }

    /**
     * 儲存數據
     */
    async save(step, type = 'original', data = null) {
        // console.log(`API save 調用: step=${step}, type=${type}`);

        try {
            // 準備請求數據
            const requestData = {
                step: step.toString(),
                type: type
            };
            // 新增：如果有 data 參數，帶入
            if (data !== null) {
                requestData.data = data;
            }

            // console.log('發送保存請求，數據:', requestData);

            // 發送請求
            const response = await fetch(`${this.baseURL}save/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify(requestData)
            });

            const contentType = response.headers.get('content-type');
            // console.log('響應內容類型:', contentType);

            if (!response.ok) {
                let errorMessage;
                try {
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.message || `請求失敗 (${response.status})`;
                    } else {
                        errorMessage = `請求失敗 (${response.status})`;
                    }
                } catch (parseError) {
                    errorMessage = `請求失敗 (${response.status})`;
                }
                throw new Error(errorMessage);
            }

            // 依 content-type 決定回傳型態
            if (contentType && contentType.includes('application/json')) {
                // 只存檔時回傳 JSON
                const responseData = await response.json();
                if (!responseData.success) {
                    throw new Error(responseData.message || '保存失敗');
                }
                return responseData;
            } else {
                // 下載時回傳 blob
                const blob = await response.blob();
                if (blob.size === 0) {
                    throw new Error('下載的檔案為空');
                }
                return blob;
            }
        } catch (error) {
            console.error('保存失敗:', error);
            throw error;
        }
    }


    /**
     * 匯出圖表
     */
    async exportChart(step, facilityId = null) {
        try {
            // console.log(`開始匯出步驟 ${step} 圖表`, facilityId ? `，設施ID: ${facilityId}` : '');

            // 🔧 修復：構建包含設施ID的FormData
            const formData = new FormData();
            formData.append('step', step);

            // 🔧 添加：如果有設施ID，一併傳送
            if (facilityId !== null && facilityId !== undefined) {
                formData.append('facility_id', facilityId);
                // console.log('傳送設施ID:', facilityId);
            }

            // 🔧 修復：正確的 URL 路徑（添加 api/ 前綴）
            const response = await fetch('/reservoir-hydro/flood-drainage/api/export-chart/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`圖表匯出失敗: ${response.status} - ${errorText}`);
            }

            // 檢查響應類型
            const contentType = response.headers.get('content-type');

            if (contentType && contentType.includes('application/json')) {
                // 錯誤響應
                const errorData = await response.json();
                throw new Error(errorData.message || '圖表匯出失敗');
            } else if (contentType && contentType.includes('image/')) {
                // 成功響應 - 圖片檔案
                const imageBlob = await response.blob();
                // console.log(`步驟 ${step} 圖表匯出成功，大小: ${imageBlob.size} bytes`);
                return imageBlob;
            } else {
                throw new Error('未知的響應格式');
            }

        } catch (error) {
            console.error(`步驟 ${step} 圖表匯出失敗:`, error);
            throw error;
        }
    }

    /**
     * 時距調整
     */
    async adjustTimeStep(step, deltaT) {
        const formData = new FormData();
        formData.append('step', step.toString());
        formData.append('delta_t', deltaT.toString());

        return this.makeRequest('adjust-timestep/', formData);
    }

    /**
     * 處理檔案下載響應
     */
    handleFileDownload(blob, defaultFilename = 'download') {
        // console.log('處理檔案下載:', blob?.size || 'undefined', 'bytes');

        try {
            // 🔧 修復：檢查是否是包裝物件
            let actualBlob = blob;

            // 如果傳入的是包含 blob 屬性的物件，提取實際的 blob
            if (blob && typeof blob === 'object' && blob.blob && blob.blob instanceof Blob) {
                // console.log('⚠️ 檢測到包裝物件，提取實際 blob');
                actualBlob = blob.blob;
            }

            // 驗證 blob
            if (!actualBlob) {
                throw new Error('檔案內容為空');
            }

            if (!(actualBlob instanceof Blob)) {
                console.error('無效的 blob 物件:', actualBlob);
                throw new Error('檔案格式錯誤');
            }

            if (actualBlob.size === 0) {
                throw new Error('檔案大小為 0');
            }

            // 創建下載連結
            const url = URL.createObjectURL(actualBlob);
            const a = document.createElement('a');
            a.href = url;

            // 生成檔案名稱
            let filename = defaultFilename;
            if (!filename.includes('.')) {
                // 根據 blob 類型添加副檔名
                if (actualBlob.type.includes('image/png')) {
                    filename += '.png';
                } else if (actualBlob.type.includes('image/jpeg')) {
                    filename += '.jpg';
                } else if (actualBlob.type.includes('application/vnd.openxmlformats')) {
                    filename += '.xlsx';
                } else if (actualBlob.type.includes('text/csv')) {
                    filename += '.csv';
                }
            }

            a.download = filename;

            // 執行下載
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            // 清理 URL
            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 1000);

            // console.log('檔案下載完成:', filename);
            return filename;

        } catch (error) {
            console.error('檔案下載處理失敗:', error);
            throw new Error(`無法處理檔案下載: ${error.message}`);
        }
    }

    /**
     * 調整入流數據的時間間距
     * @param {number} step - 步驟編號 (通常是 2)
     * @param {number} deltaT - 目標時間間距 (小時)
     * @returns {Promise} 調整結果
     */
    async adjustInflow(step, deltaT) {
        // console.log(`API adjustInflow 調用: step=${step}, deltaT=${deltaT}`);

        try {
            // 驗證參數
            if (!step || !deltaT) {
                throw new Error('步驟和時間間距都是必需的參數');
            }

            if (deltaT <= 0) {
                throw new Error('時間間距必須大於 0');
            }

            // 準備請求數據
            const requestData = JSON.stringify({
                step: step.toString(),
                delta_t: parseFloat(deltaT)
            });

            // console.log('發送調整請求:', requestData);

            // 發送請求
            const response = await fetch(`${this.baseURL}adjust-inflow/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'Content-Type': 'application/json',
                },
                body: requestData
            });

            // console.log('調整API響應狀態:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('調整請求失敗:', errorText);
                throw new Error(`調整請求失敗 (${response.status}): ${errorText}`);
            }

            // 解析響應
            const result = await response.json();
            // console.log('調整API響應:', result);

            if (!result.success) {
                throw new Error(result.message || '調整失敗，原因未知');
            }

            return result;

        } catch (error) {
            console.error('調整入流數據失敗:', error);
            throw error;
        }
    }

    /**
     * 獲取調整數據的詳細資訊
     * @param {number} step - 步驟編號 (通常是 2)
     * @returns {Promise} 調整資訊
     */
    async getAdjustmentInfo(step) {
        // console.log(`API getAdjustmentInfo 調用: step=${step}`);

        try {
            // 構建 URL 參數
            const params = new URLSearchParams({
                step: step.toString()
            });

            // 發送請求
            const response = await fetch(`${this.baseURL}adjustment-info/?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'Content-Type': 'application/json',
                }
            });

            // console.log('調整資訊API響應狀態:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('調整資訊請求失敗:', errorText);
                throw new Error(`調整資訊請求失敗 (${response.status}): ${errorText}`);
            }

            // 解析響應
            const result = await response.json();
            // console.log('調整資訊API響應:', result);

            return result;

        } catch (error) {
            console.error('獲取調整資訊失敗:', error);
            throw error;
        }
    }

    /**
     * 下載調整後的數據
     * @param {number} step - 步驟編號
     * @param {string} type - 數據類型 ('original' 或 'adjusted')
     * @returns {Promise} 下載結果
     */
    async downloadAdjustedData(step, type = 'adjusted') {
        // console.log(`API downloadAdjustedData 調用: step=${step}, type=${type}`);

        try {
            // 使用現有的 save 方法，但指定類型
            return await this.save(step, type);

        } catch (error) {
            console.error('下載調整後數據失敗:', error);
            throw error;
        }
    }
}

// 創建全局實例
window.fdAPI = new APIManager();