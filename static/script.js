/**
 * SMARTSTOCK - INVENTORY DEMAND FORECASTING DASHBOARD
 * Frontend logic, Chart.js integrations, API calls, and interactive filters.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Chart References
    let forecastChart = null;
    let monthlyTrendChart = null;
    let categorySalesChart = null;
    let topProductsChart = null;
    let stockDistributionChart = null;

    // DOM Elements
    const productSelect = document.getElementById("productSelect");
    const forecastHorizon = document.getElementById("forecastHorizon");
    const leadTimeInput = document.getElementById("leadTimeInput");
    const btnRunForecast = document.getElementById("btnRunForecast");
    const globalSearchInput = document.getElementById("globalSearchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const filterPills = document.querySelectorAll(".filter-pill");
    const btnRetrainModel = document.getElementById("btnRetrainModel");
    const btnQuickForecast = document.getElementById("btnQuickForecast");
    const btnRegeneratePlots = document.getElementById("btnRegeneratePlots");
    const toast = document.getElementById("toastNotification");
    const toastMessage = document.getElementById("toastMessage");

    // KPI Elements
    const kpiCurrentInv = document.getElementById("kpiCurrentInv");
    const kpiForecastDemand = document.getElementById("kpiForecastDemand");
    const kpiForecastDays = document.getElementById("kpiForecastDays");
    const kpiSafetyStock = document.getElementById("kpiSafetyStock");
    const kpiRecommendedInv = document.getElementById("kpiRecommendedInv");
    const kpiReorderQty = document.getElementById("kpiReorderQty");
    const kpiReorderStatus = document.getElementById("kpiReorderStatus");
    const forecastChartTitle = document.getElementById("forecastChartTitle");

    // =========================================================================
    // 1. INITIALIZATION
    // =========================================================================
    initSidebarNav();
    initAnalyticsCharts();
    initStockDistributionChart();

    // Trigger initial forecast for the first product
    if (productSelect && productSelect.options.length > 0) {
        updateLeadTimeFromSelectedProduct();
        runForecast();
    }

    // =========================================================================
    // 2. EVENT LISTENERS
    // =========================================================================

    // Product dropdown change
    productSelect.addEventListener("change", () => {
        updateLeadTimeFromSelectedProduct();
        runForecast();
    });

    // Horizon change
    forecastHorizon.addEventListener("change", () => {
        runForecast();
    });

    // Run Forecast button click
    btnRunForecast.addEventListener("click", () => {
        runForecast();
    });

    // Global Search Filter
    globalSearchInput.addEventListener("input", filterTable);

    // Category Filter Dropdown
    categoryFilter.addEventListener("change", filterTable);

    // Status Filter Pills
    filterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            filterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            filterTable();
        });
    });

    // Quick Forecast button in topbar
    if (btnQuickForecast) {
        btnQuickForecast.addEventListener("click", () => {
            const forecastSection = document.getElementById("forecast-tool");
            if (forecastSection) {
                forecastSection.scrollIntoView({ behavior: "smooth" });
                runForecast();
            }
        });
    }

    // Table Row "Forecast" button click
    document.querySelectorAll(".btn-inspect").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const prodId = btn.getAttribute("data-id");
            const lead = btn.getAttribute("data-lead");
            if (prodId) {
                productSelect.value = prodId;
                if (lead) leadTimeInput.value = lead;
                const forecastSection = document.getElementById("forecast-tool");
                forecastSection.scrollIntoView({ behavior: "smooth" });
                runForecast();
            }
        });
    });

    // Model Retrain Button
    if (btnRetrainModel) {
        btnRetrainModel.addEventListener("click", async () => {
            const origHtml = btnRetrainModel.innerHTML;
            btnRetrainModel.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Retraining...';
            btnRetrainModel.disabled = true;

            try {
                const response = await fetch("/api/retrain", { method: "POST" });
                const res = await response.json();
                if (res.success) {
                    showToast(`Model retrained! R²: ${res.metrics.r2}, MAE: ${res.metrics.mae}`);
                    // Refresh current forecast
                    runForecast();
                } else {
                    showToast(`Retrain failed: ${res.error}`, true);
                }
            } catch (err) {
                showToast(`Retrain error: ${err.message}`, true);
            } finally {
                btnRetrainModel.innerHTML = origHtml;
                btnRetrainModel.disabled = false;
            }
        });
    }

    // Refresh Matplotlib Images Button
    if (btnRegeneratePlots) {
        btnRegeneratePlots.addEventListener("click", () => {
            const timestamp = new Date().getTime();
            document.querySelectorAll(".gallery-item img").forEach(img => {
                const baseSrc = img.src.split("?")[0];
                img.src = `${baseSrc}?t=${timestamp}`;
            });
            showToast("Visual graphs refreshed successfully!");
        });
    }

    // =========================================================================
    // 3. FORECAST ENGINE CALL & CHART RENDERING
    // =========================================================================

    function updateLeadTimeFromSelectedProduct() {
        const selectedOpt = productSelect.options[productSelect.selectedIndex];
        if (selectedOpt) {
            const lead = selectedOpt.getAttribute("data-lead");
            if (lead) {
                leadTimeInput.value = lead;
            }
        }
    }

    async function runForecast() {
        const productId = productSelect.value;
        const days = parseInt(forecastHorizon.value, 10);
        const leadTime = parseInt(leadTimeInput.value, 10);

        if (!productId) return;

        // Visual loading state
        btnRunForecast.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Forecasting...';
        btnRunForecast.disabled = true;

        try {
            const response = await fetch("/api/forecast", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    product_id: productId,
                    days: days,
                    lead_time: leadTime
                })
            });

            const result = await response.json();
            if (!result.success) {
                showToast(`Forecast error: ${result.error}`, true);
                return;
            }

            const data = result.data;
            updateForecastKPIs(data);
            renderForecastTimelineChart(data);

        } catch (err) {
            showToast(`Forecast request failed: ${err.message}`, true);
        } finally {
            btnRunForecast.innerHTML = '<i class="fa-solid fa-play"></i> Run Demand Forecast';
            btnRunForecast.disabled = false;
        }
    }

    function updateForecastKPIs(data) {
        kpiCurrentInv.textContent = data.current_inventory.toLocaleString();
        kpiForecastDemand.textContent = data.total_predicted_demand.toLocaleString();
        kpiForecastDays.textContent = `Across ${data.forecast_days} projected days`;
        kpiSafetyStock.textContent = data.safety_stock.toLocaleString();
        kpiRecommendedInv.textContent = data.recommended_inventory.toLocaleString();
        kpiReorderQty.textContent = data.reorder_quantity.toLocaleString();

        // Update Reorder Badge
        kpiReorderStatus.className = "reorder-badge";
        if (data.alert_badge === "critical") {
            kpiReorderStatus.classList.add("badge-critical");
            kpiReorderStatus.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Critical Reorder';
        } else if (data.alert_badge === "warning") {
            kpiReorderStatus.classList.add("badge-warning");
            kpiReorderStatus.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Reorder Soon';
        } else {
            kpiReorderStatus.classList.add("badge-success");
            kpiReorderStatus.innerHTML = '<i class="fa-solid fa-circle-check"></i> Stock Sufficient';
        }

        forecastChartTitle.textContent = `Demand Forecast: ${data.product_name} (${data.category}) - Next ${data.forecast_days} Days`;
    }

    function renderForecastTimelineChart(data) {
        const ctx = document.getElementById("forecastTimelineChart").getContext("2d");

        // Prepare combined timeline labels
        const allLabels = [...data.historical_dates, ...data.forecast_dates];
        const histLen = data.historical_dates.length;
        const forecastLen = data.forecast_dates.length;

        // Historical series (padded with nulls for future days)
        const historicalSeries = [...data.historical_sales];
        for (let i = 0; i < forecastLen; i++) {
            historicalSeries.push(null);
        }

        // Forecast series (connect smoothly from the last historical point)
        const forecastSeries = [];
        for (let i = 0; i < histLen - 1; i++) {
            forecastSeries.push(null);
        }
        forecastSeries.push(data.historical_sales[histLen - 1]); // connection bridge
        forecastSeries.push(...data.forecast_values);

        if (forecastChart) {
            forecastChart.destroy();
        }

        forecastChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: allLabels,
                datasets: [
                    {
                        label: "Historical Actual Sales",
                        data: historicalSeries,
                        borderColor: "#94A3B8",
                        backgroundColor: "rgba(148, 163, 184, 0.1)",
                        borderWidth: 2,
                        tension: 0.25,
                        pointRadius: 2.5,
                        pointHoverRadius: 5,
                        fill: false
                    },
                    {
                        label: "ML Predicted Demand",
                        data: forecastSeries,
                        borderColor: "#3B82F6",
                        backgroundColor: "rgba(59, 130, 246, 0.12)",
                        borderWidth: 2.8,
                        borderDash: [5, 5],
                        tension: 0.3,
                        pointRadius: 3.5,
                        pointHoverRadius: 6,
                        pointBackgroundColor: "#2563EB",
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0F172A",
                        titleFont: { family: "Plus Jakarta Sans", size: 12, weight: "bold" },
                        bodyFont: { family: "Plus Jakarta Sans", size: 11 },
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                if (context.raw !== null && context.raw !== undefined) {
                                    return ` ${context.dataset.label}: ${context.raw} units`;
                                }
                                return null;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            maxTicksLimit: 12,
                            font: { family: "Plus Jakarta Sans", size: 10 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#F1F5F9" },
                        ticks: {
                            font: { family: "Plus Jakarta Sans", size: 10 },
                            callback: value => value + " units"
                        }
                    }
                }
            }
        });
    }

    // =========================================================================
    // 4. ANALYTICS CHARTS (Monthly, Category, Top Products)
    // =========================================================================

    async function initAnalyticsCharts() {
        try {
            const response = await fetch("/api/analytics");
            const res = await response.json();
            if (!res.success) return;

            const data = res.data;

            // 1. Monthly Trend Chart
            const monthlyCtx = document.getElementById("monthlyTrendChart").getContext("2d");
            const months = Object.keys(data.monthly_trend);
            const monthlyUnits = Object.values(data.monthly_trend);

            monthlyTrendChart = new Chart(monthlyCtx, {
                type: "bar",
                data: {
                    labels: months,
                    datasets: [{
                        label: "Total Units Sold",
                        data: monthlyUnits,
                        backgroundColor: "#3B82F6",
                        borderRadius: 6,
                        maxBarThickness: 32
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { backgroundColor: "#0F172A", cornerRadius: 8 }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                        y: { grid: { color: "#F1F5F9" }, beginAtZero: true, ticks: { font: { size: 10 } } }
                    }
                }
            });

            // 2. Category Sales Doughnut Chart
            const catCtx = document.getElementById("categorySalesChart").getContext("2d");
            const catNames = Object.keys(data.category_sales);
            const catUnits = Object.values(data.category_sales);

            categorySalesChart = new Chart(catCtx, {
                type: "doughnut",
                data: {
                    labels: catNames,
                    datasets: [{
                        data: catUnits,
                        backgroundColor: ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444"],
                        borderWidth: 2,
                        borderColor: "#FFFFFF"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "68%",
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: { boxWidth: 12, font: { size: 11, family: "Plus Jakarta Sans" } }
                        }
                    }
                }
            });

            // 3. Top Products Horizontal Bar Chart
            const topCtx = document.getElementById("topProductsChart").getContext("2d");
            topProductsChart = new Chart(topCtx, {
                type: "bar",
                data: {
                    labels: data.top_products.names.map(name => name.length > 20 ? name.substring(0, 18) + ".." : name),
                    datasets: [{
                        label: "Total Units Sold",
                        data: data.top_products.units,
                        backgroundColor: "#2563EB",
                        borderRadius: 6,
                        maxBarThickness: 20
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { backgroundColor: "#0F172A", cornerRadius: 8 }
                    },
                    scales: {
                        x: { grid: { color: "#F1F5F9" }, beginAtZero: true, ticks: { font: { size: 10 } } },
                        y: { grid: { display: false }, ticks: { font: { size: 10 } } }
                    }
                }
            });

        } catch (err) {
            console.error("Failed to load analytics charts:", err);
        }
    }

    // 4. Stock Distribution Doughnut Chart
    function initStockDistributionChart() {
        const rows = document.querySelectorAll("#inventoryRecommendationsTable tbody tr");
        let critical = 0, warning = 0, success = 0;

        rows.forEach(r => {
            const st = r.getAttribute("data-status");
            if (st === "critical") critical++;
            else if (st === "warning") warning++;
            else success++;
        });

        const ctx = document.getElementById("stockDistributionChart").getContext("2d");
        stockDistributionChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Critical Low Stock", "Reorder Soon", "Stock Sufficient"],
                datasets: [{
                    data: [critical, warning, success],
                    backgroundColor: ["#EF4444", "#F59E0B", "#10B981"],
                    borderWidth: 2,
                    borderColor: "#FFFFFF"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, font: { size: 11, family: "Plus Jakarta Sans" } }
                    }
                }
            }
        });
    }

    // =========================================================================
    // 5. TABLE SEARCH & FILTERING LOGIC
    // =========================================================================

    function filterTable() {
        const searchTerm = globalSearchInput.value.toLowerCase().trim();
        const selectedCategory = categoryFilter.value;
        const activePill = document.querySelector(".filter-pill.active");
        const statusFilter = activePill ? activePill.getAttribute("data-filter") : "all";

        const rows = document.querySelectorAll("#inventoryRecommendationsTable tbody tr");

        rows.forEach(row => {
            const rowSearch = row.getAttribute("data-search").toLowerCase();
            const rowCategory = row.getAttribute("data-category");
            const rowStatus = row.getAttribute("data-status");

            const matchesSearch = !searchTerm || rowSearch.includes(searchTerm);
            const matchesCategory = selectedCategory === "all" || rowCategory === selectedCategory;
            const matchesStatus = statusFilter === "all" || rowStatus === statusFilter;

            if (matchesSearch && matchesCategory && matchesStatus) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }

    // =========================================================================
    // 6. SIDEBAR NAVIGATION HIGHLIGHT
    // =========================================================================

    function initSidebarNav() {
        const navItems = document.querySelectorAll(".nav-item");
        navItems.forEach(item => {
            item.addEventListener("click", () => {
                navItems.forEach(n => n.classList.remove("active"));
                item.classList.add("active");
            });
        });
    }

    // =========================================================================
    // 7. TOAST NOTIFICATION UTILITY
    // =========================================================================

    function showToast(message, isError = false) {
        if (!toast || !toastMessage) return;
        toastMessage.textContent = message;
        toast.style.backgroundColor = isError ? "#EF4444" : "#0F172A";
        toast.classList.add("show");

        setTimeout(() => {
            toast.classList.remove("show");
        }, 4000);
    }
});
