import { useCallback, useEffect, useState } from "react";
import { jobsApi, userApi } from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import type { JobDetail } from "../types";

function timeAgo(dateStr: string | null): string | null {
  if (!dateStr) return null;
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000,
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

export default function MatchList() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<JobDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchMatches = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const token = await user.getIdToken();
      const { matches } = await userApi(token).getMatches();

      if (matches.length === 0) {
        setJobs([]);
        return;
      }

      const latest = matches[0];
      const fetchedJobs = await jobsApi().getJobsBatch(latest.matched_job_ids);
      setJobs(fetchedJobs);
    } catch {
      setError("Could not load matches.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchMatches();
  }, [fetchMatches]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Your Matches</h2>
        <button
          onClick={fetchMatches}
          disabled={loading}
          className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50 cursor-pointer"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {!loading && jobs.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <p className="font-medium">No matches yet</p>
          <p className="text-sm mt-1">
            Update your profile to find matching jobs
          </p>
        </div>
      )}

      {loading && jobs.length === 0 && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-gray-100 rounded-lg h-24" />
          ))}
        </div>
      )}

      <div className="space-y-3">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="border border-gray-100 rounded-lg p-4 hover:border-blue-200 hover:bg-blue-50/30 transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h3 className="font-medium text-gray-900 truncate">
                  {job.title}
                </h3>
                <p className="text-sm text-gray-600">
                  {job.company}
                  {timeAgo(job.posted_at ?? job.created_at) && (
                    <span className="text-gray-400"> · {timeAgo(job.posted_at ?? job.created_at)}</span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {job.location && (
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      {job.location}
                    </span>
                  )}
                  {job.remote && (
                    <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded">
                      Remote
                    </span>
                  )}
                  {job.salary_min != null && (
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      ${job.salary_min.toLocaleString()}
                      {job.salary_max
                        ? ` - $${job.salary_max.toLocaleString()}`
                        : "+"}
                    </span>
                  )}
                </div>
              </div>
              {job.url && (
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Apply
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
