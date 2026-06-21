import { getSelectedModelDescriptor } from './model-registry.js';

let onnxSessionPromise = null;
let onnxSessionModelId = null;

export async function extractCoinFromDataUrl(dataUrl, options = {}) {
    const debugEnabled = !!options?.debug;
    const image = await loadImage(dataUrl);
    const display = fitToMax(image.width, image.height, 1400);
    const imageCanvas = document.createElement('canvas');
    imageCanvas.width = display.width;
    imageCanvas.height = display.height;
    imageCanvas.getContext('2d', { willReadFrequently: true }).drawImage(image, 0, 0, display.width, display.height);

    const proposal = await createProposal(imageCanvas);
    const cutout = createCutout(imageCanvas, proposal.maskCanvas, proposal.metadata);
    const debug = debugEnabled ? createDebugInfo(proposal, imageCanvas, cutout.geometry) : null;

    return {
        dataUrl: cutout.dataUrl,
        usedOnnx: proposal.usedOnnx,
        confidence: proposal.confidence,
        width: cutout.width,
        height: cutout.height,
        modelDisplayName: proposal.modelDisplayName ?? null,
        debug,
        message: proposal.usedOnnx
            ? `Münze mit ${proposal.modelDisplayName ?? 'ONNX'} freigestellt.`
            : 'Münze per Heuristik freigestellt.'
    };
}

async function createProposal(imageCanvas) {
    const onnx = await tryCreateOnnxMask(imageCanvas);
    if (onnx?.maskCanvas) return onnx;

    const heuristic = createHeuristicMask(imageCanvas);
    return {
        usedOnnx: false,
        confidence: heuristic.confidence,
        maskCanvas: heuristic.maskCanvas,
        metadata: heuristic.metadata,
        modelId: onnx?.modelId ?? null,
        modelDisplayName: onnx?.modelDisplayName ?? null,
        modelPath: onnx?.modelPath ?? null,
        modelUrl: onnx?.modelUrl ?? null,
        threshold: onnx?.threshold ?? null,
        onnxError: onnx?.onnxError ?? null,
        fallbackReason: onnx?.fallbackReason ?? 'Kein ONNX-Modell verfügbar.'
    };
}

async function tryCreateOnnxMask(imageCanvas) {
    const activeModel = await getOnnxSession();
    const descriptor = activeModel?.descriptor ?? null;
    const threshold = Number.isFinite(descriptor?.output?.threshold) ? descriptor.output.threshold : 0.5;
    const baseDebug = {
        modelId: descriptor?.id ?? null,
        modelDisplayName: descriptor?.displayName ?? null,
        modelPath: descriptor?.path ?? null,
        modelUrl: descriptor?.url ?? null,
        threshold
    };

    if (!activeModel?.session || !descriptor) {
        return {
            usedOnnx: false,
            ...baseDebug,
            onnxError: activeModel?.onnxError ?? null,
            fallbackReason: activeModel?.fallbackReason ?? 'ONNX-Modell nicht verfügbar.'
        };
    }

    const { session } = activeModel;

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
        const maskCanvas = tensorToMaskCanvas(outputTensor, imageCanvas.width, imageCanvas.height, threshold);
        const metadata = analyzeMask(maskCanvas);

        return { usedOnnx: true, confidence: 0.9, maskCanvas, metadata, ...baseDebug, onnxError: null, fallbackReason: null };
    } catch (error) {
        return {
            usedOnnx: false,
            ...baseDebug,
            onnxError: formatError(error),
            fallbackReason: 'ONNX-Inferenz fehlgeschlagen, Heuristik verwendet.'
        };
    }
}

