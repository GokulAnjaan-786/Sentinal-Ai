/**
 * API Service
 * =============
 * Axios-based HTTP client for communicating with the SentinelAI backend.
 * Handles authentication headers, token refresh, and error handling.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { LoginRequest, LoginResponse, PaginatedResponse, ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Create a configured Axios instance for API communication.
 * Includes request/response interceptors for auth token management.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor: Attaches JWT access token to outgoing requests.
 * Automatically retrieves the token from localStorage.
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('sentinelai_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor: Handles authentication errors globally.
 * If a 401 response is received, attempts token refresh or redirects to login.
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear auth state and redirect to login
      localStorage.removeItem('sentinelai_access_token');
      localStorage.removeItem('sentinelai_refresh_token');
      localStorage.removeItem('sentinelai_user');

      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ========================
// Authentication API
// ========================

export const authApi = {
  /**
   * Authenticate a user with username and password.
   * Returns JWT tokens and user profile on success.
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', data);
    return response.data;
  },

  /**
   * Terminate the current user session.
   */
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  /**
   * Refresh an expired access token using a refresh token.
   */
  refreshToken: async (refreshToken: string): Promise<{ access_token: string; token_type: string; expires_in: number }> => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  /**
   * Change the current user's password.
   */
  changePassword: async (data: { current_password: string; new_password: string; confirm_password: string }): Promise<void> => {
    await apiClient.post('/auth/change-password', data);
  },

  /**
   * Get the current authenticated user's profile.
   */
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

// ========================
// Dashboard API
// ========================

export const dashboardApi = {
  /**
   * Get dashboard summary with all key metrics.
   */
  getSummary: async () => {
    const response = await apiClient.get('/dashboard/summary');
    return response.data;
  },

  /**
   * Get threat timeline data for charts.
   */
  getTimeline: async (days: number = 7) => {
    const response = await apiClient.get('/dashboard/timeline', { params: { days } });
    return response.data;
  },

  /**
   * Get recent activity feed.
   */
  getRecentActivity: async (limit: number = 20) => {
    const response = await apiClient.get('/dashboard/recent-activity', { params: { limit } });
    return response.data;
  },

  /**
   * Get security posture scorecard.
   */
  getScorecard: async () => {
    const response = await apiClient.get('/dashboard/scorecard');
    return response.data;
  },

  /**
   * Get department risk summary.
   */
  getDepartmentRisk: async () => {
    const response = await apiClient.get('/dashboard/department-risk');
    return response.data;
  },
};

// ========================
// Alerts API
// ========================

export const alertsApi = {
  /**
   * List alerts with filtering and pagination.
   */
  list: async (params: Record<string, unknown> = {}): Promise<PaginatedResponse<any>> => {
    const response = await apiClient.get('/alerts', { params });
    return response.data;
  },

  /**
   * Get detailed alert information.
   */
  get: async (alertId: string) => {
    const response = await apiClient.get(`/alerts/${alertId}`);
    return response.data;
  },

  /**
   * Acknowledge a security alert.
   */
  acknowledge: async (alertId: string): Promise<void> => {
    await apiClient.post(`/alerts/${alertId}/acknowledge`);
  },

  /**
   * Resolve a security alert.
   */
  resolve: async (alertId: string, notes?: string, isFalsePositive: boolean = false): Promise<void> => {
    await apiClient.post(`/alerts/${alertId}/resolve`, null, {
      params: { resolution_notes: notes, is_false_positive: isFalsePositive },
    });
  },

  /**
   * Get alert statistics.
   */
  getStats: async (days: number = 7) => {
    const response = await apiClient.get('/alerts/stats', { params: { days } });
    return response.data;
  },
};

// ========================
// Activities API
// ========================

export const activitiesApi = {
  /**
   * List activities with filtering and pagination.
   */
  list: async (params: Record<string, unknown> = {}): Promise<PaginatedResponse<any>> => {
    const response = await apiClient.get('/activities', { params });
    return response.data;
  },

  /**
   * Get activity statistics.
   */
  getStats: async (days: number = 7) => {
    const response = await apiClient.get('/activities/stats', { params: { days } });
    return response.data;
  },
};

// ========================
// Risk API
// ========================

export const riskApi = {
  /**
   * Trigger risk assessment for a user.
   */
  assess: async (userId: string) => {
    const response = await apiClient.post(`/risk/assess/${userId}`);
    return response.data;
  },

  /**
   * Get risk score trend for a user.
   */
  getTrend: async (userId: string) => {
    const response = await apiClient.get(`/risk/trend/${userId}`);
    return response.data;
  },

  /**
   * Get top risk users.
   */
  getTopRisk: async (limit: number = 10) => {
    const response = await apiClient.get('/risk/top-risk', { params: { limit } });
    return response.data;
  },
};

// ========================
// Users API
// ========================

export const usersApi = {
  /**
   * List users with filtering and pagination.
   */
  list: async (params: Record<string, unknown> = {}): Promise<PaginatedResponse<any>> => {
    const response = await apiClient.get('/users', { params });
    return response.data;
  },

  /**
   * Get detailed user information.
   */
  get: async (userId: string) => {
    const response = await apiClient.get(`/users/${userId}`);
    return response.data;
  },
};

// ========================
// Quantum-Safe Security API
// ========================

export const quantumApi = {
  /**
   * Get PQC demonstration information.
   */
  getDemo: async () => {
    const response = await apiClient.get('/quantum/demo');
    return response.data;
  },

  /**
   * Generate quantum-safe key pairs.
   */
  generateKeys: async (algorithm: string = 'CRYSTALS-Kyber') => {
    const response = await apiClient.post('/quantum/generate-keys', { algorithm });
    return response.data;
  },

  /**
   * Encrypt data using quantum-safe encryption.
   */
  encrypt: async (data: string, publicKeyHex: string) => {
    const response = await apiClient.post('/quantum/encrypt', {
      data, public_key_hex: publicKeyHex,
    });
    return response.data;
  },

  /**
   * Create a quantum-safe digital signature.
   */
  sign: async (message: string, privateKeyHex: string) => {
    const response = await apiClient.post('/quantum/sign', {
      message, private_key_hex: privateKeyHex,
    });
    return response.data;
  },

  /**
   * Protect a secret using PQC.
   */
  protectSecret: async (secret: string, purpose: string = 'general') => {
    const response = await apiClient.post('/quantum/protect-secret', { secret, purpose });
    return response.data;
  },
};

export default apiClient;
