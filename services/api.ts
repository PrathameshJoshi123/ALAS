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
    const response = await this.client.post("/api/auth/signup", data);
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post("/api/auth/login", {
      email,
      password,
    });
    return response.data;
  }

  async logout() {
    try {
      await this.client.post("/api/auth/logout");
    } finally {
      Cookies.remove("access_token");
      Cookies.remove("refresh_token");
    }
  }

  async getCurrentUser() {
    const response = await this.client.get("/api/auth/me");
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
    return response.data;
  }

  async getContracts(page = 1, limit = 10) {
    const response = await this.client.get("/api/contracts/list", {
      params: { page, limit },
    });
    return response.data;
  }

  async getContractDetails(contractId: string) {
    const response = await this.client.get(`/api/contracts/${contractId}`);
    return response.data;
  }

  async getContractClauses(contractId: string) {
    const response = await this.client.get(
      `/api/contracts/${contractId}/clauses`,
    );
    return response.data;
  }

  async getContractAnalysis(contractId: string) {
    const response = await this.client.get(
      `/api/contracts/${contractId}/analysis`,
    );
    return response.data;
  }

  async deleteContract(contractId: string) {
    const response = await this.client.delete(`/api/contracts/${contractId}`);
    return response.data;
  }
}

export const apiClient = new APIClient();
