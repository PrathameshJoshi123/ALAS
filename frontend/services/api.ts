import axios, { AxiosInstance, AxiosError } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AnalysisPayload = {
  overall_risk_score: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  analysis_summary: string;
  recommended_actions: string[];
  clauses: any[];
  analysis_markdown?: string;
  source?: string;
  status?: string;
  live?: Record<string, any>;
  detailed_suggestions?: any;
};

type RetryableRequest = {
  _retry?: boolean;
  headers?: Record<string, string>;
};

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      const token = Cookies.get("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = (error.config || {}) as RetryableRequest;
        if (
          error.response?.status === 401 &&
          originalRequest &&
          !originalRequest._retry
        ) {
          try {
            originalRequest._retry = true;
            const refreshToken = Cookies.get("refresh_token");
            if (refreshToken) {
              const response = await this.client.post("/api/auth/refresh", {
                refresh_token: refreshToken,
              });
              const { access_token } = response.data;
              Cookies.set("access_token", access_token);
              originalRequest.headers = {
                ...(originalRequest.headers || {}),
                Authorization: `Bearer ${access_token}`,
              };
              return this.client(originalRequest as any);
            }
          } catch (err) {
            Cookies.remove("access_token");
            Cookies.remove("refresh_token");
            window.location.href = "/auth/login";
          }
        }
        return Promise.reject(error);
      },
    );
  }

  // Auth endpoints
  async getTenants() {
    const response = await this.client.get("/api/auth/tenants");
    return response.data;
  }

  async registerUser(data: {
    tenant_id: string;
    email: string;
    password: string;
    name: string;
  }) {
    // 1. Signup user
    await this.client.post("/api/auth/signup", {
      tenant_id: data.tenant_id,
      email: data.email,
      password: data.password,
      name: data.name,
    });

    // 2. Auto login
    const loginResponse = await this.client.post("/api/auth/login", {
      tenant_id: data.tenant_id,
      email: data.email,
      password: data.password,
    });
    return loginResponse.data;
  }

  async signup(data: {
    company_name: string;
    industry: string;
    subscription_tier: string;
    email: string;
    password: string;
    name: string;
  }) {
    // 1. Create tenant
    const tenantRes = await this.client.post("/api/auth/tenants", {
      company_name: data.company_name,
      industry: data.industry,
      subscription_tier: data.subscription_tier,
    });
    const tenantId = tenantRes.data.id;

    // 2. Signup user
    await this.client.post("/api/auth/signup", {
      tenant_id: tenantId,
      email: data.email,
      password: data.password,
      name: data.name,
    });

    // 3. Auto login
    const loginResponse = await this.client.post("/api/auth/login", {
      tenant_id: tenantId,
      email: data.email,
      password: data.password,
    });
    return loginResponse.data;
  }

  async login(email: string, password: string, tenantId: string) {
    const response = await this.client.post("/api/auth/login", {
      tenant_id: tenantId,
      email,
      password,
    });
    return response.data;
  }

  async logout(userId?: string, tenantId?: string) {
    try {
      if (userId && tenantId) {
        await this.client.post("/api/auth/logout", null, {
          params: { user_id: userId, tenant_id: tenantId },
        });
      }
    } finally {
      Cookies.remove("access_token");
      Cookies.remove("refresh_token");
    }
  }

  async getCurrentUser(userId: string) {
    const response = await this.client.get(`/api/auth/users/${userId}`);
    return response.data;
  }

  // Contract endpoints
  async uploadContract(
    file: File,
    metadata: {
      company_name?: string;
      counterparty_name?: string;
      contract_type?: string;
      contract_prompt?: string;
    },
  ) {
    const formData = new FormData();
    formData.append("file", file);
    if (metadata.company_name) formData.append("company_name", metadata.company_name);
    if (metadata.counterparty_name) formData.append("counterparty_name", metadata.counterparty_name);
    if (metadata.contract_type) formData.append("contract_type", metadata.contract_type);
    if (metadata.contract_prompt) formData.append("contract_prompt", metadata.contract_prompt);

    const response = await this.client.post("/api/contracts/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return response.data;
  }

  async getContracts(page = 1, limit = 10) {
    const response = await this.client.get("/api/contracts", {
      params: { page, page_size: limit },
    });
    return response.data;
  }

  async getContractDetails(contractId: string) {
    const response = await this.client.get(`/api/contracts/${contractId}`);
    return response.data;
  }

  async getContractClauses(contractId: string) {
    const analysis = await this.getContractAnalysis(contractId);
    return { items: analysis.clauses || [] };
  }

  private normalizeAnalysisPayload(raw: any): AnalysisPayload {
    const base: AnalysisPayload = {
      overall_risk_score: Number(
        raw?.overall_risk_score || raw?.risk_score || 0,
      ),
      critical_issues: Number(raw?.critical_issues || raw?.critical || 0),
      high_issues: Number(raw?.high_issues || raw?.high || 0),
      medium_issues: Number(raw?.medium_issues || raw?.medium || 0),
      low_issues: Number(raw?.low_issues || raw?.low || 0),
      analysis_summary:
        raw?.analysis_summary || raw?.summary || "Analysis not ready yet.",
      recommended_actions: Array.isArray(raw?.recommended_actions)
        ? raw.recommended_actions
        : Array.isArray(raw?.recommendations)
          ? raw.recommendations
          : [],
      clauses: [],
      analysis_markdown: raw?.analysis_markdown || "",
      source: raw?.source,
      status: raw?.status,
      live: raw?.live,
      detailed_suggestions: raw?.detailed_suggestions,
    };

    if (raw?.source === "memories_markdown" || raw?.analysis_markdown) {
      base.clauses = Array.isArray(raw?.clauses) ? raw.clauses : [];
      return base;
    }

    const clauses = Array.isArray(raw?.clauses)
      ? raw.clauses.map((c: any, i: number) => ({
          id: c?.id || c?.clause_id || `${i + 1}`,
          clause_number: c?.clause_number || i + 1,
          clause_type: c?.clause_type || c?.type || "general",
          section_title: c?.section_title || c?.title || `Clause ${i + 1}`,
          raw_text: c?.raw_text || c?.text || "",
          severity: String(c?.severity || "info").toUpperCase(),
          risk_description: c?.risk_description || c?.risk || "",
          legal_reasoning: c?.legal_reasoning || c?.reasoning || "",
          confidence_score: Number(c?.confidence_score || c?.confidence || 0),
          applicable_statute: c?.applicable_statute,
          statute_section: c?.statute_section,
        }))
      : [];

    base.clauses = clauses;
    return base;
  }

  async getContractAnalysis(contractId: string) {
    try {
      const response = await this.client.get(
        `/api/contracts/${contractId}/analysis`,
      );
      return this.normalizeAnalysisPayload(
        response.data?.result || response.data || {},
      );
    } catch {
      return this.normalizeAnalysisPayload({});
    }
  }

  async deleteContract(contractId: string) {
    const response = await this.client.delete(`/api/contracts/${contractId}`);
    return response.data;
  }

  async analyzeContract(contractId: string) {
    const response = await this.client.post(
      `/api/contracts/${contractId}/analyze`,
    );
    return response.data;
  }

  async askContractQuestion(contractId: string, question: string) {
    const response = await this.client.post(`/api/contracts/${contractId}/qa`, {
      question,
    });
    return response.data;
  }

  async listMarkdownFiles() {
    const response = await this.client.get("/api/contracts/markdown");
    return response.data;
  }

  async getMarkdownContent(filename: string) {
    const response = await this.client.get(
      `/api/contracts/markdown/${encodeURIComponent(filename)}`,
    );
    return response.data;
  }
}

export const apiClient = new APIClient();
