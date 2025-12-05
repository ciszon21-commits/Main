// ========== Search and Filter Functionality ==========

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const filterTags = document.querySelectorAll('.filter-tag');
    const achievementCards = document.querySelectorAll('.achievement-card');
    const categorySections = document.querySelectorAll('.category-section');
    const totalCountEl = document.getElementById('totalCount');
    const noResultsEl = document.getElementById('noResults');
    const showMoreBtns = document.querySelectorAll('.show-more-btn');

    // Initialize: show first 10 cards per category, hide rest
    const INITIAL_VISIBLE = 10;

    function initializeCardVisibility() {
        categorySections.forEach(section => {
            const cards = section.querySelectorAll('.achievement-card');
            cards.forEach((card, index) => {
                if (index >= INITIAL_VISIBLE) {
                    card.style.display = 'none';
                    card.dataset.collapsed = 'true';
                }
            });
        });
    }

    initializeCardVisibility();
    updateResultsCount();

    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function () {
            filterAchievements();
        }, 200));
    }

    // Category filter functionality
    filterTags.forEach(tag => {
        tag.addEventListener('click', function () {
            // Toggle active state
            if (this.dataset.category === 'all') {
                filterTags.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            } else {
                // Remove 'all' active state
                const allTag = document.querySelector('.filter-tag[data-category="all"]');
                if (allTag) allTag.classList.remove('active');

                // Toggle this tag
                this.classList.toggle('active');

                // If no tags selected, select 'all'
                const activeTags = document.querySelectorAll('.filter-tag.active');
                if (activeTags.length === 0 && allTag) {
                    allTag.classList.add('active');
                }
            }
            filterAchievements();
        });
    });

    // Show more/less functionality
    showMoreBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const categoryId = this.dataset.category;
            const section = document.querySelector(`.category-section[data-category-id="${categoryId}"]`);
            const cards = section.querySelectorAll('.achievement-card[data-collapsed="true"]');
            const isExpanded = this.dataset.expanded === 'true';

            if (isExpanded) {
                // Collapse
                cards.forEach(card => {
                    card.style.display = 'none';
                });
                this.dataset.expanded = 'false';
                this.innerHTML = `顯示更多 <svg fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/></svg>`;
                this.classList.remove('expanded');
            } else {
                // Expand
                cards.forEach(card => {
                    card.style.display = '';
                });
                this.dataset.expanded = 'true';
                this.innerHTML = `收合 <svg fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.646 4.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1-.708.708L8 5.707l-5.646 5.647a.5.5 0 0 1-.708-.708l6-6z"/></svg>`;
                this.classList.add('expanded');
            }
        });
    });

    function filterAchievements() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const activeFilters = Array.from(document.querySelectorAll('.filter-tag.active'))
            .map(t => t.dataset.category);
        const showAll = activeFilters.includes('all') || activeFilters.length === 0;

        let visibleCount = 0;

        categorySections.forEach(section => {
            const categoryId = section.dataset.categoryId;
            const cards = section.querySelectorAll('.achievement-card');
            let categoryVisible = 0;

            cards.forEach(card => {
                const name = card.dataset.name.toLowerCase();
                const summary = card.dataset.summary.toLowerCase();
                const matchesSearch = searchTerm === '' ||
                    name.includes(searchTerm) ||
                    summary.includes(searchTerm);
                const matchesCategory = showAll || activeFilters.includes(categoryId);

                if (matchesSearch && matchesCategory) {
                    // Check if card was collapsed originally
                    if (card.dataset.collapsed === 'true') {
                        const btn = document.querySelector(`.show-more-btn[data-category="${categoryId}"]`);
                        if (btn && btn.dataset.expanded === 'true') {
                            card.style.display = '';
                        } else {
                            card.style.display = 'none';
                        }
                    } else {
                        card.style.display = '';
                    }
                    card.classList.remove('hidden');
                    categoryVisible++;
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                    card.classList.add('hidden');
                }
            });

            // Update category count
            const countEl = section.querySelector('.category-count');
            if (countEl) {
                countEl.textContent = categoryVisible;
            }

            // Hide section if no visible cards
            if (categoryVisible === 0) {
                section.classList.add('hidden');
            } else {
                section.classList.remove('hidden');
            }
        });

        // Update total count
        if (totalCountEl) {
            totalCountEl.textContent = visibleCount;
        }

        // Show/hide no results message
        if (noResultsEl) {
            noResultsEl.classList.toggle('visible', visibleCount === 0);
        }
    }

    function updateResultsCount() {
        const visibleCards = document.querySelectorAll('.achievement-card:not(.hidden)');
        if (totalCountEl) {
            totalCountEl.textContent = visibleCards.length;
        }
    }

    // Debounce helper
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Initial count
    const allCards = document.querySelectorAll('.achievement-card');
    if (totalCountEl) {
        totalCountEl.textContent = allCards.length;
    }
});

