
"""Hand detection for SignSpeak using MediaPipe Tasks API."""

import os
import threading
import time

import cv2
import mediapipe as mp

from features import landmarks_to_features


class HandTracker:
    """Detect one hand and return its 42-number feature vector."""

    def __init__(
        self,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5
    ):
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "models",
            "hand_landmarker.task"
        )

        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Hand Landmarker model not found: {model_path}"
            )

        self._lock = threading.Lock()
        self._last_timestamp_ms = 0

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=model_path
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        self._hands = (
            mp.tasks.vision.HandLandmarker.create_from_options(options)
        )

        # Connections between the 21 hand landmarks.
        self._connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20),
            (0, 17)
        ]

    def process(self, frame_bgr, draw=True):
        """Return 42 features, or None if no hand is detected."""

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        with self._lock:
            timestamp_ms = max(
                time.monotonic_ns() // 1_000_000,
                self._last_timestamp_ms + 1
            )
            self._last_timestamp_ms = timestamp_ms

            result = self._hands.detect_for_video(
                mp_image,
                timestamp_ms
            )

        if not result.hand_landmarks:
            return None

        hand = result.hand_landmarks[0]

        if draw:
            height, width = frame_bgr.shape[:2]

            points = [
                (int(point.x * width), int(point.y * height))
                for point in hand
            ]

            for start, end in self._connections:
                cv2.line(
                    frame_bgr,
                    points[start],
                    points[end],
                    (0, 255, 0),
                    2
                )

            for point in points:
                cv2.circle(
                    frame_bgr,
                    point,
                    4,
                    (0, 0, 255),
                    -1
                )

        return landmarks_to_features(hand)

    def close(self):
        """Release the MediaPipe hand detector."""
        with self._lock:
            self._hands.close()