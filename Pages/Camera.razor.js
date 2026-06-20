import { extractCoinFromDataUrl } from '../js/coin-processing.js';
import { getSelectedModelDescriptor } from '../js/model-registry.js';

let stream = null;
let video = null;

export async function init(videoElementId) {
    video = document.getElementById(videoElementId);
    if (!video) {
        throw new Error('Video-Element nicht gefunden');
    }
    video.setAttribute('playsinline', '');
    video.setAttribute('autoplay', '');
    video.setAttribute('muted', '');

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia wird in diesem Browser nicht unterstützt.');
    }

    stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false
    });
    video.srcObject = stream;
    await video.play();
}

export function capture() {
    if (!video || !video.videoWidth || !video.videoHeight) {
        throw new Error('Video nicht bereit');
    }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/png');
}

export async function extractCoin(dataUrl) {
    return await extractCoinFromDataUrl(dataUrl);
}

export async function getActiveModelName() {
    const descriptor = await getSelectedModelDescriptor();
    return descriptor?.displayName ?? null;
}

export function stop() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    if (video) {
        video.srcObject = null;
    }
}

export async function downloadFromStream(streamRef, filename, contentType) {
    try {
        const buf = await streamRef.arrayBuffer();
        const blob = new Blob([buf], { type: contentType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.download = filename;
        a.href = url;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        document.body.removeChild(a);
    } finally {
        streamRef.dispose();
    }
}
