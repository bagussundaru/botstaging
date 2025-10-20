// Dashboard JavaScript - Using BybitDataManager only

// Utility Functions
async function fetchWithRetry(url, options = {}, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        } catch (error) {
            console.warn(`Fetch attempt ${i + 1} failed for ${url}:`, error.message);
            
            if (i === maxRetries - 1) {
                throw new Error(`Failed to fetch ${url} after ${maxRetries} attempts: ${error.message}`);
            }
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
    }
}

function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = new Date().toLocaleString();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Update time every second
    setInterval(updateCurrentTime, 1000);
    updateCurrentTime();
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Interactive Chart Manager
class ChartManager {
    constructor() {
        this.charts = {};
        this.chartData = {};
        this.updateInterval = 10000; // 10 seconds
        this.init();
    }

    init() {
        this.initializePnlChart();
        this.initializePerformanceChart();
        this.startRealTimeUpdates();
    }

    async initializePnlChart() {
        try {
            const response = await fetch('/api/pnl-chart');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.createPnlChart(data.data);
            }
        } catch (error) {
            console.error('Error loading PnL chart:', error);
        }
    }

    createPnlChart(data) {
        const ctx = document.getElementById('pnlChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.pnl) {
            this.charts.pnl.destroy();
        }

        this.charts.pnl = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Cumulative PnL ($)',
                    data: data.values || [],
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `PnL: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'PnL ($)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    async initializePerformanceChart() {
        try {
            const response = await fetch('/api/trading-stats');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.createPerformanceChart(data.data);
            }
        } catch (error) {
            console.error('Error loading performance chart:', error);
        }
    }

    createPerformanceChart(data) {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.performance) {
            this.charts.performance.destroy();
        }

        const winRate = data.win_rate || 0;
        const lossRate = 100 - winRate;

        this.charts.performance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Wins', 'Losses'],
                datasets: [{
                    data: [winRate, lossRate],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });

        // Add center text
        const centerText = document.createElement('div');
        centerText.className = 'chart-center-text';
        centerText.innerHTML = `
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                <div style="font-size: 2rem; font-weight: bold; color: #4f46e5;">${winRate.toFixed(1)}%</div>
                <div style="font-size: 0.9rem; color: #666;">Win Rate</div>
            </div>
        `;
        ctx.parentElement.style.position = 'relative';
        ctx.parentElement.appendChild(centerText);
    }

    async updateCharts() {
        await Promise.all([
            this.initializePnlChart(),
            this.initializePerformanceChart()
        ]);
    }

    startRealTimeUpdates() {
        setInterval(() => {
            this.updateCharts();
        }, this.updateInterval);
    }

    // Chart control methods
    toggleChartPeriod(chartId, period) {
        const buttons = document.querySelectorAll(`#${chartId} .chart-btn`);
        buttons.forEach(btn => btn.classList.remove('active'));
        
        const activeBtn = document.querySelector(`#${chartId} .chart-btn[data-period="${period}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        // Reload chart with new period
        this.loadChartData(chartId, period);
    }

    async loadChartData(chartId, period = '24h') {
        try {
            const response = await fetch(`/api/chart-data/${chartId}?period=${period}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateChartData(chartId, data.data);
            }
        } catch (error) {
            console.error(`Error loading ${chartId} data:`, error);
        }
    }

    updateChartData(chartId, newData) {
        const chart = this.charts[chartId];
        if (!chart) return;

        chart.data.labels = newData.labels;
        chart.data.datasets[0].data = newData.values;
        chart.update('none');
    }
}

// StatsManager removed - using BybitDataManager instead

// Bybit Data Manager for real-time API integration
class BybitDataManager {
    constructor() {
        this.updateInterval = 10000; // 10 seconds
        this.isLoading = false;
        this.lastUpdate = null;
        this.currentSymbol = 'ETHUSDT';
        
        this.init();
    }

    init() {
        this.setupSymbolSelector();
        this.loadInitialData();
        this.startRealTimeUpdates();
    }

    setupSymbolSelector() {
        const symbolSelector = document.getElementById('symbolSelector');
        if (symbolSelector) {
            symbolSelector.addEventListener('change', (e) => {
                this.currentSymbol = e.target.value;
                this.loadAllData();
            });
        }
    }

    async loadInitialData() {
        await this.loadAllData();
    }

    async loadAllData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            // Load comprehensive dashboard data with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
            
