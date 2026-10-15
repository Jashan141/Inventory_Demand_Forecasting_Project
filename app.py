"""
app.py
------
Flask Web Application for the Inventory Demand Forecasting System.

Features:
- Dashboard with summary KPIs and inventory alerts
- Machine learning demand forecasting endpoint
- Interactive recommendations and reorder calculator
- Analytics and visualizations API
- CSV report export
- One-click model retraining
"""

import io
import os
import csv
from flask import Flask, render_template, request, jsonify, Response
from forecasting import (
    load_and_clean_data,
    load_model_package,
    train_forecasting_model,
    forecast_demand,
    get_dashboard_summary,
    get_analytics_charts_data
)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route("/")
def index():
    """
    Renders main dashboard application.
    """
    try:
        # Load or ensure model exists
        package = load_model_package()
        metrics = package.get("metrics", {})
        
        # Load summary data
        summary = get_dashboard_summary()
        
        # Unique products and categories for filters
        df = load_and_clean_data()
        products_meta = df[["Product_ID", "Product_Name", "Category", "Price", "Lead_Time_Days"]].drop_duplicates().to_dict(orient="records")
        categories = sorted(list(df["Category"].unique()))

        return render_template(
            "index.html",
            summary=summary,
            products=products_meta,
            categories=categories,
            metrics=metrics
        )
    except Exception as e:
        return f"Application initialization error: {str(e)}", 500


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route("/api/summary", methods=["GET"])
def api_summary():
    """
    Returns dashboard summary KPIs and table recommendations in JSON.
    """
    try:
        summary = get_dashboard_summary()
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/forecast", methods=["POST"])
def api_forecast():
    """
    Generates demand forecast and reorder recommendation for a specific product.
    Request JSON: { "product_id": "P101", "days": 30, "lead_time": 5 (optional) }
    """
    try:
        data = request.get_json(force=True) if request.is_json else request.form
        product_id = data.get("product_id")
        days = int(data.get("days", 30))
        lead_time = data.get("lead_time")
        lead_time = int(lead_time) if lead_time else None

        if not product_id:
            return jsonify({"success": False, "error": "Product ID is required."}), 400

        result = forecast_demand(product_id=product_id, days=days, custom_lead_time=lead_time)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """
    Returns aggregated analytics for charts (monthly trends, category split, top products).
    """
    try:
        data = get_analytics_charts_data()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/retrain", methods=["POST"])
def api_retrain():
    """
    Retrains the Random Forest Regressor and returns new evaluation metrics.
    """
    try:
        package = train_forecasting_model()
        return jsonify({
            "success": True,
            "message": "Model retrained successfully!",
            "metrics": package["metrics"],
            "trained_at": package.get("trained_at")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export-report", methods=["GET"])
def api_export_report():
    """
    Generates downloadable CSV containing inventory recommendation and reorder data.
    """
    try:
        summary = get_dashboard_summary()
        recommendations = summary.get("recommendations", [])

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Product ID",
            "Product Name",
            "Category",
            "Unit Price ($)",
            "Current Inventory",
            "Lead Time (Days)",
            "30-Day Forecast Demand",
            "Safety Stock",
            "Recommended Inventory Level",
            "Reorder Quantity",
            "Reorder Status",
            "Alert Level"
        ])

        for r in recommendations:
            writer.writerow([
                r["product_id"],
                r["product_name"],
                r["category"],
                f"{r['price']:.2f}",
                r["current_inventory"],
                r["lead_time_days"],
                r["total_predicted_demand"],
                r["safety_stock"],
                r["recommended_inventory"],
                r["reorder_quantity"],
                r["reorder_status"],
                r["alert_level"]
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=inventory_reorder_report.csv"}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Ensure model is ready before serving
    load_model_package()
    print("[INFO] Starting Inventory Demand Forecasting Web Server...")
    print("[INFO] Open your browser and navigate to: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
