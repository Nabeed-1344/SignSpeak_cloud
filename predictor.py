
"""Letter prediction and sentence building for SignSpeak.

How a sentence is formed
------------------------
* Every frame, the model predicts a letter and confidence.
* A letter is added after being held steadily for HOLD_SECONDS.
* Once typed, the same letter cannot be typed again until the
  hand has been released for RELEASE_SECONDS.
* Brief prediction-confidence fluctuations do not unlock a typed letter.
* If no hand is detected for AUTO_SPACE_SECONDS, a space is added.
* Repeated letters (e.g. LL) require releasing and showing the
  same gesture again.
"""

import os
import threading
import time

import numpy as np


# ---------------- Configuration ----------------

MODEL_PATH = "model.pkl"

CONF_THRESHOLD = 0.70
HOLD_SECONDS = 1.0
RELEASE_SECONDS = 0.5
AUTO_SPACE_SECONDS = 2.0

MAX_TEXT_LENGTH = 200


class Predictor:

    def __init__(self, model=None, model_path=MODEL_PATH,
                 clock=time.monotonic):

        self._lock = threading.Lock()
        self._clock = clock

        # Load trained machine learning model
        self.model = model

        if self.model is None and os.path.exists(model_path):
            import joblib
            self.model = joblib.load(model_path)

        # Current prediction information
        self.text = ""
        self.letter = None
        self.confidence = 0.0
        self.hand = False

        # Gesture hold tracking
        self._candidate = None
        self._since = 0.0

        # Prevent repeated letters from one continuous gesture
        self._locked = False

        # Track hand release
        self._release_since = None
        self._no_hand_since = None

        # Prevent repeated automatic spaces
        self._auto_space_added = False

    # ------------------------------------------------
    # Process each webcam frame
    # ------------------------------------------------

    def update(self, features):

        """Process hand features and update the sentence.

        features: 42-number array from HandTracker, or None.
        """

        now = self._clock()

        with self._lock:

            self.hand = features is not None

            letter = None
            conf = 0.0

            # Get prediction from trained model
            if features is not None and self.model is not None:

                proba = self.model.predict_proba([features])[0]

                i = int(np.argmax(proba))

                conf = float(proba[i])

                if conf >= CONF_THRESHOLD:
                    letter = str(self.model.classes_[i])

            self.letter = letter
            self.confidence = conf

            # ----------------------------------------
            # HAND NOT DETECTED
            # ----------------------------------------

            if features is None:

                if self._no_hand_since is None:
                    self._no_hand_since = now

                if self._release_since is None:
                    self._release_since = now

                # Unlock only after a sufficient release
                if now - self._release_since >= RELEASE_SECONDS:

                    self._candidate = None
                    self._locked = False

                # Automatically add one space after absence
                if (
                    now - self._no_hand_since >= AUTO_SPACE_SECONDS
                    and not self._auto_space_added
                ):

                    self._append(" ")
                    self._auto_space_added = True

                return

            # ----------------------------------------
            # HAND DETECTED
            # ----------------------------------------

            self._no_hand_since = None
            self._release_since = None
            self._auto_space_added = False

            # ----------------------------------------
            # UNCERTAIN PREDICTION
            # ----------------------------------------

            if letter is None:

                # Do not unlock an already typed letter
                if not self._locked:
                    self._candidate = None

                return

            # ----------------------------------------
            # NEW GESTURE DETECTED
            # ----------------------------------------

            if letter != self._candidate:

                self._candidate = letter
                self._since = now

                self._locked = False

            # ----------------------------------------
            # HOLD-TO-TYPE
            # ----------------------------------------

            elif (
                not self._locked
                and now - self._since >= HOLD_SECONDS
            ):

                self._append(letter)

                # Lock until the hand is released
                self._locked = True

    # ------------------------------------------------
    # Add text to sentence
    # ------------------------------------------------

    def _append(self, ch):

        if len(self.text) >= MAX_TEXT_LENGTH:
            return

        # Prevent leading and consecutive spaces
        if ch == " " and (
            not self.text or self.text.endswith(" ")
        ):
            return

        self.text += ch

    # ------------------------------------------------
    # Sentence editing controls
    # ------------------------------------------------

    def apply_action(self, action):

        """Apply space, backspace or clear action."""

        with self._lock:

            if action == "space":

                self._append(" ")

            elif action == "backspace":

                self.text = self.text[:-1]

            elif action == "clear":

                self.text = ""

            else:

                return False

            return True

    # ------------------------------------------------
    # Return current application state
    # ------------------------------------------------

    def state(self):

        now = self._clock()

        with self._lock:

            if self._candidate is None:

                progress = 0.0

            elif self._locked:

                progress = 1.0

            else:

                progress = min(
                    (now - self._since) / HOLD_SECONDS,
                    1.0
                )

            return {

                "letter": self.letter,

                "confidence": round(
                    self.confidence, 2
                ),

                "progress": round(
                    progress, 2
                ),

                "hand": self.hand,

                "text": self.text,

                "model_ready": self.model is not None

            }
