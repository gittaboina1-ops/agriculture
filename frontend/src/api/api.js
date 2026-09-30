import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Attach JWT token automatically to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('agrigraph_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Intercept 401 unauthorized to clear expired session
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('agrigraph_token');
      localStorage.removeItem('agrigraph_user');
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/signup')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  signup: (userData) => api.post('/auth/signup', userData),
  getMe: () => api.get('/auth/me')
};

export const farmerAPI = {
  submitQuery: (query) => api.post('/query', { query }),
  translate: (payloadOrText, targetLanguage = 'Telugu') => {
    if (typeof payloadOrText === 'string') {
      return api.post('/translate', { text: payloadOrText, target_language: targetLanguage });
    }
    return api.post('/translate', payloadOrText);
  },
  getHistory: () => api.get('/history')
};

export const adminAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getGraph: () => api.get('/graph'),
  getSources: () => api.get('/sources'),
  getConflicts: () => api.get('/conflicts'),
  getValidation: () => api.get('/validation'),
  getDocuments: () => api.get('/admin/documents'),
  getDocumentDetails: (id) => api.get(`/admin/documents/${id}`),
  getDocumentStatus: (id) => api.get(`/admin/documents/${id}/status`),
  uploadResource: (payload) => api.post('/admin/upload', payload),
  triggerCreateGraph: (documentId) => api.post(`/admin/documents/${documentId}/create-graph`)
};

export default api;
