/**
 * API Service for AIVision OCR Backend
 */

import axios, { AxiosInstance } from 'axios';
import type {
  Account,
  Country,
  Template,
  Extraction,
  DashboardStats,
  BatchExtractionResult,
  WebhookConfig,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIService {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    this.token = localStorage.getItem('aivision_token');
    if (this.token) {
      this.setAuthToken(this.token);
    }

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearAuth();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setAuthToken(token: string) {
    this.token = token;
    localStorage.setItem('aivision_token', token);
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuth() {
    this.token = null;
    localStorage.removeItem('aivision_token');
    delete this.client.defaults.headers.common['Authorization'];
  }

  // ============================================================================
  // ACCOUNTS
  // ============================================================================

  async createAccount(data: { name: string; email: string; plan?: string }) {
    const response = await this.client.post<Account>('/api/v1/accounts', data);
    if (response.data.api_token) {
      this.setAuthToken(response.data.api_token);
    }
    return response.data;
  }

  async getCurrentAccount() {
    const response = await this.client.get<Account>('/api/v1/accounts/me');
    return response.data;
  }

  async regenerateToken() {
    const response = await this.client.post<{ api_token: string; message: string }>(
      '/api/v1/accounts/regenerate-token'
    );
    if (response.data.api_token) {
      this.setAuthToken(response.data.api_token);
    }
    return response.data;
  }

  async getUsage() {
    const response = await this.client.get('/api/v1/accounts/usage');
    return response.data;
  }

  async getLimits() {
    const response = await this.client.get('/api/v1/accounts/limits');
    return response.data;
  }

  // ============================================================================
  // EXTRACTIONS
  // ============================================================================

  async extractDocument(
    file: File,
    options: {
      template_id?: string;
      vision_model?: string;
      fallback_models?: string;
      confidence_threshold?: number;
      auto_detect?: boolean;
    } = {}
  ) {
    const formData = new FormData();
    formData.append('file', file);

    if (options.template_id) formData.append('template_id', options.template_id);
    if (options.vision_model) formData.append('vision_model', options.vision_model);
    if (options.fallback_models) formData.append('fallback_models', options.fallback_models);
    if (options.confidence_threshold !== undefined)
      formData.append('confidence_threshold', String(options.confidence_threshold));
    if (options.auto_detect !== undefined)
      formData.append('auto_detect', String(options.auto_detect));

    const response = await this.client.post<Extraction>('/api/v1/extractions/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async getExtraction(extractionId: string) {
    const response = await this.client.get<Extraction>(`/api/v1/extractions/${extractionId}`);
    return response.data;
  }

  async listExtractions(params?: {
    status_filter?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await this.client.get<Extraction[]>('/api/v1/extractions', { params });
    return response.data;
  }

  async exportExtraction(extractionId: string, format: 'json' | 'csv' = 'json') {
    const response = await this.client.get(
      `/api/v1/extractions/${extractionId}/export?format=${format}`,
      {
        responseType: format === 'csv' ? 'blob' : 'json',
      }
    );
    return response.data;
  }

  async deleteExtraction(extractionId: string) {
    const response = await this.client.delete(`/api/v1/extractions/${extractionId}`);
    return response.data;
  }

  // ============================================================================
  // BATCH PROCESSING
  // ============================================================================

  async batchExtract(files: File[], options: {
    template_id?: string;
    vision_model?: string;
    auto_detect?: boolean;
    confidence_threshold?: number;
  } = {}) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    if (options.template_id) formData.append('template_id', options.template_id);
    if (options.vision_model) formData.append('vision_model', options.vision_model);
    if (options.auto_detect !== undefined)
      formData.append('auto_detect', String(options.auto_detect));
    if (options.confidence_threshold !== undefined)
      formData.append('confidence_threshold', String(options.confidence_threshold));

    const response = await this.client.post<BatchExtractionResult>(
      '/api/v1/extractions/batch',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  async getBatchStatus(batchId: string) {
    const response = await this.client.get<BatchExtractionResult>(
      `/api/v1/extractions/batch/${batchId}`
    );
    return response.data;
  }

  // ============================================================================
  // TEMPLATES
  // ============================================================================

  async listTemplates(params?: {
    category?: string;
    country_id?: number;
    active_only?: boolean;
  }) {
    const response = await this.client.get<Template[]>('/api/v1/templates', { params });
    return response.data;
  }

  async getTemplate(templateId: string) {
    const response = await this.client.get<Template>(`/api/v1/templates/${templateId}`);
    return response.data;
  }

  async createTemplate(data: Partial<Template>) {
    const response = await this.client.post<Template>('/api/v1/templates', data);
    return response.data;
  }

  async updateTemplate(templateId: string, data: Partial<Template>) {
    const response = await this.client.put<Template>(`/api/v1/templates/${templateId}`, data);
    return response.data;
  }

  async deleteTemplate(templateId: string) {
    const response = await this.client.delete(`/api/v1/templates/${templateId}`);
    return response.data;
  }

  async getTemplateStats(templateId: string) {
    const response = await this.client.get(`/api/v1/templates/${templateId}/stats`);
    return response.data;
  }

  // ============================================================================
  // COUNTRIES
  // ============================================================================

  async listCountries(active_only: boolean = true) {
    const response = await this.client.get<Country[]>('/api/v1/countries', {
      params: { active_only },
    });
    return response.data;
  }

  async getCountry(code: string) {
    const response = await this.client.get<Country>(`/api/v1/countries/${code}`);
    return response.data;
  }

  async createCountry(data: { code: string; name: string; is_active?: boolean }) {
    const response = await this.client.post<Country>('/api/v1/countries', data);
    return response.data;
  }

  async activateCountry(code: string) {
    const response = await this.client.patch(`/api/v1/countries/${code}/activate`);
    return response.data;
  }

  async deactivateCountry(code: string) {
    const response = await this.client.patch(`/api/v1/countries/${code}/deactivate`);
    return response.data;
  }

  // ============================================================================
  // ANALYTICS
  // ============================================================================

  async getDashboard(days: number = 30) {
    const response = await this.client.get<DashboardStats>('/api/v1/analytics/dashboard', {
      params: { days },
    });
    return response.data;
  }

  async getUsageAnalytics(days: number = 30) {
    const response = await this.client.get('/api/v1/analytics/usage', {
      params: { days },
    });
    return response.data;
  }

  async getTemplateAnalytics() {
    const response = await this.client.get('/api/v1/analytics/templates');
    return response.data;
  }

  async getModelPerformance(days: number = 30) {
    const response = await this.client.get('/api/v1/analytics/models', {
      params: { days },
    });
    return response.data;
  }

  async getAnalytics(params?: { days?: number }) {
    const response = await this.client.get('/api/v1/analytics/usage', { params });
    return response.data;
  }

  // ============================================================================
  // API LOGS
  // ============================================================================

  async getAPILogs(params?: {
    days?: number;
    limit?: number;
    offset?: number;
    method?: string;
    status_code?: number;
  }) {
    const response = await this.client.get('/api/v1/logs', { params });
    return response.data;
  }

  // ============================================================================
  // TAGS
  // ============================================================================

  async listTags(category?: string) {
    const response = await this.client.get('/api/v1/tags', {
      params: category ? { category } : undefined,
    });
    return response.data;
  }

  async createTag(data: { tag_name: string; color?: string; tag_category?: string }) {
    const response = await this.client.post('/api/v1/tags', data);
    return response.data;
  }

  async updateTag(tagId: number, data: { tag_name?: string; color?: string; tag_category?: string }) {
    const response = await this.client.put(`/api/v1/tags/${tagId}`, data);
    return response.data;
  }

  async deleteTag(tagId: number) {
    const response = await this.client.delete(`/api/v1/tags/${tagId}`);
    return response.data;
  }

  // ============================================================================
  // CATEGORIES
  // ============================================================================

  async listCategories() {
    const response = await this.client.get('/api/v1/categories');
    return response.data;
  }

  async createCategory(data: {
    name: string;
    display_name: string;
    description?: string;
    icon?: string;
    color?: string;
  }) {
    const response = await this.client.post('/api/v1/categories', data);
    return response.data;
  }

  async updateCategory(categoryId: number, data: {
    display_name?: string;
    description?: string;
    icon?: string;
    color?: string;
  }) {
    const response = await this.client.put(`/api/v1/categories/${categoryId}`, data);
    return response.data;
  }

  async deleteCategory(categoryId: number) {
    const response = await this.client.delete(`/api/v1/categories/${categoryId}`);
    return response.data;
  }

  // ============================================================================
  // AUTH HELPERS
  // ============================================================================

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getToken(): string | null {
    return this.token;
  }

  // ============================================================================
  // TEMPLATES (Alias for backward compatibility)
  // ============================================================================

  async getTemplates(params?: {
    category?: string;
    country_id?: number;
    active_only?: boolean;
  }) {
    return this.listTemplates(params);
  }

  // ============================================================================
  // WEBHOOKS
  // ============================================================================

  async listWebhooks() {
    const response = await this.client.get<WebhookConfig[]>('/api/v1/webhooks');
    return response.data;
  }

  async createWebhook(data: {
    url: string;
    events: string[];
    is_active?: boolean;
    secret?: string;
  }) {
    const response = await this.client.post<WebhookConfig>('/api/v1/webhooks', data);
    return response.data;
  }

  async updateWebhook(webhookId: number, data: Partial<WebhookConfig>) {
    const response = await this.client.put<WebhookConfig>(`/api/v1/webhooks/${webhookId}`, data);
    return response.data;
  }

  async deleteWebhook(webhookId: number) {
    const response = await this.client.delete(`/api/v1/webhooks/${webhookId}`);
    return response.data;
  }

  async testWebhook(webhookId: number) {
    const response = await this.client.post(`/api/v1/webhooks/${webhookId}/test`);
    return response.data;
  }

  // Aliases for convenience
  setToken(token: string) {
    this.setAuthToken(token);
  }

  async extract(file: File, options?: { template_id?: string; vision_model?: string }) {
    return this.extractDocument(file, options);
  }
}

export const api = new APIService();
export default api;
