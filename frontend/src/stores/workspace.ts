import { defineStore } from "pinia";

interface WorkspaceState {
  currentCaseId: string | null;
  currentDocumentId: string | null;
}

export const useWorkspaceStore = defineStore("workspace", {
  state: (): WorkspaceState => ({
    currentCaseId: localStorage.getItem("current_case_id"),
    currentDocumentId: localStorage.getItem("current_document_id")
  }),
  actions: {
    setCurrentCaseId(caseId: string | null) {
      this.currentCaseId = caseId;
      if (caseId) {
        localStorage.setItem("current_case_id", caseId);
      } else {
        localStorage.removeItem("current_case_id");
      }
    },
    setCurrentDocumentId(documentId: string | null) {
      this.currentDocumentId = documentId;
      if (documentId) {
        localStorage.setItem("current_document_id", documentId);
      } else {
        localStorage.removeItem("current_document_id");
      }
    }
  }
});
