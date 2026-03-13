// ==================== RPG 特效與互動 ====================
// 現場監造工程師職涯冒險培訓系統

// ==================== 全域變數 ====================
let currentTrial = null;
let trialTimer = null;
let trialStartTime = null;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function () {
    initializeAnimations();
    initializeSkillTree();
    initializeEquipment();
    initializeTrial();
    initializeManagerSeal();
});

// ==================== 動畫效果 ====================
function initializeAnimations() {
    // 卡片進入動畫
    const cards = document.querySelectorAll('.rpg-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // 按鈕點擊音效（可選）
    const buttons = document.querySelectorAll('.rpg-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function (e) {
            createRipple(e, this);
        });
    });
}

// 漣漪效果
function createRipple(event, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');

    element.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
}

// 升級動畫
function playLevelUpAnimation() {
    const overlay = document.createElement('div');
    overlay.className = 'level-up-overlay';
    overlay.innerHTML = `
        <div class="level-up-content">
            <h1>🎉 LEVEL UP! 🎉</h1>
            <p>恭喜升級！</p>
        </div>
    `;
    document.body.appendChild(overlay);

    setTimeout(() => {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 500);
    }, 3000);
}

// ==================== 技能樹系統 ====================
function initializeSkillTree() {
    const skillNodes = document.querySelectorAll('.skill-node');

    skillNodes.forEach(node => {
        node.addEventListener('click', function () {
            if (!this.classList.contains('locked')) {
                showSkillDetail(this);
            }
        });

        // Hover 效果
        node.addEventListener('mouseenter', function () {
            if (!this.classList.contains('locked')) {
                showSkillTooltip(this);
            }
        });

        node.addEventListener('mouseleave', function () {
            hideSkillTooltip();
        });
    });

    // 繪製技能樹連線
    drawSkillTreeConnections();
}

function showSkillDetail(node) {
    const skillId = node.dataset.skillId;
    // 可以使用 AJAX 載入詳細資訊，或導向詳細頁面
    window.location.href = `/rpg/skill/${skillId}/`;
}

function showSkillTooltip(node) {
    const tooltip = document.createElement('div');
    tooltip.className = 'skill-tooltip';
    tooltip.innerHTML = `
        <h4>${node.dataset.skillName}</h4>
        <p>${node.dataset.skillDesc}</p>
    `;

    const rect = node.getBoundingClientRect();
    tooltip.style.position = 'fixed';
    tooltip.style.left = rect.right + 10 + 'px';
    tooltip.style.top = rect.top + 'px';

    document.body.appendChild(tooltip);
}

