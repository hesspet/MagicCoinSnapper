window.startCamera = async function (videoElement) {
    console.log("▶️ startCamera aufgerufen");
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { ideal: "environment" } }
        });

        if (!stream) {
            console.error("❌ Kein Stream erhalten");
            return;
        }

        videoElement.srcObject = stream;
        await videoElement.play();
        console.log("✅ Kamera-Stream gestartet");
    } catch (err) {
        console.error("❌ Kamera-Zugriff verweigert:", err);
    }
};

window.captureSnapshot = function (videoElement, canvasElement) {
    console.log("📸 captureSnapshot aufgerufen");

    const ctx = canvasElement.getContext("2d");
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    ctx.drawImage(videoElement, 0, 0);

    const dataUrl = canvasElement.toDataURL("image/jpeg");
    return dataUrl;
};