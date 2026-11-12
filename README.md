# SignSpeak - Sprint 1

Flask web app that shows a live webcam feed in the browser.

**Stories covered (11 points):** US-07 (open in browser), US-09 (served locally via Flask), US-01 (webcam access), US-08 (live feed on the page).

Not in this sprint: hand landmarks, feature vectors, model training and prediction (Sprints 2-3).

## Setup

```bash
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in Chrome or Firefox and allow camera access if asked.

## Test

```bash
python -m unittest test_app.py
```

The tests also pass on a machine with no webcam (a placeholder frame is streamed).

## Project structure

```
signspeak_sprint1/
├── app.py              Flask routes: /, /video_feed, /camera_status
├── camera.py           OpenCV webcam wrapper + MJPEG frame generator
├── templates/
│   └── index.html      Page with the live video and status badge
├── static/
│   ├── css/style.css
│   └── js/main.js      Polls /camera_status and updates the badge
├── test_app.py         Sprint 1 unit tests
├── requirements.txt
└── README.md
```

## Work split (6 members)

| # | Member | Task | Story | Files | Done when |
|---|--------|------|-------|-------|-----------|
| 1 | Member 1 | Flask skeleton, routes, local run config, folder structure | US-09 | `app.py` | `python app.py` serves the app at 127.0.0.1:5000 |
| 2 | Member 2 | Webcam capture class: open, read, release, mirror, resolution | US-01 | `camera.py` (`open`, `read`, `release`) | Frames are read from the webcam in a standalone script |
| 3 | Member 3 | MJPEG streaming: frame encoding, `/video_feed` route, placeholder frame when no camera | US-08 | `camera.py` (`stream`, `encode`, `placeholder`), `/video_feed` in `app.py` | Opening `/video_feed` directly shows live video |
| 4 | Member 4 | Page layout and styling, video element, responsive design | US-07, US-08 | `templates/index.html`, `static/css/style.css` | Page looks right in Chrome and Firefox |
| 5 | Member 5 | Camera status badge, `/camera_status` route, error messages for denied or busy camera | US-08 | `static/js/main.js`, `/camera_status` in `app.py` | Badge turns green with camera, red without |
| 6 | Member 6 | `requirements.txt`, README, unit tests, GitHub repo setup, cross-browser check, record issues for US-15 | US-07 (verify), supports US-13 | `test_app.py`, `requirements.txt`, `README.md`, `.gitignore` | Fresh venv install runs and tests pass |

**Integration order:** 1 and 2 work first, in parallel. 3 plugs into both. 4 and 5 build on the running app. 6 tests everything at the end of the week.

Replace "Member 1-6" with names. Suggested: give the camera work (2, 3) to whoever has a working webcam, and the testing role (6) to someone who can use a second OS or browser.
