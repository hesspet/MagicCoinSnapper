const EXPERT_MODE_KEY = 'mcs.expertMode';

export function getExpertMode() {
    return localStorage.getItem(EXPERT_MODE_KEY) === 'true';
}

export function setExpertMode(enabled) {
    localStorage.setItem(EXPERT_MODE_KEY, enabled ? 'true' : 'false');
}
