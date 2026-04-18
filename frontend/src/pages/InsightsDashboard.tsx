import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { userApi } from "../api/client";
import Header from "../components/Header";
import OccupationDetail from "../components/explore/OccupationDetail";
import SkillDetail from "../components/explore/SkillDetail";
import {
  filterOccupations,
  getFilterMetadata,
  getGuidedQuestions,
  postTextInsight,
} from "../api/insightsApi";
import type {
  FilterMetadataResponse,
  OccupationResult,
  TextInsightMode,
  TextInsightResponse,
} from "../types";

type BrowseSelection =
  | { kind: "none" }
  | { kind: "occupation"; socCode: string }
  | { kind: "skill"; name: string };

function formatSalary(val: number | null | undefined): string {
  if (val == null) return "—";
  return "$" + val.toLocaleString();
}

function formatEmployment(val: number | null | undefined): string {
  if (val == null) return "—";
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + "M";
  if (val >= 1_000) return (val / 1_000).toFixed(0) + "K";
  return val.toLocaleString();
}

function OccupationResultCard({
  row,
  onSelect,
  highlightScore,
}: {
  row: OccupationResult;
  onSelect: (soc: string) => void;
  highlightScore?: boolean;
}) {
  const score =
    row.average_skill_score ?? row.skill_score ?? null;
  return (
    <button
      type="button"
      onClick={() => onSelect(row.soc_code)}
      className="w-full text-left bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:border-indigo-200 hover:shadow transition cursor-pointer"
    >
      <p className="text-xs text-gray-400 font-mono">{row.soc_code}</p>
      <p className="text-sm font-semibold text-gray-900 mt-0.5">{row.title}</p>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
        <span>Mean {formatSalary(row.a_mean)}</span>
        <span>Med. {formatSalary(row.a_median)}</span>
        <span>Emp. {formatEmployment(row.tot_emp)}</span>
        {highlightScore && score != null && (
          <span className="text-indigo-600 font-medium tabular-nums">
            Score {Number(score).toFixed(2)}
          </span>
        )}
      </div>
      {row.preferred_education && (
        <p className="text-xs text-gray-500 mt-2">{row.preferred_education}</p>
      )}
    </button>
  );
}

const MODE_OPTIONS: { value: TextInsightMode; label: string; hint: string }[] = [
  { value: "full", label: "Full", hint: "Skills, occupations, and recommendations" },
  { value: "occupations", label: "Occupations", hint: "Top matching roles" },
  { value: "skills_gap", label: "Skills gap", hint: "Skills to develop" },
  { value: "learning", label: "Learning", hint: "What to learn next" },
];

/** Build request body: visible user text + profile skills (not shown in the textarea). */
function buildInsightPayload(visible: string, profileSkills: string[]): string {
  const v = visible.trim();
  const skillsLine = profileSkills.length ? profileSkills.join(", ") : "";
  if (!v) return skillsLine;
  if (!skillsLine) return v;
  return `${v}\n\n${skillsLine}`;
}

