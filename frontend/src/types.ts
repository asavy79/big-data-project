export interface UserProfile {
  id: string;
  email: string | null;
  display_name: string | null;
  bio: string | null;
  skills: string[];
  location: string | null;
  remote_preference: boolean;
  salary_min: number | null;
  salary_max: number | null;
  needs_refresh: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface UserUpdate {
  email?: string | null;
  display_name?: string | null;
  bio?: string | null;
  skills?: string[] | null;
  location?: string | null;
  remote_preference?: boolean | null;
  salary_min?: number | null;
  salary_max?: number | null;
}

export interface JobMatch {
  matched_job_ids: number[];
  calculated_at: string;
}

export interface MatchesResponse {
  matches: JobMatch[];
  total: number;
}

export interface JobDetail {
  id: number;
  title: string;
  company: string;
  description: string | null;
  location: string | null;
  remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  url: string | null;
  source: string | null;
  posted_at: string | null;
  created_at: string | null;
}

export interface Occupation {
  soc_code: string;
  title: string;
  a_mean: number | null;
  a_median: number | null;
  tot_emp: number | null;
}

export interface OccupationDetail {
  soc_code: string;
  title: string;
  description: string;
  salary_and_education: {
    a_mean: number | null;
    a_median: number | null;
    tot_emp: number | null;
    preferred_education: string | null;
    preferred_edu_pct: number | null;
  } | null;
  top_skills: { skill_name: string; data_value: number }[];
}

export interface Skill {
  name: string;
  average_data_value: number;
}

export interface SkillDetail {
  skill_name: string;
  average_data_value: number;
  top_occupations: { soc_code: string; title: string; data_value: number }[];
}
