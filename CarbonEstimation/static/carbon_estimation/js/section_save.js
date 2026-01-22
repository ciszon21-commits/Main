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
            showToast('✅ 分類數據已儲存', 'success');

            // 重置髒值狀態
            if (window.sectionCalculator) {
                window.sectionCalculator.resetDirtyState(categoryId);
            }
        } else {
            showToast('❌ 儲存失敗: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('儲存錯誤:', error);
        showToast('❌ 儲存時發生錯誤', 'error');
    }
}

/**
 * 儲存所有分類的數據
 */
async function saveAllCategories(scenarioId) {
    const categoryIds = [...new Set(
        Array.from(document.querySelectorAll('tr.data-row'))
            .map(row => row.dataset.categoryId)
    )];

    let successCount = 0;
    let failCount = 0;

    for (const categoryId of categoryIds) {
        try {
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

            if (data.length === 0) continue; // 跳過沒有數據的分類

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

    if (failCount === 0) {
        showToast(`✅ 所有數據已成功儲存（${successCount} 個分類）`, 'success');

        // 全部儲存成功，重置所有狀態
        if (window.sectionCalculator) {
            window.sectionCalculator.resetAllDirtyStates();
        }
    } else {
        showToast(`⚠️ 部分儲存失敗（成功: ${successCount}, 失敗: ${failCount}）`, 'warning');
    }
}

/**
 * 顯示提示訊息
 */
function showToast(message, type = 'info') {
    // 簡單的 alert 提示，可以之後改為更美觀的 Toast 元件
    alert(message);
}
