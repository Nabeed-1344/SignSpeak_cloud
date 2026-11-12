
"""Collect ASL alphabet training samples for SignSpeak.

Run:
    python collect_data.py

Press A-Z to collect samples for a letter.
Press ESC to quit.

Each letter collects 200 valid hand-landmark samples.
"""

import csv
import os
import string
import time

import cv2

from camera import Camera
from features import NUM_FEATURES
from hand_tracker import HandTracker


DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "landmarks.csv")

SAMPLES_PER_LETTER = 200
COUNTDOWN_SECONDS = 3

FONT = cv2.FONT_HERSHEY_SIMPLEX


def load_counts():

    counts = {letter: 0 for letter in string.ascii_uppercase}

    if os.path.exists(DATA_FILE):

        with open(DATA_FILE, newline="") as file:

            for row in csv.reader(file):

                if (
                    len(row) == NUM_FEATURES + 1
                    and row[0] in counts
                ):
                    counts[row[0]] += 1

    return counts


def main():

    os.makedirs(DATA_DIR, exist_ok=True)

    camera = Camera()
    tracker = HandTracker()

    counts = load_counts()

    target = None
    start_at = 0.0
    recorded = 0

    try:

        with open(DATA_FILE, "a", newline="") as file:

            writer = csv.writer(file)

            while True:

                frame = camera.read()

                if frame is None:

                    print(
                        "Camera unavailable. "
                        "Close other applications using the webcam."
                    )
                    break

                features = tracker.process(frame)

                now = time.monotonic()

                message = "Press A-Z to record a letter | ESC = quit"

                if target:

                    if now < start_at:

                        remaining = int(start_at - now) + 1

                        message = (
                            f"Get ready for {target}: {remaining}"
                        )

                    else:

                        message = (
                            f"Recording {target}: "
                            f"{recorded}/{SAMPLES_PER_LETTER}"
                        )

                        if features is not None:

                            if len(features) == NUM_FEATURES:

                                writer.writerow(
                                    [target] +
                                    [f"{value:.6f}" for value in features]
                                )

                                recorded += 1
                                counts[target] += 1

                            else:

                                print("Invalid feature count. Sample skipped.")

                        else:

                            message += " - No hand detected"

                        if recorded >= SAMPLES_PER_LETTER:

                            file.flush()

                            print(
                                f"Saved {recorded} samples for {target}. "
                                f"Total: {counts[target]}"
                            )

                            target = None

                cv2.putText(
                    frame,
                    message,
                    (10, 30),
                    FONT,
                    0.65,
                    (0, 255, 0),
                    2
                )

                done = " ".join(
                    f"{letter}:{count}"
                    for letter, count in counts.items()
                    if count
                )

                cv2.putText(
                    frame,
                    done[-70:] or "No samples collected yet",
                    (10, 465),
                    FONT,
                    0.5,
                    (255, 255, 255),
                    1
                )

                cv2.imshow("SignSpeak - Data Collection", frame)

                key = cv2.waitKey(1) & 0xFF

                if key == 27:
                    break

                if (
                    target is None
                    and 97 <= key <= 122
                ):

                    target = chr(key).upper()
                    recorded = 0

                    start_at = (
                        time.monotonic() + COUNTDOWN_SECONDS
                    )

                    print(f"Preparing to collect {target}...")

    finally:

        camera.release()
        tracker.close()
        cv2.destroyAllWindows()

        print("Data collection stopped.")
        print("Run python train_model.py after collecting your samples.")


if __name__ == "__main__":

    assert NUM_FEATURES == 42

    main()
