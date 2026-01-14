/**
 * 排洪演算平台 - 步驟5：排洪演算結果圖表管理
 */
class Step5Manager {
    constructor() {
        this.step = 5;
        this.api = window.fdAPI;
        this.charts = window.fdCharts;
        this.utils = window.fdUtils;

        // 狀態
        this.chartData = null;

        // 檢查依賴
        if (!this.api) console.warn('fdAPI 未載入');
        if (!this.charts) console.warn('fdCharts 未載入');
        if (!this.utils) console.warn('fdUtils 未載入');
    }

    /**
     * 初始化步驟5
     */
    init() {
        // 可擴充：初始化狀態或UI
        this.chartData = null;
    }

    /**
     * 載入步驟數據（如有需要）
     */
    loadStepData() {
        // 可擴充：從 sessionStorage 或 API 載入資料
        this.chartData = null;
    }

    /**
     * 呼叫後端 API 取得資料並繪圖
     * @param {Object} params - 可選參數
     */
    async drawChart(params = {}) {
        try {
            this.utils.showLoading(this.step, 'draw');
            const payload = {
                q_start: params.q_start ?? 0,
                q_power: params.q_power ?? 0,
                q_end: params.q_end ?? 0
            };
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            // const response = await fetch('/reservoir-hydro/flood-drainage/api/run-flood-calculation-simple/', {
            const response = await fetch('/reservoir-hydro/flood-drainage/api/run-flood-calculation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                this.utils.showMessage('error', '後端回傳非 JSON，請檢查伺服器');
                console.error('❌ 非 JSON 響應，內容如下：', text);
                return;
            }
            const result = await response.json();
            if (!result.success) {
                this.utils.showMessage('error', result.message || '排洪演算失敗');
                if (result.trace) console.error(result.trace);
                return;
            }
            // 整理資料
            const data = result.data;
            this.chartData = {
                times: data.map(row => row['時間(hr)']),
                inflow: data.map(row => row['流量(cms)']),
                outflow: data.map(row => row['總出流量(cms)']),
                waterlevel: data.map(row => row['水庫水位(m)'])
            };
            const success = this.charts.createChart(this.step, this.chartData);
            if (success) {
                this.utils.showMessage('success', '排洪演算圖表繪製完成');
            } else {
                throw new Error('圖表繪製失敗');
            }
        } catch (err) {
            this.utils.showMessage('error', 'API 呼叫異常: ' + err.message);
            console.error('API 呼叫異常:', err);
        } finally {
            this.utils.hideLoading(this.step, 'draw');
        }
    }

    /**
     * 匯出圖表
     */
    async exportChart() {
        try {
            this.utils.showLoading(this.step, 'export');
            // 呼叫 APIManager 的 exportChart
            const imageBlob = await this.api.exportChart(this.step);
            // 產生檔名
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `最終輸出_排洪演算結果圖表_${timestamp}.png`;
            // 處理檔案下載
            this.api.handleFileDownload(imageBlob, filename);
            this.utils.showMessage('success', `圖表已下載！檔案: ${filename}`);
        } catch (err) {
            this.utils.showMessage('error', '圖表下載失敗: ' + err.message);
        } finally {
            this.utils.hideLoading(this.step, 'export');
        }
    }

    /**
     * 清除圖表
     */
    clearChart() {
        this.charts.destroyChart(this.step);
        this.chartData = null;
        this.utils.showMessage('info', '圖表已清除');
    }

    /**
     * 數據存檔
     */
    async saveData() {
        try {
            // 1. 檢查是否有演算結果
            if (!this.chartData || !Array.isArray(this.chartData.times) || this.chartData.times.length === 0) {
                this.utils.showMessage('error', '請先執行排洪演算並繪製圖表');
                return;
            }

            this.utils.showLoading(this.step, 'save');
            // 取得 CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            // 送出請求到後端
            const response = await fetch('/reservoir-hydro/flood-drainage/api/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ step: 5 })
            });

            // 2. 檢查回傳的 content-type
            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                // 嘗試解析錯誤訊息
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || '後端回應失敗');
                } else {
                    throw new Error('後端回應失敗');
                }
            }

            // 3. 檢查是否為 Excel 檔
            if (!contentType || !contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                // 可能是錯誤訊息的 JSON
                const text = await response.text();
                try {
                    const errorData = JSON.parse(text);
                    throw new Error(errorData.message || '下載失敗，後端未回傳 Excel 檔');
                } catch {
                    throw new Error('下載失敗，後端未回傳 Excel 檔');
                }
            }

            const blob = await response.blob();
            if (blob.size === 0) {
                throw new Error('下載的檔案為空');
            }

            // 產生檔名
            const now = new Date();
            const timestamp = now.getFullYear() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');
            const filename = `最終輸出_排洪演算結果_${timestamp}.xlsx`;

            // 用 handleFileDownload 統一下載
            this.api.handleFileDownload(blob, filename);
            this.utils.showMessage('success', `排洪演算結果下載成功！檔案: ${filename}`);
        } catch (err) {
            this.utils.showMessage('error', '排洪演算結果下載失敗: ' + err.message);
        } finally {
            this.utils.hideLoading(this.step, 'save');
        }
    }
}

// 掛載全域
window.fdStep5 = new Step5Manager();