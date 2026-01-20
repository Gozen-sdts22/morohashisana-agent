// 諸橋沙夏情報収集システム - メインJavaScript

// グローバル変数
let currentPage = 1;
let currentFilters = {
    period: '7d',
    importance: 'all',
    category: 'all',
    keyword: ''
};
let hasNextPage = false;
let wasRunning = false; // 前回の実行状態を記憶して完了を検知する

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // イベントリスナーを設定
    setupEventListeners();

    // カテゴリを読み込み
    loadCategories();

    // アイテムを読み込み
    loadItems();

    // 最終実行情報を読み込み
    loadLastExecution();

    // 実行状態を定期的にチェック
    setInterval(checkExecutionStatus, 3000);
});

// イベントリスナーの設定
function setupEventListeners() {
    // 実行ボタン
    document.getElementById('executeBtn').addEventListener('click', executeCollection);

    // フィルター適用ボタン
    document.getElementById('applyFilterBtn').addEventListener('click', applyFilters);

    // もっと見るボタン
    document.getElementById('loadMoreBtn').addEventListener('click', loadMoreItems);

    // Enterキーでフィルター適用
    document.getElementById('keywordFilter').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            applyFilters();
        }
    });
}

// カテゴリを読み込み
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();

        const categorySelect = document.getElementById('categoryFilter');
        data.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('カテゴリの読み込みエラー:', error);
    }
}

// アイテムを読み込み
async function loadItems(append = false) {
    const container = document.getElementById('itemsContainer');

    if (!append) {
        container.innerHTML = '<div class="loading">読み込み中...</div>';
        currentPage = 1;
    }

    try {
        const params = new URLSearchParams({
            period: currentFilters.period,
            importance: currentFilters.importance,
            category: currentFilters.category,
            keyword: currentFilters.keyword,
            page: currentPage,
            per_page: 20
        });

        const response = await fetch(`/api/items?${params}`);
        const data = await response.json();

        if (!append) {
            container.innerHTML = '';
        } else {
            // ローディング表示を削除
            const loading = container.querySelector('.loading');
            if (loading) loading.remove();
        }

        // アイテムを表示
        if (data.items.length === 0 && !append) {
            container.innerHTML = '<div class="empty-message">該当する情報が見つかりませんでした</div>';
        } else {
            data.items.forEach(item => {
                container.appendChild(createItemCard(item));
            });
        }

        // ページネーション情報を更新
        updatePagination(data);

    } catch (error) {
        console.error('アイテムの読み込みエラー:', error);
        container.innerHTML = '<div class="error-message">エラーが発生しました</div>';
    }
}

// アイテムカードを作成
function createItemCard(item) {
    const card = document.createElement('div');
    card.className = 'item-card';

    // 重要度バッジ
    const importanceClass = `importance-${item.importance_level}`;
    const importanceText = {
        'high': '🔴 重要',
        'medium': '🟡 中',
        'low': '⚪ 低'
    }[item.importance_level] || '⚪ 低';

    // 日時をフォーマット
    const publishedDate = new Date(item.published_at);
    const formattedDate = publishedDate.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });

    // ソース名を日本語化
    const sourceName = {
        'twitter': 'X (Twitter)',
        'yahoo_news': 'Yahoo!ニュース',
        'modelpress': 'モデルプレス'
    }[item.source] || item.source;

    // メトリクス表示
    let metricsHTML = '';
    if (item.metrics && item.source === 'twitter') {
        const metrics = item.metrics;
        metricsHTML = `
            <div class="item-metrics">
                ${metrics.likes ? `<span>❤️ ${metrics.likes.toLocaleString()}</span>` : ''}
                ${metrics.retweets ? `<span>🔁 ${metrics.retweets.toLocaleString()}</span>` : ''}
                ${metrics.views ? `<span>👁️ ${metrics.views.toLocaleString()}</span>` : ''}
            </div>
        `;
    }

    card.innerHTML = `
        <div class="item-header">
            <span class="importance-badge ${importanceClass}">${importanceText}</span>
            <span class="item-category">${item.category || 'その他'}</span>
        </div>
        <div class="item-meta">
            <span>${formattedDate}</span>
            <span>${sourceName}</span>
        </div>
        ${item.title ? `<div class="item-title">${escapeHtml(item.title)}</div>` : ''}
        ${item.summary ? `<div class="item-summary">${escapeHtml(item.summary)}</div>` : ''}
        ${item.content && !item.summary ? `<div class="item-summary">${escapeHtml(item.content.substring(0, 100))}...</div>` : ''}
        ${metricsHTML}
        <a href="${item.url}" target="_blank" class="item-link">記事を開く ↗</a>
    `;

    return card;
}

