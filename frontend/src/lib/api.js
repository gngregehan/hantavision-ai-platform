const API_BASE = import.meta.env.VITE_API_BASE_URL
  || (typeof window !== 'undefined' && window.location.hostname.endsWith('onrender.com')
    ? 'https://hantavision-ai-api.onrender.com'
    : 'http://127.0.0.1:8000');
const SESSION_KEY = 'hantavision.session';

export function loadSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY));
  } catch {
    return null;
  }
}

export function saveSession(session) {
  if (!session) {
    localStorage.removeItem(SESSION_KEY);
    return;
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body,
  });
  if (!response.ok) {
    let detail = 'İstek tamamlanamadı.';
    try {
      const error = await response.json();
      detail = error.detail || detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

export function login(payload) {
  return request('/api/auth/login', { method: 'POST', body: payload });
}

export function register(payload) {
  return request('/api/auth/register', { method: 'POST', body: payload });
}

export function uploadAnalysis(file, token) {
  const form = new FormData();
  form.append('file', file);
  return request('/api/analyses', { method: 'POST', body: form, token });
}

export function listAnalyses(token, includeAll = false) {
  return request(`/api/analyses?include_all=${includeAll ? 'true' : 'false'}`, { token });
}

export function getPerformance(token) {
  return request('/api/admin/model-performance', { token });
}

export function getOverview(token) {
  return request('/api/admin/overview', { token });
}

export function getResearchEvidence() {
  return request('/api/research/evidence');
}

export function getModelStatus() {
  return request('/api/model-status');
}

export function assistantChat(payload) {
  return request('/api/assistant/chat', { method: 'POST', body: payload });
}

export async function downloadReport(analysisId, token) {
  const response = await fetch(`${API_BASE}/api/analyses/${analysisId}/report.pdf`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    let detail = 'PDF rapor indirilemedi.';
    try {
      const error = await response.json();
      detail = error.detail || detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }
  return response.blob();
}