async function getOnnxSession() {
    const descriptor = await getSelectedModelDescriptor();
    if (!descriptor) {
        resetOnnxSession();
        return { session: null, descriptor: null, onnxError: null, fallbackReason: 'Kein ONNX-Modell ausgewählt oder gefunden.' };
    }

    if (onnxSessionPromise && onnxSessionModelId === descriptor.id) {
        const result = await onnxSessionPromise;
        return result.session
            ? { session: result.session, descriptor, onnxError: null, fallbackReason: null }
            : { session: null, descriptor, onnxError: result.onnxError, fallbackReason: result.fallbackReason };
    }

    resetOnnxSession();
    onnxSessionModelId = descriptor.id;
    onnxSessionPromise = (async () => {
        try {
            const modelUrl = descriptor.url;
            const response = await fetch(modelUrl, { method: 'HEAD', cache: 'no-cache' }).catch(error => ({ __mcsError: error }));
            if (response?.__mcsError) {
                return { session: null, onnxError: formatError(response.__mcsError), fallbackReason: 'ONNX-Modell konnte nicht geprüft werden, Heuristik verwendet.' };
            }

            if (!response || !response.ok) {
                const status = response ? `${response.status} ${response.statusText}`.trim() : 'keine Antwort';
                return { session: null, onnxError: `Modell nicht erreichbar (${status}).`, fallbackReason: 'ONNX-Modell konnte nicht geladen werden, Heuristik verwendet.' };
            }

            const ort = await import(new URL('vendor/onnxruntime-web/ort.all.min.mjs', document.baseURI).toString());
            window.__mcsOrt = ort;
            ort.env.wasm.numThreads = 1;
            ort.env.wasm.wasmPaths = new URL('vendor/onnxruntime-web/', document.baseURI).toString();
            const session = await ort.InferenceSession.create(modelUrl, { executionProviders: ['wasm'] });
            return { session, onnxError: null, fallbackReason: null };
        } catch (error) {
            return { session: null, onnxError: formatError(error), fallbackReason: 'ONNX-Modell konnte nicht geladen werden, Heuristik verwendet.' };
        }
    })();

    const result = await onnxSessionPromise;
    return result.session
        ? { session: result.session, descriptor, onnxError: null, fallbackReason: null }
        : { session: null, descriptor, onnxError: result.onnxError, fallbackReason: result.fallbackReason };
}

function resetOnnxSession() {
    const previousSessionPromise = onnxSessionPromise;
    if (previousSessionPromise) {
        previousSessionPromise.then(result => result?.session?.release?.()).catch(() => { });
    }

    onnxSessionPromise = null;
    onnxSessionModelId = null;
}

