import { z } from 'zod';

export const DocumentUploadSchema = z.object({
  fileName: z.string().min(1).max(255),
  fileSize: z.number().min(1).max(52428800), // 50MB max
  fileType: z.string(),
  content: z.string(),
  language: z.string().default('en'),
});

export async function extractTextFromPDF(arrayBuffer: ArrayBuffer): Promise<string> {
  try {
    const { getDocument } = await import('pdfjs-dist');
    const pdfData = new Uint8Array(arrayBuffer);
    const pdf = await getDocument({ data: pdfData }).promise;

    let fullText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map((item: any) => item.str).join(' ');
      fullText += pageText + '\n';
    }

    return fullText.trim();
  } catch (error) {
    console.error('Error extracting text from PDF:', error);
    throw new Error('Failed to extract text from PDF');
  }
}

export async function extractTextFromFile(
  file: File,
): Promise<string> {
  const fileType = file.type;

  if (fileType === 'application/pdf') {
    const arrayBuffer = await file.arrayBuffer();
    return extractTextFromPDF(arrayBuffer);
  } else if (
    fileType === 'text/plain' ||
    fileType === 'text/markdown'
  ) {
    return await file.text();
  } else if (
    fileType === 'application/msword' ||
    fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ) {
    return extractTextFromWord(file);
  }

  throw new Error(`Unsupported file type: ${fileType}`);
}

async function extractTextFromWord(file: File): Promise<string> {
  try {
    const buffer = await file.arrayBuffer();
    const mammoth = await import('mammoth');
    const result = await mammoth.extractRawText({ buffer: Buffer.from(buffer) });
    return result.value || '';
  } catch (error) {
    console.error('Error extracting text from Word document:', error);
    return '';
  }
}

export function isValidFileType(fileType: string): boolean {
  const supported = [
    'application/pdf',
    'text/plain',
    'text/markdown',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ];
  return supported.includes(fileType);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function generateDocumentId(): string {
  return `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function getLanguageFromContent(content: string): string {
  const romanianWords = ['și', 'sau', 'pentru', 'în', 'de', 'a', 'că', 'cu', 'din', 'la'];
  const englishWords = ['the', 'and', 'or', 'for', 'in', 'a', 'that', 'with', 'from', 'to'];

  const contentLower = content.toLowerCase();
  const romanianCount = romanianWords.filter((word) =>
    contentLower.includes(` ${word} `),
  ).length;
  const englishCount = englishWords.filter((word) =>
    contentLower.includes(` ${word} `),
  ).length;

  return romanianCount > englishCount ? 'ro' : 'en';
}

export async function validateDocumentSize(file: File): Promise<boolean> {
  const maxSize = parseInt(process.env.MAX_FILE_SIZE_MB || '50', 10) * 1024 * 1024;
  return file.size <= maxSize;
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
}

export function truncateText(text: string, length: number): string {
  return text.length > length ? text.substring(0, length) + '...' : text;
}

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function createErrorResponse(statusCode: number, message: string) {
  return {
    status: statusCode,
    error: {
      message,
      timestamp: new Date().toISOString(),
    },
  };
}

export function createSuccessResponse<T>(data: T, statusCode: number = 200) {
  return {
    status: statusCode,
    data,
  };
}
