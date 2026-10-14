import { supabaseClient, supabaseAdmin } from './supabase';
import { toAnalysisPoints, toPublicInfo, toStringList } from './analysis-points';
import {
  User,
  Document,
  AnalysisResult,
  DocumentType,
  Jurisdiction,
  AnalysisStatus,
  AnalysisPoint,
  PublicInfoItem,
} from './types';

export async function createOrUpdateUser(clerkId: string, email: string, name: string): Promise<User> {
  const { data, error } = await supabaseClient
    .from('users')
    .upsert(
      {
        clerk_id: clerkId,
        email,
        name,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'clerk_id' },
    )
    .select()
    .single();

  if (error) {
    throw new Error(`Failed to create/update user: ${error.message}`);
  }

  return mapUserRow(data);
}

export async function getUser(clerkId: string): Promise<User | null> {
  const { data, error } = await supabaseClient
    .from('users')
    .select('*')
    .eq('clerk_id', clerkId)
    .single();

  if (error || !data) {
    return null;
  }

  return mapUserRow(data);
}

export async function createDocument(
  userId: string,
  fileName: string,
  fileSize: number,
  fileType: string,
  documentType: DocumentType,
  language: string,
  content?: string,
): Promise<Document> {
  const { data, error } = await supabaseClient
    .from('documents')
    .insert({
      user_id: userId,
      file_name: fileName,
      file_size: fileSize,
      file_type: fileType,
      document_type: documentType,
      language,
      content: content || null,
      status: AnalysisStatus.PENDING,
    })
    .select()
    .single();

  if (error) {
    throw new Error(`Failed to create document: ${error.message}`);
  }

  return mapDocumentRow(data);
}

export async function getDocument(documentId: string, userId: string): Promise<Document | null> {
  const { data, error } = await supabaseClient
    .from('documents')
    .select('*')
    .eq('id', documentId)
    .eq('user_id', userId)
    .single();

  if (error || !data) {
    return null;
  }

  return mapDocumentRow(data);
}

export async function getUserDocuments(userId: string, limit: number = 50): Promise<Document[]> {
  const { data, error } = await supabaseClient
    .from('documents')
    .select('*')
    .eq('user_id', userId)
    .order('uploaded_at', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('Failed to fetch documents:', error);
    return [];
  }

  return (data || []).map(mapDocumentRow);
}

export async function updateDocumentStatus(
  documentId: string,
  status: AnalysisStatus,
): Promise<void> {
  const { error } = await supabaseClient
    .from('documents')
    .update({ status })
    .eq('id', documentId);

  if (error) {
    throw new Error(`Failed to update document status: ${error.message}`);
  }
}

export async function createAnalysis(
  documentId: string,
  userId: string,
  jurisdiction: Jurisdiction,
  documentType: DocumentType,
  language: string,
  strengths: AnalysisPoint[],
  weaknesses: AnalysisPoint[],
  legalErrors: AnalysisPoint[],
  defenseStrategy: AnalysisPoint[],
  riskLevel: string,
  summary: string,
  recommendations: AnalysisPoint[],
  legalFramework: string[],
  publicInfo: PublicInfoItem[],
): Promise<AnalysisResult> {
  const { data, error } = await supabaseClient
    .from('analysis_results')
    .insert({
      document_id: documentId,
      user_id: userId,
      jurisdiction,
      document_type: documentType,
      language,
      strengths,
      weaknesses,
      legal_errors: legalErrors,
      defense_strategy: defenseStrategy,
      risk_level: riskLevel,
      summary,
      recommendations,
      legal_framework: legalFramework,
      public_info: publicInfo,
      cached_at: new Date().toISOString(),
    })
    .select()
    .single();

  if (error) {
    throw new Error(`Failed to create analysis: ${error.message}`);
  }

  return mapAnalysisRow(data);
}

export async function getAnalysis(analysisId: string, userId: string): Promise<AnalysisResult | null> {
  const { data, error } = await supabaseClient
    .from('analysis_results')
    .select('*')
    .eq('id', analysisId)
    .eq('user_id', userId)
    .single();

  if (error || !data) {
    return null;
  }

  return mapAnalysisRow(data);
}

export async function getDocumentAnalysis(
  documentId: string,
  userId: string,
): Promise<AnalysisResult | null> {
  const { data, error } = await supabaseClient
    .from('analysis_results')
    .select('*')
    .eq('document_id', documentId)
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  if (error || !data) {
    return null;
  }

  return mapAnalysisRow(data);
}

export async function getUserAnalyses(userId: string, limit: number = 50): Promise<AnalysisResult[]> {
  const { data, error } = await supabaseClient
    .from('analysis_results')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('Failed to fetch analyses:', error);
    return [];
  }

  return (data || []).map(mapAnalysisRow);
}

function mapUserRow(row: any): User {
  return {
    id: row.id,
    clerkId: row.clerk_id,
    email: row.email,
    name: row.name,
    createdAt: new Date(row.created_at),
    updatedAt: new Date(row.updated_at),
  };
}

function mapDocumentRow(row: any): Document {
  return {
    id: row.id,
    userId: row.user_id,
    fileName: row.file_name,
    fileSize: row.file_size,
    fileType: row.file_type,
    documentType: row.document_type,
    jurisdiction: row.jurisdiction,
    uploadedAt: new Date(row.uploaded_at),
    content: row.content,
    language: row.language,
    status: row.status,
  };
}

function mapAnalysisRow(row: any): AnalysisResult {
  return {
    id: row.id,
    documentId: row.document_id,
    userId: row.user_id,
    jurisdiction: row.jurisdiction,
    documentType: row.document_type,
    language: row.language,
    strengths: toAnalysisPoints(row.strengths),
    weaknesses: toAnalysisPoints(row.weaknesses),
    legalErrors: toAnalysisPoints(row.legal_errors),
    defenseStrategy: toAnalysisPoints(row.defense_strategy),
    riskLevel: row.risk_level,
    summary: row.summary,
    recommendations: toAnalysisPoints(row.recommendations),
    legalFramework: toStringList(row.legal_framework),
    publicInfo: toPublicInfo(row.public_info),
    cachedAt: row.cached_at ? new Date(row.cached_at) : undefined,
    createdAt: new Date(row.created_at),
    updatedAt: new Date(row.updated_at),
  };
}
