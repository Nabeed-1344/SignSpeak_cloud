(() => {
  // static/js/images.js
  (function() {
    "use strict";
    const API_URL = "https://nkxmop6p8b.execute-api.ap-southeast-2.amazonaws.com/prod/status/images";
    const AUTH_STORAGE_PREFIX = "oidc.user:";
    const fileInput = document.getElementById("image-file");
    const uploadButton = document.getElementById("image-upload-button");
    const statusText = document.getElementById("image-upload-status");
    const preview = document.getElementById("uploaded-image");
    if (!fileInput || !uploadButton || !statusText || !preview) {
      console.error("SignSpeak image upload elements were not found.");
      return;
    }
    function getIdToken() {
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && key.startsWith(AUTH_STORAGE_PREFIX)) {
          try {
            const user = JSON.parse(sessionStorage.getItem(key));
            if (user && user.id_token && user.expires_at > Math.floor(Date.now() / 1e3)) {
              return user.id_token;
            }
          } catch (error) {
            console.error("Unable to read sign-in session:", error);
          }
        }
      }
      return null;
    }
    function setStatus(message) {
      statusText.textContent = message;
    }
    uploadButton.addEventListener("click", async function() {
      const file = fileInput.files[0];
      if (!file) {
        setStatus("Please select an image first.");
        return;
      }
      if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
        setStatus("Please select a JPG, PNG, or WebP image.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setStatus("Image size must be 10 MB or less.");
        return;
      }
      const idToken = getIdToken();
      if (!idToken) {
        setStatus("Please sign in with Google before uploading.");
        return;
      }
      uploadButton.disabled = true;
      preview.hidden = true;
      setStatus("Preparing your secure upload...");
      try {
        const filename = file.name.replace(/\.jpg$/i, ".jpeg");
        const uploadResponse = await fetch(`${API_URL}?filename=${encodeURIComponent(filename)}`, {
          method: "POST",
          headers: {
            Authorization: idToken
          }
        });
        if (!uploadResponse.ok) {
          throw new Error(`Upload preparation failed (${uploadResponse.status}).`);
        }
        const uploadData = await uploadResponse.json();
        setStatus("Uploading image to secure storage...");
        const s3Response = await fetch(uploadData.uploadUrl, {
          method: "PUT",
          headers: {
            "Content-Type": file.type
          },
          body: file
        });
        if (!s3Response.ok) {
          throw new Error(`S3 upload failed (${s3Response.status}).`);
        }
        setStatus("Retrieving your image...");
        const viewResponse = await fetch(`${API_URL}?key=${encodeURIComponent(uploadData.key)}`, {
          method: "GET",
          headers: {
            Authorization: idToken
          }
        });
        if (!viewResponse.ok) {
          throw new Error(`Image retrieval failed (${viewResponse.status}).`);
        }
        const viewData = await viewResponse.json();
        preview.onload = function() {
          preview.hidden = false;
          setStatus("Image uploaded successfully!");
        };
        preview.onerror = function() {
          setStatus("Image uploaded, but its preview could not be displayed.");
        };
        preview.src = viewData.viewUrl;
      } catch (error) {
        console.error("Image upload error:", error);
        setStatus(error.message || "Something went wrong. Please try again.");
      } finally {
        uploadButton.disabled = false;
      }
    });
  })();
})();
