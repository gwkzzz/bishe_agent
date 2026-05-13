export interface HealthResponse {
  status: string;
  service: string;
  trace_id?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

export interface UserRead {
  username: string;
  created_at?: string;
  avatar_url?: string | null;
  signature?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserRead;
}

export interface CaseRead {
  id: string;
  user_id: string;
  title: string;
  domain: string;
  cause: string | null;
  status: string;
  summary: string | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface CaseCreate {
  title: string;
  domain?: string;
  cause?: string | null;
  summary?: string | null;
}

export interface CaseFactRead {
  id: string;
  fact_text: string;
  occurred_at: string | null;
  source: string | null;
  confidence: number | null;
  confirmed_by_user: boolean;
  created_at: string;
}

export interface EvidenceItemRead {
  id: string;
  case_id: string;
  name: string;
  evidence_type: string | null;
  file_url: string | null;
  extracted_text: string | null;
  proves: string | null;
  strength: string | null;
  risk: string | null;
  confirmed_by_user: boolean;
  created_at: string;
  updated_at: string;
}

export interface GeneratedDocumentRead {
  id: string;
  case_id: string;
  document_type: string;
  title: string;
  content_md: string;
  status: "draft" | "confirmed" | string;
  created_at: string;
  updated_at: string;
}

export interface ProfileCandidateRead {
  id: string;
  case_id: string;
  candidate_type: "timeline" | "evidence" | "todo" | "fact" | string;
  content_json: Record<string, unknown>;
  status: "pending" | "confirmed" | "rejected" | string;
  created_at: string;
  updated_at: string;
}

export interface CaseDetailRead extends CaseRead {
  facts: CaseFactRead[];
  evidence_items: EvidenceItemRead[];
  generated_documents: GeneratedDocumentRead[];
  profile_candidates: ProfileCandidateRead[];
}

export interface ConfirmProfileResponse {
  candidate: ProfileCandidateRead;
  created_resource_id: string | null;
}

export interface LaborRelation {
  employer: string | null;
  employee: string | null;
  start_date: string | null;
  end_date: string | null;
  salary: string | null;
  has_written_contract: boolean | null;
}

export interface ExtractedFact {
  fact: string;
  time: string | null;
  source: string;
  confidence: number;
}

export interface IntakeSummary {
  summary: string;
  labor_relation: LaborRelation;
  facts: ExtractedFact[];
  claims: string[];
  missing_questions: string[];
}

export interface CauseCandidate {
  cause: string;
  confidence: number;
}

export interface LaborCauseResult {
  primary_domain: string;
  supported: boolean;
  possible_causes: CauseCandidate[];
  procedure_hint: string;
  risk_flags: string[];
}

export interface IssueAnalysis {
  issue: string;
  burden_of_proof: string;
  current_evidence_status: string;
  needed_evidence: string[];
  impact: "low" | "medium" | "high" | string;
}

export interface EvidenceFinding {
  name: string;
  evidence_type: string | null;
  proves: string;
  strength: "unknown" | "low" | "medium" | "high" | string;
  risk: string;
}

export interface EvidenceAnalysisResult {
  evidence_items: EvidenceFinding[];
  missing_evidence: string[];
}

export interface LegalBasis {
  source_id: string;
  title: string;
  article: string | null;
  summary: string;
  source_url: string | null;
  score: number;
  verified: boolean;
  metadata: Record<string, unknown>;
}

export interface PrecedentReference {
  source_id: string;
  title: string;
  cause: string | null;
  court: string | null;
  summary: string;
  similarities: string[];
  differences: string[];
  source_url: string | null;
  score: number;
  verified: boolean;
  metadata: Record<string, unknown>;
}

export interface StrategyStep {
  step: string;
  action: string;
  materials: string[];
  risk_hint: string | null;
}

export interface DeadlineRisk {
  name: string;
  due_date: string | null;
  risk_level: "unknown" | "low" | "medium" | "high" | string;
  message: string;
}

export interface ProfileCandidateDraft {
  candidate_type: "timeline" | "evidence" | "todo" | "fact" | string;
  content_json: Record<string, unknown>;
  status: "pending" | "confirmed" | "rejected" | string;
  confidence: number;
}

export interface ArbitrationDocumentDraft {
  case_id: string;
  title: string;
  content_md: string;
  status: "draft" | "confirmed";
  missing_fields: string[];
  safety_notice: string;
  trace_id?: string | null;
}

export interface AgentAnalyzeResponse {
  trace_id?: string | null;
  case_id: string;
  summary: string;
  cause: string | null;
  confidence: number | null;
  needs_more_info: boolean;
  questions: string[];
  intake: IntakeSummary | null;
  cause_result: LaborCauseResult | null;
  issues: IssueAnalysis[];
  evidence_analysis: EvidenceAnalysisResult;
  evidence_gaps: string[];
  strategy_steps: StrategyStep[];
  strategy: string[];
  deadline: DeadlineRisk | null;
  deadline_risk: string | null;
  legal_basis: LegalBasis[];
  precedents: PrecedentReference[];
  profile_candidates: ProfileCandidateDraft[];
  arbitration_document: ArbitrationDocumentDraft | null;
  answer: string;
  safety_notice: string;
  risk_flags: string[];
  node_trace: string[];
  degraded?: boolean;
  error?: string;
}

export interface ChatStatusEvent {
  stage?: string;
  case_id?: string;
  trace_id?: string;
  message?: string;
}

export interface AnalyzeEvidenceResponse {
  task_id: string;
  evidence_id: string;
  status: string;
}

export interface TaskRead {
  id: string;
  case_id: string | null;
  evidence_id: string | null;
  task_type: string;
  status: string;
  progress: number;
  result_json: Record<string, unknown> | null;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}
