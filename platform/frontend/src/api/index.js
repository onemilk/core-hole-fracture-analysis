import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getSamples: () => api.get('/samples'),
  createSample: (data) => api.post('/samples', data),
  uploadImage: (sampleId, formData) => api.post(`/samples/${sampleId}/images`, formData),
  submitAnalysis: (data) => api.post('/analysis', data),
  getAnalysis: (id) => api.get(`/analysis/${id}`),
};
