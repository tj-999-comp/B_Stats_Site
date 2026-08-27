import { getSupabaseClient } from './client';

export async function signIn(email: string, password: string) {
  return getSupabaseClient().auth.signInWithPassword({ email, password });
}

export async function signOut() {
  return getSupabaseClient().auth.signOut();
}

export async function getSession() {
  return getSupabaseClient().auth.getSession();
}

export async function getUser() {
  return getSupabaseClient().auth.getUser();
}
