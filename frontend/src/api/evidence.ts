import { http } from "@/api/http";
import type { AnalyzeEvidenceResponse, EvidenceItemRead, TaskRead } from "@/types/api";

export interface EvidenceUploadPayload {
  caseId: string;
  file: File;
  name?: string;
  evidenceType?: string;
}

export async function listCaseEvidence(caseId: string) {
  const response = await http.get<EvidenceItemRead[]>(`/api/cases/${caseId}/evidence`);
  return response.data;
}

export async function uploadEvidence(payload: EvidenceUploadPayload) {
  const data = new FormData();
  data.append("case_id", payload.caseId);
  data.append("file", payload.file);
  if (payload.name) data.append("name", payload.name);
  if (payload.evidenceType) data.append("evidence_type", payload.evidenceType);

  const response = await http.post<EvidenceItemRead>("/api/evidence/upload", data, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
}

export async function analyzeEvidence(evidenceId: string) {
  const response = await http.post<AnalyzeEvidenceResponse>(`/api/evidence/${evidenceId}/analyze`);
  return response.data;
}

export async function getTask(taskId: string) {
  const response = await http.get<TaskRead>(`/api/tasks/${taskId}`);
  return response.data;
}
