import axios, { AxiosInstance, AxiosError } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
        const originalRequest = error.config;
        if (
          error.response?.status === 401 &&
          originalRequest &&
          !originalRequest.headers["Authorization"]
        ) {
          try {
            const refreshToken = Cookies.get("refresh_token");
            if (refreshToken) {
              const response = await this.client.post("/api/auth/refresh", {
                refresh_token: refreshToken,
              });
              const { access_token } = response.data;
              Cookies.set("access_token", access_token);
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access_token}`;
              }
              return this.client(originalRequest);
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
  async signup(data: {
    company_name: string;
    email: string;
    password: string;
    name: string;
  }) {
    // 1. Create tenant
    const tenantRes = await this.client.post("/api/auth/tenants", {
      company_name: data.company_name,
      industry: "Legal",
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
      counterparty_name: string;
      contract_type: string;
    },
  ) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("counterparty_name", metadata.counterparty_name);
    formData.append("contract_type", metadata.contract_type);

    const response = await this.client.post("/api/contracts/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    
    // Initiate analysis immediately after upload
    try {
      const contractId = response.data.id;
      await this.client.post(`/api/contracts/${contractId}/analyze`);
    } catch (e) {
      console.error("Failed to initiate analysis", e);
    }

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
    const response = await this.client.get(
      `/api/contracts/${contractId}/risk-analysis`,
    );
    return { items: response.data.clauses || [] };
  }

  async getContractAnalysis(contractId: string) {
    const response = await this.client.get(
      `/api/contracts/${contractId}/risk-analysis`,
    );
    return response.data;
  }

  async deleteContract(contractId: string) {
    const response = await this.client.delete(`/api/contracts/${contractId}`);
    return response.data;
  }
}

export const apiClient = new APIClient();
