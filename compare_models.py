import csv
import json
import numpy as np
from sklearn.metrics import accuracy_score

DATA_FILE = "data/landmarks.csv"

OLD_MODEL = "static/models/sign_model.json"
NEW_MODEL = "static/models/sign_model_new.json"


def load_model(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def predict(features, model):
    probabilities = np.zeros(len(model["classes"]))

    for tree in model["trees"]:
        node = 0

        while tree["left"][node] != -1:
            feature_index = tree["feature"][node]

            if features[feature_index] <= tree["threshold"][node]:
                node = tree["left"][node]
            else:
                node = tree["right"][node]

        probabilities += np.array(tree["leaf_values"][node])

    probabilities /= model["n_trees"]

    return model["classes"][np.argmax(probabilities)]


def evaluate(model, X, y):
    predictions = [predict(row, model) for row in X]
    return accuracy_score(y, predictions) * 100


def main():
    with open(DATA_FILE, newline="") as file:
        rows = list(csv.reader(file))

    y = np.array([row[0] for row in rows])
    X = np.array([
        [float(value) for value in row[1:]]
        for row in rows
    ])

    old_model = load_model(OLD_MODEL)
    new_model = load_model(NEW_MODEL)

    print("Dataset samples:", len(y))
    print("\nComparing browser models...")

    old_accuracy = evaluate(old_model, X, y)
    new_accuracy = evaluate(new_model, X, y)

    print("\n========== RESULTS ==========")
    print(f"Old browser model: {old_accuracy:.2f}%")
    print(f"New browser model: {new_accuracy:.2f}%")
    print("=============================")


if __name__ == "__main__":
    main()
