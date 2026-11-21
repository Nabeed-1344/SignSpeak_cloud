
import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("data/landmarks.csv")

X = df.iloc[:, 1:].to_numpy(dtype=float)
y = df.iloc[:, 0].astype(str).to_numpy()

model = joblib.load("model.pkl")
predictions = model.predict(X)

print("\nA-Z CLASSIFICATION REPORT")
print("=========================")

print(classification_report(
    y,
    predictions,
    labels=sorted(model.classes_),
    zero_division=0
))

print("\nCONFUSION MATRIX")
print("================")

matrix = confusion_matrix(
    y,
    predictions,
    labels=sorted(model.classes_)
)

print(pd.DataFrame(
    matrix,
    index=sorted(model.classes_),
    columns=sorted(model.classes_)
))
