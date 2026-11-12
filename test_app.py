"""Basic Sprint 1 checks. Run with:  python -m unittest test_app.py

These pass even on a machine without a webcam, because the app falls back
to a placeholder frame.
"""
import unittest

from app import app
from camera import Camera


class Sprint1Tests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page_loads(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"/video_feed", r.data)

    def test_camera_status_is_json(self):
        r = self.client.get("/camera_status")
        self.assertEqual(r.status_code, 200)
        self.assertIn("available", r.get_json())

    def test_video_feed_content_type(self):
        r = self.client.get("/video_feed", buffered=False)
        self.assertEqual(r.status_code, 200)
        self.assertIn("multipart/x-mixed-replace", r.content_type)
        first_chunk = next(iter(r.response))
        self.assertTrue(first_chunk.startswith(b"--frame"))
        r.close()

    def test_placeholder_encodes_to_jpeg(self):
        jpeg = Camera.encode(Camera.placeholder())
        self.assertTrue(jpeg.startswith(b"\xff\xd8"))


if __name__ == "__main__":
    unittest.main()
