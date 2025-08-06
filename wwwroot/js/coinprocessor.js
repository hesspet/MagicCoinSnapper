window.extractCoinFromImage = function (imageDataUrl, canvasOutId) {
    const img = new Image();
    img.onload = function () {
        if (typeof cv === 'undefined' || !cv.Mat) {
            console.error("❌ OpenCV ist nicht bereit!");
            return;
        }

        const src = cv.imread(img);
        const gray = new cv.Mat();
        cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY, 0);

        const circles = new cv.Mat();
        cv.HoughCircles(gray, circles, cv.HOUGH_GRADIENT, 1, 45, 100, 30, 30, 100);

        if (circles.rows > 0) {
            let x = circles.data32F[0];
            let y = circles.data32F[1];
            let r = circles.data32F[2];

            const ctx = document.getElementById(canvasOutId).getContext("2d");
            ctx.clearRect(0, 0, 512, 512);
            ctx.beginPath();
            ctx.arc(x, y, r, 0, 2 * Math.PI);
            ctx.clip();
            ctx.drawImage(img, 0, 0);
        } else {
            console.log("❌ Keine Münze erkannt.");
        }

        src.delete(); gray.delete(); circles.delete();
    };
    img.src = imageDataUrl;
};

window.waitForOpenCv = function () {
    return new Promise(resolve => {
        if (typeof cv === 'undefined') {
            console.error("❌ OpenCV ist nicht geladen (cv undefined)");
            resolve(false);
            return;
        }

        if (cv.Mat) {
            console.log("✅ OpenCV bereits bereit");
            resolve(true);
        } else {
            cv['onRuntimeInitialized'] = () => {
                console.log("✅ OpenCV wurde initialisiert");
                resolve(true);
            };
        }
    });
};