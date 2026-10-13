import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials not configured. Some features may not work.');
}

// Placeholders keep `next build` from crashing when env vars are missing;
// real requests still need the real values set in Vercel.
const url = supabaseUrl || 'http://localhost:54321';

export const supabaseClient = createClient(url, supabaseAnonKey || 'missing-anon-key');

export const supabaseAdmin = createClient(url, supabaseServiceRoleKey || 'missing-service-role-key');

export type Database = any;

export async function testSupabaseConnection(): Promise<boolean> {
  try {
    const { data, error } = await supabaseClient
      .from('users')
      .select('count()', { count: 'exact' })
      .limit(0);

    if (error) {
      console.error('Supabase connection error:', error);
      return false;
    }
    return true;
  } catch (error) {
    console.error('Supabase test failed:', error);
    return false;
  }
}
