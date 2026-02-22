import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl) {
	throw new Error('Supabase URL is not configured.');
}

if (!supabasePublishableKey) {
	throw new Error('Supabase publishable key is not configured.');
}

export const supabase = createClient<Database>(supabaseUrl, supabasePublishableKey);
