import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Load the dataset
df = pd.read_csv("inventory_demand_forecasting.csv")

# Convert Date to datetime
df["Date"] = pd.to_datetime(df["Date"])

# Sort by date
df = df.sort_values("Date")

# Display basic information
print("First 5 rows:")
print(df.head())

print("\nDataset shape:")
print(df.shape)

print("\nMissing values:")
print(df.isnull().sum())

# Create a numerical day feature
df["Day"] = (df["Date"] - df["Date"].min()).dt.days

# Features and target
X = df[["Day"]]
y = df["Demand"]

# Train the Linear Regression model
model = LinearRegression()
model.fit(X, y)

# Predict demand
df["Predicted_Demand"] = model.predict(X)

# Display results
print("\nActual vs Predicted Demand:")
print(df[["Date", "Demand", "Predicted_Demand"]].tail(10))

# Plot actual and predicted demand
plt.figure(figsize=(12, 6))

plt.plot(
    df["Date"],
    df["Demand"],
    label="Actual Demand",
    color="blue"
)

plt.plot(
    df["Date"],
    df["Predicted_Demand"],
    label="Predicted Demand",
    color="red"
)

plt.xlabel("Date")
plt.ylabel("Demand")
plt.title("Inventory Demand Forecasting")
plt.legend()
plt.grid(True)

plt.show()