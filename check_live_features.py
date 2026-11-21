import pandas as pd
import numpy as np

df = pd.read_csv("data/landmarks.csv")

labels = df.iloc[:, 0].astype(str).to_numpy()
X = df.iloc[:, 1:].astype(float).to_numpy()

live = np.array([
    0, 0, 0.1892, -0.1086, 0.3455, -0.2646,
    0.4714, -0.3427, 0.5892, -0.4095, 0.268, -0.6121,
    0.3692, -0.853, 0.4842, -0.8499, 0.5741, -0.7764,
    0.1998, -0.6217, 0.3209, -0.907, 0.4586, -0.8886,
    0.5554, -0.7932, 0.1241, -0.5966, 0.2376, -0.8657,
    0.3832, -0.8575, 0.4934, -0.783, 0.0479, -0.532,
    0.1595, -0.6914, 0.2863, -0.7422, 0.4003, -0.7521
])

distances = np.linalg.norm(X - live, axis=1)
nearest = np.argsort(distances)[:15]

print("\n15 CLOSEST TRAINING SAMPLES")
print("---------------------------")

for i in nearest:
    print(f"Label: {labels[i]} | Distance: {distances[i]:.4f}")