function tensorToMaskCanvas(tensor, width, height, threshold) {
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
        const v = data[offset + i] > threshold ? 255 : 0;
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

function createDebugInfo(proposal, imageCanvas, finalGeometry) {
    const stats = getMaskStats(proposal.maskCanvas);
    return {
        usedOnnx: proposal.usedOnnx,
        modelId: proposal.modelId ?? null,
        modelDisplayName: proposal.modelDisplayName ?? null,
        modelPath: proposal.modelPath ?? null,
        modelUrl: proposal.modelUrl ?? null,
        threshold: proposal.threshold ?? null,
        confidence: proposal.confidence,
        maskPixelCount: stats.pixelCount,
        maskCoverage: stats.coverage,
        finalMaskMode: finalGeometry?.mode ?? null,
        onnxError: proposal.onnxError ?? null,
        fallbackReason: proposal.fallbackReason ?? null,
        maskPreviewDataUrl: createMaskPreviewDataUrl(imageCanvas, proposal.maskCanvas, finalGeometry)
    };
}

function getMaskStats(maskCanvas) {
    const ctx = maskCanvas.getContext('2d', { willReadFrequently: true });
    const { width, height } = maskCanvas;
    const data = ctx.getImageData(0, 0, width, height).data;
    let pixelCount = 0;

    for (let i = 3; i < data.length; i += 4) {
        if (data[i] > 127) {
            pixelCount++;
        }
    }

    return { pixelCount, coverage: pixelCount / (width * height) };
}

function createMaskPreviewDataUrl(imageCanvas, maskCanvas, finalGeometry) {
    const preview = document.createElement('canvas');
    preview.width = imageCanvas.width;
    preview.height = imageCanvas.height;
    const previewCtx = preview.getContext('2d', { willReadFrequently: true });
    previewCtx.drawImage(imageCanvas, 0, 0);

    const maskCtx = maskCanvas.getContext('2d', { willReadFrequently: true });
    const maskData = maskCtx.getImageData(0, 0, maskCanvas.width, maskCanvas.height).data;
    const overlayCanvas = document.createElement('canvas');
    overlayCanvas.width = preview.width;
    overlayCanvas.height = preview.height;
    const overlayCtx = overlayCanvas.getContext('2d');
    const overlay = overlayCtx.createImageData(preview.width, preview.height);

    for (let i = 0; i < maskData.length; i += 4) {
        if (maskData[i + 3] > 127) {
            overlay.data[i] = 255;
            overlay.data[i + 1] = 178;
            overlay.data[i + 2] = 72;
            overlay.data[i + 3] = 110;
        }
    }

    overlayCtx.putImageData(overlay, 0, 0);
    previewCtx.drawImage(overlayCanvas, 0, 0);

    if (finalGeometry && !finalGeometry.isFallback) {
        const lineWidth = Math.max(2, Math.round(Math.max(preview.width, preview.height) / 350));
        const fontSize = Math.max(14, Math.round(Math.max(preview.width, preview.height) / 45));
        previewCtx.save();
        previewCtx.strokeStyle = '#24d6ff';
        previewCtx.lineWidth = lineWidth;
        previewCtx.beginPath();
        previewCtx.ellipse(finalGeometry.cx, finalGeometry.cy, finalGeometry.rx, finalGeometry.ry, 0, 0, Math.PI * 2);
        previewCtx.stroke();
        previewCtx.font = `${fontSize}px sans-serif`;
        previewCtx.textBaseline = 'top';
        previewCtx.fillStyle = 'rgba(0, 0, 0, 0.65)';
        previewCtx.fillRect(8, 8, fontSize * 10.5, fontSize * 1.6);
        previewCtx.fillStyle = '#ffffff';
        previewCtx.fillText('raw mask + final ellipse', 14, 12);
        previewCtx.restore();
    }

    return preview.toDataURL('image/png');
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
    const pixelCount = width * height;
    const visited = new Uint8Array(pixelCount);
    const queue = new Int32Array(pixelCount);
    let best = null;
    let componentCount = 0;

    for (let start = 0; start < pixelCount; start++) {
        if (visited[start] || data[start * 4 + 3] <= 127) continue;

        componentCount++;
        let head = 0;
        let tail = 0;
        let minX = width;
        let minY = height;
        let maxX = 0;
        let maxY = 0;
        let count = 0;
        let sx = 0;
        let sy = 0;

        visited[start] = 1;
        queue[tail++] = start;

        while (head < tail) {
            const p = queue[head++];
            const x = p % width;
            const y = (p - x) / width;
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x);
            maxY = Math.max(maxY, y);
            sx += x;
            sy += y;
            count++;

            if (x > 0) tail = enqueueMaskPixel(p - 1, data, visited, queue, tail);
            if (x < width - 1) tail = enqueueMaskPixel(p + 1, data, visited, queue, tail);
            if (y > 0) tail = enqueueMaskPixel(p - width, data, visited, queue, tail);
            if (y < height - 1) tail = enqueueMaskPixel(p + width, data, visited, queue, tail);
        }

        if (!best || count > best.count) {
            best = { minX, minY, maxX, maxY, count, sx, sy };
        }
    }

    if (!best) {
        const r = Math.min(width, height) * 0.22;
        return { cx: width / 2, cy: height / 2, rx: r, ry: r, isEmpty: true };
    }

    return {
        cx: (best.minX + best.maxX) / 2,
        cy: (best.minY + best.maxY) / 2,
        centroidX: best.sx / best.count,
        centroidY: best.sy / best.count,
        rx: Math.max(8, (best.maxX - best.minX + 1) / 2),
        ry: Math.max(8, (best.maxY - best.minY + 1) / 2),
        minX: best.minX,
        minY: best.minY,
        maxX: best.maxX,
        maxY: best.maxY,
        componentCount,
        mainComponentPixelCount: best.count,
        isEmpty: false
    };
}

