/**
 * RSS Aggregator - Frontend JavaScript
 */

const API_BASE = '';

// ============ Utility Functions ============

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Скопійовано!', 'success');
    }).catch(() => {
        showToast('Помилка копіювання', 'error');
    });
}

function copyFeedUrl(feedId) {
    const url = `${window.location.origin}/rss/feed/${feedId}`;
    navigator.clipboard.writeText(url).then(() => {
        showToast('RSS URL скопійовано!', 'success');
    }).catch(() => {
        showToast('Помилка копіювання', 'error');
    });
}

// ============ Feed Management ============

async function addFeed(event) {
    event.preventDefault();
    
    const urlInput = document.getElementById('feedUrl');
    const nameInput = document.getElementById('feedName');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    const url = urlInput.value.trim();
    const name = nameInput.value.trim();
    
    if (!url) {
        showToast('Введіть URL стрічки', 'error');
        return;
    }
    
    // Disable button during request
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner" style="width: 18px; height: 18px;"></span> Додаємо...';
    
    try {
        const response = await fetch(`${API_BASE}/api/feeds`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, name: name || null })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Помилка додавання');
        }
        
        const feed = await response.json();
        showToast(`Стрічку "${feed.name}" додано!`, 'success');
        
        // Clear form and reload page
        urlInput.value = '';
        nameInput.value = '';
        window.location.reload();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Додати
        `;
    }
}

async function deleteFeed(feedId) {
    if (!confirm('Ви впевнені, що хочете видалити цю стрічку?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/feeds/${feedId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Помилка видалення');
        }
        
        showToast('Стрічку видалено', 'success');
        
        // Remove card from DOM
        const card = document.querySelector(`[data-feed-id="${feedId}"]`);
        if (card) {
            card.style.opacity = '0';
            card.style.transform = 'translateX(20px)';
            setTimeout(() => card.remove(), 200);
        }
        
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function refreshFeeds() {
    const btn = document.getElementById('refreshBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width: 18px; height: 18px;"></span> Оновлюємо...';
    
    try {
        const response = await fetch(`${API_BASE}/api/feeds/refresh`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Помилка оновлення');
        }
        
        showToast('Стрічки оновлено!', 'success');
        window.location.reload();
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 2v6h-6"/>
                <path d="M3 12a9 9 0 0 1 15-6.7L21 8"/>
                <path d="M3 22v-6h6"/>
                <path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
            </svg>
            Оновити всі
        `;
    }
}

// ============ Modal Functions ============

async function viewFeed(feedId) {
    const modal = document.getElementById('feedModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modal.classList.add('active');
    modalBody.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        // Get feed info
        const feedsResponse = await fetch(`${API_BASE}/api/feeds`);
        const feedsData = await feedsResponse.json();
        const feed = feedsData.feeds.find(f => f.id === feedId);
        
        if (feed) {
            modalTitle.textContent = feed.name;
        }
        
        // Get items
        const itemsResponse = await fetch(`${API_BASE}/api/feeds/${feedId}/items`);
        const itemsData = await itemsResponse.json();
        
        if (itemsData.items.length === 0) {
            modalBody.innerHTML = `
                <div class="empty-state">
                    <p>Немає новин</p>
                </div>
            `;
            return;
        }
        
        modalBody.innerHTML = itemsData.items.map(item => `
            <div class="news-item">
                <h4><a href="${escapeHtml(item.link)}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a></h4>
                <p class="description">${escapeHtml(stripHtml(item.description || ''))}</p>
                <div class="meta">
                    ${item.pub_date ? formatDate(item.pub_date) : ''}
                    ${item.author ? ` • ${escapeHtml(item.author)}` : ''}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <p>Помилка завантаження: ${error.message}</p>
            </div>
        `;
    }
}

function closeModal() {
    const modal = document.getElementById('feedModal');
    modal.classList.remove('active');
}

// Close modal on outside click
document.getElementById('feedModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ============ Helper Functions ============

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function stripHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
}

function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('uk-UA', {
            day: 'numeric',
            month: 'long',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr;
    }
}

// ============ Initialize ============

document.addEventListener('DOMContentLoaded', () => {
    // Setup form handler
    const addFeedForm = document.getElementById('addFeedForm');
    if (addFeedForm) {
        addFeedForm.addEventListener('submit', addFeed);
    }
    
    // Update endpoint URLs with current origin
    const allFeedsUrl = document.getElementById('allFeedsUrl');
    if (allFeedsUrl) {
        allFeedsUrl.textContent = `${window.location.origin}/rss/all`;
    }
});


