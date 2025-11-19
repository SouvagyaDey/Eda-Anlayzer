import axios from 'axios';

// Use environment variable for API URL, fallback to proxy in development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadCSV = async (file, theme = 'light') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('theme', theme);

  const response = await axios.post(`${API_BASE_URL}/upload_csv/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const getEdaCharts = async (sessionId) => {
  const response = await api.get(`/eda_charts/${sessionId}/`);
  return response.data;
};

export const getAiInsights = async (sessionId) => {
  const response = await api.get(`/ai_insights/${sessionId}/`);
  return response.data;
};

export const getSessions = async () => {
  const response = await api.get('/sessions/');
  return response.data;
};

export const getSessionDetail = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}/`);
  return response.data;
};

export const getColumnInfo = async (sessionId) => {
  const response = await api.get(`/columns/${sessionId}/`);
  return response.data;
};

export const generateCustomCharts = async (sessionId, columns, theme = 'light') => {
  const response = await api.post(`/generate_charts/${sessionId}/`, {
    columns,
    theme
  });
  return response.data;
};

export const generateOnDemandCharts = async (sessionId, x_axis = null, y_axis = null, chart_types = null, theme = 'light') => {
  const payload = { theme };
  if (x_axis) payload.x_axis = x_axis;
  if (y_axis) payload.y_axis = y_axis;
  if (chart_types) payload.chart_types = chart_types;

  const response = await api.post(`/generate_on_demand/${sessionId}/`, payload);
  return response.data;
};

export default api;
