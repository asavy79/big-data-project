import type {
  FilterMetadataResponse,
  GuidedQuestionsResponse,
  InsightOccupationDetail,
  Occupation,
  OccupationFilterResponse,
  Skill,
  SkillDetail,
  TextInsightMode,
  TextInsightResponse,
} from "../types";
import { insightsApiBaseUrl } from "../config";

const base = insightsApiBaseUrl;

async function parseErrorBody(res: Response): Promise<string> {
  const text = await res.text().catch(() => "Unknown error");
  try {
    const j = JSON.parse(text) as { detail?: unknown };
    if (Array.isArray(j.detail)) {
      return j.detail
        .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
        .join("; ");
    }
  } catch {
    /* ignore */
  }
  return text;
}

async function requestJson<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const msg = await parseErrorBody(res);
    throw new Error(`Insights API ${res.status}: ${msg}`);
  }
  return res.json();
}

async function getJson<T>(url: string): Promise<T> {
  return requestJson<T>(url);
}

async function getJsonOrNull<T>(url: string): Promise<T | null> {
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) {
    const msg = await parseErrorBody(res);
    throw new Error(`Insights API ${res.status}: ${msg}`);
  }
  return res.json();
}

// ——— Insights ———

export async function postTextInsight(
  text: string,
  mode: TextInsightMode
): Promise<TextInsightResponse> {
  return requestJson<TextInsightResponse>(`${base}/insights/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, mode }),
  });
}

export async function getGuidedQuestions(): Promise<GuidedQuestionsResponse> {
  return getJson<GuidedQuestionsResponse>(`${base}/insights/questions`);
}

export async function getFilterMetadata(): Promise<FilterMetadataResponse> {
  return getJson<FilterMetadataResponse>(`${base}/insights/filters/metadata`);
}

export async function filterOccupations(params: {
  skill?: string | null;
  min_salary?: number | null;
  min_skill_score?: number | null;
  education?: string | null;
}): Promise<OccupationFilterResponse> {
  const sp = new URLSearchParams();
  if (params.skill != null && params.skill !== "")
    sp.set("skill", params.skill);
  if (params.min_salary != null) sp.set("min_salary", String(params.min_salary));
  if (params.min_skill_score != null)
    sp.set("min_skill_score", String(params.min_skill_score));
  if (params.education != null && params.education !== "")
    sp.set("education", params.education);
  const q = sp.toString();
  const url = `${base}/insights/occupations/filter${q ? `?${q}` : ""}`;
  return getJson<OccupationFilterResponse>(url);
}

export async function fetchInsightOccupationDetail(
  socCode: string
): Promise<InsightOccupationDetail> {
  const encoded = encodeURIComponent(socCode);
  return getJson<InsightOccupationDetail>(
    `${base}/insights/occupation/${encoded}`
  );
}

// ——— Legacy browse endpoints (same deployment) ———

export async function fetchTopOccupations(): Promise<Occupation[]> {
  const data = await getJson<{ top_occupations: Occupation[] }>(
    `${base}/top-occupations`
  );
  return data.top_occupations;
}

export async function fetchTopSkills(): Promise<Skill[]> {
  const data = await getJson<{ top_skills: Skill[] }>(`${base}/top-skills`);
  return data.top_skills;
}

export async function fetchSkillDetail(
  name: string
): Promise<SkillDetail | null> {
  const encoded = encodeURIComponent(name);
  return getJsonOrNull<SkillDetail>(`${base}/skill/${encoded}`);
}
