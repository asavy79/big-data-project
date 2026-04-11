import { useEffect, useState } from "react";
import { fetchTopSkills } from "../../api/dummyExploreData";
import type { Skill } from "../../types";

interface Props {
  onSelect: (name: string) => void;
  selectedName: string | null;
}

export default function TopSkills({ onSelect, selectedName }: Props) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTopSkills().then((data) => {
      setSkills(data);
      setLoading(false);
    });
  }, []);

  const maxValue = skills.length > 0 ? skills[0].average_data_value : 1;

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-5 bg-gray-200 rounded w-1/3" />
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="h-10 bg-gray-100 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Top Skills by Importance
      </h2>
      <div className="space-y-2">
        {skills.map((skill, idx) => (
          <button
            key={skill.name}
            onClick={() => onSelect(skill.name)}
            className={`w-full text-left p-3 rounded-lg transition-colors cursor-pointer ${
              selectedName === skill.name
                ? "bg-blue-50 ring-1 ring-blue-200"
                : "hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-gray-900">
                <span className="text-gray-400 mr-2">{idx + 1}.</span>
                {skill.name}
              </span>
              <span className="text-xs text-gray-500 tabular-nums">
                {skill.average_data_value.toFixed(2)}
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5">
              <div
                className="bg-blue-500 h-1.5 rounded-full transition-all"
                style={{
                  width: `${(skill.average_data_value / maxValue) * 100}%`,
                }}
              />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
