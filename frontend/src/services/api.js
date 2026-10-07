const API_BASE = '/api';

// Helper to get auth headers
const getHeaders = (isFormData = false) => {
  const token = localStorage.getItem('feedbackpulse_token');
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  return headers;
};

export const api = {
  // --- Auth ---
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  async signup(fullName, email, password) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Signup failed');
    }
    return res.json();
  },

  async getCurrentUser() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Not authenticated');
    return res.json();
  },

  // --- Existing API ---
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch system health');
    return res.json();
  },

  async listDatasets() {
    const res = await fetch(`${API_BASE}/datasets`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load datasets');
    return res.json();
  },

  async uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/reviews/upload`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload CSV file');
    }
    return res.json();
  },

  async analyzeDataset(payload) {
    const res = await fetch(`${API_BASE}/reviews/analyze`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to analyze reviews');
    }
    return res.json();
  },

  async getDashboard(datasetId = null) {
    const url = datasetId ? `${API_BASE}/dashboard?dataset_id=${datasetId}` : `${API_BASE}/dashboard`;
    const res = await fetch(url, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load dashboard metrics');
    return res.json();
  },

  async getIssues(datasetId = null, severity = null, isEmerging = null) {
    const params = new URLSearchParams();
    if (datasetId) params.append('dataset_id', datasetId);
    if (severity) params.append('severity', severity);
    if (isEmerging !== null && isEmerging !== undefined) params.append('is_emerging', isEmerging);
    
    const url = `${API_BASE}/issues?${params.toString()}`;
    const res = await fetch(url, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load issues');
    return res.json();
  },

  async getIssue(issueId) {
    const res = await fetch(`${API_BASE}/issues/${issueId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load issue details');
    return res.json();
  },

  async getIssueEvidence(issueId, limit = 20) {
    const res = await fetch(`${API_BASE}/issues/${issueId}/evidence?limit=${limit}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load issue evidence');
    return res.json();
  },

  async getIssueBrief(issueId) {
    const targetId = issueId || 0;
    const res = await fetch(`${API_BASE}/issues/${targetId}/brief`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to generate PM Brief');
    return res.json();
  },

  async getReviews(params = {}) {
    const searchParams = new URLSearchParams(params);
    const res = await fetch(`${API_BASE}/reviews?${searchParams.toString()}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load reviews');
    return res.json();
  },

  // --- Intelligence API ---
  async getIssueIntelligence(issueId) {
    const res = await fetch(`${API_BASE}/intelligence/${issueId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load issue intelligence');
    return res.json();
  },

  async getDashboardIntelligence(datasetId) {
    const res = await fetch(`${API_BASE}/intelligence/dashboard/${datasetId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load dashboard intelligence');
    return res.json();
  },

  async submitRLFeedback(issueId, datasetId, actionTaken, reward) {
    const res = await fetch(`${API_BASE}/intelligence/feedback`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ issue_id: issueId, dataset_id: datasetId, action_taken: actionTaken, reward }),
    });
    if (!res.ok) throw new Error('Failed to submit RL feedback');
    return res.json();
  }
};
