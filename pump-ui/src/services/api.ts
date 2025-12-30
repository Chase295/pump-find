import axios from 'axios';
import type {
  HealthResponse,
  ConfigResponse,
  ConfigUpdateRequest,
  ConfigUpdateResponse
} from '../types/api';

// API Base URL - HTTP für alle externen Zugriffe
const getApiBaseUrl = (): string => {
  // Für lokale Entwicklung ohne Proxy
  if (import.meta.env.DEV) {
    return 'http://localhost:8001';
  }

  // Für Produktion: HTTP mit aktueller Domain/IP (nginx proxy)
  const currentHost = window.location.hostname;
  const currentPort = window.location.port || '80';

  return `http://${currentHost}:${currentPort}`;
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request Interceptor für Error Handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const pumpApi = {
  // Health Check
  async getHealth(): Promise<HealthResponse> {
    const response = await api.get('/health');
    return response.data;
  },

  // Configuration Management
  async getConfig(): Promise<ConfigResponse> {
    const response = await api.get('/config');
    return response.data;
  },

  async updateConfig(config: ConfigUpdateRequest): Promise<ConfigUpdateResponse> {
    const response = await api.put('/config', config);
    return response.data;
  },

  // Prometheus Metrics (als Text)
  async getMetrics(): Promise<string> {
    const response = await api.get('/metrics', {
      headers: { 'Accept': 'text/plain' },
      responseType: 'text'
    });
    return response.data;
  },

  // Database Statistics
  async getStreamStats(): Promise<any> {
    const response = await api.get('/database/streams/stats');
    return response.data;
  },

  async getPhases(): Promise<any> {
    const response = await api.get('/database/phases');
    return response.data;
  },

  // Utility Functions
  getApiUrl(): string {
    return API_BASE_URL;
  },

  // Health Check mit Timeout für UI
  async checkServiceHealth(): Promise<boolean> {
    try {
      const response = await api.get('/health', { timeout: 5000 });
      return response.status === 200;
    } catch {
      return false;
    }
  }
};

export default api;
