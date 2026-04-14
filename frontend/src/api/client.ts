import type { JobDetail, MatchesResponse, UserProfile, UserUpdate } from "../types";
import { gatewayBaseUrl } from "../config";

const USER_API = `${gatewayBaseUrl}/api/user`;
const JOBS_API = `${gatewayBaseUrl}/api/jobs`;

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export function userApi(token: string) {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };

  return {
    getProfile: () =>
      request<UserProfile>(`${USER_API}/me`, { headers }),

    updateProfile: (data: UserUpdate) =>
      request<UserProfile>(`${USER_API}/me`, {
        method: "PATCH",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),

    getMatches: () =>
      request<MatchesResponse>(`${USER_API}/me/matches`, { headers }),
  };
}

export function jobsApi() {
  return {
    getJob: (id: number) => request<JobDetail>(`${JOBS_API}/jobs/${id}`),

    getJobsBatch: (ids: number[]) => {
      if (ids.length === 0) return Promise.resolve([]);
      const params = ids.map((id) => `ids=${id}`).join("&");
      return request<JobDetail[]>(`${JOBS_API}/jobs/batch?${params}`);
    },
  };
}