            const response = await fetch(`/api/bybit/dashboard-data?symbol=${this.currentSymbol}`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success && result.data) {
                this.updateAccountInfo(result.data.account);
                this.updatePositions(result.data.positions);
                this.updateRecentTrades(result.data.recent_trades);
                this.updatePnLAnalysis(result.data.pnl_analysis);
                this.updateMarketData(result.data.market_data);
                
                this.lastUpdate = new Date();
                this.updateLastUpdateTime();
                this.clearErrorState();
            } else {
                this.showError(result.error || 'Failed to load Bybit data');
            }
        } catch (error) {
            console.error('Error loading Bybit data:', error);
            
            if (error.name === 'AbortError') {
                this.showError('Request timeout - please check your connection');
            } else if (error.message.includes('Failed to fetch')) {
                this.showError('Network connection error - retrying...');
                // Auto retry after 5 seconds
                setTimeout(() => {
                    if (!this.isLoading) {
                        this.loadAllData();
                    }
                }, 5000);
            } else {
                this.showError(`Error loading data: ${error.message}`);
            }
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    updateAccountInfo(accountData) {
        if (!accountData) return;

        // Update balance (Bybit section)
        const balanceElement = document.getElementById('currentBalance');
        if (balanceElement && accountData.total_balance !== undefined) {
            balanceElement.textContent = `$${accountData.total_balance.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }

        // Update balance (Top stats section)
        const totalBalanceElement = document.getElementById('totalBalance');
        if (totalBalanceElement && accountData.total_balance !== undefined) {
            totalBalanceElement.textContent = `$${accountData.total_balance.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }

        // Update available balance
        const availableElement = document.getElementById('availableBalance');
        if (availableElement && accountData.available_balance !== undefined) {
            availableElement.textContent = `$${accountData.available_balance.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }

        // Update margin ratio
        const marginElement = document.getElementById('marginRatio');
        if (marginElement && accountData.margin_ratio !== undefined) {
            const ratio = accountData.margin_ratio;
            marginElement.textContent = `${ratio.toFixed(2)}%`;
            
            // Color coding for margin ratio
            if (ratio > 80) {
                marginElement.className = 'text-red-600 font-bold';
            } else if (ratio > 60) {
                marginElement.className = 'text-yellow-600 font-bold';
            } else {
                marginElement.className = 'text-green-600 font-bold';
            }
        }

        // Update daily PnL
        const dailyPnlElement = document.getElementById('dailyPnl');
        if (dailyPnlElement && accountData.daily_pnl !== undefined) {
            const pnl = accountData.daily_pnl;
            dailyPnlElement.textContent = `$${pnl.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
            dailyPnlElement.className = pnl >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold';
        }

        // Update total PnL (Top stats section)
        const totalPnlElement = document.getElementById('totalPnl');
        if (totalPnlElement && accountData.daily_pnl !== undefined) {
            const pnl = accountData.daily_pnl;
            totalPnlElement.textContent = `$${pnl.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
            totalPnlElement.className = `stat-value ${pnl >= 0 ? 'positive' : 'negative'}`;
        }
    }

    updatePositions(positionsData) {
        if (!positionsData) return;

        const positionsContainer = document.getElementById('positionsContainer');
        if (!positionsContainer) return;

        if (positionsData.length === 0) {
            positionsContainer.innerHTML = '<div class="text-gray-500 text-center py-4">No open positions</div>';
            return;
        }

        const positionsHtml = positionsData.map(position => `
            <div class="position-card bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                <div class="flex justify-between items-start mb-2">
                    <div class="font-semibold text-lg">${position.symbol}</div>
                    <div class="text-sm ${position.side === 'Buy' ? 'text-green-600' : 'text-red-600'} font-medium">
                        ${position.side} ${position.size}
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>
                        <span class="text-gray-500">Entry:</span>
                        <span class="font-medium">$${parseFloat(position.avg_price).toLocaleString()}</span>
                    </div>
                    <div>
                        <span class="text-gray-500">Mark:</span>
                        <span class="font-medium">$${parseFloat(position.mark_price).toLocaleString()}</span>
                    </div>
                    <div>
                        <span class="text-gray-500">PnL:</span>
                        <span class="font-medium ${parseFloat(position.unrealised_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}">
                            $${parseFloat(position.unrealised_pnl).toFixed(2)}
                        </span>
                    </div>
                    <div>
                        <span class="text-gray-500">ROE:</span>
                        <span class="font-medium ${parseFloat(position.unrealised_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}">
                            ${(parseFloat(position.unrealised_pnl) / parseFloat(position.position_value) * 100).toFixed(2)}%
                        </span>
                    </div>
                </div>
            </div>
        `).join('');

        positionsContainer.innerHTML = positionsHtml;
    }

    updateRecentTrades(tradesData) {
        if (!tradesData) return;

        const tradesContainer = document.getElementById('recentTradesContainer');
        if (!tradesContainer) return;

        if (tradesData.length === 0) {
            tradesContainer.innerHTML = '<div class="text-gray-500 text-center py-4">No recent trades</div>';
            return;
        }

        const tradesHtml = tradesData.map(trade => `
            <div class="trade-row flex justify-between items-center py-2 border-b border-gray-100">
                <div class="flex items-center space-x-3">
                    <div class="w-2 h-2 rounded-full ${trade.side === 'Buy' ? 'bg-green-500' : 'bg-red-500'}"></div>
                    <div>
                        <div class="font-medium">${trade.symbol}</div>
                        <div class="text-xs text-gray-500">${new Date(trade.exec_time).toLocaleTimeString()}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="font-medium">$${parseFloat(trade.exec_price).toLocaleString()}</div>
                    <div class="text-xs text-gray-500">${trade.exec_qty}</div>
                </div>
            </div>
        `).join('');

        tradesContainer.innerHTML = tradesHtml;
    }

    updatePnLAnalysis(pnlData) {
        if (!pnlData) return;

        // Update total PnL
        const totalPnlElement = document.getElementById('totalPnl');
        if (totalPnlElement && pnlData.total_pnl !== undefined) {
            const pnl = pnlData.total_pnl;
            totalPnlElement.textContent = `$${pnl.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
            totalPnlElement.className = pnl >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold';
        }

        // Update win rate (Bybit section)
        const winRateElement = document.getElementById('winRate');
        if (winRateElement && pnlData.win_rate !== undefined) {
            winRateElement.textContent = `${pnlData.win_rate.toFixed(1)}%`;
        }

        // Update total trades (Bybit section)
        const totalTradesElement = document.getElementById('totalTrades');
        if (totalTradesElement && pnlData.total_trades !== undefined) {
            totalTradesElement.textContent = pnlData.total_trades;
        }

        // Update win rate (Top stats section) - using same ID
        // Update total trades (Top stats section) - using same ID
    }

    updateMarketData(marketData) {
        if (!marketData) return;

        // Update current price
        const priceElement = document.getElementById('currentPrice');
        if (priceElement && marketData.price !== undefined) {
            priceElement.textContent = `$${parseFloat(marketData.price).toLocaleString()}`;
        }

        // Update 24h change
        const changeElement = document.getElementById('priceChange24h');
        if (changeElement && marketData.price_change_24h !== undefined) {
            const change = marketData.price_change_24h;
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeElement.className = change >= 0 ? 'text-green-600' : 'text-red-600';
        }

        // Update volume
        const volumeElement = document.getElementById('volume24h');
        if (volumeElement && marketData.volume_24h !== undefined) {
            volumeElement.textContent = `$${(marketData.volume_24h / 1000000).toFixed(1)}M`;
        }
    }

    showLoadingState() {
        const loadingElements = document.querySelectorAll('.loading-spinner');
        loadingElements.forEach(el => el.style.display = 'block');
    }

    hideLoadingState() {
        const loadingElements = document.querySelectorAll('.loading-spinner');
        loadingElements.forEach(el => el.style.display = 'none');
    }

    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    <strong>Error:</strong> ${message}
                    <button onclick="this.parentElement.remove()" class="float-right text-red-700 hover:text-red-900">×</button>
                </div>
            `;
        }
    }

    clearErrorState() {
        const errorContainer = document.getElementById('errorContainer');
        if (errorContainer) {
            errorContainer.innerHTML = '';
        }
    }

    updateLastUpdateTime() {
        const updateTimeElement = document.getElementById('lastUpdateTime');
        if (updateTimeElement && this.lastUpdate) {
            updateTimeElement.textContent = `Last updated: ${this.lastUpdate.toLocaleTimeString()}`;
        }
    }

    startRealTimeUpdates() {
        setInterval(() => {
            if (!this.isLoading) {
                this.loadAllData();
            }
        }, this.updateInterval);
    }

    // Manual refresh method
    async refresh() {
        await this.loadAllData();
    }
}

// Initialize managers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart manager if Chart.js is available
    if (typeof Chart !== 'undefined') {
        window.chartManager = new ChartManager();
    }
    
    // Initialize stats manager (disabled - using Bybit data instead)
    // window.statsManager = new StatsManager();
    
    // Initialize Bybit data manager
    window.bybitManager = new BybitDataManager();
    
    // Start real-time updates for Bybit data
    window.bybitManager.startRealTimeUpdates();
    
    // Load initial data
    window.bybitManager.loadAllData();
    
    // Add chart control event listeners
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('chart-btn')) {
            const chartContainer = e.target.closest('.chart-container');
            const chartId = chartContainer?.id;
            const period = e.target.dataset.period;
            
            if (chartId && period && window.chartManager) {
                window.chartManager.toggleChartPeriod(chartId, period);
            }
        }
        
        // Handle refresh button
        if (e.target.id === 'refreshButton' || e.target.closest('#refreshButton')) {
            if (window.bybitManager) {
                window.bybitManager.refresh();
            }
        }
    });
});