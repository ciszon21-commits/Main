// Scenario Save/Load JavaScript
// Handles saving and loading scenarios with AJAX

class ScenarioManager {
    constructor() {
        this.currentScenarioId = null;
        this.init();
    }

    init() {
        // Check for scenario ID in URL
        const urlParams = new URLSearchParams(window.location.search);
        const scenarioId = urlParams.get('scenario');
        if (scenarioId) {
            this.currentScenarioId = scenarioId;
            this.loadScenarioData(scenarioId);
        }

        // Add event listeners to category save buttons
        document.querySelectorAll('.category-save-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const categoryId = btn.dataset.categoryId;
                this.saveCategory(categoryId);
            });
        });

        // Add Save All listener
        const saveAllBtn = document.getElementById('save-all-btn');
        if (saveAllBtn) {
            saveAllBtn.addEventListener('click', () => {
                this.saveAllCategories();
            });
        }
    }

    setButtonLoading(btn, isLoading, originalText = null) {
        if (!btn) return;

        if (isLoading) {
            if (originalText) btn.dataset.originalText = originalText;
            btn.classList.add('btn-loading');
            // Text is hidden by CSS color: transparent, spinner shown by ::after
        } else {
            btn.classList.remove('btn-loading');
            // If text was changed (though we just hid it), we could restore it if we modified it. 
            // In this approach we just toggle class.
        }
    }

    async loadScenarioData(scenarioId) {
        try {
            const response = await fetch(`/carbon/api/scenarios/${scenarioId}/load/`);
            if (response.ok) {
                const result = await response.json();
                this.populateData(result.data);
                this.updatePageTitle(result.scenario);
                console.log('Scenario loaded:', result.scenario.scenario_name);

                // Set loaded data as initial state (clean state)
                if (window.carbonCalculator) {
                    window.carbonCalculator.resetAllDirtyStates();
                }
            } else {
                console.error('Failed to load scenario data');
            }
        } catch (error) {
            console.error('Error loading scenario:', error);
        }
    }

    populateData(data) {
        // Iterate through data and fill inputs
        for (const [itemId, quantity] of Object.entries(data)) {
            const input = document.querySelector(`.quantity-input[data-item-id="${itemId}"]`);
            if (input) {
                input.value = quantity;
                // Trigger input event to update calculations
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    }

    updatePageTitle(scenarioInfo) {
        // Keep the original page title, show scenario info in subtitle
        const subtitleEl = document.querySelector('.subtitle');
        if (subtitleEl) {
            subtitleEl.textContent = `${scenarioInfo.project_name} - ${scenarioInfo.scenario_name}`;
        }
    }

    async saveCategory(categoryId) {
        const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);
        const data = [];

        categoryRows.forEach(row => {
            const input = row.querySelector('.quantity-input');
            if (input) {
                const itemId = input.dataset.itemId;
                const quantity = parseFloat(input.value) || 0;

                if (quantity > 0) {  // Only save non-zero quantities
                    data.push({
                        component_item_id: itemId,
                        quantity: quantity
                    });
                }
            }
        });

        if (data.length === 0) {
            alert('此分類沒有填寫數量的項目');
            return;
        }

        const btn = document.querySelector(`.category-save-btn[data-category-id="${categoryId}"]`);

        // If no scenario is loaded, prompt to create one
        if (!this.currentScenarioId) {
            // promptCreateScenario handles its own button state if we pass it, 
            // but here we might want to start loading on the category button
            this.setButtonLoading(btn, true);
            // We need to pass btn to promptCreateScenario so it can turn it off on cancel/error
            this.promptCreateScenario(categoryId, data, btn);
        } else {
            this.setButtonLoading(btn, true);
            this.saveCategoryData(categoryId, data).then(() => {
                this.setButtonLoading(btn, false);
            });
        }
    }

    promptCreateScenario(categoryId, data, btn = null) {
        const projectNumber = prompt('請輸入計畫編號：');
        if (!projectNumber) {
            this.setButtonLoading(btn, false);
            return;
        }

        const projectName = prompt('請輸入計畫名稱：');
        if (!projectName) {
            this.setButtonLoading(btn, false);
            return;
        }

        const scenarioName = prompt('請輸入方案名稱：');
        if (!scenarioName) {
            this.setButtonLoading(btn, false);
            return;
        }

        // Create scenario and save data
        this.createScenario(projectNumber, projectName, scenarioName, categoryId, data, btn);
    }

    async createScenario(projectNumber, projectName, scenarioName, categoryId, data, btn = null) {
        try {
            const response = await fetch('/carbon/api/scenarios/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    project_number: projectNumber,
                    project_name: projectName,
                    scenario_name: scenarioName,
                    category_id: categoryId,
                    data: data
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.currentScenarioId = result.scenario_id;
                alert(`方案 "${scenarioName}" 已成功建立並儲存！`);
                this.updateScenarioInfo(result);
                // Reset dirty state
                if (window.carbonCalculator) {
                    window.carbonCalculator.resetDirtyState(categoryId);
                }
            } else {
                alert('儲存失敗，請稍後再試');
            }
        } catch (error) {
            console.error('Save error:', error);
            alert('儲存時發生錯誤');
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    async saveCategoryData(categoryId, data) {
        try {
            const response = await fetch(`/carbon/api/scenarios/${this.currentScenarioId}/save-category/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    category_id: categoryId,
                    data: data
                })
            });

            if (response.ok) {
                alert('分類資料已儲存！');
                // Reset dirty state
                if (window.carbonCalculator) {
                    window.carbonCalculator.resetDirtyState(categoryId);
                }
            } else {
                alert('儲存失敗');
            }
        } catch (error) {
            console.error('Save error:', error);
            alert('儲存時發生錯誤');
        }
    }

    updateScenarioInfo(info) {
        // Update UI to show current scenario
        console.log('Scenario info:', info);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    async saveAllCategories() {
        if (!window.carbonCalculator || window.carbonCalculator.unsavedCategories.size === 0) {
            alert('目前沒有未儲存的變更');
            return;
        }

        const unsavedIds = Array.from(window.carbonCalculator.unsavedCategories);

        // Prepare all data
        const payloads = [];
        for (const catId of unsavedIds) {
            const data = this.collectCategoryData(catId);
            if (data.length > 0) {
                payloads.push({ categoryId: catId, data: data });
            }
        }

        if (payloads.length === 0) {
            alert('沒有可儲存的數據');
            return;
        }

        // If no scenario exists, create one with the first payload
        let startIndex = 0;
        if (!this.currentScenarioId) {
            const firstPayload = payloads[0];
            const projectNumber = prompt('請輸入計畫編號：');
            if (!projectNumber) return;
            const projectName = prompt('請輸入計畫名稱：');
            if (!projectName) return;
            const scenarioName = prompt('請輸入方案名稱：');
            if (!scenarioName) return;

            // Create scenario
            try {
                const response = await fetch('/carbon/api/scenarios/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        project_number: projectNumber,
                        project_name: projectName,
                        scenario_name: scenarioName,
                        category_id: firstPayload.categoryId,
                        data: firstPayload.data
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    this.currentScenarioId = result.scenario_id;
                    this.updateScenarioInfo(result);
                    window.carbonCalculator.resetDirtyState(firstPayload.categoryId);
                    startIndex = 1; // Skip the first one as it's saved
                } else {
                    alert('建立方案失敗，中止儲存');
                    return;
                }
            } catch (error) {
                console.error(error);
                alert('建立方案發生錯誤');
                return;
            }
        }

        // Save remaining categories
        let successCount = 0;
        for (let i = startIndex; i < payloads.length; i++) {
            const payload = payloads[i];
            try {
                const result = await this.saveCategoryDataSilent(payload.categoryId, payload.data);
                if (result) {
                    window.carbonCalculator.resetDirtyState(payload.categoryId);
                    successCount++;
                }
            } catch (error) {
                console.error(`Error saving category ${payload.categoryId}`, error);
            }
        }

        this.setButtonLoading(saveAllBtn, false);

        // Final feedback
        // If we created a scenario, count that as success too (1 + successCount)
        const totalSaved = (startIndex === 1 ? 1 : 0) + successCount;
        alert(`已成功儲存 ${totalSaved} 個分類的變更！`);
    }

    collectCategoryData(categoryId) {
        // Extracted helper to avoid duplication
        const categoryRows = document.querySelectorAll(`.data-row[data-category-id="${categoryId}"]`);
        const data = [];
        categoryRows.forEach(row => {
            const input = row.querySelector('.quantity-input');
            if (input) {
                const quantity = parseFloat(input.value) || 0;
                if (quantity > 0) {
                    data.push({ component_item_id: input.dataset.itemId, quantity: quantity });
                }
            }
        });
        return data;
    }

    async saveCategoryDataSilent(categoryId, data) {
        // Return true/false instead of alerting
        try {
            const response = await fetch(`/carbon/api/scenarios/${this.currentScenarioId}/save-category/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCSRFToken() },
                body: JSON.stringify({ category_id: categoryId, data: data })
            });
            return response.ok;
        } catch (e) {
            return false;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.scenarioManager = new ScenarioManager();
    console.log('Scenario Manager initialized');
});