// ページネーション情報を更新
function updatePagination(data) {
    const itemCount = document.getElementById('itemCount');
    const loadMoreBtn = document.getElementById('loadMoreBtn');

    const start = (data.page - 1) * data.per_page + 1;
    const end = Math.min(start + data.items.length - 1, data.total);

    itemCount.textContent = `表示: ${start}-${end} / ${data.total}件`;

    hasNextPage = data.has_next;
    loadMoreBtn.style.display = hasNextPage ? 'block' : 'none';
}

// フィルターを適用
function applyFilters() {
    currentFilters = {
        period: document.getElementById('periodFilter').value,
        importance: document.getElementById('importanceFilter').value,
        category: document.getElementById('categoryFilter').value,
        keyword: document.getElementById('keywordFilter').value.trim()
    };

    loadItems();
}

// もっと見る
function loadMoreItems() {
    currentPage++;

    // ローディング表示を追加
    const container = document.getElementById('itemsContainer');
    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.textContent = '読み込み中...';
    container.appendChild(loading);

    loadItems(true);
}

// 情報収集を実行
async function executeCollection() {
    const btn = document.getElementById('executeBtn');
    const statusDiv = document.getElementById('executionStatus');

    btn.disabled = true;
    wasRunning = true; // 実行開始を記録（完了時にリロードするため）
    statusDiv.textContent = '情報収集を開始しています...';

    try {
        const response = await fetch('/api/execute', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.status === 'started') {
            statusDiv.textContent = '情報収集中... (完了まで数分かかります)';
        } else if (data.status === 'already_running') {
            statusDiv.textContent = 'すでに実行中です';
            btn.disabled = false;
        }
    } catch (error) {
        console.error('実行エラー:', error);
        statusDiv.textContent = 'エラーが発生しました';
        btn.disabled = false;
    }
}

// 実行状態をチェック
async function checkExecutionStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const btn = document.getElementById('executeBtn');
        const statusDiv = document.getElementById('executionStatus');

        if (data.is_running) {
            btn.disabled = true;
            statusDiv.textContent = '情報収集中...';
        } else {
            btn.disabled = false;
            statusDiv.textContent = '';

            // 直前まで実行中だった場合のみ、完了後にリストと最終実行情報をリロード
            if (wasRunning) {
                wasRunning = false;
                loadItems();          // 最新データを取得
                loadLastExecution();  // 最終実行情報を更新
            }
        }
    } catch (error) {
        console.error('ステータスチェックエラー:', error);
    }
}

// 最終実行情報を読み込み
async function loadLastExecution() {
    try {
        const response = await fetch('/api/logs?limit=1');
        const data = await response.json();

        if (data.logs.length > 0) {
            const lastExec = data.logs[0];
            const lastExecDiv = document.getElementById('lastExecution');

            const completedAt = new Date(lastExec.completed_at || lastExec.started_at);
            const formattedDate = completedAt.toLocaleString('ja-JP');

            lastExecDiv.textContent = `最終実行: ${formattedDate} (${lastExec.total_saved}件取得)`;
        }
    } catch (error) {
        console.error('最終実行情報の読み込みエラー:', error);
    }
}

// HTMLエスケープ
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
