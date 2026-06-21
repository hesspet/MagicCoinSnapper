const EXPERT_MODE_KEY = 'mcs.expertMode';
const DESIGN_KEY = 'mcs.design';
const SELECTED_MODEL_ID_KEY = 'mcs.selectedModelId';
const SCAN_DEBUG_MODE_KEY = 'mcs.scanDebugMode';
const DARK_DESIGN = 'dark';
const LIGHT_DESIGN = 'light';

function getDesign() {
    const value = readStorage(DESIGN_KEY);
    return value === LIGHT_DESIGN || value === DARK_DESIGN ? value : DARK_DESIGN;
}

function readStorage(key) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

function writeStorage(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch {
        // Keep the in-memory UI usable if browser storage is blocked.
    }
}

function removeStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch {
        // Keep the in-memory UI usable if browser storage is blocked.
    }
}

export function applyDesign(design = getDesign()) {
    const normalizedDesign = design === LIGHT_DESIGN ? LIGHT_DESIGN : DARK_DESIGN;
    document.documentElement.dataset.theme = normalizedDesign;

    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeColor) {
        themeColor.setAttribute('content', normalizedDesign === LIGHT_DESIGN ? '#fff9ef' : '#101016');
    }
}

export function getExpertMode() {
    return readStorage(EXPERT_MODE_KEY) === 'true';
}

export function setExpertMode(enabled) {
    writeStorage(EXPERT_MODE_KEY, enabled ? 'true' : 'false');
}

export function getScanDebugMode() {
    return readStorage(SCAN_DEBUG_MODE_KEY) === 'true';
}

export function setScanDebugMode(enabled) {
    writeStorage(SCAN_DEBUG_MODE_KEY, enabled ? 'true' : 'false');
}

export function getIsDarkDesign() {
    const design = getDesign();
    applyDesign(design);
    return design === DARK_DESIGN;
}

export function setIsDarkDesign(isDarkDesign) {
    const design = isDarkDesign ? DARK_DESIGN : LIGHT_DESIGN;
    writeStorage(DESIGN_KEY, design);
    applyDesign(design);
}

export function getSelectedModelId() {
    const value = readStorage(SELECTED_MODEL_ID_KEY);
    return value && value.trim() ? value : null;
}

export function setSelectedModelId(modelId) {
    if (modelId && modelId.trim()) {
        writeStorage(SELECTED_MODEL_ID_KEY, modelId);
        return;
    }

    removeStorage(SELECTED_MODEL_ID_KEY);
}
