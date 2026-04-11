import { useEffect, useState } from "react";
import { fetchTopOccupations } from "../../api/dummyExploreData";
import type { Occupation } from "../../types";

interface Props {
  onSelect: (socCode: string) => void;
  selectedCode: string | null;
}

function formatSalary(val: number | null): string {
  if (val == null) return "—";
  return "$" + val.toLocaleString();
}

function formatEmployment(val: number | null): string {
  if (val == null) return "—";
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + "M";
  if (val >= 1_000) return (val / 1_000).toFixed(0) + "K";
  return val.toLocaleString();
}

export default function TopOccupations({ onSelect, selectedCode }: Props) {
  const [occupations, setOccupations] = useState<Occupation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTopOccupations().then((data) => {
      setOccupations(data);
      setLoading(false);
    });
  }, []);

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
        Top Occupations by Salary
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="pb-2 pr-3 font-medium">#</th>
              <th className="pb-2 pr-3 font-medium">Title</th>
              <th className="pb-2 pr-3 font-medium text-right">Mean Salary</th>
              <th className="pb-2 font-medium text-right hidden sm:table-cell">
                Employment
              </th>
            </tr>
          </thead>
          <tbody>
            {occupations.map((occ, idx) => (
              <tr
                key={occ.soc_code}
                onClick={() => onSelect(occ.soc_code)}
                className={`border-b border-gray-50 cursor-pointer transition-colors ${
                  selectedCode === occ.soc_code
                    ? "bg-blue-50"
                    : "hover:bg-gray-50"
                }`}
              >
                <td className="py-2.5 pr-3 text-gray-400 tabular-nums">
                  {idx + 1}
                </td>
                <td className="py-2.5 pr-3 font-medium text-gray-900">
                  {occ.title}
                </td>
                <td className="py-2.5 pr-3 text-right text-gray-700 tabular-nums">
                  {formatSalary(occ.a_mean)}
                </td>
                <td className="py-2.5 text-right text-gray-500 tabular-nums hidden sm:table-cell">
                  {formatEmployment(occ.tot_emp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
