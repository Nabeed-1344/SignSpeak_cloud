
import joblib
import numpy as np

model = joblib.load("model.pkl")

live = np.array([[
    0, 0, 0.1892, -0.1086, 0.3455, -0.2646,
    0.4714, -0.3427, 0.5892, -0.4095, 0.268, -0.6121,
    0.3692, -0.853, 0.4842, -0.8499, 0.5741, -0.7764,
    0.1998, -0.6217, 0.3209, -0.907, 0.4586, -0.8886,
    0.5554, -0.7932, 0.1241, -0.5966, 0.2376, -0.8657,
    0.3832, -0.8575, 0.4934, -0.783, 0.0479, -0.532,
    0.1595, -0.6914, 0.2863, -0.7422, 0.4003, -0.7521
]])

probabilities = model.predict_proba(live)[0]
ranked = sorted(
    zip(model.classes_, probabilities),
    key=lambda item: item[1],
    reverse=True
)

print("\nPYTHON MODEL PREDICTION")
for letter, confidence in ranked[:5]:
    print(f"{letter}: {confidence:.4f}")
