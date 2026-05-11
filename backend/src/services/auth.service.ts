import type { Session, User } from '@supabase/supabase-js';
import { HttpError } from '../common/HttpError.js';
import { env } from '../config/env.js';
import { createAnonClient } from '../lib/supabase.js';
import type {
  LoginBody,
  PasswordForgotBody,
  PasswordResetBody,
  RefreshBody,
  SignupBody,
} from '../schemas/auth.schemas.js';

const emailRedirectAllowed = (): string => `${env.PUBLIC_APP_URL.replace(/\/$/, '')}/auth/callback`;

export interface AuthSessionResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  expires_at: number | undefined;
  token_type: string;
  user: {
    id: string;
    email: string | undefined;
    email_confirmed_at: string | undefined;
  };
}

function sessionToJson(session: Session, user: User): AuthSessionResponse {
  return {
    access_token: session.access_token,
    refresh_token: session.refresh_token,
    expires_in: session.expires_in,
    expires_at: session.expires_at,
    token_type: session.token_type,
    user: {
      id: user.id,
      email: user.email,
      email_confirmed_at: user.email_confirmed_at,
    },
  };
}

function mapAuthError(code: unknown, fallback: string): string {
  if (typeof code === 'string') {
    return code;
  }
  return fallback;
}

function requireSessionUser(session: Session | null, user: User | null, err: HttpError) {
  if (session === null || user === null) {
    throw err;
  }
  return { session, user };
}

function requireSession(session: Session | null, err: HttpError) {
  if (session === null) {
    throw err;
  }
  return session;
}

function requireUser(user: User | null, err: HttpError) {
  if (user === null) {
    throw err;
  }
  return user;
}

export type SignupResponse = AuthSessionResponse | { userId: string | null };

export async function signup(body: SignupBody): Promise<SignupResponse> {
  const supabase = createAnonClient();
  const credentials: {
    email: string;
    password: string;
    options?: { data: Record<string, string> };
  } = {
    email: body.email,
    password: body.password,
  };
  if (body.display_name !== undefined) {
    credentials.options = {
      data: { display_name: body.display_name, full_name: body.display_name },
    };
  }
  const { data, error } = await supabase.auth.signUp(credentials);
  if (error) {
    throw new HttpError(400, error.message);
  }
  if (data.session !== null && data.user !== null) {
    return sessionToJson(data.session, data.user);
  }
  return { userId: data.user?.id ?? null };
}

export async function login(body: LoginBody): Promise<AuthSessionResponse> {
  const supabase = createAnonClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email: body.email,
    password: body.password,
  });
  if (error) {
    throw new HttpError(
      401,
      mapAuthError(error.code, error.message || 'Invalid email or password'),
    );
  }
  const { session, user } = requireSessionUser(
    data.session,
    data.user,
    new HttpError(401, 'Invalid email or password'),
  );
  return sessionToJson(session, user);
}

export async function requestPasswordReset(body: PasswordForgotBody) {
  const supabase = createAnonClient();
  const { error } = await supabase.auth.resetPasswordForEmail(body.email, {
    redirectTo: emailRedirectAllowed(),
  });
  if (error) {
    throw new HttpError(400, error.message);
  }
  return { ok: true as const };
}

export async function completePasswordReset(body: PasswordResetBody): Promise<AuthSessionResponse> {
  const supabase = createAnonClient();
  const { data, error } = await supabase.auth.verifyOtp({
    email: body.email,
    token: body.token,
    type: 'recovery',
  });
  if (error) {
    throw new HttpError(400, error.message);
  }
  const session = requireSession(
    data.session,
    new HttpError(400, 'Invalid or expired recovery token'),
  );
  const setRes = await supabase.auth.setSession({
    access_token: session.access_token,
    refresh_token: session.refresh_token,
  });
  if (setRes.error) {
    throw new HttpError(400, setRes.error.message);
  }
  const { data: updated, error: updErr } = await supabase.auth.updateUser({
    password: body.newPassword,
  });
  if (updErr) {
    throw new HttpError(400, updErr.message);
  }
  const sessionUser = requireUser(updated.user, new HttpError(400, 'Could not update password'));
  return sessionToJson(session, sessionUser);
}

export async function refreshSession(body: RefreshBody): Promise<AuthSessionResponse> {
  const supabase = createAnonClient();
  const { data, error } = await supabase.auth.refreshSession({
    refresh_token: body.refresh_token,
  });
  if (error) {
    throw new HttpError(401, error.message);
  }
  const { session, user } = requireSessionUser(
    data.session,
    data.user,
    new HttpError(401, 'Invalid refresh token'),
  );
  return sessionToJson(session, user);
}
