"""
generate_charts.py
------------------
Generates professional Matplotlib visual graphs for inventory analysis and reporting.
Saved charts can be viewed in reports, presentations, and the web application.

Generated Graphs:
1. static/charts/sales_trend.png
2. static/charts/category_distribution.png
3. static/charts/top_products.png
4. static/charts/inventory_vs_recommendation.png
5. static/charts/reorder_status_distribution.png
6. static/charts/forecast_sample.png
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend suitable for server scripts
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from forecasting import (
    load_and_clean_data,
    get_dashboard_summary,
    forecast_demand
)

CHARTS_DIR = os.path.join(os.path.dirname(__file__), "static", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# Styling defaults
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "Segoe UI, Arial, DejaVu Sans, sans-serif"
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.linewidth"] = 0.8


def generate_all_charts():
    print("[INFO] Generating Matplotlib visualization charts...")
    df = load_and_clean_data()
    summary = get_dashboard_summary()

    # 1. SALES TREND OVER TIME
    plt.figure(figsize=(10, 4.5))
    daily_sales = df.groupby("Date")["Units_Sold"].sum().reset_index()
    daily_sales["Rolling_7"] = daily_sales["Units_Sold"].rolling(7, min_periods=1).mean()
    
    plt.plot(daily_sales["Date"], daily_sales["Units_Sold"], color="#94A3B8", alpha=0.45, label="Daily Total Sales")
    plt.plot(daily_sales["Date"], daily_sales["Rolling_7"], color="#3B82F6", linewidth=2.5, label="7-Day Moving Average")
    plt.title("Historical Daily Sales Trend & Seasonality", fontsize=14, fontweight="bold", pad=12, color="#0F172A")
    plt.xlabel("Date", fontsize=11, color="#334155")
    plt.ylabel("Total Units Sold", fontsize=11, color="#334155")
    plt.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "sales_trend.png"), dpi=160)
    plt.close()

    # 2. CATEGORY SALES DISTRIBUTION
    plt.figure(figsize=(7, 5))
    cat_sales = df.groupby("Category")["Units_Sold"].sum().sort_values(ascending=False)
    colors = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444"]
    wedges, texts, autotexts = plt.pie(
        cat_sales,
        labels=cat_sales.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(cat_sales)],
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2)
    )
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.title("Sales Distribution by Product Category", fontsize=13, fontweight="bold", pad=15, color="#0F172A")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "category_distribution.png"), dpi=160)
    plt.close()

    # 3. TOP SELLING PRODUCTS
    plt.figure(figsize=(9, 4.8))
    top_prods = df.groupby("Product_Name")["Units_Sold"].sum().sort_values(ascending=True).tail(8)
    bars = plt.barh(top_prods.index, top_prods.values, color="#2563EB", height=0.65)
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 50, bar.get_y() + bar.get_height()/2, f"{int(w):,}", va="center", ha="left", fontsize=9, fontweight="bold", color="#1E293B")
    plt.title("Top Selling Products by Units Sold", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
    plt.xlabel("Total Units Sold", fontsize=10, color="#334155")
    plt.xlim(0, max(top_prods.values) * 1.15)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "top_products.png"), dpi=160)
    plt.close()

    # 4. CURRENT INVENTORY VS RECOMMENDED LEVEL
    plt.figure(figsize=(11, 5))
    recs = summary["recommendations"]
    p_names = [r["product_name"][:18] + (".." if len(r["product_name"]) > 18 else "") for r in recs]
    current_inv = [r["current_inventory"] for r in recs]
    rec_inv = [r["recommended_inventory"] for r in recs]

    x = np.arange(len(p_names))
    width = 0.38
    plt.bar(x - width/2, current_inv, width, label="Current Stock", color="#64748B")
    plt.bar(x + width/2, rec_inv, width, label="Recommended (30-Day)", color="#10B981")
    plt.xticks(x, p_names, rotation=45, ha="right", fontsize=9)
    plt.ylabel("Units", fontsize=11, color="#334155")
    plt.title("Current Inventory vs Recommended Target Level", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
    plt.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "inventory_vs_recommendation.png"), dpi=160)
    plt.close()

    # 5. REORDER STATUS DISTRIBUTION
    plt.figure(figsize=(7, 4.5))
    statuses = {"Critical Stock": 0, "Reorder Soon": 0, "Stock Sufficient": 0}
    for r in recs:
        statuses[r["alert_level"]] = statuses.get(r["alert_level"], 0) + 1
    
    stat_colors = ["#EF4444", "#F59E0B", "#10B981"]
    bars = plt.bar(list(statuses.keys()), list(statuses.values()), color=stat_colors, width=0.55)
    for b in bars:
        h = b.get_height()
        plt.text(b.get_x() + b.get_width()/2, h + 0.15, str(int(h)), ha="center", va="bottom", fontweight="bold", fontsize=11)
    plt.title("Inventory Stock Status Breakdown", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
    plt.ylabel("Number of Products", fontsize=10, color="#334155")
    plt.ylim(0, max(statuses.values()) + 2)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "reorder_status_distribution.png"), dpi=160)
    plt.close()

    # 6. SAMPLE FORECAST CHART (P101 - Wireless Ergonomic Mouse)
    plt.figure(figsize=(10, 4.5))
    sample_fc = forecast_demand("P101", days=30)
    h_dates = pd.to_datetime(sample_fc["historical_dates"])
    f_dates = pd.to_datetime(sample_fc["forecast_dates"])

    plt.plot(h_dates, sample_fc["historical_sales"], color="#3B82F6", marker="o", markersize=4, label="Historical Actual Sales (Past 30 Days)")
    plt.plot(f_dates, sample_fc["forecast_values"], color="#8B5CF6", linestyle="--", marker="s", markersize=4, label="ML Forecast (Next 30 Days)")
    plt.axvline(x=h_dates[-1], color="#EF4444", linestyle=":", label="Forecast Cutoff Date")
    plt.title(f"Demand Forecast: {sample_fc['product_name']}", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
    plt.xlabel("Date", fontsize=10, color="#334155")
    plt.ylabel("Units Sold / Demand", fontsize=10, color="#334155")
    plt.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "forecast_sample.png"), dpi=160)
    plt.close()

    print(f"[SUCCESS] All Matplotlib charts saved to '{CHARTS_DIR}'.")

if __name__ == "__main__":
    generate_all_charts()
