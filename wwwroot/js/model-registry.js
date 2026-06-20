import { getSelectedModelId } from './app-settings.js';

const SCHEMA = 'mcs-model-index-v1';
const MANIFEST_PATH = 'models/manifest.json';
const LEGACY_MODEL_PATH = 'models/coin-segmentation.onnx';
const LEGACY_MODEL_ID = 'legacy-coin-segmentation';

let modelIndexPromise = null;

export async function getModelIndex() {
    if (!modelIndexPromise) {
        modelIndexPromise = loadModelIndex();
    }

    return await modelIndexPromise;
}

export async function getAvailableModels() {
    const index = await getModelIndex();
    return index.models;
}

export async function getSelectedModelDescriptor() {
    const index = await getModelIndex();
    const models = index.models;
    const selectedModelId = getSelectedModelId();
    return models.find(model => model.id === selectedModelId)
        ?? models.find(model => model.id === index.defaultModelId)
        ?? models[0]
        ?? null;
}

async function loadModelIndex() {
    const manifest = await tryLoadManifest();
    if (manifest) {
        return manifest;
    }

    return await createLegacyIndex();
}

async function tryLoadManifest() {
    const manifestUrl = new URL(MANIFEST_PATH, document.baseURI).toString();
    const response = await fetch(manifestUrl, { cache: 'no-cache' }).catch(() => null);
    if (!response || !response.ok) {
        return null;
    }

    const manifest = await response.json().catch(() => null);
    if (!manifest || manifest.schemaVersion !== SCHEMA || !Array.isArray(manifest.models)) {
        return null;
    }

    const models = manifest.models
        .map(model => normalizeModel(model, manifestUrl))
        .filter(Boolean);

    const defaultModelId = typeof manifest.defaultModelId === 'string' ? manifest.defaultModelId.trim() : '';
    if (defaultModelId) {
        models.sort((a, b) => a.id === defaultModelId ? -1 : b.id === defaultModelId ? 1 : 0);
    }

    return { schemaVersion: SCHEMA, defaultModelId, models };
}

async function createLegacyIndex() {
    if (!await exists(LEGACY_MODEL_PATH)) {
        return { schemaVersion: SCHEMA, defaultModelId: null, models: [] };
    }

    return {
        schemaVersion: SCHEMA,
        defaultModelId: LEGACY_MODEL_ID,
        models: [normalizeModel({
            id: LEGACY_MODEL_ID,
            displayName: 'Legacy-ONNX-Modell',
            description: 'Gebundeltes Standardmodell fuer die Muenzsegmentierung.',
            modelUrl: LEGACY_MODEL_PATH,
            output: { threshold: 0.5 }
        }, document.baseURI)]
    };
}

function normalizeModel(model, baseUrl) {
    const id = typeof model.id === 'string' ? model.id.trim() : '';
    const path = typeof model.modelUrl === 'string' ? model.modelUrl.trim()
        : typeof model.path === 'string' ? model.path.trim()
            : typeof model.url === 'string' ? model.url.trim()
                : '';
    if (!id || !path) {
        return null;
    }

    const threshold = Number(model.output?.threshold);

    return {
        id,
        displayName: typeof model.displayName === 'string' && model.displayName.trim() ? model.displayName.trim() : id,
        description: typeof model.description === 'string' ? model.description.trim() : '',
        version: typeof model.version === 'string' ? model.version.trim() : '',
        path,
        url: resolveModelUrl(path, baseUrl),
        output: Number.isFinite(threshold) ? { threshold } : {}
    };
}

function resolveModelUrl(path, manifestUrl) {
    if (/^[a-z][a-z0-9+.-]*:/i.test(path)) {
        return path;
    }

    if (path.startsWith('/') || path.includes('/')) {
        return new URL(path, document.baseURI).toString();
    }

    return new URL(path, manifestUrl).toString();
}

async function exists(path) {
    const url = new URL(path, document.baseURI).toString();
    const response = await fetch(url, { method: 'HEAD', cache: 'no-cache' }).catch(() => null);
    return !!response?.ok;
}