function hideSkillTooltip() {
    const tooltip = document.querySelector('.skill-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function drawSkillTreeConnections() {
    const canvas = document.getElementById('skill-tree-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;

    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;

    const nodes = document.querySelectorAll('.skill-node');

    nodes.forEach(node => {
        const parents = node.dataset.parents ? node.dataset.parents.split(',') : [];

        parents.forEach(parentId => {
            const parentNode = document.querySelector(`[data-skill-id="${parentId}"]`);
            if (parentNode) {
                drawConnection(ctx, parentNode, node);
            }
        });
    });
}

function drawConnection(ctx, fromNode, toNode) {
    const fromRect = fromNode.getBoundingClientRect();
    const toRect = toNode.getBoundingClientRect();
    const containerRect = ctx.canvas.getBoundingClientRect();

    const fromX = fromRect.left + fromRect.width / 2 - containerRect.left;
    const fromY = fromRect.top + fromRect.height / 2 - containerRect.top;
    const toX = toRect.left + toRect.width / 2 - containerRect.left;
    const toY = toRect.top + toRect.height / 2 - containerRect.top;

    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.strokeStyle = '#D4AF37';
    ctx.lineWidth = 2;
    ctx.stroke();
}

// ==================== 裝備系統 ====================
function initializeEquipment() {
    // 註解：拖放功能已在 equipment.html 中實作，這裡不再需要
    /*
    const equipmentItems = document.querySelectorAll('.equipment-item');
    const equipmentSlots = document.querySelectorAll('.equipment-slot');
    
    // 拖放功能
    equipmentItems.forEach(item => {
        item.draggable = true;
        
        item.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('equipment-id', this.dataset.equipmentId);
            this.style.opacity = '0.5';
        });
        
        item.addEventListener('dragend', function() {
            this.style.opacity = '1';
        });
    });
    
    equipmentSlots.forEach(slot => {
        slot.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = '#D4AF37';
        });
        
        slot.addEventListener('dragleave', function() {
            this.style.borderColor = '';
        });
        
        slot.addEventListener('drop', function(e) {
            e.preventDefault();
            const equipmentId = e.dataTransfer.getData('equipment-id');
            equipItem(equipmentId, this.dataset.slotType);
            this.style.borderColor = '';
        });
    });
    */
}

function equipItem(equipmentId, toolSlotIndex = null) {
    console.log('📦 rpg-effects.js equipItem 被呼叫:', { equipmentId, toolSlotIndex });

    // 發送 AJAX 請求裝備物品
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
    if (toolSlotIndex) {
        formData.append('tool_slot_index', toolSlotIndex);
    }

    fetch(`/rpg/equipment/${equipmentId}/equip/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('裝備成功！', 'success');
                location.reload();
            } else {
                showNotification(data.message || '裝備失敗！', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('發生錯誤！', 'error');
        });
}

// 強化裝備
function enhanceEquipment(userEquipmentId) {
    if (!confirm('確定要強化此裝備嗎？將消耗 1 個強化卷軸。')) {
        return;
    }

    fetch(`/rpg/equipment/${userEquipmentId}/enhance/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                playEnhanceAnimation(data.enhancement_level);
                setTimeout(() => location.reload(), 2000);
            } else {
                showNotification(data.message || '強化失敗！', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function playEnhanceAnimation(level) {
    const overlay = document.createElement('div');
    overlay.className = 'enhance-overlay';
    overlay.innerHTML = `
        <div class="enhance-content">
            <h1>✨ 強化成功！ ✨</h1>
            <p>+${level}</p>
        </div>
    `;
    document.body.appendChild(overlay);

    setTimeout(() => {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 500);
    }, 2000);
}

// ==================== 試煉系統 ====================
function initializeTrial() {
    const trialForm = document.getElementById('trial-form');
    if (!trialForm) return;

    const timeLimit = parseInt(trialForm.dataset.timeLimit) * 60; // 轉換為秒
    startTrialTimer(timeLimit);

    // 選項選擇
    const options = document.querySelectorAll('.trial-option');
    options.forEach(option => {
        option.addEventListener('click', function () {
            const questionId = this.dataset.questionId;
            const questionType = this.dataset.questionType;

            if (questionType === 'MULTIPLE') {
                // 多選題
                this.classList.toggle('selected');
            } else {
                // 單選題或是非題
                document.querySelectorAll(`[data-question-id="${questionId}"]`).forEach(opt => {
                    opt.classList.remove('selected');
                });
                this.classList.add('selected');
            }
        });
    });

    // 提交試煉
    trialForm.addEventListener('submit', function (e) {
        if (!confirm('確定要提交答案嗎？')) {
            e.preventDefault();
        } else {
            clearInterval(trialTimer);
        }
    });
}

function startTrialTimer(timeLimit) {
    trialStartTime = Date.now();
    const timerDisplay = document.getElementById('trial-timer');
    if (!timerDisplay) return;

    trialTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - trialStartTime) / 1000);
        const remaining = timeLimit - elapsed;

        if (remaining <= 0) {
            clearInterval(trialTimer);
            document.getElementById('trial-form').submit();
            return;
        }

        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        // 最後 1 分鐘警告
        if (remaining <= 60) {
            timerDisplay.classList.add('warning');
        }
    }, 1000);
}

// 裝備技能使用
function useEquipmentSkill(skillType) {
    const currentQuestion = document.querySelector('.trial-question.active');
    if (!currentQuestion) return;

    switch (skillType) {
        case 'UAV':
            // 上帝視角：刪去一個錯誤選項
            eliminateWrongOption(currentQuestion);
            break;
        case 'GLASSES':
            // 透視眼：顯示提示
            showHint(currentQuestion);
            break;
        case 'APP':
            // 快速檢索：標示關鍵字
            highlightKeywords(currentQuestion);
            break;
    }
}

