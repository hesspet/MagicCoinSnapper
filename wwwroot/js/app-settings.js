const EXPERT_MODE_KEY = 'mcs.expertMode';
const SELECTED_MODEL_ID_KEY = 'mcs.selectedModelId';

export function getExpertMode() {
    return localStorage.getItem(EXPERT_MODE_KEY) === 'true';
}

export function setExpertMode(enabled) {
    localStorage.setItem(EXPERT_MODE_KEY, enabled ? 'true' : 'false');
}

export function getSelectedModelId() {
    const value = localStorage.getItem(SELECTED_MODEL_ID_KEY);
    return value && value.trim() ? value : null;
}

export function setSelectedModelId(modelId) {
    if (modelId && modelId.trim()) {
        localStorage.setItem(SELECTED_MODEL_ID_KEY, modelId);
        return;
    }

    localStorage.removeItem(SELECTED_MODEL_ID_KEY);
}
