"""
forecasting.py
--------------
Core Machine Learning and Inventory Demand Forecasting Engine.

This module handles:
1. Loading and preprocessing historical sales data.
2. Feature engineering (date features, lag values, rolling statistics).
3. Training a Scikit-Learn Random Forest Regressor model.
4. Saving and loading the trained model pipeline with joblib.
5. Generating future demand predictions for any selected product and period.
6. Calculating Inventory Recommendations:
   - Safety Stock
   - Recommended Inventory Level
   - Reorder Quantity
   - Reorder Status and Alert Levels (Critical, Reorder Soon, Sufficient)
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sales_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "forecasting_model.pkl")

# Service level factor Z for 95% cycle service level
SERVICE_LEVEL_Z = 1.65


# ============================================================================
# 1. DATA PREPROCESSING & FEATURE ENGINEERING
# ============================================================================

def load_and_clean_data(file_path=DATA_PATH):
    """
    Loads raw CSV data, cleans missing or duplicated records, parses dates,
    and sorts data chronologically.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sales data file not found at: {file_path}")

    # Load CSV using pandas
    df = pd.read_csv(file_path)

    # 1. Remove duplicate records
    df = df.drop_duplicates()

    # 2. Parse Date into datetime format
    df["Date"] = pd.to_datetime(df["Date"])

    # 3. Handle missing values
    # Ensure numeric columns have no NaNs
    df["Units_Sold"] = pd.to_numeric(df["Units_Sold"], errors="coerce").fillna(0).astype(int)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(df["Price"].median())
    df["Inventory_Level"] = pd.to_numeric(df["Inventory_Level"], errors="coerce").fillna(0).astype(int)
    df["Lead_Time_Days"] = pd.to_numeric(df["Lead_Time_Days"], errors="coerce").fillna(7).astype(int)

    # 4. Sort chronologically
    df = df.sort_values(by=["Product_ID", "Date"]).reset_index(drop=True)

    return df


def engineer_features(df):
    """
    Extracts time-based and lag/rolling statistical features for the ML model.
    """
    df = df.copy()

    # Date-based features
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["DayOfWeek"] = df["Date"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6]).astype(int)
    df["Quarter"] = df["Date"].dt.quarter
    df["DayOfYear"] = df["Date"].dt.dayofyear

    # Lag features (past demand gives strong predictive signal)
    # Group by product so lag calculations don't bleed across different products
    df["Units_Sold_Lag_7"] = df.groupby("Product_ID")["Units_Sold"].shift(7)
    df["Units_Sold_Lag_14"] = df.groupby("Product_ID")["Units_Sold"].shift(14)

    # Rolling window statistics (7-day rolling average)
    df["Rolling_Mean_7"] = df.groupby("Product_ID")["Units_Sold"].transform(
        lambda s: s.shift(1).rolling(window=7, min_periods=1).mean()
    )

    # Fill any NaNs created by shifts using the overall product median or zero
    df["Units_Sold_Lag_7"] = df["Units_Sold_Lag_7"].bfill().fillna(df["Units_Sold"].median())
    df["Units_Sold_Lag_14"] = df["Units_Sold_Lag_14"].bfill().fillna(df["Units_Sold"].median())
    df["Rolling_Mean_7"] = df["Rolling_Mean_7"].bfill().fillna(df["Units_Sold"].median())

    return df


# ============================================================================
# 2. MODEL TRAINING & PERSISTENCE
# ============================================================================

