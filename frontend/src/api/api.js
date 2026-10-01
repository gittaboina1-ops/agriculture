import axios from 'axios';

const getApiBaseURL = () => {
  const configured = import.meta.env.VITE_API_URL;

  if (configured) {
    return configured;
  }

  if (!import.meta.env.DEV) {
    console.warn('[API] VITE_API_URL is missing in production. Falling back to localhost. This will fail on Render.');
  }

  return 'http://localhost:8000/api';
};

const api = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('agrigraph_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

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

    if (error.response?.status === 404) {
      console.error('[API] 404 Error:', {
        baseURL: api.defaults.baseURL,
        endpoint: error.config?.url,
        method: error.config?.method
      });
    } else if (error.response?.status === 500) {
      console.error('[API] 500 Error:', {
        baseURL: api.defaults.baseURL,
        endpoint: error.config?.url,
        method: error.config?.method
      });
    } else if (error.code === 'ERR_NETWORK' || !error.response) {
      console.error('[API] Network/backend unavailable:', {
        baseURL: api.defaults.baseURL,
        endpoint: error.config?.url,
        method: error.config?.method,
        message: error.message
      });
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
