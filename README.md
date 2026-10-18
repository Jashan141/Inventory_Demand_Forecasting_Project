# SmartStock: Inventory Demand Forecasting System

An end-to-end, beginner-friendly yet production-quality **Inventory Demand Forecasting and Stock Replenishment Recommendation System** built with **Python, Machine Learning (Scikit-Learn Random Forest), Pandas, NumPy, Matplotlib, Flask, HTML5, CSS3, and JavaScript (Chart.js)**.

---

## 1. Project Overview & Business Problem

### The Problem
Retailers and warehouse operators face a chronic dilemma:
- **Overstocking**: Excessive inventory ties up working capital, increases storage, insurance, and depreciation costs, and risks product obsolescence or spoilage.
- **Understocking**: Inadequate inventory leads to stock-outs, unfulfilled customer orders, lost revenue, and damaged brand reputation.

### The Solution
**SmartStock** bridges historical point-of-sale patterns with Machine Learning regression to accurately predict future product demand across 7, 14, or 30 days. It couples this demand forecast with supplier lead times and statistical safety stock buffers to recommend the optimal **Reorder Quantity** and classify items into clear operational priorities:
- **Critical Stock**: Inventory is dangerously below safety stock.
- **Reorder Soon**: Inventory will not cover the forecasted period plus safety buffer.
- **Stock Sufficient**: Ample inventory on hand.

---

## 2. Complete Workflow Diagram

```
[ Historical Sales Data CSV ]
            │
            ▼
[ Data Cleaning & Preprocessing (Pandas, NumPy) ]
  • Missing values handling
  • Deduplication & Chronological sorting
  • Feature Engineering (Lags, 7-Day Rolling Averages, Calendar Signals)
            │
            ▼
[ Machine Learning Engine (Scikit-Learn Random Forest) ]
  • 100 Decision Trees ensemble
  • Evaluation: MAE, RMSE, and R² Score
            │
            ▼
[ Multi-Step Demand Forecasting ]
  • 7, 14, or 30-day projection per product
            │
            ▼
[ Inventory Recommendation Engine ]
  • Safety Stock Buffer = Z × σ_daily × √(Lead_Time)
  • Recommended Level  = Predicted Demand + Safety Stock
  • Reorder Quantity   = Predicted Demand + Safety Stock − Current Stock
            │
            ▼
[ Interactive Modern Web Dashboard (Flask + HTML/CSS/JS) ]
  • Real-time KPI Stat Cards
  • Chart.js Interactive Timeline Visualizations
  • Catalog Search & Category Filters
  • Matplotlib Report Gallery & CSV Export
```

---

## 3. Dataset Columns Explained

The dataset is located at `data/sales_data.csv` and contains daily historical transaction records:

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| **`Date`** | String / Date (`YYYY-MM-DD`) | The calendar date of the recorded sales record. | `2025-06-15` |
| **`Product_ID`** | Categorical (`P101`, `P102`...) | Unique alphanumeric SKU code identifying the product. | `P101` |
| **`Product_Name`** | String | Human-readable product display name. | `Wireless Ergonomic Mouse` |
| **`Category`** | Categorical | The business category the product belongs to. | `Peripherals`, `Audio`, `Electronics` |
| **`Units_Sold`** | Integer (Target Variable) | Number of units sold on that specific date. | `24` |
| **`Price`** | Float | Unit selling price in USD ($). | `29.99` |
| **`Inventory_Level`** | Integer | Warehouse stock on-hand at the end of that day. | `85` |
| **`Lead_Time_Days`** | Integer | Number of days needed from placing supplier order to delivery arrival. | `5` |

---

## 4. How the Machine Learning Model Works

### Algorithm: Random Forest Regressor
Instead of relying on a single linear line (which fails to capture complex weekend spikes and monthly holiday waves), we use **Random Forest Regression** (`sklearn.ensemble.RandomForestRegressor`):
1. **Bagging (Bootstrap Aggregation)**: The model creates 100 independent decision trees. Each tree learns from a random subset of training days and features.
2. **Non-Linear Pattern Recognition**: Trees capture non-linear relationships such as higher sales on Fridays and Saturdays, summer surges, and end-of-year holiday spikes.
3. **Overfitting Reduction**: By averaging the predictions across all 100 individual trees, the variance is greatly minimized, yielding a robust generalized model.

### Feature Engineering
Before training, raw timestamps are converted into predictive machine learning features:
- **`DayOfWeek` & `IsWeekend`**: Flags weekly purchasing rhythms (e.g. Saturdays usually have higher sales).
- **`Month` & `Quarter`**: Captures quarterly seasonality (e.g., Q4 holiday surges).
- **`DayOfYear`**: Captures yearly cyclical trends.
- **`Units_Sold_Lag_7` & `Units_Sold_Lag_14`**: Sales recorded 7 and 14 days ago (captures week-over-week momentum).
- **`Rolling_Mean_7`**: 7-day moving average demand (captures short-term sales velocity).

### Model Performance Metrics
- **Mean Absolute Error (MAE)**: ~`3.55 units` (average prediction error per product per day).
- **Root Mean Squared Error (RMSE)**: ~`5.02 units`.
- **R² Score**: `~0.857` (explains ~86% of sales variance).

---

## 5. Inventory Recommendation & Reorder Formulas

### 1. Safety Stock Formula
Safety stock acts as a protective cushion against unforeseen supplier delivery delays and sudden sales spikes:
$$\text{Safety Stock} = Z \times \sigma_{\text{daily}} \times \sqrt{\text{Lead Time}}$$
- $Z = 1.65$ represents a **95% cycle service level** from standard normal distribution.
- $\sigma_{\text{daily}}$ is the standard deviation of historical daily sales.
- $\text{Lead Time}$ is the supplier fulfillment period in days.

