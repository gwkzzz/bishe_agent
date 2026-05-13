import { http } from "@/api/http";
import type {
  CaseCreate,
  CaseDetailRead,
  CaseRead,
  ConfirmProfileResponse
} from "@/types/api";

export async function listCases() {
  const response = await http.get<CaseRead[]>("/api/cases");
  return response.data;
}

export async function createCase(payload: CaseCreate) {
  const response = await http.post<CaseRead>("/api/cases", payload);
  return response.data;
}

export async function getCase(caseId: string) {
  const response = await http.get<CaseDetailRead>(`/api/cases/${caseId}`);
  return response.data;
}

export async function confirmProfileCandidate(
  caseId: string,
  candidateId: string,
  status: "confirmed" | "rejected"
) {
  const response = await http.post<ConfirmProfileResponse>(`/api/cases/${caseId}/confirm-profile`, {
    candidate_id: candidateId,
    status
  });
  return response.data;
}
