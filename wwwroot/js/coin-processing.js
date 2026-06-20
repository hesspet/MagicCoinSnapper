let onnxSessionPromise = null;

export async function extractCoinFromDataUrl(dataUrl) {
    const image = await loadImage(dataUrl);
    const display = fitToMax(image.width, image.height, 1400);
    const imageCanvas = document.createElement('canvas');
    imageCanvas.width = display.width;
    imageCanvas.height = display.height;
    imageCanvas.getContext('2d', { willReadFrequently: true }).drawImage(image, 0, 0, display.width, display.height);

    const proposal = await createProposal(imageCanvas);
    const cutout = createCutout(imageCanvas, proposal.maskCanvas, proposal.metadata);

    return {
        dataUrl: cutout.dataUrl,
        usedOnnx: proposal.usedOnnx,
        confidence: proposal.confidence,
        width: cutout.width,
        height: cutout.height,
        message: proposal.usedOnnx ? 'Muenze per ONNX freigestellt.' : 'Muenze per Heuristik freigestellt. ONNX-Modell fehlt noch.'
    };
}

async function createProposal(imageCanvas) {
    const onnx = await tryCreateOnnxMask(imageCanvas);
    if (onnx) return onnx;

    const heuristic = createHeuristicMask(imageCanvas);
    return {
        usedOnnx: false,
        confidence: heuristic.confidence,
        maskCanvas: heuristic.maskCanvas,
        metadata: heuristic.metadata
    };
}

async function tryCreateOnnxMask(imageCanvas) {
    const session = await getOnnxSession();
    if (!session) return null;

    try {
        const size = 512;
        const inputCanvas = document.createElement('canvas');
        inputCanvas.width = size;
        inputCanvas.height = size;
        const inputCtx = inputCanvas.getContext('2d', { willReadFrequently: true });
        inputCtx.drawImage(imageCanvas, 0, 0, size, size);
        const imageData = inputCtx.getImageData(0, 0, size, size).data;
        const tensorData = new Float32Array(1 * 3 * size * size);

        for (let i = 0, p = 0; i < imageData.length; i += 4, p++) {
            tensorData[p] = imageData[i] / 255;
            tensorData[size * size + p] = imageData[i + 1] / 255;
            tensorData[2 * size * size + p] = imageData[i + 2] / 255;
        }

        const inputName = session.inputNames[0];
        const output = await session.run({ [inputName]: new window.__mcsOrt.Tensor('float32', tensorData, [1, 3, size, size]) });
        const outputTensor = output[session.outputNames[0]];
        const maskCanvas = tensorToMaskCanvas(outputTensor, imageCanvas.width, imageCanvas.height);
        const metadata = analyzeMask(maskCanvas);

        return { usedOnnx: true, confidence: 0.9, maskCanvas, metadata };
    } catch {
        return null;
    }
}

async function getOnnxSession() {
    if (onnxSessionPromise) return await onnxSessionPromise;

    onnxSessionPromise = (async () => {
        const modelUrl = new URL('models/coin-segmentation.onnx', document.baseURI).toString();
        const response = await fetch(modelUrl, { method: 'HEAD', cache: 'no-cache' }).catch(() => null);
        if (!response || !response.ok) return null;

        const ort = await import(new URL('vendor/onnxruntime-web/ort.all.min.mjs', document.baseURI).toString());
        window.__mcsOrt = ort;
        ort.env.wasm.numThreads = 1;
        ort.env.wasm.wasmPaths = new URL('vendor/onnxruntime-web/', document.baseURI).toString();
        return await ort.InferenceSession.create(modelUrl, { executionProviders: ['wasm'] });
    })().catch(() => null);

    return await onnxSessionPromise;
}

function tensorToMaskCanvas(tensor, width, height) {
    const data = tensor.data;
    const dims = tensor.dims;
    const sourceWidth = dims[dims.length - 1] || 512;
    const sourceHeight = dims[dims.length - 2] || 512;
    const small = document.createElement('canvas');
    small.width = sourceWidth;
    small.height = sourceHeight;
    const ctx = small.getContext('2d');
    const imageData = ctx.createImageData(sourceWidth, sourceHeight);
    const offset = data.length >= sourceWidth * sourceHeight * 2 ? sourceWidth * sourceHeight : 0;

    for (let i = 0; i < sourceWidth * sourceHeight; i++) {
        const v = data[offset + i] > 0.5 ? 255 : 0;
        imageData.data[i * 4] = 255;
        imageData.data[i * 4 + 1] = 255;
        imageData.data[i * 4 + 2] = 255;
        imageData.data[i * 4 + 3] = v;
    }

    ctx.putImageData(imageData, 0, 0);
    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = width;
    maskCanvas.height = height;
    maskCanvas.getContext('2d').drawImage(small, 0, 0, width, height);
    return maskCanvas;
}

