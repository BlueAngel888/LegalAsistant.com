import { NextResponse } from "next/server";
import { requireUserId } from "@/lib/auth";
import { listDocuments } from "@/lib/db";
import { jsonError } from "@/utils/http";

export async function GET() {
  const userId = await requireUserId();
  if (!userId) return jsonError("Unauthorized", 401);
  const documents = await listDocuments(userId);
  return NextResponse.json({ documents });
}