### 2. Recommended Inventory Level
$$\text{Recommended Inventory Level} = \text{Predicted Demand} + \text{Safety Stock}$$

### 3. Reorder Quantity Formula
$$\text{Reorder Quantity} = \text{Predicted Demand} + \text{Safety Stock} - \text{Current Inventory}$$

### 4. Alert & Status Classification Logic
- **If $\text{Reorder Quantity} > 0$**:
  - If $\text{Current Inventory} \le \text{Safety Stock}$: Status is **"Reorder Required"** with **🔴 Critical Stock** alert.
  - Else: Status is **"Reorder Required"** with **🟠 Reorder Soon** alert.
- **If $\text{Reorder Quantity} \le 0$**:
  - Reorder Quantity is clamped to `0`.
  - Status is **"Stock Sufficient"** with **🟢 Stock Sufficient** alert.

---

## 6. Project Structure

```
Inventory demand forcasting/
│
├── data/
│   └── sales_data.csv                 # Clean historical dataset (5,475 rows)
│
├── model/
│   └── forecasting_model.pkl          # Trained Random Forest model package
│
├── static/
│   ├── charts/                        # Saved Matplotlib static export plots
│   │   ├── sales_trend.png
│   │   ├── category_distribution.png
│   │   ├── top_products.png
│   │   ├── inventory_vs_recommendation.png
│   │   └── reorder_status_distribution.png
│   ├── style.css                      # Modern CSS styling (responsive)
│   └── script.js                      # Chart.js visualizations & frontend logic
│
├── templates/
│   └── index.html                     # Main interactive dashboard UI
│
├── app.py                             # Flask web server & REST API
├── forecasting.py                     # ML forecasting & inventory logic engine
├── train_model.py                     # Standalone model training script
├── generate_dataset.py                # Synthetic realistic dataset generator
├── generate_charts.py                 # Matplotlib chart rendering script
├── requirements.txt                   # Python dependencies
└── README.md                          # Project documentation
```

---

## 7. Step-by-Step Installation & Running Guide

### Prerequisites
- Python 3.9, 3.10, 3.11, 3.12, 3.13, or 3.14 installed on your system.
- VS Code or any preferred code editor.

---

### Step 1: Open the Project in VS Code
1. Open **Visual Studio Code**.
2. Click **File** > **Open Folder...**
3. Select the folder: `c:\Users\Admin\OneDrive\Desktop\Inventory demand forcasting`
4. Open the integrated terminal in VS Code (`Ctrl + ` ` or **Terminal** > **New Terminal**).

---

### Step 2: Install Required Dependencies
In your VS Code terminal, execute:
```bash
pip install -r requirements.txt
```
*This installs Flask, Scikit-Learn, Pandas, NumPy, and Matplotlib.*

---

### Step 3 (Optional): Regenerate the Dataset
If you ever want to re-create the sample dataset:
```bash
python generate_dataset.py
```

---

### Step 4: Train the Machine Learning Model
To train the Random Forest model and save it to `model/forecasting_model.pkl`:
```bash
python train_model.py
```
You will see output displaying:
```
============================================================
  INVENTORY DEMAND FORECASTING - MODEL TRAINING
============================================================
[INFO] Training Random Forest Regressor on 4395 rows; Testing on 1080 rows...
[SUCCESS] Model Trained Successfully!
          - MAE  (Mean Absolute Error):     3.55 units
          - RMSE (Root Mean Squared Error): 5.02 units
          - R2 Score:                       0.8570
[SUCCESS] Saved model package to: model/forecasting_model.pkl
```

---

### Step 5 (Optional): Generate Static Matplotlib Charts
To generate high-resolution PNG charts for reports and presentations:
```bash
python generate_charts.py
```

---

### Step 6: Start the Web Dashboard
Launch the Flask web server:
```bash
python app.py
```

You will see:
```
[INFO] Starting Inventory Demand Forecasting Web Server...
[INFO] Open your browser and navigate to: http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

---

### Step 7: Open the Dashboard in Your Browser
Open your favorite web browser (Chrome, Edge, Firefox) and navigate to:
```
http://127.0.0.1:5000
```

You will now see the live interactive dashboard!

---

## 8. Key Dashboard Features & Usage

1. **Top KPI Cards**: Displays real-time counts for Total Products, Total Inventory, 30-Day Predicted Demand, Reorder Needed, Critical Alerts, and Historical Revenue.
2. **Interactive Demand Forecaster**:
   - Choose any product from the dropdown (e.g. `P101 - Wireless Ergonomic Mouse`).
   - Select forecast horizon (`7 Days`, `14 Days`, or `30 Days`).
   - Adjust supplier lead time if desired.
   - Click **Run Demand Forecast** to view live predictions, safety stock buffer, recommended inventory level, and interactive Chart.js timeline graph.
3. **Catalog & Reorder Table**:
   - Filter by status (**All**, **Critical**, **Reorder Soon**, **Stock Sufficient**).
   - Filter by product category.
   - Instant search bar for real-time SKU and keyword filtering.
   - Click the **Forecast** action button on any row to instantly project demand for that product.
4. **Visual Analytics**:
   - Monthly sales volume trend.
   - Sales breakdown by category.
   - Top selling items.
   - Stock health distribution doughnut.
   - Matplotlib export gallery.
5. **CSV Export**: Click **Export CSV Report** on the top navigation bar to download a spreadsheet report for supply chain operations.
6. **One-Click Retrain**: Click the **Retrain Model** button in the sidebar anytime to re-evaluate the model on updated data.
