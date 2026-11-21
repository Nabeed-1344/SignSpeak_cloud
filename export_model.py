
"""Export the trained SignSpeak Random Forest to browser JSON format."""

import json
from pathlib import Path

import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent

MODEL_FILE = BASE_DIR / "model.pkl"
OUTPUT_FILE = BASE_DIR / "static" / "models" / "sign_model_new.json"


def main():
    classifier = joblib.load(MODEL_FILE)

    classes = [str(label) for label in classifier.classes_]

    if len(classes) != 26 or classifier.n_features_in_ != 42:
        raise ValueError("Unexpected model classes or feature count.")

    exported_trees = []

    for estimator in classifier.estimators_:
        tree = estimator.tree_

        leaf_values = []

        for node in range(tree.node_count):
            if tree.children_left[node] == -1:
                values = tree.value[node][0].astype(float)
                total = values.sum()

                probabilities = (
                    values / total if total > 0
                    else np.zeros(len(classes))
                )

                leaf_values.append(probabilities.tolist())
            else:
                leaf_values.append(None)

        exported_trees.append({
            "left": tree.children_left.tolist(),
            "right": tree.children_right.tolist(),
            "feature": tree.feature.tolist(),
            "threshold": tree.threshold.tolist(),
            "leaf_values": leaf_values,
        })

    model_data = {
        "classes": classes,
        "n_features": int(classifier.n_features_in_),
        "n_trees": len(exported_trees),
        "trees": exported_trees,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(model_data, file, separators=(",", ":"))

    print("Export successful!")
    print("Classes:", len(classes))
    print("Trees:", len(exported_trees))
    print("Features:", classifier.n_features_in_)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