function eliminateWrongOption(question) {
    const options = question.querySelectorAll('.trial-option:not(.selected)');
    const wrongOptions = Array.from(options).filter(opt => !opt.dataset.isCorrect);

    if (wrongOptions.length > 0) {
        const randomWrong = wrongOptions[Math.floor(Math.random() * wrongOptions.length)];
        randomWrong.style.opacity = '0.3';
        randomWrong.style.pointerEvents = 'none';
        showNotification('已刪除一個錯誤選項！', 'success');
    }
}

function showHint(question) {
    const hint = question.dataset.hint;
    if (hint) {
        showNotification(`提示：${hint}`, 'info');
    }
}

function highlightKeywords(question) {
    const keywords = question.dataset.keywords ? question.dataset.keywords.split(',') : [];
    const content = question.querySelector('.question-content');

    keywords.forEach(keyword => {
        const regex = new RegExp(keyword, 'gi');
        content.innerHTML = content.innerHTML.replace(regex, `<mark>${keyword}</mark>`);
    });
}

// ==================== 主管審核系統 ====================
function initializeManagerSeal() {
    const seal = document.querySelector('.manager-seal');
    const approvalArea = document.querySelector('.approval-area');

    if (!seal || !approvalArea) return;

    seal.draggable = true;

    seal.addEventListener('dragstart', function (e) {
        e.dataTransfer.setData('text/plain', 'seal');
    });

    approvalArea.addEventListener('dragover', function (e) {
        e.preventDefault();
    });

    approvalArea.addEventListener('drop', function (e) {
        e.preventDefault();
        stampApproval(e);
    });
}

function stampApproval(event) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const stamp = document.createElement('div');
    stamp.className = 'approval-stamp stamped';
    stamp.style.position = 'absolute';
    stamp.style.left = x - 75 + 'px';
    stamp.style.top = y - 75 + 'px';
    stamp.innerHTML = '准';

    event.currentTarget.appendChild(stamp);

    // 播放蓋章音效（可選）
    playSoundEffect('stamp');

    // 啟用提交按鈕
    setTimeout(() => {
        document.getElementById('approve-btn').disabled = false;
    }, 500);
}

// ==================== 通知系統 ====================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `rpg-notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== 工具函式 ====================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function playSoundEffect(effectName) {
    // 可以加入音效播放
    // const audio = new Audio(`/static/EngineerRPG/sounds/${effectName}.mp3`);
    // audio.play();
}

// ==================== HP/MP 條動畫 ====================
function updateStatBar(barId, currentValue, maxValue) {
    const bar = document.getElementById(barId);
    if (!bar) return;

    const percentage = (currentValue / maxValue) * 100;
    const fill = bar.querySelector('.rpg-stat-bar-fill');
    const text = bar.querySelector('.rpg-stat-bar-text');

    fill.style.width = percentage + '%';
    text.textContent = `${currentValue} / ${maxValue}`;
}

// ==================== 排行榜動畫 ====================
function animateLeaderboard() {
    const rows = document.querySelectorAll('.leaderboard-table tbody tr');
    rows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, index * 50);
    });
}

// ==================== 成就解鎖動畫 ====================
function unlockAchievement(achievementName, achievementIcon) {
    const overlay = document.createElement('div');
    overlay.className = 'achievement-overlay';
    overlay.innerHTML = `
        <div class="achievement-content">
            <div class="achievement-icon">${achievementIcon}</div>
            <h2>成就解鎖！</h2>
            <h3>${achievementName}</h3>
        </div>
    `;
    document.body.appendChild(overlay);

    setTimeout(() => {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 500);
    }, 4000);
}

// ==================== 載入動畫 ====================
function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'rpg-loader';
    loader.innerHTML = `
        <div class="loader-spinner"></div>
        <p>載入中...</p>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.querySelector('.rpg-loader');
    if (loader) {
        loader.remove();
    }
}

// ==================== 匯出函式供外部使用 ====================
window.RPG = {
    playLevelUpAnimation,
    enhanceEquipment,
    useEquipmentSkill,
    showNotification,
    updateStatBar,
    unlockAchievement,
    showLoading,
    hideLoading
};
