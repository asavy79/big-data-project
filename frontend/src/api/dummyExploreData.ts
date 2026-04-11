import type { Occupation, OccupationDetail, Skill, SkillDetail } from "../types";

const OCCUPATIONS: Occupation[] = [
  { soc_code: "11-1021", title: "General and Operations Managers", a_mean: 125_740, a_median: 101_280, tot_emp: 2_984_920 },
  { soc_code: "15-1252", title: "Software Developers", a_mean: 132_270, a_median: 127_260, tot_emp: 1_847_900 },
  { soc_code: "29-1228", title: "Physicians, All Other", a_mean: 229_300, a_median: 223_410, tot_emp: 69_410 },
  { soc_code: "15-2051", title: "Data Scientists", a_mean: 108_660, a_median: 103_500, tot_emp: 192_300 },
  { soc_code: "13-2011", title: "Accountants and Auditors", a_mean: 86_740, a_median: 79_880, tot_emp: 1_443_000 },
  { soc_code: "17-2199", title: "Engineers, All Other", a_mean: 106_350, a_median: 100_640, tot_emp: 165_600 },
  { soc_code: "23-1011", title: "Lawyers", a_mean: 176_580, a_median: 145_760, tot_emp: 813_900 },
  { soc_code: "15-1211", title: "Computer Systems Analysts", a_mean: 104_810, a_median: 102_240, tot_emp: 538_800 },
  { soc_code: "29-1141", title: "Registered Nurses", a_mean: 89_010, a_median: 81_220, tot_emp: 3_175_390 },
  { soc_code: "25-1011", title: "Business Teachers, Postsecondary", a_mean: 112_210, a_median: 96_640, tot_emp: 93_800 },
];

const SKILLS: Skill[] = [
  { name: "Critical Thinking", average_data_value: 4.12 },
  { name: "Complex Problem Solving", average_data_value: 3.98 },
  { name: "Judgment and Decision Making", average_data_value: 3.87 },
  { name: "Active Learning", average_data_value: 3.76 },
  { name: "Reading Comprehension", average_data_value: 3.72 },
  { name: "Systems Analysis", average_data_value: 3.65 },
  { name: "Programming", average_data_value: 3.58 },
  { name: "Mathematics", average_data_value: 3.45 },
  { name: "Science", average_data_value: 3.32 },
  { name: "Writing", average_data_value: 3.28 },
];