function createHeuristicMask(imageCanvas) {
    const width = imageCanvas.width;
    const height = imageCanvas.height;
    const ctx = imageCanvas.getContext('2d', { willReadFrequently: true });
    const data = ctx.getImageData(0, 0, width, height).data;
    const cx0 = width / 2;
    const cy0 = height / 2;
    let sum = 0;
    let wx = 0;
    let wy = 0;
    const points = [];
    const step = Math.max(2, Math.round(Math.min(width, height) / 280));

    for (let y = step; y < height - step; y += step) {
        for (let x = step; x < width - step; x += step) {
            const i = (y * width + x) * 4;
            const ix = (y * width + x + step) * 4;
            const iy = ((y + step) * width + x) * 4;
            const gradient = Math.abs(luma(data, i) - luma(data, ix)) + Math.abs(luma(data, i) - luma(data, iy));
            const centerWeight = Math.max(0.05, 1 - Math.hypot((x - cx0) / width, (y - cy0) / height) * 1.65);
            const weight = gradient * centerWeight;

            if (weight > 18) {
                sum += weight;
                wx += x * weight;
                wy += y * weight;
                points.push({ x, y });
            }
        }
    }

    const cx = sum > 0 ? wx / sum : cx0;
    const cy = sum > 0 ? wy / sum : cy0;
    const distances = points
        .map(p => Math.hypot(p.x - cx, p.y - cy))
        .filter(d => d > Math.min(width, height) * 0.06)
        .sort((a, b) => a - b);
    const radius = clamp(percentile(distances, 0.68) || Math.min(width, height) * 0.22, Math.min(width, height) * 0.12, Math.min(width, height) * 0.38);
    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = width;
    maskCanvas.height = height;
    const maskCtx = maskCanvas.getContext('2d');
    maskCtx.fillStyle = '#ffffff';
    maskCtx.beginPath();
    maskCtx.arc(cx, cy, radius, 0, Math.PI * 2);
    maskCtx.fill();

    return {
        confidence: points.length ? 0.45 : 0.25,
        maskCanvas,
        metadata: { cx, cy, rx: radius, ry: radius }
    };
}

function analyzeMask(maskCanvas) {
    const ctx = maskCanvas.getContext('2d', { willReadFrequently: true });
    const { width, height } = maskCanvas;
    const data = ctx.getImageData(0, 0, width, height).data;
    let minX = width;
    let minY = height;
    let maxX = 0;
    let maxY = 0;
    let count = 0;
    let sx = 0;
    let sy = 0;

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            if (data[(y * width + x) * 4 + 3] > 127) {
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
                sx += x;
                sy += y;
                count++;
            }
        }
    }

    if (!count) {
        const r = Math.min(width, height) * 0.22;
        return { cx: width / 2, cy: height / 2, rx: r, ry: r };
    }

    return {
        cx: sx / count,
        cy: sy / count,
        rx: Math.max(8, (maxX - minX) / 2),
        ry: Math.max(8, (maxY - minY) / 2)
    };
}

function createCutout(imageCanvas, maskCanvas, metadata) {
    const meta = metadata || analyzeMask(maskCanvas);
    const pad = Math.max(meta.rx, meta.ry) * 0.08;
    const sx = clamp(meta.cx - meta.rx - pad, 0, imageCanvas.width);
    const sy = clamp(meta.cy - meta.ry - pad, 0, imageCanvas.height);
    const sw = clamp(meta.rx * 2 + pad * 2, 1, imageCanvas.width - sx);
    const sh = clamp(meta.ry * 2 + pad * 2, 1, imageCanvas.height - sy);
    const size = Math.max(128, Math.round(Math.max(sw, sh)));
    const output = document.createElement('canvas');
    output.width = size;
    output.height = size;
    const out = output.getContext('2d');
    out.clearRect(0, 0, size, size);
    out.drawImage(imageCanvas, sx, sy, sw, sh, 0, 0, size, size);
    out.globalCompositeOperation = 'destination-in';
    out.beginPath();
    out.arc(size / 2, size / 2, size * 0.47, 0, Math.PI * 2);
    out.fillStyle = '#ffffff';
    out.fill();
    out.globalCompositeOperation = 'source-over';

    return { dataUrl: output.toDataURL('image/png'), width: size, height: size };
}

function loadImage(src) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error('Bild konnte nicht geladen werden.'));
        image.src = src;
    });
}

function fitToMax(width, height, maxSide) {
    const scale = Math.min(1, maxSide / Math.max(width, height));
    return { width: Math.round(width * scale), height: Math.round(height * scale) };
}

function luma(data, index) {
    return data[index] * 0.299 + data[index + 1] * 0.587 + data[index + 2] * 0.114;
}

function percentile(values, p) {
    if (!values.length) return 0;
    return values[Math.min(values.length - 1, Math.max(0, Math.floor(values.length * p)))];
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}
