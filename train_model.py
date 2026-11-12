
"""Train SignSpeak's ASL alphabet classifier."""

import csv
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "data" / "landmarks.csv"
MODEL_FILE = BASE_DIR / "model.pkl"

NUM_FEATURES = 42


def load_data():

    X = []
    y = []

    if not DATA_FILE.exists():

        sys.exit(
            f"{DATA_FILE} not found. Run collect_data.py first."
        )

    with open(DATA_FILE, newline="") as file:

        reader = csv.reader(file)

        for line_number, row in enumerate(reader, start=1):

            if len(row) != NUM_FEATURES + 1:
                print(f"Skipping invalid row {line_number}")
                continue

            try:

                label = row[0].strip().upper()

                features = [
                    float(value)
                    for value in row[1:]
                ]

                if len(label) != 1 or not label.isalpha():
                    continue

                if not np.all(np.isfinite(features)):
                    continue

                X.append(features)
                y.append(label)

            except ValueError:

                print(f"Skipping malformed row {line_number}")

    if not X:

        sys.exit(
            "No valid samples found. Collect training data first."
        )

    return (
        np.asarray(X, dtype=np.float32),
        np.asarray(y)
    )


def main():

    X, y = load_data()

    counts = Counter(y)

    print("\nSamples per letter:")

    for letter, count in sorted(counts.items()):
        print(f"{letter}: {count}")

    if len(counts) < 2:

        sys.exit(
            "At least two different letters are required."
        )

    if min(counts.values()) < 20:

        sys.exit(
            "Some letters have fewer than 20 samples. "
            "Collect more balanced data before training."
        )

    if len(X) < 50:

        sys.exit("Not enough training samples.")

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # Train classifier
    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )

    print("\nTraining classifier...")

    classifier.fit(X_train, y_train)

    # Evaluate classifier
    predictions = classifier.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(
        f"\nTest accuracy: {accuracy * 100:.2f}%"
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    # Retrain using all available data
    print("\nTraining final model on all samples...")

    classifier.fit(X, y)

    joblib.dump(classifier, MODEL_FILE)

    print(f"\nModel saved successfully: {MODEL_FILE}")

    print("Restart the Flask application to load the new model.")


if __name__ == "__main__":

    main()