const OCCUPATION_DETAILS: Record<string, OccupationDetail> = {
  "15-1252": {
    soc_code: "15-1252",
    title: "Software Developers",
    description:
      "Research, design, and develop computer and network software or specialized utility programs. Analyze user needs and develop software solutions, applying principles and techniques of computer science, engineering, and mathematical analysis.",
    salary_and_education: {
      a_mean: 132_270,
      a_median: 127_260,
      tot_emp: 1_847_900,
      preferred_education: "Bachelor's degree",
      preferred_edu_pct: 68.2,
    },
    top_skills: [
      { skill_name: "Programming", data_value: 4.85 },
      { skill_name: "Complex Problem Solving", data_value: 4.50 },
      { skill_name: "Critical Thinking", data_value: 4.37 },
      { skill_name: "Systems Analysis", data_value: 4.25 },
      { skill_name: "Mathematics", data_value: 3.90 },
      { skill_name: "Active Learning", data_value: 3.85 },
      { skill_name: "Judgment and Decision Making", data_value: 3.62 },
      { skill_name: "Reading Comprehension", data_value: 3.50 },
    ],
  },
  "11-1021": {
    soc_code: "11-1021",
    title: "General and Operations Managers",
    description:
      "Plan, direct, or coordinate the operations of public or private sector organizations, overseeing multiple departments or locations.",
    salary_and_education: {
      a_mean: 125_740,
      a_median: 101_280,
      tot_emp: 2_984_920,
      preferred_education: "Bachelor's degree",
      preferred_edu_pct: 55.0,
    },
    top_skills: [
      { skill_name: "Judgment and Decision Making", data_value: 4.50 },
      { skill_name: "Critical Thinking", data_value: 4.37 },
      { skill_name: "Complex Problem Solving", data_value: 4.12 },
      { skill_name: "Active Learning", data_value: 3.75 },
      { skill_name: "Writing", data_value: 3.50 },
      { skill_name: "Reading Comprehension", data_value: 3.45 },
    ],
  },
  "29-1228": {
    soc_code: "29-1228",
    title: "Physicians, All Other",
    description:
      "Diagnose and treat diseases and injuries. Includes physicians with specialties not separately classified.",
    salary_and_education: {
      a_mean: 229_300,
      a_median: 223_410,
      tot_emp: 69_410,
      preferred_education: "Doctoral or professional degree",
      preferred_edu_pct: 92.0,
    },
    top_skills: [
      { skill_name: "Critical Thinking", data_value: 4.75 },
      { skill_name: "Judgment and Decision Making", data_value: 4.62 },
      { skill_name: "Science", data_value: 4.50 },
      { skill_name: "Active Learning", data_value: 4.37 },
      { skill_name: "Reading Comprehension", data_value: 4.25 },
      { skill_name: "Complex Problem Solving", data_value: 4.12 },
    ],
  },
  "15-2051": {
    soc_code: "15-2051",
    title: "Data Scientists",
    description:
      "Develop and implement methods to collect, process, and analyze large datasets. Use statistical techniques, machine learning, and data visualization to extract insights.",
    salary_and_education: {
      a_mean: 108_660,
      a_median: 103_500,
      tot_emp: 192_300,
      preferred_education: "Master's degree",
      preferred_edu_pct: 52.3,
    },
    top_skills: [
      { skill_name: "Mathematics", data_value: 4.62 },
      { skill_name: "Programming", data_value: 4.50 },
      { skill_name: "Critical Thinking", data_value: 4.37 },
      { skill_name: "Complex Problem Solving", data_value: 4.25 },
      { skill_name: "Systems Analysis", data_value: 4.00 },
      { skill_name: "Active Learning", data_value: 3.87 },
      { skill_name: "Science", data_value: 3.75 },
    ],
  },
  "13-2011": {
    soc_code: "13-2011",
    title: "Accountants and Auditors",
    description:
      "Examine, analyze, and interpret accounting records to prepare financial statements, give advice, or audit and evaluate statements.",
    salary_and_education: {
      a_mean: 86_740,
      a_median: 79_880,
      tot_emp: 1_443_000,
      preferred_education: "Bachelor's degree",
      preferred_edu_pct: 72.0,
    },
    top_skills: [
      { skill_name: "Mathematics", data_value: 4.25 },
      { skill_name: "Critical Thinking", data_value: 4.00 },
      { skill_name: "Reading Comprehension", data_value: 3.87 },
      { skill_name: "Judgment and Decision Making", data_value: 3.75 },
      { skill_name: "Active Learning", data_value: 3.37 },
      { skill_name: "Writing", data_value: 3.25 },
    ],
  },
  "17-2199": {
    soc_code: "17-2199",
    title: "Engineers, All Other",
    description:
      "All engineers not listed separately, applying engineering principles to design, develop, and evaluate systems and processes.",
    salary_and_education: {
      a_mean: 106_350,
      a_median: 100_640,
      tot_emp: 165_600,
      preferred_education: "Bachelor's degree",
      preferred_edu_pct: 62.5,
    },
    top_skills: [
      { skill_name: "Complex Problem Solving", data_value: 4.50 },
      { skill_name: "Critical Thinking", data_value: 4.37 },
      { skill_name: "Mathematics", data_value: 4.25 },
      { skill_name: "Science", data_value: 4.00 },
      { skill_name: "Systems Analysis", data_value: 3.87 },
      { skill_name: "Judgment and Decision Making", data_value: 3.62 },
    ],
  },
  "23-1011": {
    soc_code: "23-1011",
    title: "Lawyers",
    description:
      "Represent clients in criminal and civil litigation and other legal proceedings, draw up legal documents, or manage or advise clients on legal transactions.",
    salary_and_education: {
      a_mean: 176_580,
      a_median: 145_760,
      tot_emp: 813_900,
      preferred_education: "Doctoral or professional degree",
      preferred_edu_pct: 98.0,
    },
    top_skills: [
      { skill_name: "Critical Thinking", data_value: 4.75 },
      { skill_name: "Reading Comprehension", data_value: 4.62 },
      { skill_name: "Judgment and Decision Making", data_value: 4.50 },
      { skill_name: "Writing", data_value: 4.37 },
      { skill_name: "Active Learning", data_value: 4.00 },
      { skill_name: "Complex Problem Solving", data_value: 3.87 },
    ],
  },
  "15-1211": {
    soc_code: "15-1211",
    title: "Computer Systems Analysts",
    description:
      "Analyze science, engineering, business, and other data processing problems to develop and implement solutions to complex applications problems, system administration issues, or network concerns.",
    salary_and_education: {
      a_mean: 104_810,
      a_median: 102_240,
      tot_emp: 538_800,
      preferred_education: "Bachelor's degree",
      preferred_edu_pct: 60.0,
    },
    top_skills: [
      { skill_name: "Systems Analysis", data_value: 4.62 },
      { skill_name: "Critical Thinking", data_value: 4.37 },
      { skill_name: "Complex Problem Solving", data_value: 4.12 },
      { skill_name: "Active Learning", data_value: 3.87 },
      { skill_name: "Programming", data_value: 3.75 },
      { skill_name: "Judgment and Decision Making", data_value: 3.62 },
    ],
  },
  "29-1141": {
    soc_code: "29-1141",
    title: "Registered Nurses",
    description:
      "Assess patient health problems and needs, develop and implement nursing care plans, and maintain medical records.",
    salary_and_education: {
      a_mean: 89_010,
      a_median: 81_220,
      tot_emp: 3_175_390,
      preferred_education: "Bachelor's degree",
      preferred_edu_pct: 64.0,
    },
    top_skills: [
      { skill_name: "Critical Thinking", data_value: 4.50 },
      { skill_name: "Active Learning", data_value: 4.25 },
      { skill_name: "Judgment and Decision Making", data_value: 4.12 },
      { skill_name: "Science", data_value: 3.87 },
      { skill_name: "Reading Comprehension", data_value: 3.75 },
      { skill_name: "Complex Problem Solving", data_value: 3.50 },
    ],
  },
  "25-1011": {
    soc_code: "25-1011",
    title: "Business Teachers, Postsecondary",
    description:
      "Teach courses in business administration and management at the postsecondary level, including courses in accounting, finance, and marketing.",
    salary_and_education: {
      a_mean: 112_210,
      a_median: 96_640,
      tot_emp: 93_800,
      preferred_education: "Doctoral or professional degree",
      preferred_edu_pct: 75.0,
    },
    top_skills: [
      { skill_name: "Critical Thinking", data_value: 4.25 },
      { skill_name: "Active Learning", data_value: 4.12 },
      { skill_name: "Writing", data_value: 4.00 },
      { skill_name: "Reading Comprehension", data_value: 3.87 },
      { skill_name: "Judgment and Decision Making", data_value: 3.75 },
      { skill_name: "Complex Problem Solving", data_value: 3.50 },
    ],
  },
};

