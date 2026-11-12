"""Webcam access for SignSpeak (Sprint 1: US-01, US-08).

Wraps OpenCV's VideoCapture and yields JPEG frames for an MJPEG stream.
If no camera can be opened, a placeholder frame with a message is streamed
instead, so the web page never shows a broken image.

Sprint 2/3: an optional `processor(frame) -> frame` function can be passed in.
It is called on every frame before encoding (used for hand tracking and
prediction, see app.py).
"""
import threading
import time
import traceback

import cv2
import numpy as np

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
JPEG_QUALITY = 80


class Camera:
    """Thread-safe, lazily opened webcam."""

    def __init__(self, index=CAMERA_INDEX, processor=None):
        self.index = index
        self.processor = processor
        self._cap = None
        self._lock = threading.Lock()

    # ---- lifecycle -------------------------------------------------------
    def open(self):
        """Open the webcam if it is not open yet. Returns True on success."""
        with self._lock:
            if self._cap is not None and self._cap.isOpened():
                return True
            cap = cv2.VideoCapture(self.index)
            if not cap.isOpened():
                cap.release()
                self._cap = None
                return False
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self._cap = cap
            return True

    def release(self):
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None

    def is_available(self):
        return self.open()

    # ---- frames ----------------------------------------------------------
    def read(self):
        """Return one BGR frame (mirrored), or None if unavailable."""
        if not self.open():
            return None
        with self._lock:
            ok, frame = self._cap.read()
        if not ok:
            return None
        return cv2.flip(frame, 1)  # mirror so it feels natural to the user

    @staticmethod
    def placeholder(message="Camera not available"):
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)
        cv2.putText(frame, message, (60, FRAME_HEIGHT // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, "Check permissions and that no other app uses it",
                    (30, FRAME_HEIGHT // 2 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        return frame

    @staticmethod
    def encode(frame):
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        return buf.tobytes() if ok else b""

    def stream(self):
        """Generator of multipart MJPEG chunks for a Flask Response."""
        while True:
            frame = self.read()
            if frame is None:
                frame = self.placeholder()
                time.sleep(0.5)  # avoid a busy loop while the camera is down
            elif self.processor is not None:
                try:
                    frame = self.processor(frame)
                except Exception:
                    traceback.print_exc()  # show the error, keep streaming
            jpeg = self.encode(frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