export default function InsightsDashboard() {
  const { user } = useAuth();

  const [browse, setBrowse] = useState<BrowseSelection>({ kind: "none" });

  const [profileSkills, setProfileSkills] = useState<string[]>([]);

  const [questions, setQuestions] = useState<string[]>([]);

  const [metadata, setMetadata] = useState<FilterMetadataResponse | null>(null);

  const [inputText, setInputText] = useState("");
  const [mode, setMode] = useState<TextInsightMode>("full");
  const [textResult, setTextResult] = useState<TextInsightResponse | null>(null);
  const [textLoading, setTextLoading] = useState(false);
  const [textError, setTextError] = useState<string | null>(null);

  const [filterSkill, setFilterSkill] = useState("");
  const [filterMinSalary, setFilterMinSalary] = useState("");
  const [filterMinSkillScore, setFilterMinSkillScore] = useState("");
  const [filterEducation, setFilterEducation] = useState("");
  const [filterResults, setFilterResults] = useState<OccupationResult[] | null>(null);
  const [filterLoading, setFilterLoading] = useState(false);
  const [filterError, setFilterError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    user
      .getIdToken()
      .then((token) => userApi(token).getProfile())
      .then((p) => setProfileSkills(p.skills ?? []))
      .catch(() => setProfileSkills([]));
  }, [user]);

  useEffect(() => {
    getGuidedQuestions()
      .then((r) => setQuestions(r.questions ?? []))
      .catch(() => setQuestions([]));
  }, []);

  useEffect(() => {
    getFilterMetadata()
      .then(setMetadata)
      .catch(() => setMetadata(null));
  }, []);

  const selectOccupation = useCallback((socCode: string) => {
    setBrowse({ kind: "occupation", socCode });
  }, []);

  const selectSkill = useCallback((name: string) => {
    setBrowse({ kind: "skill", name });
  }, []);

  const clearBrowse = useCallback(() => setBrowse({ kind: "none" }), []);

  const canAnalyze =
    inputText.trim().length > 0 || profileSkills.length > 0;

  const runTextAnalysis = async () => {
    if (!user) return;
    if (!canAnalyze) {
      setTextError("Add text above or add skills to your profile.");
      return;
    }
    setTextLoading(true);
    setTextError(null);
    try {
      let skills = profileSkills;
      try {
        const token = await user.getIdToken();
        const fresh = await userApi(token).getProfile();
        skills = fresh.skills ?? [];
        setProfileSkills(skills);
      } catch {
        /* use cached profileSkills */
      }
      const payload = buildInsightPayload(inputText, skills);
      if (!payload.trim()) {
        setTextError("Nothing to analyze.");
        setTextLoading(false);
        return;
      }
      const res = await postTextInsight(payload, mode);
      setTextResult(res);
    } catch (e: unknown) {
      setTextError(e instanceof Error ? e.message : "Analysis failed");
      setTextResult(null);
    } finally {
      setTextLoading(false);
    }
  };

  const runFilter = useCallback(async () => {
    setFilterLoading(true);
    setFilterError(null);
    try {
      const minSalary =
        filterMinSalary.trim() === "" ? null : Number(filterMinSalary);
      const minSkill =
        filterMinSkillScore.trim() === "" ? null : Number(filterMinSkillScore);
      const res = await filterOccupations({
        skill: filterSkill || null,
        min_salary: minSalary != null && !Number.isNaN(minSalary) ? minSalary : null,
        min_skill_score:
          minSkill != null && !Number.isNaN(minSkill) ? minSkill : null,
        education: filterEducation || null,
      });
      setFilterResults(res.results ?? []);
    } catch (e: unknown) {
      setFilterError(e instanceof Error ? e.message : "Filter failed");
      setFilterResults(null);
    } finally {
      setFilterLoading(false);
    }
  }, [filterSkill, filterMinSalary, filterMinSkillScore, filterEducation]);

  const applyFirstDetectedSkill = () => {
    const first = textResult?.detected_skills?.[0];
    if (!first) return;
    setFilterSkill(first);
    setFilterLoading(true);
    setFilterError(null);
    const minSalary =
      filterMinSalary.trim() === "" ? null : Number(filterMinSalary);
    const minSkill =
      filterMinSkillScore.trim() === "" ? null : Number(filterMinSkillScore);
    filterOccupations({
      skill: first,
      min_salary: minSalary != null && !Number.isNaN(minSalary) ? minSalary : null,
      min_skill_score:
        minSkill != null && !Number.isNaN(minSkill) ? minSkill : null,
      education: filterEducation || null,
    })
      .then((res) => setFilterResults(res.results ?? []))
      .catch((e: unknown) => {
        setFilterError(e instanceof Error ? e.message : "Filter failed");
        setFilterResults(null);
      })
      .finally(() => setFilterLoading(false));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Insights</h1>
          <p className="text-sm text-gray-500 mt-1 max-w-2xl">
            Describe goals or interests in your own words. We match keywords to skills
            and occupations; your profile skills are included in the analysis
            automatically when you run it.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
          <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Text insights</h2>

            <label className="block text-xs font-medium text-gray-500 mb-2">Mode</label>
            <div className="flex flex-wrap gap-2 mb-4">
              {MODE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  title={opt.hint}
                  onClick={() => setMode(opt.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition cursor-pointer ${
                    mode === opt.value
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <label htmlFor="insight-text" className="block text-xs font-medium text-gray-500 mb-2">
              Your text
            </label>
            <textarea
              id="insight-text"
              rows={5}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="e.g. I enjoy data analysis, Python, and presenting findings to stakeholders."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <p className="mt-2 text-xs text-gray-500">
              {profileSkills.length > 0 ? (
                <>
                  <span className="text-gray-700 font-medium">
                    {profileSkills.length} skill{profileSkills.length === 1 ? "" : "s"}{" "}
                  </span>
                  from your profile will be merged into the request when you analyze (not
                  shown above).
                </>
              ) : (
                <>Add skills on your profile to improve matching without typing them here.</>
              )}
            </p>

            {questions.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-gray-500 mb-2">Guided prompts</p>
                <div className="flex flex-wrap gap-2">
                  {questions.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => setInputText(q)}
                      className="text-left text-xs bg-gray-50 hover:bg-indigo-50 border border-gray-200 rounded-lg px-3 py-2 text-gray-700 max-w-full cursor-pointer"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              type="button"
              disabled={textLoading || !canAnalyze}
              onClick={runTextAnalysis}
              className="mt-4 w-full sm:w-auto px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {textLoading ? "Analyzing…" : "Analyze text"}
            </button>
            {textError && (
              <p className="mt-3 text-sm text-red-600">{textError}</p>
            )}
          </section>

          <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter occupations</h2>
            <p className="text-xs text-gray-500 mb-4">
              Filters run independently from text analysis. After you analyze text, you
              can apply the first detected skill with one click.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Skill</label>
                <select
                  value={filterSkill}
                  onChange={(e) => setFilterSkill(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Any skill</option>
                  {(metadata?.skills ?? []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Min. salary
                  </label>
                  <input
                    type="number"
                    min={0}
                    placeholder="e.g. 60000"
                    value={filterMinSalary}
                    onChange={(e) => setFilterMinSalary(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Min. skill score
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="Optional"
                    value={filterMinSkillScore}
                    onChange={(e) => setFilterMinSkillScore(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Education
                </label>
                <select
                  value={filterEducation}
                  onChange={(e) => setFilterEducation(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="">Any level</option>
                  {(metadata?.education_levels ?? []).map((e) => (
                    <option key={e} value={e}>
                      {e}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="button"
              disabled={filterLoading}
              onClick={runFilter}
              className="mt-5 px-5 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {filterLoading ? "Loading…" : "Apply filters"}
            </button>
            {filterError && (
              <p className="mt-3 text-sm text-red-600">{filterError}</p>
            )}
          </section>
        </div>

        {textResult && (
          <section className="mb-10">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Text analysis</h2>
              <p className="text-xs text-gray-500">{textResult.message}</p>
            </div>

            {textResult.detected_skills.length > 0 && (
              <button
                type="button"
                onClick={applyFirstDetectedSkill}
                className="mb-4 text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-2 hover:bg-indigo-100 cursor-pointer"
              >
                Filter by first detected skill:{" "}
                <span className="font-semibold">{textResult.detected_skills[0]}</span>
              </button>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Detected skills
                </h3>
                {textResult.detected_skills.length === 0 ? (
                  <p className="text-sm text-gray-400">None for this mode</p>
                ) : (
                  <ul className="flex flex-wrap gap-2">
                    {textResult.detected_skills.map((s) => (
                      <li
                        key={s}
                        className="text-sm bg-gray-100 text-gray-800 rounded-full px-3 py-1"
                      >
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Skills to add
                </h3>
                {textResult.recommended_skills_to_add.length === 0 ? (
                  <p className="text-sm text-gray-400">None for this mode</p>
                ) : (
                  <ul className="flex flex-wrap gap-2">
                    {textResult.recommended_skills_to_add.map((s) => (
                      <li
                        key={s}
                        className="text-sm bg-emerald-50 text-emerald-900 rounded-full px-3 py-1"
                      >
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-4 md:col-span-1">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Top occupations (from text)
                </h3>
                {textResult.top_occupations.length === 0 ? (
                  <p className="text-sm text-gray-400">None for this mode</p>
                ) : (
                  <p className="text-sm text-gray-600">
                    {textResult.top_occupations.length} role
                    {textResult.top_occupations.length === 1 ? "" : "s"} — click a card
                    to see full detail.
                  </p>
                )}
              </div>
            </div>

            {textResult.top_occupations.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {textResult.top_occupations.map((row) => (
                  <OccupationResultCard
                    key={row.soc_code}
                    row={row}
                    onSelect={selectOccupation}
                    highlightScore
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {filterResults !== null && (
          <section className="mb-10">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Filter results ({filterResults.length})
            </h2>
            {filterResults.length === 0 ? (
              <p className="text-sm text-gray-500 bg-white border border-gray-200 rounded-xl p-6">
                No occupations match these filters.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filterResults.map((row) => (
                  <OccupationResultCard
                    key={row.soc_code}
                    row={row}
                    onSelect={selectOccupation}
                    highlightScore
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {(browse.kind === "occupation" || browse.kind === "skill") && (
          <section className="mb-10 max-w-3xl">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Detail</h2>
            {browse.kind === "occupation" ? (
              <OccupationDetail
                socCode={browse.socCode}
                onBack={clearBrowse}
                onSkillClick={selectSkill}
              />
            ) : (
              <SkillDetail
                skillName={browse.name}
                onBack={clearBrowse}
                onOccupationClick={selectOccupation}
              />
            )}
          </section>
        )}
      </main>
    </div>
  );
}
