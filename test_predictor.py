"""Tests for feature extraction and sentence building (no webcam or MediaPipe
needed). Run with:  python -m unittest test_predictor.py
"""
import unittest
from types import SimpleNamespace

import numpy as np

from features import NUM_FEATURES, landmarks_to_features
from predictor import AUTO_SPACE_SECONDS, HOLD_SECONDS, Predictor


class FakeModel:
    classes_ = np.array(["A", "B"])

    def __init__(self):
        self.proba = [0.95, 0.05]

    def predict_proba(self, X):
        return np.array([self.proba])


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


FEATURES = np.zeros(NUM_FEATURES)


class FeatureTests(unittest.TestCase):
    def _hand(self, scale=1.0, dx=0.0, dy=0.0):
        base = [(i * 0.01, i * 0.02) for i in range(21)]
        return [SimpleNamespace(x=x * scale + dx, y=y * scale + dy) for x, y in base]

    def test_length(self):
        self.assertEqual(len(landmarks_to_features(self._hand())), NUM_FEATURES)

    def test_position_and_size_independent(self):
        a = landmarks_to_features(self._hand())
        b = landmarks_to_features(self._hand(scale=2.5, dx=0.3, dy=0.1))
        np.testing.assert_allclose(a, b, atol=1e-5)


class PredictorTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.model = FakeModel()
        self.p = Predictor(model=self.model, clock=self.clock)

    def show(self, seconds, features=FEATURES, step=0.1):
        for _ in range(int(round(seconds / step))):
            self.p.update(features)
            self.clock.advance(step)

    def test_letter_typed_after_hold(self):
        self.show(HOLD_SECONDS + 0.3)
        self.assertEqual(self.p.text, "A")

    def test_short_hold_types_nothing(self):
        self.show(HOLD_SECONDS - 0.5)
        self.assertEqual(self.p.text, "")

    def test_holding_does_not_repeat(self):
        self.show(5)
        self.assertEqual(self.p.text, "A")

    def test_release_then_hold_repeats_letter(self):
        self.show(HOLD_SECONDS + 0.3)
        self.show(0.2, features=None)
        self.show(HOLD_SECONDS + 0.3)
        self.assertEqual(self.p.text, "AA")

    def test_low_confidence_is_ignored(self):
        self.model.proba = [0.5, 0.5]
        self.show(3)
        self.assertEqual(self.p.text, "")

    def test_auto_space_once(self):
        self.show(HOLD_SECONDS + 0.3)
        self.show(AUTO_SPACE_SECONDS + 2, features=None)
        self.assertEqual(self.p.text, "A ")

    def test_no_leading_space(self):
        self.show(AUTO_SPACE_SECONDS + 2, features=None)
        self.assertEqual(self.p.text, "")

    def test_actions(self):
        self.show(HOLD_SECONDS + 0.3)
        self.assertTrue(self.p.apply_action("space"))
        self.assertEqual(self.p.text, "A ")
        self.assertTrue(self.p.apply_action("backspace"))
        self.assertEqual(self.p.text, "A")
        self.assertTrue(self.p.apply_action("clear"))
        self.assertEqual(self.p.text, "")
        self.assertFalse(self.p.apply_action("explode"))

    def test_state_keys(self):
        s = self.p.state()
        for key in ("letter", "confidence", "progress", "hand", "text", "model_ready"):
            self.assertIn(key, s)

    def test_no_model(self):
        p = Predictor(model=None, model_path="does_not_exist.pkl", clock=self.clock)
        p.update(FEATURES)
        self.assertFalse(p.state()["model_ready"])


if __name__ == "__main__":
    unittest.main()
