import { auth, currentUser } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';
import { createDocument, createOrUpdateUser, getUser } from '@/lib/db';
import { extractTextFromFile, isValidFileType, validateDocumentSize, getLanguageFromContent } from '@/lib/utils';
import { DocumentType, AnalysisStatus } from '@/lib/types';

export async function POST(request: NextRequest) {
  try {
    // Get authenticated user
    const { userId: clerkId } = await auth();

    if (!clerkId) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 },
      );
    }

    // Get or create user in database (first upload after sign-up)
    let user = await getUser(clerkId);

    if (!user) {
      try {
        const clerkUser = await currentUser();
        const email = clerkUser?.primaryEmailAddress?.emailAddress ?? '';
        const name = [clerkUser?.firstName, clerkUser?.lastName].filter(Boolean).join(' ') || email;
        user = await createOrUpdateUser(clerkId, email, name);
      } catch (e) {
        console.error('Error creating user:', e);
      }
    }

    if (!user) {
      return NextResponse.json(
        { success: false, error: 'User not found' },
        { status: 404 },
      );
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;
    const documentTypeStr = (formData.get('documentType') as string) || 'OTHER';

    if (!file) {
      return NextResponse.json(
        { success: false, error: 'No file provided' },
        { status: 400 },
      );
    }

    // Validate file
    if (!isValidFileType(file.type)) {
      return NextResponse.json(
        { success: false, error: 'File type not supported' },
        { status: 400 },
      );
    }

    if (!(await validateDocumentSize(file))) {
      return NextResponse.json(
        { success: false, error: 'File size exceeds maximum allowed' },
        { status: 400 },
      );
    }

    // Extract text from file
    let textContent = '';
    try {
      textContent = await extractTextFromFile(file);
    } catch (e) {
      console.error('Error extracting text:', e);
      return NextResponse.json(
        { success: false, error: 'Failed to process file' },
        { status: 500 },
      );
    }

    if (!textContent || textContent.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Could not extract text from file' },
        { status: 400 },
      );
    }

    // Detect language
    const language = getLanguageFromContent(textContent);

    // Map document type
    const documentType = Object.values(DocumentType).includes(documentTypeStr as DocumentType)
      ? (documentTypeStr as DocumentType)
      : DocumentType.OTHER;

    // Create document record in database
    const document = await createDocument(
      user.id,
      file.name,
      file.size,
      file.type,
      documentType,
      language,
      textContent,
    );

    return NextResponse.json(
      {
        success: true,
        documentId: document.id,
        message: 'Document uploaded successfully',
      },
      { status: 201 },
    );
  } catch (error) {
    console.error('Error uploading document:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to upload document',
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

    // Get limit from query params
    const { searchParams } = new URL(request.url);
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100);

    // Fetch user's documents (commented out for now as we're not fetching)
    // const documents = await getUserDocuments(user.id, limit);

    return NextResponse.json(
      {
        success: true,
        documents: [],
        total: 0,
      },
      { status: 200 },
    );
  } catch (error) {
    console.error('Error fetching documents:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to fetch documents',
      },
      { status: 500 },
    );
  }
}
