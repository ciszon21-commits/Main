// RndRequest - 研發需求提案 JavaScript

document.addEventListener('DOMContentLoaded', function () {
    initVoting();
    initStatusControl();
    initCommentForm();
});

function initVoting() {
    const voteButtons = document.querySelectorAll('.vote-btn, .vote-btn-large');

    voteButtons.forEach(button => {
        button.addEventListener('click', handleVote);
    });
}

function initStatusControl() {
    const updateStatusBtn = document.getElementById('updateStatusBtn');
    if (updateStatusBtn) {
        updateStatusBtn.addEventListener('click', handleStatusUpdate);
    }
}

async function handleVote(event) {
    const button = event.currentTarget;
    const requestId = button.dataset.requestId;
    const voteType = button.dataset.voteType;

    if (!requestId || !voteType) return;

    try {
        const response = await fetch(`/rnd-request/${requestId}/vote/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `vote_type=${voteType}`
        });

        const data = await response.json();

        if (data.success) {
            // 更新 UI
            updateVoteUI(requestId, voteType, data);
            // 顯示提示訊息
            showToast(data.message);
        } else {
            showToast(data.error || '投票失敗', 'error');
        }
    } catch (error) {
        console.error('投票錯誤:', error);
        showToast('投票時發生錯誤，請稍後再試', 'error');
    }
}

function updateVoteUI(requestId, voteType, data) {
    // 更新卡片上的按鈕狀態
    const card = document.querySelector(`.request-card[data-request-id="${requestId}"]`);
    if (card) {
        const upvoteBtn = card.querySelector('.vote-btn.upvote');
        const downvoteBtn = card.querySelector('.vote-btn.downvote');
        const scoreElement = card.querySelector('.vote-score');

        // 更新投票按鈕狀態
        if (upvoteBtn) {
            upvoteBtn.classList.toggle('voted', voteType === '1');
        }
        if (downvoteBtn) {
            downvoteBtn.classList.toggle('voted', voteType === '-1');
        }

        // 更新分數
        if (scoreElement) {
            scoreElement.textContent = data.vote_score;
            scoreElement.classList.remove('positive', 'negative');
            if (data.vote_score > 0) scoreElement.classList.add('positive');
            else if (data.vote_score < 0) scoreElement.classList.add('negative');
        }
    }

    // 更新詳情頁的按鈕狀態
    const detailUpvote = document.querySelector('.detail-vote-section .vote-btn-large.upvote');
    const detailDownvote = document.querySelector('.detail-vote-section .vote-btn-large.downvote');
    const detailScore = document.querySelector('.vote-score-large .score-number');

    if (detailUpvote) {
        detailUpvote.classList.toggle('voted', voteType === '1');
    }
    if (detailDownvote) {
        detailDownvote.classList.toggle('voted', voteType === '-1');
    }
    if (detailScore) {
        detailScore.textContent = data.vote_score;
        const scoreContainer = detailScore.closest('.vote-score-large');
        if (scoreContainer) {
            scoreContainer.classList.remove('positive', 'negative');
            if (data.vote_score > 0) scoreContainer.classList.add('positive');
            else if (data.vote_score < 0) scoreContainer.classList.add('negative');
        }
    }

    // 更新投票統計
    const voteStats = document.querySelector('.vote-stats');
    if (voteStats) {
        voteStats.innerHTML = `
            <span class="stat-positive">${data.upvote_count} 贊成</span>
            <span class="stat-divider">|</span>
            <span class="stat-negative">${data.downvote_count} 反對</span>
        `;
    }

    // 更新投票通知
    const voteNotice = document.querySelector('.vote-notice');
    if (voteNotice) {
        voteNotice.textContent = `您已投過票（${voteType === '1' ? '贊成' : '反對'}），可點選另一方更改投票`;
    }
}

async function handleStatusUpdate() {
    const statusSelect = document.getElementById('statusSelect');
    const requestId = statusSelect.dataset.requestId;
    const newStatus = statusSelect.value;

    try {
        const response = await fetch(`/rnd-request/${requestId}/status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `status=${newStatus}`
        });

        const data = await response.json();

        if (data.success) {
            // 更新狀態 badge
            const statusBadge = document.getElementById('statusBadge');
            if (statusBadge) {
                statusBadge.textContent = data.status_display;
                statusBadge.className = `badge status-${data.status}`;
            }
            showToast('狀態已更新');
        } else {
            showToast(data.error || '更新失敗', 'error');
        }
    } catch (error) {
        console.error('狀態更新錯誤:', error);
        showToast('更新時發生錯誤，請稍後再試', 'error');
    }
}

function showToast(message, type = 'success') {
    // 移除現有的 toast
    const existingToast = document.querySelector('.toast-message');
    if (existingToast) {
        existingToast.remove();
    }

    // 建立 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    toast.textContent = message;

    // 添加樣式
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        padding: 12px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        background: ${type === 'success' ? '#22c55e' : '#ef4444'};
    `;

    document.body.appendChild(toast);

    // 3 秒後移除
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getCSRFToken() {
    // 從 cookie 中獲取 CSRF token
    const name = 'csrftoken';
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

// 添加動畫樣式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
`;
document.head.appendChild(style);

// Comment form initialization
function initCommentForm() {
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmit);
    }
}

async function handleCommentSubmit(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const requestId = form.dataset.requestId;
    const contentTextarea = document.getElementById('commentContent');
    const content = contentTextarea.value.trim();

    if (!content) {
        showToast('請輸入留言內容', 'error');
        return;
    }

    try {
        const response = await fetch(`/rnd-request/${requestId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `content=${encodeURIComponent(content)}`
        });

        const data = await response.json();

        if (data.success) {
            // 清空輸入框
            contentTextarea.value = '';

            // 新增留言到列表
            addCommentToList(data.comment);

            // 更新留言數量
            updateCommentCount(1);

            showToast(data.message);
        } else {
            showToast(data.error || '留言失敗', 'error');
        }
    } catch (error) {
        console.error('留言錯誤:', error);
        showToast('留言時發生錯誤，請稍後再試', 'error');
    }
}

function addCommentToList(comment) {
    const commentList = document.getElementById('commentList');
    if (!commentList) return;

    // 移除無留言提示
    const noComments = commentList.querySelector('.no-comments');
    if (noComments) {
        noComments.remove();
    }

    // 建立新留言元素
    const commentItem = document.createElement('div');
    commentItem.className = 'comment-item';
    commentItem.dataset.commentId = comment.id;
    commentItem.innerHTML = `
        <div class="comment-header">
            <span class="comment-author">
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                </svg>
                ${comment.user}
            </span>
            <span class="comment-time">${comment.created_at}</span>
        </div>
        <div class="comment-content">
            <p>${comment.content.replace(/\n/g, '</p><p>')}</p>
        </div>
    `;

    // 插入到列表最前面
    commentList.insertBefore(commentItem, commentList.firstChild);
}

function updateCommentCount(increment) {
    const sectionTitle = document.querySelector('.comment-section .section-title');
    if (sectionTitle) {
        const text = sectionTitle.textContent;
        const match = text.match(/\((\d+)\)/);
        if (match) {
            const currentCount = parseInt(match[1]);
            sectionTitle.innerHTML = sectionTitle.innerHTML.replace(
                /\(\d+\)/,
                `(${currentCount + increment})`
            );
        }
    }
}
