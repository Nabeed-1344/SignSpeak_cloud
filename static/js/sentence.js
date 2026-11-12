/* SignSpeak - Live prediction, sentence building and speech. */

(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);

  const letterEl = $('ss-letter');
  const statusEl = $('ss-status');
  const textEl = $('ss-text');
  const holdBar = $('ss-bar');
  const confidenceBar = $('ss-confidence-bar');
  const confidenceEl = $('ss-confidence');
  const progressEl = $('ss-progress-value');
  const speechStatus = $('ss-speech-status');
  const voiceSelect = $('ss-voice');

  let lastText = '';
  let voices = [];

  // ---------------------------------------
  // Display prediction information
  // ---------------------------------------

  function render(data) {
    if (!data) return;

    letterEl.textContent = data.letter || '-';

    const confidence = Math.round((data.confidence || 0) * 100);

    const progress = Math.round((data.progress || 0) * 100);

    confidenceEl.textContent = confidence + '%';
    confidenceBar.style.width = confidence + '%';

    progressEl.textContent = progress + '%';
    holdBar.style.width = progress + '%';

    if (!data.model_ready) {
      statusEl.textContent = 'No trained model. Collect data and train the classifier.';
    } else if (!data.hand) {
      statusEl.textContent = 'Show your hand to the camera.';
    } else if (!data.letter) {
      statusEl.textContent = 'Gesture uncertain. Adjust your hand position.';
    } else if (progress >= 100) {
      statusEl.textContent = 'Letter registered. Change gesture or release your hand.';
    } else {
      statusEl.textContent = 'Hold ' + data.letter + ' steadily to register it.';
    }

    lastText = data.text || '';

    if (lastText) {
      textEl.textContent = lastText;
      textEl.classList.remove('empty');
    } else {
      textEl.textContent = 'Your sentence will appear here...';
      textEl.classList.add('empty');
    }
  }

  // ---------------------------------------
  // Retrieve backend prediction
  // ---------------------------------------

  async function pollPrediction() {
    try {
      const response = await fetch('/prediction', {
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error('Prediction request failed');
      }

      const data = await response.json();
      render(data);
    } catch {
      statusEl.textContent = 'Cannot connect to SignSpeak server.';
    } finally {
      window.setTimeout(pollPrediction, 200);
    }
  }

  // ---------------------------------------
  // Sentence editing buttons
  // ---------------------------------------

  document.querySelectorAll('button[data-a]').forEach((button) => {
    button.addEventListener('click', async () => {
      const action = button.dataset.a;

      button.disabled = true;

      try {
        const response = await fetch('/sentence/' + action, { method: 'POST' });

        if (!response.ok) {
          throw new Error('Sentence action failed');
        }

        render(await response.json());
      } catch {
        statusEl.textContent = 'Unable to update sentence. Try again.';
      } finally {
        button.disabled = false;
      }
    });
  });

  // ---------------------------------------
  // Load available browser speech voices
  // ---------------------------------------

  function loadVoices() {
    if (!('speechSynthesis' in window)) {
      speechStatus.textContent = 'Speech synthesis is not supported by this browser.';
      $('ss-speak').disabled = true;
      $('ss-stop').disabled = true;
      return;
    }

    voices = window.speechSynthesis.getVoices();

    const selectedVoice = voiceSelect.value;

    voiceSelect.innerHTML = '<option value="">Default system voice</option>';

    voices.forEach((voice, index) => {
      const option = document.createElement('option');

      option.value = String(index);
      option.textContent = voice.name + ' (' + voice.lang + ')';

      voiceSelect.appendChild(option);
    });

    if (selectedVoice && Number(selectedVoice) < voices.length) {
      voiceSelect.value = selectedVoice;
    }
  }

  if ('speechSynthesis' in window) {
    loadVoices();

    window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
  }

  // ---------------------------------------
  // Speak sentence
  // ---------------------------------------

  $('ss-speak').addEventListener('click', () => {
    const sentence = lastText.trim();

    if (!sentence) {
      speechStatus.textContent = 'Please create a sentence before speaking.';
      return;
    }

    if (!('speechSynthesis' in window)) {
      speechStatus.textContent = 'Speech is not supported by this browser.';
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(sentence);

    const selected = voiceSelect.value;

    if (selected !== '') {
      const voice = voices[Number(selected)];

      if (voice) {
        utterance.voice = voice;
      }
    }

    utterance.onstart = () => {
      speechStatus.textContent = 'Speaking your sentence...';
    };

    utterance.onend = () => {
      speechStatus.textContent = 'Finished speaking.';
    };

    utterance.onerror = (event) => {
      speechStatus.textContent = 'Speech error: ' + event.error;
    };

    window.speechSynthesis.speak(utterance);
  });

  // ---------------------------------------
  // Stop speech
  // ---------------------------------------

  $('ss-stop').addEventListener('click', () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      speechStatus.textContent = 'Speech stopped.';
    }
  });

  // Start prediction updates
  pollPrediction();
})();