// ========== Comment Form (AJAX) ==========

document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.getElementById('commentForm');

    if (commentForm) {
        commentForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const formData = new FormData(commentForm);
            const submitButton = commentForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;

            // Disable button and show loading state
            submitButton.disabled = true;
            submitButton.textContent = '送出中...';

            try {
                const response = await fetch(`/showcase/achievement/${achievementId}/comment/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    // Clear form
                    commentForm.reset();

                    // Add new comment to list
                    const commentsList = document.getElementById('commentsList');
                    const noComments = commentsList.querySelector('.no-comments');

                    if (noComments) {
                        noComments.remove();
                    }

                    const newComment = document.createElement('div');
                    newComment.className = 'comment-item';
                    newComment.style.animation = 'fadeInUp 0.5s ease';
                    newComment.innerHTML = `
                        <div class="comment-header">
                            <div class="comment-avatar">${data.comment.user.charAt(0)}</div>
                            <div class="comment-info">
                                <strong>${data.comment.user}</strong>
                                <span class="comment-time">${data.comment.created_at}</span>
                            </div>
                        </div>
                        <div class="comment-content">${data.comment.content}</div>
                    `;

                    commentsList.insertBefore(newComment, commentsList.firstChild);

                    // Show success message
                    showNotification('留言已送出，開發者將收到郵件通知', 'success');
                } else {
                    // Show error
                    const errors = Object.values(data.errors).flat().join(', ');
                    showNotification(errors, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('送出失敗，請稍後再試', 'error');
            } finally {
                // Re-enable button
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }
});

// Notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#48bb78' : '#f56565'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ========== Video Modal Functionality ==========

document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('videoModal');
    const modalVideo = document.getElementById('modalVideo');
    const modalTitle = document.getElementById('modalTitle');
    const modalDetailLink = document.getElementById('modalDetailLink');
    const closeBtn = document.querySelector('.video-modal-close');
    const overlay = document.querySelector('.video-modal-overlay');
    const videoClickables = document.querySelectorAll('.video-clickable');

    // Open modal when clicking on video
    videoClickables.forEach(videoElement => {
        videoElement.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent card click

            const videoUrl = this.dataset.videoUrl;
            const achievementTitle = this.dataset.achievementTitle;
            const achievementUrl = this.dataset.achievementUrl;

            // Set modal content
            modalVideo.src = videoUrl;
            modalTitle.textContent = achievementTitle;
            modalDetailLink.href = achievementUrl;

            // Show modal
            modal.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent background scroll

            // Play video
            modalVideo.play();
        });
    });

    // Close modal function
    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scroll

        // Pause and reset video
        modalVideo.pause();
        modalVideo.currentTime = 0;
        modalVideo.src = '';
    }

    // Close when clicking close button
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close when clicking overlay
    if (overlay) {
        overlay.addEventListener('click', closeModal);
    }

    // Close when pressing Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Prevent modal content click from closing
    const modalContent = document.querySelector('.video-modal-content');
    if (modalContent) {
        modalContent.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }
});
