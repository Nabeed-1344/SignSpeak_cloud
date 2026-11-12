"""Turn MediaPipe hand landmarks into a feature vector (numpy only).

Kept separate from hand_tracker.py so it can be tested without MediaPipe.
"""
import numpy as np

NUM_LANDMARKS = 21
NUM_FEATURES = NUM_LANDMARKS * 2  # x and y for each landmark


def landmarks_to_features(landmarks):
    """21 landmarks (objects with .x and .y) -> 42 numbers.

    1. Shift so the wrist (landmark 0) is the origin  -> position independent
    2. Divide by the largest distance from the wrist  -> hand-size independent
    """
    pts = np.array([[lm.x, lm.y] for lm in landmarks], dtype=np.float32)
    pts -= pts[0]
    scale = float(np.max(np.linalg.norm(pts, axis=1)))
    if scale > 0:
        pts /= scale
    return pts.flatten()
