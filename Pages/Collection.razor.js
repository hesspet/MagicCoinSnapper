const DB_NAME = 'magiccoinsnapper-raw-images';
const DB_VERSION = 1;
const STORE_NAME = 'rawImages';

export async function saveRawImage(metadata, dataUrl) {
    const sampleMetadata = metadata || {};
    const imageBlob = await dataUrlToBlob(dataUrl);
    const dimensions = await getImageDimensions(dataUrl);
    const now = new Date().toISOString();
    const id = sampleMetadata.id || `raw-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    const sample = {
        id,
        source: sampleMetadata.source || 'collection',
        contentType: imageBlob.type || sampleMetadata.contentType || 'image/png',
        sizeBytes: imageBlob.size,
        width: dimensions.width,
        height: dimensions.height,
        createdAt: now,
        notes: sampleMetadata.notes || ''
    };

    const db = await openDb();
    await putSample(db, { ...sample, imageBlob });
    return sample;
}

export async function listRawImages() {
    const db = await openDb();
    const all = await requestToPromise(db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll());
    return all
        .map(toPublicSample)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
}

export async function deleteRawImage(id) {
    const db = await openDb();
    await requestToPromise(db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(id));
}

export async function exportRawImages() {
    const db = await openDb();
    const samples = await requestToPromise(db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll());
    if (!samples.length) {
        return { count: 0, exportedAt: new Date().toISOString(), samples: [] };
    }

    const JSZip = await loadJsZip();
    const zip = new JSZip();
    const publicSamples = [];

    for (let index = 0; index < samples.length; index++) {
        const sample = samples[index];
        const extension = getExtension(sample.contentType);
        const name = `sample-${String(index + 1).padStart(4, '0')}${extension}`;
        const path = `images/${name}`;
        zip.file(path, sample.imageBlob);
        publicSamples.push({ ...toPublicSample(sample), image: path, tags: [] });
    }

    const exportedAt = new Date().toISOString();
    zip.file('metadata.json', JSON.stringify({
        schemaVersion: 'mcs-raw-images-v1',
        datasetId: `raw-${Date.now().toString(36)}`,
        exportedAt,
        source: 'MagicCoinSnapper PWA',
        samples: publicSamples
    }, null, 2));

    const blob = await zip.generateAsync({ type: 'blob' });
    downloadBlob(blob, `mcs-raw-images-${new Date().toISOString().slice(0, 10)}.zip`);
    return { count: samples.length, exportedAt, samples: publicSamples };
}

function toPublicSample(sample) {
    return {
        id: sample.id,
        source: sample.source,
        contentType: sample.contentType,
        sizeBytes: sample.sizeBytes,
        width: sample.width,
        height: sample.height,
        createdAt: sample.createdAt,
        notes: sample.notes
    };
}

async function loadJsZip() {
    if (!window.JSZip) {
        await import(new URL('vendor/jszip/jszip.min.js', document.baseURI).toString());
    }
    if (!window.JSZip) {
        throw new Error('JSZip wurde nicht gefunden. Bitte npm install ausfuehren.');
    }
    return window.JSZip;
}

function openDb() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'id' });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function putSample(db, sample) {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put(sample);
    return transactionToPromise(tx);
}

function requestToPromise(request) {
    return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function transactionToPromise(tx) {
    return new Promise((resolve, reject) => {
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(tx.error);
    });
}

async function dataUrlToBlob(dataUrl) {
    return await (await fetch(dataUrl)).blob();
}

function getImageDimensions(dataUrl) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
        image.onerror = () => reject(new Error('Bild konnte nicht gelesen werden.'));
        image.src = dataUrl;
    });
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.download = filename;
    a.href = url;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    document.body.removeChild(a);
}

function getExtension(contentType) {
    if (contentType === 'image/jpeg') return '.jpg';
    if (contentType === 'image/png') return '.png';
    return '.png';
}
