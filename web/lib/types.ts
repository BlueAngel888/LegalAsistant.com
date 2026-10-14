export enum Jurisdiction {
  EU_DE = 'EU_DE',
  EU_FR = 'EU_FR',
  EU_IT = 'EU_IT',
  EU_ES = 'EU_ES',
  EU_RO = 'EU_RO',
  EU_GB = 'EU_GB',
  EU_NL = 'EU_NL',
  EU_BE = 'EU_BE',
  EU_AT = 'EU_AT',
  EU_SE = 'EU_SE',
  USA = 'USA',
  USA_NY = 'USA_NY',
  USA_CA = 'USA_CA',
  USA_TX = 'USA_TX',
  UNKNOWN = 'UNKNOWN',
}

export enum DocumentType {
  CONTRACT = 'CONTRACT',
  NDA = 'NDA',
  EMPLOYMENT = 'EMPLOYMENT',
  LEASE = 'LEASE',
  POLICY = 'POLICY',
  TERMS_OF_SERVICE = 'TERMS_OF_SERVICE',
  PRIVACY_POLICY = 'PRIVACY_POLICY',
  OTHER = 'OTHER',
}

export enum AnalysisStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

export interface User {
  id: string;
  clerkId: string;
  email: string;
  name: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Document {
  id: string;
  userId: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  documentType: DocumentType;
  jurisdiction?: Jurisdiction;
  uploadedAt: Date;
  content?: string;
  language: string;
  status: AnalysisStatus;
}

/** Whether a clause complies with the law that governs it. */
export type ComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'UNCLEAR';

/** One point of an analysis, tied to the law it rests on. */
export interface AnalysisPoint {
  text: string;
  /** The article or act this point relies on, e.g. "art. 1.823 Cod civil". Empty when none applies. */
  legalBasis: string;
  /** Set for points that judge a clause (strengths, weaknesses, legal issues). */
  status?: ComplianceStatus;
}

export interface AnalysisResult {
  id: string;
  documentId: string;
  userId: string;
  jurisdiction: Jurisdiction;
  documentType: DocumentType;
  language: string;
  strengths: AnalysisPoint[];
  weaknesses: AnalysisPoint[];
  legalErrors: AnalysisPoint[];
  defenseStrategy: AnalysisPoint[];
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  summary: string;
  recommendations: AnalysisPoint[];
  cachedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface UploadResponse {
  success: boolean;
  documentId?: string;
  error?: string;
  message?: string;
}

export interface AnalysisRequest {
  documentId: string;
  language?: string;
  jurisdiction?: Jurisdiction;
}

export interface AnalysisResponse {
  success: boolean;
  analysisId?: string;
  analysis?: AnalysisResult;
  error?: string;
  message?: string;
}

export interface ClaudeAnalysisPayload {
  documentContent: string;
  language: string;
  jurisdiction?: Jurisdiction;
}

export interface ClaudeAnalysisOutput {
  jurisdiction: Jurisdiction;
  documentType: DocumentType;
  strengths: AnalysisPoint[];
  weaknesses: AnalysisPoint[];
  legalErrors: AnalysisPoint[];
  defenseStrategy: AnalysisPoint[];
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  summary: string;
  recommendations: AnalysisPoint[];
}
