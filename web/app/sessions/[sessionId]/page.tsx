"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Loader2, FileText, Edit3, Terminal, Bot } from "lucide-react";

interface Event {
  id: string;
  step: number;
  action: string;
  input: string;
  output: string;
  metadata: { status?: string; file?: string };
}

interface DetectionResult {
  session_id: string;
  status: string;
  issues: Array<{
    type: string;
    severity: string;
    description: string;
    step_range: string;
  }>;
  metrics: {
    total_steps: number;
    success_count: number;
    failure_count: number;
    action_distribution: Record<string, number>;
  };
}

const SEVERITY_COLORS: Record<string, string> = {
  low: "border-l-gray-500 bg-gray-50",
  medium: "border-l-amber-500 bg-amber-50",
  high: "border-l-red-500 bg-red-50",
};

const STATUS_COLORS: Record<string, string> = {
  healthy: "bg-green-100 text-green-800",
  looping: "bg-amber-100 text-amber-800",
  drifting: "bg-purple-100 text-purple-800",
  failing: "bg-red-100 text-red-800",
};

const ACTION_ICONS = {
  read_file: FileText,
  write_file: Edit3,
  run_command: Terminal,
  llm_call: Bot,
};

function LoadingSpinner() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        <p className="text-sm text-gray-500">Loading session...</p>
      </div>
    </div>
  );
}

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [events, setEvents] = useState<Event[]>([]);
  const [analysis, setAnalysis] = useState<DetectionResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [eventsRes, analysisRes] = await Promise.all([
          fetch(`http://localhost:8000/events/${sessionId}`),
          fetch(`http://localhost:8000/sessions/${sessionId}/analyze`),
        ]);

        const eventsData = await eventsRes.json();
        const analysisData = await analysisRes.json();

        setEvents(eventsData);
        setAnalysis(analysisData);
      } catch (e) {
        console.error("Failed to fetch session data:", e);
      } finally {
        setLoading(false);
      }
    }

    if (sessionId) {
      fetchData();
      const interval = setInterval(fetchData, 3000);
      return () => clearInterval(interval);
    }
  }, [sessionId]);

  if (loading) {
    return <LoadingSpinner />;
  }

  const status = analysis?.status || "unknown";
  const issues = analysis?.issues || [];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-4xl">
        <Link
          href="/sessions"
          className="text-sm text-gray-500 hover:text-gray-700 transition"
        >
          ← Back to Sessions
        </Link>

        <div className="mt-4 flex items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">{sessionId}</h1>
          <span
            className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${
              STATUS_COLORS[status] || "bg-gray-100 text-gray-800"
            }`}
          >
            {status}
          </span>
        </div>

        {issues.length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-semibold text-gray-900">
              Detected Issues
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({issues.length})
              </span>
            </h2>
            <div className="mt-4 space-y-3">
              {issues.map((issue, i) => (
                <div
                  key={i}
                  className={`rounded-lg border-l-4 p-4 shadow-sm ${
                    SEVERITY_COLORS[issue.severity] || "border-l-gray-500 bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wide">
                      {issue.severity}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="text-xs font-medium text-gray-600">
                      {issue.type}
                    </span>
                  </div>
                  <div className="mt-1 text-gray-700">{issue.description}</div>
                  <div className="mt-2 text-sm text-gray-400">
                    Steps: {issue.step_range}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900">
            Event Timeline
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({events.length} events)
            </span>
          </h2>
          <div className="mt-4 space-y-2">
            {events.map((event, i) => {
              const Icon = ACTION_ICONS[event.action as keyof typeof ACTION_ICONS] || FileText;
              return (
                <div
                  key={event.id}
                  className={`flex items-center gap-4 rounded-lg border border-gray-100 p-4 transition hover:border-gray-300 ${
                    i % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                  }`}
                >
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-sm font-semibold text-gray-600">
                    {event.step}
                  </div>
                  <Icon className="h-5 w-5 flex-shrink-0 text-gray-400" />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-gray-900">{event.action}</div>
                    <div className="truncate text-sm text-gray-500">
                      {event.input}
                    </div>
                    {event.output && (
                      <div className="mt-1 truncate text-sm text-gray-400">
                        → {event.output}
                      </div>
                    )}
                  </div>
                  <div
                    className={`flex-shrink-0 rounded px-2.5 py-1 text-xs font-medium ${
                      event.metadata?.status === "success"
                        ? "bg-green-100 text-green-700"
                        : event.metadata?.status === "failure"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {event.metadata?.status || "unknown"}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}