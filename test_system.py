"""
test_system.py
--------------
Automated test suite verifying all routes, forecasting logic, and data structures.
"""

from app import app
import json

def run_tests():
    print("[TEST] Running automated system tests...")
    client = app.test_client()

    # 1. Test Home Route
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"SmartStock" in res.data, "Brand name not found in home page"
    print("  [PASS] GET / (Dashboard HTML loaded)")

    # 2. Test API Summary
    res = client.get("/api/summary")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True
    assert "total_products" in data["data"]
    assert "recommendations" in data["data"]
    print(f"  [PASS] GET /api/summary (Returned {data['data']['total_products']} products)")

    # 3. Test API Forecast
    res = client.post("/api/forecast", json={"product_id": "P101", "days": 14})
    assert res.status_code == 200
    f_data = json.loads(res.data)
    assert f_data["success"] is True
    assert f_data["data"]["forecast_days"] == 14
    assert len(f_data["data"]["forecast_values"]) == 14
    print(f"  [PASS] POST /api/forecast (Predicted 14-day demand: {f_data['data']['total_predicted_demand']} units)")

    # 4. Test API Analytics
    res = client.get("/api/analytics")
    assert res.status_code == 200
    a_data = json.loads(res.data)
    assert a_data["success"] is True
    assert "monthly_trend" in a_data["data"]
    assert "category_sales" in a_data["data"]
    print("  [PASS] GET /api/analytics (Charts data retrieved)")

    # 5. Test CSV Export
    res = client.get("/api/export-report")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert b"Product ID,Product Name" in res.data
    print("  [PASS] GET /api/export-report (CSV generated and downloaded)")

    print("\n[SUCCESS] All 5 system tests passed with zero errors!")

if __name__ == "__main__":
    run_tests()
