import { useEffect, useState } from "react";
import { fetchInsightOccupationDetail } from "../../api/insightsApi";
import type { InsightOccupationDetail as InsightOccupationDetailType } from "../../types";

interface Props {
  socCode: string;
  onBack: () => void;
  onSkillClick: (name: string) => void;
}

function formatSalary(val: number | null | undefined): string {
  if (val == null) return "—";
  return "$" + val.toLocaleString();
}

export default function OccupationDetail({ socCode, onBack, onSkillClick }: Props) {
  const [detail, setDetail] = useState<InsightOccupationDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchInsightOccupationDetail(socCode)
      .then((data) => {
        setDetail(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load occupation");
        setLoading(false);
      });
  }, [socCode]);

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6">
        <button onClick={onBack} className="text-sm text-blue-600 hover:text-blue-800 mb-4 cursor-pointer">
          &larr; Back to list
        </button>
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-5 bg-gray-200 rounded w-2/3" />
          <div className="h-20 bg-gray-100 rounded" />
          <div className="h-32 bg-gray-100 rounded" />
        </div>
      </div>
    );
  }

  if (!detail || !detail.found) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <button onClick={onBack} className="text-sm text-blue-600 hover:text-blue-800 mb-4 cursor-pointer">
          &larr; Back to list
        </button>
        <p className="text-gray-500">Occupation not found.</p>
      </div>
    );
  }

  const maxSkillValue =
    detail.top_skills.length > 0
      ? Math.max(...detail.top_skills.map((s) => s.skill_score))
      : 1;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <button onClick={onBack} className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer">
        &larr; Back to list
      </button>

      <div className="mt-3">
        <span className="text-xs text-gray-400 font-mono">{detail.soc_code}</span>
        <h2 className="text-xl font-bold text-gray-900 mt-0.5">{detail.title ?? "—"}</h2>
        {detail.description && (
          <p className="text-sm text-gray-600 mt-2 leading-relaxed">{detail.description}</p>
        )}
      </div>

      <div className="mt-5 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500">Mean Salary</p>
          <p className="text-lg font-semibold text-gray-900">{formatSalary(detail.a_mean)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500">Median Salary</p>
          <p className="text-lg font-semibold text-gray-900">{formatSalary(detail.a_median)}</p>
        </div>
        {detail.preferred_education && (
          <div className="bg-gray-50 rounded-lg p-3 col-span-2 sm:col-span-1">
            <p className="text-xs text-gray-500">Preferred Education</p>
            <p className="text-sm font-semibold text-gray-900">{detail.preferred_education}</p>
            {detail.preferred_edu_pct != null && (
              <p className="text-xs text-gray-400">{detail.preferred_edu_pct}% of workers</p>
            )}
          </div>
        )}
      </div>

      {detail.top_skills.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Skills</h3>
          <div className="space-y-2">
            {detail.top_skills.map((skill) => (
              <button
                key={skill.skill_name}
                onClick={() => onSkillClick(skill.skill_name)}
                className="w-full text-left group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-800 group-hover:text-blue-600 transition-colors">
                    {skill.skill_name}
                  </span>
                  <span className="text-xs text-gray-400 tabular-nums">
                    {skill.skill_score.toFixed(2)}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-indigo-500 h-1.5 rounded-full"
                    style={{ width: `${(skill.skill_score / maxSkillValue) * 100}%` }}
                  />
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
