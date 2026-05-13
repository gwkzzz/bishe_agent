import { http } from "@/api/http";
import type { UserRead } from "@/types/api";

export async function getMe() {
  const response = await http.get<UserRead>("/api/auth/me");
  return response.data;
}

export async function updateSignature(signature: string | null) {
  const response = await http.patch<UserRead>("/api/auth/me", {
    signature
  });
  return response.data;
}

export async function uploadAvatar(file: File) {
  const data = new FormData();
  data.append("file", file);
  const response = await http.post<UserRead>("/api/auth/me/avatar", data, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}
