"""
generate_dataset.py
--------------------
Generates a realistic, clean, and comprehensive historical sales dataset
for the Inventory Demand Forecasting System.

Dataset Columns:
- Date: Date of recorded sales (YYYY-MM-DD)
- Product_ID: Unique identifier for the product
- Product_Name: Display name of the product
- Category: Product category
- Units_Sold: Daily units sold (Demand target)
- Price: Unit selling price (USD)
- Inventory_Level: Current stock in warehouse
- Lead_Time_Days: Days needed from supplier order to stock arrival
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_sales_data(output_file="data/sales_data.csv", seed=42):
    np.random.seed(seed)
    
    # Define realistic product catalog with specific baseline demand & lead time
    products = [
        {"id": "P101", "name": "Wireless Ergonomic Mouse", "category": "Peripherals", "price": 29.99, "base_demand": 28, "lead_time": 5, "min_stock": 20, "max_stock": 180},
        {"id": "P102", "name": "RGB Mechanical Keyboard", "category": "Peripherals", "price": 79.99, "base_demand": 18, "lead_time": 7, "min_stock": 15, "max_stock": 120},
        {"id": "P103", "name": "USB-C 7-in-1 Hub Adapter", "category": "Accessories", "price": 39.99, "base_demand": 22, "lead_time": 6, "min_stock": 25, "max_stock": 140},
        {"id": "P104", "name": "27-inch 4K IPS Monitor", "category": "Electronics", "price": 329.99, "base_demand": 9, "lead_time": 14, "min_stock": 10, "max_stock": 60},
        {"id": "P105", "name": "1080p HD Streaming Webcam", "category": "Electronics", "price": 54.99, "base_demand": 16, "lead_time": 7, "min_stock": 12, "max_stock": 90},
        {"id": "P106", "name": "Noise Cancelling Headphones", "category": "Audio", "price": 149.99, "base_demand": 14, "lead_time": 10, "min_stock": 10, "max_stock": 80},
        {"id": "P107", "name": "Waterproof Bluetooth Speaker", "category": "Audio", "price": 49.99, "base_demand": 20, "lead_time": 5, "min_stock": 18, "max_stock": 110},
        {"id": "P108", "name": "Cardioid Studio Condenser Mic", "category": "Audio", "price": 89.99, "base_demand": 11, "lead_time": 8, "min_stock": 8, "max_stock": 65},
        {"id": "P109", "name": "1TB High-Speed Portable SSD", "category": "Storage", "price": 109.99, "base_demand": 15, "lead_time": 9, "min_stock": 14, "max_stock": 85},
        {"id": "P110", "name": "20000mAh Fast Power Bank", "category": "Accessories", "price": 34.99, "base_demand": 25, "lead_time": 5, "min_stock": 20, "max_stock": 150},
        {"id": "P111", "name": "Ergonomic Lumbar Office Chair", "category": "Furniture", "price": 199.99, "base_demand": 7, "lead_time": 16, "min_stock": 5, "max_stock": 45},
        {"id": "P112", "name": "Dual Motor Electric Standing Desk", "category": "Furniture", "price": 379.99, "base_demand": 5, "lead_time": 20, "min_stock": 4, "max_stock": 35},
        {"id": "P113", "name": "Heavy-Duty Dual Monitor Arm", "category": "Furniture", "price": 49.99, "base_demand": 12, "lead_time": 7, "min_stock": 10, "max_stock": 70},
        {"id": "P114", "name": "Laptop Privacy Screen Protector", "category": "Accessories", "price": 24.99, "base_demand": 19, "lead_time": 4, "min_stock": 15, "max_stock": 100},
        {"id": "P115", "name": "Braided 100W USB-C Cable 2-Pack", "category": "Accessories", "price": 14.99, "base_demand": 35, "lead_time": 4, "min_stock": 30, "max_stock": 220}
    ]

    # Date range: 365 days (1 full year of historical records)
    start_date = datetime(2025, 1, 1)
    date_list = [start_date + timedelta(days=i) for i in range(365)]
    
    rows = []

    for prod in products:
        # Dynamic inventory tracker for realistic simulation
        curr_inventory = np.random.randint(int(prod["min_stock"] * 1.5), int(prod["max_stock"] * 0.9))

        for single_date in date_list:
            day_of_week = single_date.weekday()  # Monday=0, Sunday=6
            month = single_date.month

            # Realistic factors:
            # 1. Weekend boost (Fri, Sat, Sun sales are 20-35% higher)
            weekend_factor = 1.25 if day_of_week in [4, 5, 6] else 1.0

            # 2. Seasonality / Holiday boost (Q4 November/December e-commerce holiday season + July mid-year sale)
            seasonality = 1.0
            if month in [11, 12]:
                seasonality = 1.45  # Q4 holiday shopping surge
            elif month == 7:
                seasonality = 1.20  # Summer Prime / Tech sales surge
            elif month in [1, 2]:
                seasonality = 0.88  # Post-holiday cooldown

            # 3. Random noise
            noise = np.random.normal(0, prod["base_demand"] * 0.18)

            # Calculate daily units sold
            expected_demand = prod["base_demand"] * weekend_factor * seasonality + noise
            units_sold = max(0, int(round(expected_demand)))

            # Simulate inventory flow:
            # Decrement by units sold
            curr_inventory = max(0, curr_inventory - units_sold)

            # Replenishment cycle: If stock drops below threshold, simulate incoming order delivery
            if curr_inventory <= prod["min_stock"]:
                restock_amt = np.random.randint(int(prod["max_stock"] * 0.7), prod["max_stock"])
                curr_inventory += restock_amt

            rows.append({
                "Date": single_date.strftime("%Y-%m-%d"),
                "Product_ID": prod["id"],
                "Product_Name": prod["name"],
                "Category": prod["category"],
                "Units_Sold": units_sold,
                "Price": prod["price"],
                "Inventory_Level": curr_inventory,
                "Lead_Time_Days": prod["lead_time"]
            })

    df = pd.DataFrame(rows)
    
    # Ensure target directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save clean CSV
    df.to_csv(output_file, index=False)
    print(f"[SUCCESS] Generated dataset successfully: '{output_file}' with {len(df)} rows across {len(products)} products.")
    return df

if __name__ == "__main__":
    generate_sales_data()
