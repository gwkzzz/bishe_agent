import { defineStore } from "pinia";

interface AuthState {
  token: string | null;
  username: string | null;
  createdAt: string | null;
  avatarUrl: string | null;
  signature: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem("auth_token"),
    username: localStorage.getItem("auth_username"),
    createdAt: localStorage.getItem("auth_created_at"),
    avatarUrl: localStorage.getItem("auth_avatar_url"),
    signature: localStorage.getItem("auth_signature")
  }),
  actions: {
    setSession(
      token: string,
      username: string,
      createdAt?: string,
      avatarUrl?: string | null,
      signature?: string | null
    ) {
      this.token = token;
      this.username = username;
      this.createdAt = createdAt ?? null;
      this.avatarUrl = avatarUrl ?? null;
      this.signature = signature ?? null;
      localStorage.setItem("auth_token", token);
      localStorage.setItem("auth_username", username);
      if (createdAt) {
        localStorage.setItem("auth_created_at", createdAt);
      } else {
        localStorage.removeItem("auth_created_at");
      }
      if (avatarUrl) {
        localStorage.setItem("auth_avatar_url", avatarUrl);
      } else {
        localStorage.removeItem("auth_avatar_url");
      }
      if (signature) {
        localStorage.setItem("auth_signature", signature);
      } else {
        localStorage.removeItem("auth_signature");
      }
    },
    setProfile(payload: {
      username?: string;
      createdAt?: string;
      avatarUrl?: string | null;
      signature?: string | null;
    }) {
      if (payload.username !== undefined) {
        this.username = payload.username;
        localStorage.setItem("auth_username", payload.username);
      }
      if (payload.createdAt !== undefined) {
        this.createdAt = payload.createdAt;
        localStorage.setItem("auth_created_at", payload.createdAt);
      }
      if (payload.avatarUrl !== undefined) {
        this.avatarUrl = payload.avatarUrl;
        if (payload.avatarUrl) {
          localStorage.setItem("auth_avatar_url", payload.avatarUrl);
        } else {
          localStorage.removeItem("auth_avatar_url");
        }
      }
      if (payload.signature !== undefined) {
        this.signature = payload.signature;
        if (payload.signature) {
          localStorage.setItem("auth_signature", payload.signature);
        } else {
          localStorage.removeItem("auth_signature");
        }
      }
    },
    logout() {
      this.token = null;
      this.username = null;
      this.createdAt = null;
      this.avatarUrl = null;
      this.signature = null;
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_username");
      localStorage.removeItem("auth_created_at");
      localStorage.removeItem("auth_avatar_url");
      localStorage.removeItem("auth_signature");
    }
  }
});
