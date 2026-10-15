/**
 * Server-side API client.
 *
 * Everything here runs on the Next.js server: the admin token is read from a
 * non-public environment variable and never reaches the browser bundle.
 */
import { getSessionToken } from "./session";
import type {
  AdminOpportunity,
  AdminStats,
  CategoryInfo,
  DashboardPayload,
  DeadlinesPayload,
  Facets,
  Opportunity,
  OpportunityDetail,
  Page,
  Profile,
  Review,
  SavedPayload,
  SourceRecord,
  Stats,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ADMIN_TOKEN = process.env.ZENKAI_ADMIN_TOKEN ?? "dev-admin-token";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly url: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends RequestInit {
  /**
   * Seconds to cache in Next's data cache.
   *
   * Defaults to 0. Most endpoints embed per-user fields (`is_saved`, `match`),
   * and the data cache is shared across requests — caching those would leak one
   * user's state to another. Only genuinely shared, user-independent data
   * (categories, facet counts) opts into caching.
   */
  revalidate?: number;
  admin?: boolean;
  /** Skip session forwarding — for sign-up and sign-in. */
  anonymous?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { revalidate = 0, admin = false, anonymous = false, headers, ...init } = options;
  const url = `${API_URL}${path}`;

  // Forward the caller's session unless the request is deliberately anonymous
  // (sign-up and sign-in, which have no session yet).
  const token = anonymous ? null : await getSessionToken();

  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      // Service-account fallback, used only when nobody is signed in. A signed-in
      // reviewer authorises through their own account instead.
      ...(admin && !token ? { "X-Admin-Token": ADMIN_TOKEN } : {}),
      ...headers,
    },
    ...(init.method && init.method !== "GET"
      ? { cache: "no-store" as const }
      : revalidate > 0
        ? { next: { revalidate } }
        : { cache: "no-store" as const }),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* response had no JSON body */
    }
    throw new ApiError(detail, response.status, url);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** Build a query string, dropping empty values and expanding arrays. */
export function qs(params: Record<string, string | number | boolean | string[] | undefined | null>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((v) => search.append(key, String(v)));
    } else {
      search.set(key, String(value));
    }
  }
  const out = search.toString();
  return out ? `?${out}` : "";
}

export interface SessionResponse {
  token: string;
  expires_at: string;
  user: Profile;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  auth: {
    signup: (body: { email: string; name: string; password: string }) =>
      request<SessionResponse>("/api/v1/auth/signup", {
        method: "POST",
        anonymous: true,
        body: JSON.stringify(body),
      }),

    login: (body: { email: string; password: string }) =>
      request<SessionResponse>("/api/v1/auth/login", {
        method: "POST",
        anonymous: true,
        body: JSON.stringify(body),
      }),

    logout: () => request<{ detail: string }>("/api/v1/auth/logout", { method: "POST" }),

    me: () => request<Profile>("/api/v1/auth/me"),

    changePassword: (body: { current_password: string; new_password: string }) =>
      request<SessionResponse>("/api/v1/auth/change-password", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },

  opportunities: (params: Parameters<typeof qs>[0] = {}) =>
    request<Page<Opportunity>>(`/api/v1/opportunities${qs(params)}`),

  opportunity: (identifier: string) =>
    request<OpportunityDetail>(`/api/v1/opportunities/${encodeURIComponent(identifier)}`),

  /*
    Public, user-independent data. Marked anonymous for two reasons: it skips
    reading cookies, which lets the landing page stay statically generated, and
    it guarantees a response cached in the shared data cache cannot vary by
    user.
  */
  facets: () =>
    request<Facets>("/api/v1/opportunities/facets", { revalidate: 120, anonymous: true }),

  categories: () =>
    request<CategoryInfo[]>("/api/v1/categories", { revalidate: 120, anonymous: true }),

  dashboard: (limit = 6) =>
    request<DashboardPayload>(`/api/v1/dashboard${qs({ limit })}`),

  stats: () => request<Stats>("/api/v1/stats"),

  recommendations: (limit = 12) =>
    request<Opportunity[]>(`/api/v1/recommendations${qs({ limit })}`),

  saved: () => request<SavedPayload>("/api/v1/saved"),

  save: (opportunity_id: string) =>
    request<{ saved: boolean; created: boolean }>("/api/v1/saved", {
      method: "POST",
      body: JSON.stringify({ opportunity_id }),
    }),

  unsave: (opportunity_id: string) =>
    request<{ saved: boolean }>(`/api/v1/saved/${opportunity_id}`, { method: "DELETE" }),

  deadlines: (params: Parameters<typeof qs>[0] = {}) =>
    request<DeadlinesPayload>(`/api/v1/deadlines${qs(params)}`),

  profile: () => request<Profile>("/api/v1/profile"),

  updateProfile: (body: unknown) =>
    request<Profile>("/api/v1/profile", { method: "PUT", body: JSON.stringify(body) }),

  admin: {
    stats: () => request<AdminStats>("/api/v1/admin/stats", { admin: true }),

    queue: (status: string, limit = 25, offset = 0) =>
      request<Page<AdminOpportunity>>(`/api/v1/admin/queue${qs({ status, limit, offset })}`, {
        admin: true,
      }),

    approve: (id: string, reviewer: string, notes?: string) =>
      request<Review>(`/api/v1/admin/opportunities/${id}/approve`, {
        method: "POST",
        admin: true,
        body: JSON.stringify({ reviewer, notes }),
      }),

    reject: (id: string, reviewer: string, notes?: string) =>
      request<Review>(`/api/v1/admin/opportunities/${id}/reject`, {
        method: "POST",
        admin: true,
        body: JSON.stringify({ reviewer, notes }),
      }),

    edit: (id: string, reviewer: string, changes: Record<string, unknown>, notes?: string) =>
      request<Review>(`/api/v1/admin/opportunities/${id}/edit`, {
        method: "POST",
        admin: true,
        body: JSON.stringify({ reviewer, changes, notes }),
      }),

    sources: () => request<SourceRecord[]>("/api/v1/admin/sources", { admin: true, revalidate: 60 }),
  },
};
