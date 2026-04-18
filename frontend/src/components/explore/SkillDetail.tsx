import { useEffect, useState } from "react";
import { fetchSkillDetail } from "../../api/insightsApi";
import type { SkillDetail as SkillDetailType } from "../../types";

interface Props {
  skillName: string;
  onBack: () => void;
  onOccupationClick: (socCode: string) => void;
}

export default function SkillDetail({ skillName, onBack, onOccupationClick }: Props) {
  const [detail, setDetail] = useState<SkillDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchSkillDetail(skillName)
      .then((data) => {
        setDetail(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load skill");
        setLoading(false);
      });
  }, [skillName]);

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
          <div className="h-32 bg-gray-100 rounded" />
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <button onClick={onBack} className="text-sm text-blue-600 hover:text-blue-800 mb-4 cursor-pointer">
          &larr; Back to list
        </button>
        <p className="text-gray-500">Skill not found.</p>
      </div>
    );
  }

  const maxVal = detail.top_occupations.length > 0 ? detail.top_occupations[0].data_value : 1;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <button onClick={onBack} className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer">
        &larr; Back to list
      </button>

      <div className="mt-3">
        <h2 className="text-xl font-bold text-gray-900">{detail.skill_name}</h2>
        <div className="mt-2 inline-flex items-center bg-blue-50 text-blue-700 rounded-full px-3 py-1 text-sm">
          Avg. importance: {detail.average_data_value.toFixed(2)}
        </div>
      </div>

      {detail.top_occupations.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Top Occupations Using This Skill
          </h3>
          <div className="space-y-2">
            {detail.top_occupations.map((occ) => (
              <button
                key={occ.soc_code}
                onClick={() => onOccupationClick(occ.soc_code)}
                className="w-full text-left group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-800 group-hover:text-blue-600 transition-colors">
                    {occ.title}
                  </span>
                  <span className="text-xs text-gray-400 tabular-nums">
                    {occ.data_value.toFixed(2)}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-green-500 h-1.5 rounded-full"
                    style={{ width: `${(occ.data_value / maxVal) * 100}%` }}
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
