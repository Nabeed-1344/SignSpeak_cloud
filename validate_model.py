
import csv
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

with open("data/landmarks.csv", newline="") as file:
    rows = list(csv.reader(file))

y = np.array([row[0] for row in rows])

X = np.array([
    [float(value) for value in row[1:]]
    for row in rows
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("\nTest accuracy:", round(
    accuracy_score(y_test, predictions) * 100, 2
), "%")

print("\nPer-letter results:")
print(classification_report(
    y_test,
    predictions,
    labels=sorted(set(y)),
    zero_division=0
))
