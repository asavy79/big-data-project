import type { Occupation, OccupationDetail, Skill, SkillDetail } from "../types";
import { careerApiBaseUrl } from "../config";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Career API ${res.status}: ${text}`);
  }
  return res.json();
}

async function getJsonOrNull<T>(url: string): Promise<T | null> {
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Career API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function fetchTopOccupations(): Promise<Occupation[]> {
  const data = await getJson<{ top_occupations: Occupation[] }>(
    `${careerApiBaseUrl}/top-occupations`
  );
  return data.top_occupations;
}

export async function fetchOccupationDetail(socCode: string): Promise<OccupationDetail | null> {
  const encoded = encodeURIComponent(socCode);
  return getJsonOrNull<OccupationDetail>(`${careerApiBaseUrl}/occupation/${encoded}`);
}

export async function fetchTopSkills(): Promise<Skill[]> {
  const data = await getJson<{ top_skills: Skill[] }>(`${careerApiBaseUrl}/top-skills`);
  return data.top_skills;
}

export async function fetchSkillDetail(name: string): Promise<SkillDetail | null> {
  const encoded = encodeURIComponent(name);
  return getJsonOrNull<SkillDetail>(`${careerApiBaseUrl}/skill/${encoded}`);
}
