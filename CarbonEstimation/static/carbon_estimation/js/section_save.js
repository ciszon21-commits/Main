// ============================================================================
// 斷面數據儲存功能
// ============================================================================

document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const scenarioId = urlParams.get('scenario');

    if (!scenarioId) {
        console.warn('⚠️  未指定方案 ID，無法儲存數據');
        return;
    }

    // 全部儲存按鈕
    const saveAllBtn = document.getElementById('save-all-btn');
    if (saveAllBtn) {
        saveAllBtn.addEventListener('click', function () {
            saveAllCategories(scenarioId);
        });
    }

    // 分類儲存按鈕
    document.querySelectorAll('.category-save-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation(); // 避免觸發分類收合
            const categoryId = this.dataset.categoryId;
            saveCategoryData(scenarioId, categoryId);
        });
    });
});

/**
 * 儲存單一分類的數據
 */
async function saveCategoryData(scenarioId, categoryId) {
    const rows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
    const data = [];

    rows.forEach(row => {
        const input = row.querySelector('.quantity-input');
        const quantity = parseFloat(input.value) || 0;

        if (quantity > 0) {
            data.push({
                section_item_id: input.dataset.itemId,
                quantity: quantity
            });
        }
    });

    // 防呆：檢查是否有填寫數量的項目
    if (data.length === 0) {
        alert('此分類沒有填寫數量的項目');
        return;
    }

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch(`/carbon/api/scenarios/${scenarioId}/save-section/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                category_id: categoryId,
                data: data
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('分類資料已儲存！');

            // 重置髒值狀態
            if (window.sectionCalculator) {
                window.sectionCalculator.resetDirtyState(categoryId);
            }
        } else {
            alert('儲存失敗');
        }
    } catch (error) {
        console.error('儲存錯誤:', error);
        alert('儲存時發生錯誤');
    }
}

/**
 * 儲存所有分類的數據
 */
async function saveAllCategories(scenarioId) {
    // 防呆：檢查是否有未儲存的變更
    if (!window.sectionCalculator || window.sectionCalculator.unsavedCategories.size === 0) {
        alert('目前沒有未儲存的變更');
        return;
    }

    const unsavedIds = Array.from(window.sectionCalculator.unsavedCategories);

    // 準備所有需要儲存的數據
    const payloads = [];
    for (const categoryId of unsavedIds) {
        const rows = document.querySelectorAll(`tr.data-row[data-category-id="${categoryId}"]`);
        const data = [];

        rows.forEach(row => {
            const input = row.querySelector('.quantity-input');
            const quantity = parseFloat(input.value) || 0;

            if (quantity > 0) {
                data.push({
                    section_item_id: input.dataset.itemId,
                    quantity: quantity
                });
            }
        });

        if (data.length > 0) {
            payloads.push({ categoryId: categoryId, data: data });
        }
    }

    // 防呆：檢查是否有可儲存的數據
    if (payloads.length === 0) {
        alert('沒有可儲存的數據');
        return;
    }

    let successCount = 0;
    let failCount = 0;

    for (const payload of payloads) {
        try {
            const data = payload.data;
            const categoryId = payload.categoryId;

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const response = await fetch(`/carbon/api/scenarios/${scenarioId}/save-section/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    category_id: categoryId,
                    data: data
                })
            });

            const result = await response.json();

            if (result.success) {
                successCount++;

                // 重置該分類的髒值狀態
                if (window.sectionCalculator) {
                    window.sectionCalculator.resetDirtyState(categoryId);
                }
            } else {
                failCount++;
            }
        } catch (error) {
            console.error(`分類 ${categoryId} 儲存失敗:`, error);
            failCount++;
        }
    }

    // 最終反饋
    if (failCount === 0) {
        alert(`已成功儲存 ${successCount} 個分類的變更！`);

        // 全部儲存成功，重置所有狀態
        if (window.sectionCalculator) {
            window.sectionCalculator.resetAllDirtyStates();
        }
    } else {
        alert(`部分儲存失敗（成功: ${successCount}, 失敗: ${failCount}）`);
    }
}

/**
 * 顯示提示訊息
 */
function showToast(message, type = 'info') {
    // 簡單的 alert 提示，可以之後改為更美觀的 Toast 元件
    alert(message);
}
