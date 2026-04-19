"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";

interface Session {
  session_id: string;
  status: string;
  total_steps: number;
  success_count: number;
  failure_count: number;
  action_distribution: Record<string, number>;
}

const STATUS_COLORS: Record<string, string> = {
  healthy: "bg-green-100 text-green-800",
  looping: "bg-amber-100 text-amber-800",
  drifting: "bg-purple-100 text-purple-800",
  failing: "bg-red-100 text-red-800",
};

function LoadingSpinner() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        <p className="text-sm text-gray-500">Loading sessions...</p>
      </div>
    </div>
  );
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSessions() {
      try {
        const res = await fetch("http://localhost:8000/sessions");
        const data = await res.json();
        setSessions(data);
      } catch (e) {
        console.error("Failed to fetch sessions:", e);
      } finally {
        setLoading(false);
      }
    }

    fetchSessions();
    const interval = setInterval(fetchSessions, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (sessions.length === 0) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <h1 className="text-2xl font-bold text-gray-900">Sessions</h1>
        <p className="mt-4 text-gray-600">
          No sessions yet. Run the agent simulator to generate events.
        </p>
        <Link
          href="/"
          className="mt-6 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          Go to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-6xl">
        <Link
          href="/"
          className="text-sm text-gray-500 hover:text-gray-700 transition"
        >
          ← Back to Dashboard
        </Link>
        <h1 className="mt-4 text-2xl font-bold text-gray-900">Sessions</h1>
        <p className="mt-1 text-sm text-gray-500">
          {sessions.length} session{sessions.length !== 1 ? "s" : ""} tracked
        </p>

        <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Session
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Steps
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Success
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Failures
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {sessions.map((session) => (
                <tr
                  key={session.session_id}
                  className="transition hover:bg-gray-50"
                >
                  <td className="whitespace-nowrap px-6 py-4">
                    <Link
                      href={`/sessions/${session.session_id}`}
                      className="font-medium text-blue-600 hover:text-blue-800"
                    >
                      {session.session_id}
                    </Link>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                        STATUS_COLORS[session.status] || "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {session.status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-gray-900">
                    {session.total_steps}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-gray-900">
                    {session.success_count}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-gray-900">
                    {session.failure_count}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {Object.entries(session.action_distribution || {})
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}