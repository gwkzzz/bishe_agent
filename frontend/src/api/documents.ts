import { http } from "@/api/http";
import type { GeneratedDocumentRead } from "@/types/api";

export async function createArbitrationDocument(caseId: string) {
  const response = await http.post<GeneratedDocumentRead>("/api/documents/arbitration", {
    case_id: caseId
  });
  return response.data;
}

export async function getDocument(documentId: string) {
  const response = await http.get<GeneratedDocumentRead>(`/api/documents/${documentId}`);
  return response.data;
}
