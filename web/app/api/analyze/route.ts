import { auth } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';
import { createAnalysis, getDocument, getUser, updateDocumentStatus } from '@/lib/db';
import { analyzeDocument } from '@/lib/claude';
import { AnalysisStatus } from '@/lib/types';
import { matchLocale } from '@/lib/i18n/config';
import { getLocale } from '@/lib/i18n/server';

export async function POST(request: NextRequest) {
  try {
    const { userId: clerkId } = await auth();

    if (!clerkId) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 },
      );
    }

    const user = await getUser(clerkId);

    if (!user) {
      return NextResponse.json(
        { success: false, error: 'User not found' },
        { status: 404 },
      );
    }

    const body = await request.json();
    const { documentId, jurisdiction } = body;
    // Report language: explicit request, else the language the visitor picked on the site.
    const language = matchLocale(body.language) ?? (await getLocale());

    if (!documentId) {
      return NextResponse.json(
        { success: false, error: 'Document ID is required' },
        { status: 400 },
      );
    }

    // Verify document exists and belongs to user
    const document = await getDocument(documentId, user.id);

    if (!document) {
      return NextResponse.json(
        { success: false, error: 'Document not found' },
        { status: 404 },
      );
    }

    if (!document.content) {
      return NextResponse.json(
        { success: false, error: 'Document content not available' },
        { status: 400 },
      );
    }

    // Update document status to processing
    try {
      await updateDocumentStatus(documentId, AnalysisStatus.PROCESSING);
    } catch (e) {
      console.error('Error updating document status:', e);
    }

    // Call Claude API for analysis
    let analysisResult;
    try {
      analysisResult = await analyzeDocument(
        document.content,
        language,
        jurisdiction,
      );
    } catch (error) {
      console.error('Analysis error:', error);
      try {
        await updateDocumentStatus(documentId, AnalysisStatus.FAILED);
      } catch (e) {
        console.error('Error updating status to failed:', e);
      }

      return NextResponse.json(
        {
          success: false,
          error: error instanceof Error ? error.message : 'Analysis failed',
        },
        { status: 500 },
      );
    }

    // Save analysis result to database
    let analysis;
    try {
      analysis = await createAnalysis(
        documentId,
        user.id,
        analysisResult.jurisdiction,
        analysisResult.documentType,
        language,
        analysisResult.strengths,
        analysisResult.weaknesses,
        analysisResult.legalErrors,
        analysisResult.defenseStrategy,
        analysisResult.riskLevel,
        analysisResult.summary,
        analysisResult.recommendations,
        analysisResult.legalFramework,
        analysisResult.publicInfo,
      );

      // Update document status to completed
      try {
        await updateDocumentStatus(documentId, AnalysisStatus.COMPLETED);
      } catch (e) {
        console.error('Error updating status to completed:', e);
      }
    } catch (error) {
      console.error('Error saving analysis:', error);
      try {
        await updateDocumentStatus(documentId, AnalysisStatus.FAILED);
      } catch (e) {
        console.error('Error updating status to failed:', e);
      }

      return NextResponse.json(
        {
          success: false,
          error: 'Failed to save analysis results',
        },
        { status: 500 },
      );
    }

    return NextResponse.json(
      {
        success: true,
        analysisId: analysis.id,
        analysis: {
          id: analysis.id,
          jurisdiction: analysis.jurisdiction,
          documentType: analysis.documentType,
          language: analysis.language,
          strengths: analysis.strengths,
          weaknesses: analysis.weaknesses,
          legalErrors: analysis.legalErrors,
          defenseStrategy: analysis.defenseStrategy,
          riskLevel: analysis.riskLevel,
          summary: analysis.summary,
          recommendations: analysis.recommendations,
          legalFramework: analysis.legalFramework,
          publicInfo: analysis.publicInfo,
          createdAt: analysis.createdAt,
        },
      },
      { status: 201 },
    );
  } catch (error) {
    console.error('Error in analysis endpoint:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to analyze document',
      },
      { status: 500 },
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { userId: clerkId } = await auth();

    if (!clerkId) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 },
      );
    }

    const user = await getUser(clerkId);

    if (!user) {
      return NextResponse.json(
        { success: false, error: 'User not found' },
        { status: 404 },
      );
    }

    const { searchParams } = new URL(request.url);
    const analysisId = searchParams.get('id');
    const documentId = searchParams.get('documentId');

    // Fetch single analysis by ID is not implemented in this endpoint
    // This would typically be a separate GET /api/analyze/:id endpoint

    return NextResponse.json(
      {
        success: true,
        message: 'Use GET /api/analyze?id=<analysisId> to fetch a specific analysis',
      },
      { status: 200 },
    );
  } catch (error) {
    console.error('Error in GET analysis:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to fetch analysis',
      },
      { status: 500 },
    );
  }
}
