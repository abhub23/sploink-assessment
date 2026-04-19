"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Activity, AlertTriangle, TrendingUp, CheckCircle } from "lucide-react";

interface Session {
  session_id: string;
  status: string;
  total_steps: number;
}

const STATUS_STATS = {
  healthy: { label: "Healthy", icon: CheckCircle, color: "text-green-500" },
  looping: { label: "Looping", icon: AlertTriangle, color: "text-amber-500" },
  drifting: { label: "Drifting", icon: TrendingUp, color: "text-purple-500" },
  failing: { label: "Failing", icon: AlertTriangle, color: "text-red-500" },
};

function LoadingSpinner() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );
}

export default function Home() {
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

  const statusCounts = sessions.reduce(
    (acc, s) => {
      acc[s.status] = (acc[s.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-4xl">
        <div className="flex items-center gap-3">
          <Activity className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            Agent Monitoring
          </h1>
        </div>
        <p className="mt-2 text-gray-600">
          Monitor AI agent activity and detect behavioral issues
        </p>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <>
            <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
              {Object.entries(STATUS_STATS).map(([status, { label, icon: Icon, color }]) => {
                const count = statusCounts[status] || 0;
                return (
                  <Link
                    key={status}
                    href="/sessions"
                    className="group flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-blue-300 hover:shadow-md"
                  >
                    <div className={`${color}`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">
                        {count}
                      </p>
                      <p className="text-sm text-gray-500">{label}</p>
                    </div>
                  </Link>
                );
              })}
            </div>

            <div className="mt-8">
              <Link
                href="/sessions"
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
              >
                View All Sessions
                <span className="rounded-full bg-white/20 px-2 py-0.5 text-xs">
                  {sessions.length}
                </span>
              </Link>
            </div>

            <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Quick Start</h2>
              <p className="mt-2 text-sm text-gray-600">
                Run the agent simulator to generate sample events:
              </p>
              <div className="mt-4 space-y-2 font-mono text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">#</span>
                  <code className="text-gray-700">python agent/simulator.py --scenario normal</code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">#</span>
                  <code className="text-gray-700">python agent/simulator.py --scenario loop</code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">#</span>
                  <code className="text-gray-700">python agent/simulator.py --scenario drift</code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">#</span>
                  <code className="text-gray-700">python agent/simulator.py --scenario failure</code>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}