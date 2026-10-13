import "server-only";
import { extractText, getDocumentProxy } from "unpdf";

export interface ParsedPdf {
  text: string;
  pageCount: number;
}

/** Extracts plain text from a PDF. Scanned PDFs return little or no text. */
export async function parsePdf(bytes: Uint8Array): Promise<ParsedPdf> {
  // unpdf/pdf.js may detach the buffer, so hand it a copy.
  const pdf = await getDocumentProxy(new Uint8Array(bytes));
  const { totalPages, text } = await extractText(pdf, { mergePages: true });
  return { text: text.replace(/[ \t]+\n/g, "\n").trim(), pageCount: totalPages };
}

/** Below this many characters we treat the PDF as scanned and send the file itself to Claude. */
export const MIN_TEXT_CHARS = 200;

export function isPdf(bytes: Uint8Array): boolean {
  // "%PDF-"
  return (
    bytes.length > 4 &&
    bytes[0] === 0x25 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x44 &&
    bytes[3] === 0x46 &&
    bytes[4] === 0x2d
  );
}
