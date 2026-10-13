import "server-only";
import { auth, currentUser } from "@clerk/nextjs/server";
import { supabaseAdmin } from "./supabase";

const syncedUsers = new Set<string>();

/**
 * Returns the signed-in Clerk user id, or null. On first sight of a user in
 * this server instance it upserts them into the `users` table, so we don't
 * need a Clerk webhook for the MVP.
 */
export async function requireUserId(): Promise<string | null> {
  const { userId } = await auth();
  if (!userId) return null;

  if (!syncedUsers.has(userId)) {
    const user = await currentUser();
    const { error } = await supabaseAdmin()
      .from("users")
      .upsert(
        {
          id: userId,
          email: user?.primaryEmailAddress?.emailAddress ?? null,
          full_name: user?.fullName ?? null,
        },
        { onConflict: "id" },
      );
    if (error) throw new Error(`User sync failed: ${error.message}`);
    syncedUsers.add(userId);
  }
  return userId;
}
