import { create } from "zustand";
import Cookies from "js-cookie";

export interface User {
  id: string;
  email: string;
  name: string;
  tenant_id: string;
  role_id: string;
  is_active: boolean;
  email_verified: boolean;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
  hydrateAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) => {
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    } else {
      localStorage.removeItem("user");
    }
    set((state) => ({
      user,
      isAuthenticated: !!user,
    }));
  },

  setLoading: (loading) => set({ isLoading: loading }),

  logout: () => {
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
    localStorage.removeItem("user");
    set({
      user: null,
      isAuthenticated: false,
    });
  },

  hydrateAuth: () => {
    const token = Cookies.get("access_token");
    const userStr = localStorage.getItem("user");

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch {
        set({ isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },
}));
