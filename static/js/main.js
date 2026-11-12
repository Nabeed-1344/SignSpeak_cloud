// Shows whether the webcam is working (US-08: "know the camera is working").
(function () {
  var statusEl = document.getElementById('status');

  function setStatus(cls, text) {
    statusEl.className = 'status ' + cls;
    statusEl.textContent = text;
  }

  function check() {
    fetch('/camera_status')
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data.available) {
          setStatus('ok', 'Camera is working');
        } else {
          setStatus('error', 'Camera not available - check permissions or other apps using it');
        }
      })
      .catch(function () {
        setStatus('error', 'Cannot reach the server');
      });
  }

  check();
  setInterval(check, 5000);
})();