function enqueueMaskPixel(p, data, visited, queue, tail) {
    if (!visited[p] && data[p * 4 + 3] > 127) {
        visited[p] = 1;
        queue[tail++] = p;
    }

    return tail;
}

function createCutout(imageCanvas, maskCanvas, metadata) {
    const meta = analyzeMask(maskCanvas);

    if (meta.isEmpty) {
        return createFallbackCutout(imageCanvas, metadata || meta);
    }

    const geometry = createFinalEllipseGeometry(meta, imageCanvas);
    const pad = Math.max(2, Math.round(Math.max(geometry.rx, geometry.ry) * 0.08));
    const sx = Math.max(0, Math.floor(geometry.cx - geometry.rx - pad));
    const sy = Math.max(0, Math.floor(geometry.cy - geometry.ry - pad));
    const ex = Math.min(imageCanvas.width, Math.ceil(geometry.cx + geometry.rx + pad));
    const ey = Math.min(imageCanvas.height, Math.ceil(geometry.cy + geometry.ry + pad));
    const sw = Math.max(1, ex - sx);
    const sh = Math.max(1, ey - sy);
    const output = document.createElement('canvas');
    output.width = sw;
    output.height = sh;
    const out = output.getContext('2d');
    out.clearRect(0, 0, sw, sh);
    out.drawImage(imageCanvas, sx, sy, sw, sh, 0, 0, sw, sh);
    out.globalCompositeOperation = 'destination-in';
    out.beginPath();
    out.ellipse(geometry.cx - sx, geometry.cy - sy, geometry.rx, geometry.ry, 0, 0, Math.PI * 2);
    out.fillStyle = '#ffffff';
    out.fill();
    out.globalCompositeOperation = 'source-over';

    return { dataUrl: output.toDataURL('image/png'), width: sw, height: sh, geometry };
}

function createFinalEllipseGeometry(meta, imageCanvas) {
    const minSide = Math.min(imageCanvas.width, imageCanvas.height);
    const averageRadius = Math.max(8, (meta.rx + meta.ry) / 2);
    const ratioLimit = 1.38;
    let rx = clamp(meta.rx, averageRadius / ratioLimit, averageRadius * ratioLimit);
    let ry = clamp(meta.ry, averageRadius / ratioLimit, averageRadius * ratioLimit);
    const inflate = 1.08;
    rx = clamp(rx * inflate, minSide * 0.06, imageCanvas.width / 2);
    ry = clamp(ry * inflate, minSide * 0.06, imageCanvas.height / 2);

    return {
        cx: clamp(meta.cx, rx, imageCanvas.width - rx),
        cy: clamp(meta.cy, ry, imageCanvas.height - ry),
        rx,
        ry,
        mode: 'ellipse-from-main-mask-component',
        isFallback: false
    };
}

function createFallbackCutout(imageCanvas, metadata) {
    const r = Math.min(imageCanvas.width, imageCanvas.height) * 0.22;
    const meta = metadata || { cx: imageCanvas.width / 2, cy: imageCanvas.height / 2, rx: r, ry: r };
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

    return {
        dataUrl: output.toDataURL('image/png'),
        width: size,
        height: size,
        geometry: { cx: meta.cx, cy: meta.cy, rx: meta.rx, ry: meta.ry, mode: 'fallback-circle', isFallback: true }
    };
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

function formatError(error) {
    if (!error) return null;
    if (typeof error === 'string') return error;
    return error.message || error.name || String(error);
}
