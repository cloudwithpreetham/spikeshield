import axios from 'axios';

// In browser, relative '/api/v1' works seamlessly locally (via Vite proxy) and in production on EB
const apiUrl = '/api/v1';

export const apiClient = axios.create({ baseURL: apiUrl, timeout: 30000 });

apiClient.interceptors.response.use(
  (r) => r,
  (err) => {
    console.error('API error:', err.response?.status, err.message);
    return Promise.reject(err);
  }
);