def train_forecasting_model(data_path=DATA_PATH, model_path=MODEL_PATH):
    """
    Trains a Random Forest Regressor on historical sales data and saves the
    model, encoders, and evaluation metrics into a pickle file.
    """
    print("[INFO] Loading and preprocessing data for training...")
    df = load_and_clean_data(data_path)
    df = engineer_features(df)

    # Categorical encoders
    le_product = LabelEncoder()
    le_category = LabelEncoder()

    df["Product_Code"] = le_product.fit_transform(df["Product_ID"])
    df["Category_Code"] = le_category.fit_transform(df["Category"])

    # Features used for ML prediction
    feature_cols = [
        "Product_Code",
        "Category_Code",
        "Price",
        "Lead_Time_Days",
        "Month",
        "Day",
        "DayOfWeek",
        "IsWeekend",
        "Quarter",
        "DayOfYear",
        "Units_Sold_Lag_7",
        "Units_Sold_Lag_14",
        "Rolling_Mean_7"
    ]

    target_col = "Units_Sold"

    # Chronological Train-Test Split (80% train, 20% test)
    # Preserves realistic time order without data leakage
    dates = df["Date"].drop_duplicates().sort_values()
    split_idx = int(len(dates) * 0.8)
    split_date = dates.iloc[split_idx]

    train_df = df[df["Date"] <= split_date]
    test_df = df[df["Date"] > split_date]

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    print(f"[INFO] Training Random Forest Regressor on {len(X_train)} rows; Testing on {len(X_test)} rows...")

    # Random Forest Regressor
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=14,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Evaluate predictions
    y_pred = model.predict(X_test)
    y_pred = np.maximum(0, np.round(y_pred))  # Demand cannot be negative

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(root_mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    print(f"[SUCCESS] Model Trained Successfully!")
    print(f"          - MAE  (Mean Absolute Error):     {mae:.2f} units")
    print(f"          - RMSE (Root Mean Squared Error): {rmse:.2f} units")
    print(f"          - R2 Score:                       {r2:.4f}")

    # Feature importances
    feature_importances = dict(zip(feature_cols, [round(float(val), 4) for val in model.feature_importances_]))

    # Package model payload
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    payload = {
        "model": model,
        "feature_cols": feature_cols,
        "le_product": le_product,
        "le_category": le_category,
        "metrics": {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4)
        },
        "feature_importances": feature_importances,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    joblib.dump(payload, model_path)
    print(f"[SUCCESS] Saved model package to: {model_path}")
    return payload


def load_model_package(model_path=MODEL_PATH):
    """
    Loads saved model package or trains a new one if not present.
    """
    if not os.path.exists(model_path):
        print(f"[WARNING] Model file {model_path} not found. Training model now...")
        return train_forecasting_model()
    return joblib.load(model_path)


# ============================================================================
# 3. DEMAND FORECASTING ENGINE
# ============================================================================

def forecast_demand(product_id, days=30, custom_lead_time=None):
    """
    Generates future daily demand forecast for a specified product using
    the trained Random Forest ML model and historical context.

    Returns:
    - Product details
    - Historical actual sales (last 30 days)
    - Future predicted daily demand (dates & values)
    - Total forecasted demand
    - Inventory & Reorder recommendations
    """
    # 1. Load model package
    package = load_model_package()
    model = package["model"]
    feature_cols = package["feature_cols"]
    le_product = package["le_product"]
    le_category = package["le_category"]

    # 2. Load and filter product data
    df = load_and_clean_data()
    prod_data = df[df["Product_ID"] == product_id].sort_values("Date").reset_index(drop=True)

    if prod_data.empty:
        raise ValueError(f"Product ID '{product_id}' was not found in dataset.")

    product_name = prod_data["Product_Name"].iloc[-1]
    category = prod_data["Category"].iloc[-1]
    price = float(prod_data["Price"].iloc[-1])
    current_inventory = int(prod_data["Inventory_Level"].iloc[-1])
    lead_time = int(custom_lead_time) if custom_lead_time is not None else int(prod_data["Lead_Time_Days"].iloc[-1])

    # Historical demand statistics (last 30-60 days)
    recent_history = prod_data.tail(30).copy()
    hist_units = recent_history["Units_Sold"].values
    hist_dates = [d.strftime("%Y-%m-%d") for d in recent_history["Date"]]

    avg_daily_demand = float(np.mean(hist_units))
    std_daily_demand = float(np.std(hist_units)) if len(hist_units) > 1 else 1.0

    # Categorical codes
    prod_code = le_product.transform([product_id])[0]
    cat_code = le_category.transform([category])[0]

    # Prepare for multi-step forward projection
    last_date = prod_data["Date"].max()
    future_dates = [last_date + timedelta(days=i + 1) for i in range(days)]

    # Maintain a working list of recent sales to dynamically compute lag and rolling values
    simulated_sales = list(prod_data["Units_Sold"].values)

    forecast_values = []

    for f_date in future_dates:
        # Construct features for this future day
        lag_7 = simulated_sales[-7] if len(simulated_sales) >= 7 else avg_daily_demand
        lag_14 = simulated_sales[-14] if len(simulated_sales) >= 14 else avg_daily_demand
        rolling_7 = np.mean(simulated_sales[-7:]) if len(simulated_sales) >= 7 else avg_daily_demand

        row_feat = {
            "Product_Code": prod_code,
            "Category_Code": cat_code,
            "Price": price,
            "Lead_Time_Days": lead_time,
            "Month": f_date.month,
            "Day": f_date.day,
            "DayOfWeek": f_date.weekday(),
            "IsWeekend": 1 if f_date.weekday() in [5, 6] else 0,
            "Quarter": (f_date.month - 1) // 3 + 1,
            "DayOfYear": f_date.timetuple().tm_yday,
            "Units_Sold_Lag_7": lag_7,
            "Units_Sold_Lag_14": lag_14,
            "Rolling_Mean_7": rolling_7
        }

        X_future = pd.DataFrame([row_feat])[feature_cols]
        pred_demand = max(0, int(round(model.predict(X_future)[0])))

        forecast_values.append(pred_demand)
        simulated_sales.append(pred_demand)

    total_predicted_demand = int(sum(forecast_values))

    # ========================================================================
    # 4. INVENTORY & REORDER RECOMMENDATION CALCULATION
    # ========================================================================
    # Formula:
    # 1. Safety Stock = Z * std_dev * sqrt(Lead_Time)
    #    (Ensures buffer against delivery delays and demand spikes)
    # 2. Recommended Inventory Level = Predicted Demand + Safety Stock
    # 3. Reorder Quantity = Predicted Demand + Safety Stock - Current Inventory
    # ========================================================================

    # Calculate Safety Stock
    safety_stock = int(round(SERVICE_LEVEL_Z * std_daily_demand * np.sqrt(lead_time)))
    safety_stock = max(5, safety_stock)  # Sensible minimum buffer

    # Recommended Inventory Level for the planning period
    # Note: We scale predicted demand to the lead time window + forecast cycle
    recommended_inventory = total_predicted_demand + safety_stock

    # Reorder Quantity
    raw_reorder = total_predicted_demand + safety_stock - current_inventory
    reorder_quantity = max(0, int(raw_reorder))

    # Determine Reorder Status and Alert Level
    if reorder_quantity > 0:
        reorder_status = "Reorder Required"
        if current_inventory <= safety_stock:
            alert_level = "Critical Stock"
            alert_badge = "critical"
            alert_icon = "🔴"
        else:
            alert_level = "Reorder Soon"
            alert_badge = "warning"
            alert_icon = "🟠"
    else:
        reorder_status = "Stock Sufficient"
        alert_level = "Stock Sufficient"
        alert_badge = "success"
        alert_icon = "🟢"

    return {
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "price": price,
        "current_inventory": current_inventory,
        "lead_time_days": lead_time,
        "forecast_days": days,
        "historical_dates": hist_dates,
        "historical_sales": [int(x) for x in hist_units],
        "forecast_dates": [d.strftime("%Y-%m-%d") for d in future_dates],
        "forecast_values": forecast_values,
        "total_predicted_demand": total_predicted_demand,
        "avg_daily_demand": round(avg_daily_demand, 1),
        "safety_stock": safety_stock,
        "recommended_inventory": recommended_inventory,
        "reorder_quantity": reorder_quantity,
        "reorder_status": reorder_status,
        "alert_level": alert_level,
        "alert_badge": alert_badge,
        "alert_icon": alert_icon
    }


# ============================================================================
# 5. INVENTORY AGGREGATIONS & OVERVIEW
# ============================================================================

def get_dashboard_summary():
    """
    Computes overall inventory KPIs and metrics for the dashboard view.
    """
    df = load_and_clean_data()
    products = df["Product_ID"].unique()

    # Get latest snapshot for each product
    latest_snapshot = df.sort_values("Date").groupby("Product_ID").last().reset_index()

    total_products = len(products)
    total_inventory = int(latest_snapshot["Inventory_Level"].sum())
    total_units_sold = int(df["Units_Sold"].sum())
    total_sales_revenue = float((df["Units_Sold"] * df["Price"]).sum())

    # Calculate 30-day recommendations across all products
    recommendations = []
    total_predicted_30d = 0
    reorder_required_count = 0
    critical_stock_count = 0

    for pid in products:
        rec = forecast_demand(pid, days=30)
        recommendations.append(rec)
        total_predicted_30d += rec["total_predicted_demand"]
        if rec["reorder_status"] == "Reorder Required":
            reorder_required_count += 1
        if rec["alert_badge"] == "critical":
            critical_stock_count += 1

    # Sort recommendations by criticality (Critical first, then warning, then success)
    priority_order = {"critical": 0, "warning": 1, "success": 2}
    recommendations.sort(key=lambda x: (priority_order.get(x["alert_badge"], 3), -x["reorder_quantity"]))

    return {
        "total_products": total_products,
        "total_inventory": total_inventory,
        "total_units_sold": total_units_sold,
        "total_sales_revenue": round(total_sales_revenue, 2),
        "total_predicted_30d": total_predicted_30d,
        "reorder_required_count": reorder_required_count,
        "critical_stock_count": critical_stock_count,
        "recommendations": recommendations
    }


def get_analytics_charts_data():
    """
    Aggregates data for dashboard visualizations:
    - Overall sales trend over time (monthly)
    - Category-wise sales
    - Top selling products
    - Inventory vs Recommended by product
    """
    df = load_and_clean_data()

    # 1. Monthly sales trend
    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")
    monthly_trend = df.groupby("YearMonth")["Units_Sold"].sum().to_dict()

    # 2. Category sales
    cat_sales = df.groupby("Category")["Units_Sold"].sum().to_dict()

    # 3. Top selling products
    top_products_df = df.groupby(["Product_Name", "Category"])["Units_Sold"].sum().reset_index()
    top_products_df = top_products_df.sort_values("Units_Sold", ascending=False).head(8)
    top_products = {
        "names": top_products_df["Product_Name"].tolist(),
        "units": top_products_df["Units_Sold"].tolist()
    }

    return {
        "monthly_trend": monthly_trend,
        "category_sales": cat_sales,
        "top_products": top_products
    }


if __name__ == "__main__":
    print("[INFO] Running standalone forecasting module test...")
    train_forecasting_model()
    test_result = forecast_demand("P101", days=14)
    print(f"[TEST] Forecast for {test_result['product_name']}:")
    print(f"       Current Inventory: {test_result['current_inventory']}")
    print(f"       Predicted Demand (14d): {test_result['total_predicted_demand']}")
    print(f"       Safety Stock: {test_result['safety_stock']}")
    print(f"       Recommended Inventory: {test_result['recommended_inventory']}")
    print(f"       Reorder Qty: {test_result['reorder_quantity']}")
    print(f"       Status: {test_result['reorder_status']} [{test_result['alert_level']}]")
