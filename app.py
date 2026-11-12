"""SignSpeak: live webcam feed, hand landmarks, ASL letter prediction and
sentence building.

Run locally:  python app.py   then open http://127.0.0.1:5000

Before the first run you need a trained model:
    python collect_data.py
    python train_model.py
"""
import cv2
from flask import Flask, Response, jsonify, render_template

from camera import Camera
from hand_tracker import HandTracker
from predictor import Predictor

app = Flask(__name__)
tracker = HandTracker()
predictor = Predictor()  # loads model.pkl if it exists

FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_overlay(frame, s):
    """Draw the current letter, hold-progress bar and sentence on the video."""
    h = frame.shape[0]
    if not s["model_ready"]:
        cv2.putText(frame, "No model: run collect_data.py + train_model.py",
                    (10, 30), FONT, 0.6, (0, 0, 255), 2)
        return
    label = s["letter"] or ("?" if s["hand"] else "")
    cv2.putText(frame, label, (20, 75), FONT, 2.2, (0, 255, 0), 4)
    cv2.rectangle(frame, (20, 90), (220, 102), (255, 255, 255), 1)
    cv2.rectangle(frame, (20, 90), (20 + int(200 * s["progress"]), 102),
                  (0, 255, 0), -1)
    cv2.putText(frame, s["text"][-35:], (20, h - 20), FONT, 0.8, (255, 255, 255), 2)


def process_frame(frame):
    """Runs on every video frame (called from Camera.stream)."""
    features = tracker.process(frame)   # also draws the hand landmarks
    predictor.update(features)
    draw_overlay(frame, predictor.state())
    return frame


camera = Camera(processor=process_frame)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(camera.stream(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera_status")
def camera_status():
    """Lets the page show whether the webcam is working."""
    return jsonify(available=camera.is_available())


@app.route("/prediction")
def prediction():
    """Current letter, confidence, hold progress and the sentence so far."""
    return jsonify(predictor.state())


@app.route("/sentence/<action>", methods=["POST"])
def sentence_action(action):
    """action: space | backspace | clear"""
    if not predictor.apply_action(action):
        return jsonify(error="unknown action"), 400
    return jsonify(predictor.state())


if __name__ == "__main__":
    # threaded=True so the video stream does not block other requests
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
