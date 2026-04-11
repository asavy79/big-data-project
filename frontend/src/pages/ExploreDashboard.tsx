import { useState } from "react";
import Header from "../components/Header";
import OccupationDetail from "../components/explore/OccupationDetail";
import SkillDetail from "../components/explore/SkillDetail";
import TopOccupations from "../components/explore/TopOccupations";
import TopSkills from "../components/explore/TopSkills";

type Selection =
  | { kind: "none" }
  | { kind: "occupation"; socCode: string }
  | { kind: "skill"; name: string };

export default function ExploreDashboard() {
  const [selection, setSelection] = useState<Selection>({ kind: "none" });

  const selectOccupation = (socCode: string) =>
    setSelection({ kind: "occupation", socCode });

  const selectSkill = (name: string) =>
    setSelection({ kind: "skill", name });

  const clearSelection = () => setSelection({ kind: "none" });

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Explore</h1>
          <p className="text-sm text-gray-500 mt-1">
            Browse top occupations and skills from labor market data
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            {selection.kind === "occupation" ? (
              <OccupationDetail
                socCode={selection.socCode}
                onBack={clearSelection}
                onSkillClick={selectSkill}
              />
            ) : (
              <TopOccupations
                onSelect={selectOccupation}
                selectedCode={null}
              />
            )}
          </div>

          <div>
            {selection.kind === "skill" ? (
              <SkillDetail
                skillName={selection.name}
                onBack={clearSelection}
                onOccupationClick={selectOccupation}
              />
            ) : (
              <TopSkills
                onSelect={selectSkill}
                selectedName={null}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
