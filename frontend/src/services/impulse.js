import { apiFetch } from './api';

export async function getImpulse() {
  const resp = await apiFetch('/api/v1/impulse');
  if (!resp.ok) throw new Error('Failed to get impulse');
  return resp.json();
}

export async function setImpulse(weights) {
  const resp = await apiFetch('/api/v1/impulse', {
    method: 'PUT',
    body: JSON.stringify({ weights }),
  });
  if (!resp.ok) throw new Error('Failed to set impulse');
  return resp.json();
}

export async function setImpulsePreset(preset) {
  const resp = await apiFetch('/api/v1/impulse/preset', {
    method: 'POST',
    body: JSON.stringify({ preset }),
  });
  if (!resp.ok) throw new Error('Failed to set impulse preset');
  return resp.json();
}

const PRESET_LABELS = {
  strict: { label: 'Строгий', icon: '🎯' },
  balanced: { label: 'Сбалансированный', icon: '⚖️' },
  creative: { label: 'Творческий', icon: '✨' },
};

export { PRESET_LABELS };
