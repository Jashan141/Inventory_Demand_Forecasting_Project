"""
train_model.py
--------------
Standalone training script for the Inventory Demand Forecasting System.

Run this script to retrain the Random Forest Regressor on historical sales data:
    python train_model.py

Outputs:
- model/forecasting_model.pkl (trained model pipeline and metadata)
- Prints MAE, RMSE, and R2 performance metrics.
"""

from forecasting import train_forecasting_model

if __name__ == "__main__":
    print("=" * 60)
    print("  INVENTORY DEMAND FORECASTING - MODEL TRAINING")
    print("=" * 60)
    
    payload = train_forecasting_model()
    metrics = payload["metrics"]
    
    print("-" * 60)
    print("Evaluation Results:")
    print(f"  * Mean Absolute Error (MAE):     {metrics['mae']} units")
    print(f"  * Root Mean Squared Error (RMSE): {metrics['rmse']} units")
    print(f"  * R-squared (R2 Score):          {metrics['r2']}")
    print("-" * 60)
    print("Top Feature Importances:")
    sorted_features = sorted(payload["feature_importances"].items(), key=lambda x: x[1], reverse=True)
    for feat, imp in sorted_features[:5]:
        print(f"  - {feat:20s}: {imp:.4f}")
    print("=" * 60)
    print("[SUCCESS] Model training complete! You can now start the web app: python app.py")
