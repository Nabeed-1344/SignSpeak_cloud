import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';
import './model.js';

(function () {
  'use strict';

  const video = document.getElementById('video');
  const cameraStatus = document.getElementById('status');

  const CONF_THRESHOLD = 0.7;
  const HOLD_SECONDS = 1.0;
  const RELEASE_SECONDS = 0.5;
  const AUTO_SPACE_SECONDS = 2.0;
  const MAX_TEXT_LENGTH = 200;

  let detector;
  let model;
  let stream;
  let running = false;
  let animationFrame;

  let text = '';
  let letter = null;
  let confidence = 0;
  let hand = false;

  let candidate = null;
  let candidateSince = 0;
  let locked = false;
  let releaseSince = null;
  let noHandSince = null;
  let autoSpaceAdded = false;
  let lastDebugLog = 0;
  let lastFeatureLog = 0;

  function setCameraStatus(type, message) {
    if (!cameraStatus) return;

    cameraStatus.className = 'status ' + type;
    cameraStatus.textContent = message;
  }

  function publishState(progress = 0) {
    window.dispatchEvent(
      new CustomEvent('signspeak:state', {
        detail: {
          letter,
          confidence,
          progress,
          hand,
          text,
          model_ready: Boolean(model),
        },
      })
    );
  }

  function append(character) {
    if (text.length >= MAX_TEXT_LENGTH) return;

    if (character === ' ' && (!text || text.endsWith(' '))) {
      return;
    }

    text += character;
  }

  function applyAction(action) {
    if (action === 'space') {
      append(' ');
    } else if (action === 'backspace') {
      text = text.slice(0, -1);
    } else if (action === 'clear') {
      text = '';
    } else {
      return;
    }

    publishState();
  }

  function landmarksToFeatures(landmarks) {
    const points = landmarks.map((point) => [point.x, point.y]);

    const wristX = points[0][0];
    const wristY = points[0][1];

    for (const point of points) {
      point[0] -= wristX;
      point[1] -= wristY;
    }

    let scale = 0;

    for (const point of points) {
      const distance = Math.hypot(point[0], point[1]);
      scale = Math.max(scale, distance);
    }

    if (scale > 0) {
      for (const point of points) {
        point[0] /= scale;
        point[1] /= scale;
      }
    }

    return points.flat();
  }

  function processPrediction(features, now) {
    if (!hand) {
      letter = null;
      confidence = 0;

      if (noHandSince === null) noHandSince = now;
      if (releaseSince === null) releaseSince = now;

      if (now - releaseSince >= RELEASE_SECONDS * 1000) {
        candidate = null;
        locked = false;
      }

      if (now - noHandSince >= AUTO_SPACE_SECONDS * 1000 && !autoSpaceAdded) {
        append(' ');
        autoSpaceAdded = true;
      }

      publishState();
      return;
    }

    noHandSince = null;
    releaseSince = null;
    autoSpaceAdded = false;

    const result = window.SignSpeakModel.predict(features, model);
    if (now - lastDebugLog >= 1000) {
      const ranked = model.classes
        .map((label, index) => ({
          letter: label,
          confidence: Number(result.probabilities[index].toFixed(3)),
        }))
        .sort((a, b) => b.confidence - a.confidence);

      console.log('SignSpeak Live Predictions:', ranked.slice(0, 5));
      lastDebugLog = now;
    }

    confidence = result.confidence;
    letter = confidence >= CONF_THRESHOLD ? result.letter : null;

    if (letter === null) {
      if (!locked) candidate = null;
      publishState();
      return;
    }

    if (letter !== candidate) {
      candidate = letter;
      candidateSince = now;
      locked = false;
    } else if (!locked && now - candidateSince >= HOLD_SECONDS * 1000) {
      append(letter);
      locked = true;
    }

    const progress = locked ? 1 : Math.min((now - candidateSince) / (HOLD_SECONDS * 1000), 1);

    publishState(progress);
  }

  function processFrame() {
    if (!running || !detector || video.readyState < 2) {
      if (running) animationFrame = requestAnimationFrame(processFrame);
      return;
    }

    try {
      const now = performance.now();
      const result = detector.detectForVideo(video, now);
      if (result.handednesses && result.handednesses.length > 0) {
        console.log('HAND DETECTED AS:', result.handednesses[0][0].categoryName);
      }

      hand = Boolean(result.landmarks && result.landmarks.length);

      if (hand) {
        const features = landmarksToFeatures(result.landmarks[0]);
        console.log(
          'WRIST X:',
          result.landmarks[0][0].x,
          '| INDEX FINGER TIP X:',
          result.landmarks[0][8].x
        );

        if (now - lastFeatureLog >= 3000) {
          console.log(
            'SignSpeak Live 42 Features:',
            features.map((value) => Number(value.toFixed(4)))
          );

          lastFeatureLog = now;
        }

        processPrediction(features, now);
      } else {
        letter = null;
        confidence = 0;
        processPrediction(null, now);
      }
    } catch (error) {
      console.error('SignSpeak frame error:', error);
    }

    animationFrame = requestAnimationFrame(processFrame);
  }

  async function start() {
    try {
      setCameraStatus('checking', 'Loading SignSpeak...');

      const [vision, modelResponse] = await Promise.all([
        FilesetResolver.forVisionTasks('/static/dist/wasm'),
        fetch('/static/models/sign_model_new.json'),
      ]);

      if (!modelResponse.ok) {
        throw new Error('Could not load the recognition model.');
      }

      model = await modelResponse.json();

      if (!window.SignSpeakModel) {
        throw new Error('JavaScript recognition engine not loaded.');
      }

      detector = await HandLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: '/static/models/hand_landmarker.task',
          delegate: 'CPU',
        },
        runningMode: 'VIDEO',
        numHands: 1,
        minHandDetectionConfidence: 0.6,
        minTrackingConfidence: 0.5,
      });

      stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
      });

      video.srcObject = stream;
      await video.play();

      running = true;
      setCameraStatus('ok', 'Camera is working');
      publishState();

      animationFrame = requestAnimationFrame(processFrame);
    } catch (error) {
      console.error('SignSpeak startup error:', error);

      const message =
        error.name === 'NotAllowedError'
          ? 'Camera permission denied. Allow camera access.'
          : error.name === 'NotFoundError'
            ? 'No webcam found on this device.'
            : error.message || 'Unable to start SignSpeak.';

      setCameraStatus('error', message);

      const status = document.getElementById('ss-status');
      if (status) status.textContent = message;
    }
  }

  function stop() {
    running = false;
    cancelAnimationFrame(animationFrame);

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }

    if (detector) detector.close();
  }

  window.SignSpeakBrowser = {
    applyAction,
    stop,
  };

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setCameraStatus('error', 'Browser webcam access requires HTTPS or localhost.');
    return;
  }

  start();

  window.addEventListener('beforeunload', stop);
})();
