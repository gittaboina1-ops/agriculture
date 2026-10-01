import axios from 'axios';

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    'http://localhost:8000/api',

  timeout: 30000,

  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('agrigraph_token');

    if (
      token &&
      token !== 'undefined' &&
      token !== 'null'
    ) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('agrigraph_token');
      localStorage.removeItem('agrigraph_user');

      if (
        !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/signup')
      ) {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => {
    return api.post('/auth/login', {
      email,
      password
    });
  },

  signup: (userData) => {
    return api.post('/auth/signup', userData);
  },

  getMe: () => {
    return api.get('/auth/me');
  }
};

export const farmerAPI = {
  submitQuery: (query) => {
    return api.post('/query', {
      query
    });
  },

  translate: (payloadOrText, targetLanguage = 'Telugu') => {
    if (typeof payloadOrText === 'string') {
      return api.post('/translate', {
        text: payloadOrText,
        target_language: targetLanguage
      });
    }

    return api.post('/translate', payloadOrText);
  },

  getHistory: () => {
    return api.get('/history');
  }
};

export const adminAPI = {
  getStats: () => {
    return api.get('/dashboard/stats');
  },

  getGraph: () => {
    return api.get('/graph');
  },

  getSources: () => {
    return api.get('/sources');
  },

  getConflicts: () => {
    return api.get('/conflicts');
  },

  getValidation: () => {
    return api.get('/validation');
  },

  getDocuments: () => {
    return api.get('/admin/documents');
  },

  getDocumentDetails: (id) => {
    return api.get(`/admin/documents/${id}`);
  },

  getDocumentStatus: (id) => {
    return api.get(`/admin/documents/${id}/status`);
  },

  uploadResource: (payload) => {
    return api.post('/admin/upload', payload);
  },

  triggerCreateGraph: (documentId) => {
    return api.post(
      `/admin/documents/${documentId}/create-graph`
    );
  }
};

export default api;
