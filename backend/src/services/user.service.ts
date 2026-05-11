import { HttpError } from '../common/HttpError.js';
import { createAdminClient, createUserScopedClient } from '../lib/supabase.js';
import type { UserRoleName } from '../types/roles.js';
import type { UpdateMyProfileBody, UpdateUserByIdBody } from '../schemas/user.schemas.js';

interface ProfileRow {
  id: string;
  display_name: string | null;
  avatar_url: string | null;
  role_id: string;
  roles: { name: UserRoleName } | { name: UserRoleName }[] | null;
}

function normalizeRole(row: ProfileRow): UserRoleName {
  const r = row.roles;
  if (Array.isArray(r)) {
    const name = r[0]?.name;
    if (name) {
      return name;
    }
  } else if (r?.name) {
    return r.name;
  }
  throw new HttpError(500, 'Profile role is missing');
}

function toPublicProfile(row: ProfileRow) {
  return {
    id: row.id,
    display_name: row.display_name,
    avatar_url: row.avatar_url,
    role: normalizeRole(row),
  };
}

export async function getProfileByAccessToken(accessToken: string) {
  const supabase = createUserScopedClient(accessToken);
  const { data, error } = await supabase
    .from('profiles')
    .select('id, display_name, avatar_url, role_id, roles(name)')
    .maybeSingle();

  if (error) {
    throw new HttpError(400, error.message);
  }
  if (!data) {
    throw new HttpError(404, 'Profile not found');
  }
  return toPublicProfile(data);
}

export async function updateMyProfile(accessToken: string, userId: string, body: UpdateMyProfileBody) {
  const supabase = createUserScopedClient(accessToken);
  const patch: Record<string, unknown> = {};
  if (body.display_name !== undefined) {
    patch['display_name'] = body.display_name;
  }
  if (body.avatar_url !== undefined) {
    patch['avatar_url'] = body.avatar_url;
  }

  const { data, error } = await supabase
    .from('profiles')
    .update(patch)
    .eq('id', userId)
    .select('id, display_name, avatar_url, role_id, roles(name)')
    .maybeSingle();

  if (error) {
    throw new HttpError(400, error.message);
  }
  if (!data) {
    throw new HttpError(404, 'Profile not found');
  }
  return toPublicProfile(data);
}

async function resolveRoleId(admin: ReturnType<typeof createAdminClient>, role: UserRoleName) {
  const { data, error } = await admin.from('roles').select('id').eq('name', role).maybeSingle();
  if (error) {
    throw new HttpError(500, error.message);
  }
  const rawId: unknown = data?.id;
  if (typeof rawId !== 'string') {
    throw new HttpError(400, 'Unknown role');
  }
  return rawId;
}

/** Admin-only: uses service role after route-level RBAC. */
export async function updateUserAsAdmin(targetUserId: string, body: UpdateUserByIdBody) {
  const admin = createAdminClient();
  const patch: Record<string, unknown> = {};
  if (body.display_name !== undefined) {
    patch['display_name'] = body.display_name;
  }
  if (body.avatar_url !== undefined) {
    patch['avatar_url'] = body.avatar_url;
  }
  if (body.role !== undefined) {
    patch['role_id'] = await resolveRoleId(admin, body.role);
  }

  const { data, error } = await admin
    .from('profiles')
    .update(patch)
    .eq('id', targetUserId)
    .select('id, display_name, avatar_url, role_id, roles(name)')
    .maybeSingle();

  if (error) {
    throw new HttpError(400, error.message);
  }
  if (!data) {
    throw new HttpError(404, 'User not found');
  }
  return toPublicProfile(data);
}

export async function listUsersAsAdmin(params: { limit: number; offset: number }) {
  const admin = createAdminClient();
  const { data, error, count } = await admin
    .from('profiles')
    .select('id, display_name, avatar_url, role_id, roles(name)', { count: 'exact' })
    .order('created_at', { ascending: true })
    .range(params.offset, params.offset + params.limit - 1);

  if (error) {
    throw new HttpError(400, error.message);
  }
  const rows: ProfileRow[] = data;
  return {
    items: rows.map(toPublicProfile),
    total: count,
  };
}
