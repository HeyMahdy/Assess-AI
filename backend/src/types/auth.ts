import type { UserRoleName } from './roles.js';

export interface AuthUser {
  id: string;
  email?: string | undefined;
  accessToken: string;
}

export interface ProfileContext {
  id: string;
  role: UserRoleName;
  display_name: string | null;
  avatar_url: string | null;
}