const SKILL_DETAILS: Record<string, SkillDetail> = {
  "Critical Thinking": {
    skill_name: "Critical Thinking",
    average_data_value: 4.12,
    top_occupations: [
      { soc_code: "29-1228", title: "Physicians, All Other", data_value: 4.75 },
      { soc_code: "23-1011", title: "Lawyers", data_value: 4.75 },
      { soc_code: "29-1141", title: "Registered Nurses", data_value: 4.50 },
      { soc_code: "15-1252", title: "Software Developers", data_value: 4.37 },
      { soc_code: "15-2051", title: "Data Scientists", data_value: 4.37 },
      { soc_code: "17-2199", title: "Engineers, All Other", data_value: 4.37 },
      { soc_code: "15-1211", title: "Computer Systems Analysts", data_value: 4.37 },
      { soc_code: "11-1021", title: "General and Operations Managers", data_value: 4.37 },
    ],
  },
  "Complex Problem Solving": {
    skill_name: "Complex Problem Solving",
    average_data_value: 3.98,
    top_occupations: [
      { soc_code: "15-1252", title: "Software Developers", data_value: 4.50 },
      { soc_code: "17-2199", title: "Engineers, All Other", data_value: 4.50 },
      { soc_code: "15-2051", title: "Data Scientists", data_value: 4.25 },
      { soc_code: "15-1211", title: "Computer Systems Analysts", data_value: 4.12 },
      { soc_code: "11-1021", title: "General and Operations Managers", data_value: 4.12 },
      { soc_code: "29-1228", title: "Physicians, All Other", data_value: 4.12 },
    ],
  },
  "Judgment and Decision Making": {
    skill_name: "Judgment and Decision Making",
    average_data_value: 3.87,
    top_occupations: [
      { soc_code: "29-1228", title: "Physicians, All Other", data_value: 4.62 },
      { soc_code: "11-1021", title: "General and Operations Managers", data_value: 4.50 },
      { soc_code: "23-1011", title: "Lawyers", data_value: 4.50 },
      { soc_code: "29-1141", title: "Registered Nurses", data_value: 4.12 },
      { soc_code: "13-2011", title: "Accountants and Auditors", data_value: 3.75 },
    ],
  },
  "Active Learning": {
    skill_name: "Active Learning",
    average_data_value: 3.76,
    top_occupations: [
      { soc_code: "29-1228", title: "Physicians, All Other", data_value: 4.37 },
      { soc_code: "29-1141", title: "Registered Nurses", data_value: 4.25 },
      { soc_code: "25-1011", title: "Business Teachers, Postsecondary", data_value: 4.12 },
      { soc_code: "23-1011", title: "Lawyers", data_value: 4.00 },
      { soc_code: "15-2051", title: "Data Scientists", data_value: 3.87 },
      { soc_code: "15-1252", title: "Software Developers", data_value: 3.85 },
    ],
  },
  "Reading Comprehension": {
    skill_name: "Reading Comprehension",
    average_data_value: 3.72,
    top_occupations: [
      { soc_code: "23-1011", title: "Lawyers", data_value: 4.62 },
      { soc_code: "29-1228", title: "Physicians, All Other", data_value: 4.25 },
      { soc_code: "13-2011", title: "Accountants and Auditors", data_value: 3.87 },
      { soc_code: "25-1011", title: "Business Teachers, Postsecondary", data_value: 3.87 },
      { soc_code: "29-1141", title: "Registered Nurses", data_value: 3.75 },
    ],
  },
  "Systems Analysis": {
    skill_name: "Systems Analysis",
    average_data_value: 3.65,
    top_occupations: [
      { soc_code: "15-1211", title: "Computer Systems Analysts", data_value: 4.62 },
      { soc_code: "15-1252", title: "Software Developers", data_value: 4.25 },
      { soc_code: "15-2051", title: "Data Scientists", data_value: 4.00 },
      { soc_code: "17-2199", title: "Engineers, All Other", data_value: 3.87 },
    ],
  },
  "Programming": {
    skill_name: "Programming",
    average_data_value: 3.58,
    top_occupations: [
      { soc_code: "15-1252", title: "Software Developers", data_value: 4.85 },
      { soc_code: "15-2051", title: "Data Scientists", data_value: 4.50 },
      { soc_code: "15-1211", title: "Computer Systems Analysts", data_value: 3.75 },
    ],
  },
  "Mathematics": {
    skill_name: "Mathematics",
    average_data_value: 3.45,
    top_occupations: [
      { soc_code: "15-2051", title: "Data Scientists", data_value: 4.62 },
      { soc_code: "13-2011", title: "Accountants and Auditors", data_value: 4.25 },
      { soc_code: "17-2199", title: "Engineers, All Other", data_value: 4.25 },
      { soc_code: "15-1252", title: "Software Developers", data_value: 3.90 },
    ],
  },
  Science: {
    skill_name: "Science",
    average_data_value: 3.32,
    top_occupations: [
      { soc_code: "29-1228", title: "Physicians, All Other", data_value: 4.50 },
      { soc_code: "17-2199", title: "Engineers, All Other", data_value: 4.00 },
      { soc_code: "29-1141", title: "Registered Nurses", data_value: 3.87 },
      { soc_code: "15-2051", title: "Data Scientists", data_value: 3.75 },
    ],
  },
  Writing: {
    skill_name: "Writing",
    average_data_value: 3.28,
    top_occupations: [
      { soc_code: "23-1011", title: "Lawyers", data_value: 4.37 },
      { soc_code: "25-1011", title: "Business Teachers, Postsecondary", data_value: 4.00 },
      { soc_code: "11-1021", title: "General and Operations Managers", data_value: 3.50 },
      { soc_code: "13-2011", title: "Accountants and Auditors", data_value: 3.25 },
    ],
  },
};

export async function fetchTopOccupations(): Promise<Occupation[]> {
  return OCCUPATIONS;
}

export async function fetchOccupationDetail(socCode: string): Promise<OccupationDetail | null> {
  return OCCUPATION_DETAILS[socCode] ?? null;
}

export async function fetchTopSkills(): Promise<Skill[]> {
  return SKILLS;
}

export async function fetchSkillDetail(name: string): Promise<SkillDetail | null> {
  const key = Object.keys(SKILL_DETAILS).find((k) => k.toLowerCase() === name.toLowerCase());
  return key ? SKILL_DETAILS[key] : null;
}
