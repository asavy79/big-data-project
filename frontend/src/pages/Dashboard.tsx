import Header from "../components/Header";
import MatchList from "../components/MatchList";
import ProfileForm from "../components/ProfileForm";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProfileForm />
          <MatchList />
        </div>
      </main>
    </div>
  );
}
