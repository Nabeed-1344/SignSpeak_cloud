
"""Collect varied ASL alphabet training samples for SignSpeak."""

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
BATCH_SIZE = 40
SAMPLE_INTERVAL = 0.2
COUNTDOWN_SECONDS = 3

FONT = cv2.FONT_HERSHEY_SIMPLEX


def load_counts():
    counts = {letter: 0 for letter in string.ascii_uppercase}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="") as file:
            for row in csv.reader(file):
                if len(row) == NUM_FEATURES + 1 and row[0] in counts:
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
    batch_recorded = 0
    last_sample_at = 0.0
    waiting_for_batch = False

    try:
        with open(DATA_FILE, "a", newline="") as file:
            writer = csv.writer(file)

            while True:
                frame = camera.read()

                if frame is None:
                    print("Camera unavailable.")
                    break

                features = tracker.process(frame)
                now = time.monotonic()

                message = "Press A-Z to collect | ESC = quit"

                if target:

                    if waiting_for_batch:
                        message = (
                            f"{target}: Batch complete. "
                            "Change hand position/angle, "
                            "then press SPACE."
                        )

                    elif now < start_at:
                        remaining = int(start_at - now) + 1
                        message = (
                            f"Get ready for {target}: {remaining}"
                        )

                    else:
                        message = (
                            f"Recording {target}: "
                            f"{recorded}/{SAMPLES_PER_LETTER} "
                            f"| Batch: {batch_recorded}/{BATCH_SIZE}"
                        )

                        if features is None:
                            message += " - No hand detected"

                        elif len(features) == NUM_FEATURES:
                            if now - last_sample_at >= SAMPLE_INTERVAL:
                                writer.writerow(
                                    [target] +
                                    [f"{value:.6f}" for value in features]
                                )

                                recorded += 1
                                batch_recorded += 1
                                counts[target] += 1
                                last_sample_at = now

                                if batch_recorded >= BATCH_SIZE:
                                    file.flush()

                                    if recorded >= SAMPLES_PER_LETTER:
                                        print(
                                            f"Finished {target}: "
                                            f"{recorded} new samples. "
                                            f"Total dataset samples: "
                                            f"{counts[target]}"
                                        )
                                        target = None

                                    else:
                                        waiting_for_batch = True
                                        print(
                                            f"{target}: Completed batch. "
                                            f"{recorded}/{SAMPLES_PER_LETTER} "
                                            "samples saved."
                                        )

                        else:
                            message += " - Invalid features"

                cv2.putText(
                    frame,
                    message,
                    (10, 30),
                    FONT,
                    0.55,
                    (0, 255, 0),
                    2
                )

                instructions = (
                    "Keep the ASL sign correct; vary distance "
                    "and wrist angle between batches."
                )

                cv2.putText(
                    frame,
                    instructions,
                    (10, 60),
                    FONT,
                    0.42,
                    (255, 255, 255),
                    1
                )

                done = " ".join(
                    f"{letter}:{count}"
                    for letter, count in counts.items()
                    if count
                )

                cv2.putText(
                    frame,
                    done[-70:] or "No samples collected yet",
                    (10, frame.shape[0] - 15),
                    FONT,
                    0.45,
                    (255, 255, 255),
                    1
                )

                cv2.imshow("SignSpeak - Data Collection", frame)

                key = cv2.waitKey(1) & 0xFF

                if key == 27:
                    break

                if target is None and 97 <= key <= 122:
                    target = chr(key).upper()
                    recorded = 0
                    batch_recorded = 0
                    waiting_for_batch = False

                    start_at = (
                        time.monotonic() + COUNTDOWN_SECONDS
                    )

                    last_sample_at = 0.0

                    print(f"Preparing to collect {target}...")

                elif target is not None and waiting_for_batch and key == 32:
                    batch_recorded = 0
                    waiting_for_batch = False

                    start_at = (
                        time.monotonic() + COUNTDOWN_SECONDS
                    )

                    last_sample_at = 0.0

                    print(
                        f"Continuing {target}: "
                        f"{recorded}/{SAMPLES_PER_LETTER}"
                    )

    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()

        print("Data collection stopped.")
        print("Existing dataset samples were preserved.")
        print("Run python train_model.py after collection.")


if __name__ == "__main__":
    assert NUM_FEATURES == 42
    main()
