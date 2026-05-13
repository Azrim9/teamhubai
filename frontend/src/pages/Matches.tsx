import React, { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../lib/api";
import { Button } from "../components/ui/Button";
import { Zap, Play, Loader2, Trophy, Search } from "lucide-react";

interface Job {
  id: string;
  title: string;
}

interface Match {
  id: string;
  job_id: string;
  agent_id: string;
  score: number;
  rank: number;
}

interface Agent {
  id: string;
  name: string;
  role: string;
}

const Matches: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [streamingText, setStreamingText] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: jobsData, isLoading: isLoadingJobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const { data } = await api.get("/jobs");
      return data;
    },
  });

  const { data: existingMatches, isLoading: isLoadingMatches, refetch: refetchMatches } = useQuery({
    queryKey: ["matches", selectedJobId],
    queryFn: async () => {
      if (!selectedJobId) return [];
      const { data } = await api.get(`/matches?job_id=${selectedJobId}`);
      return data;
    },
    enabled: !!selectedJobId,
  });

  const { data: agentsData } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const { data } = await api.get("/agents");
      return data;
    },
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamingText]);

  const runMatching = () => {
    if (!selectedJobId) return;

    setStreamingText("");
    setIsStreaming(true);
    
    const token = localStorage.getItem("access_token");
    const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const eventSource = new EventSource(`${baseUrl}/match/stream/${selectedJobId}?token=${token}`);

    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        eventSource.close();
        setTimeout(() => {
          refetchMatches();
          setIsStreaming(false);
        }, 1500);
        return;
      }
      
      try {
        const data = JSON.parse(event.data);
        if (data.token) {
          setStreamingText((prev) => prev + data.token);
        }
      } catch (e) {
        // Fallback for non-json data if any
        setStreamingText((prev) => prev + event.data);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Error:", err);
      eventSource.close();
      setIsStreaming(false);
    };
  };

  const getAgentName = (agentId: string) => {
    const agent = agentsData?.items?.find((a: Agent) => a.id === agentId);
    return agent ? agent.name : "Unknown Agent";
  };

  const getAgentRole = (agentId: string) => {
    const agent = agentsData?.items?.find((a: Agent) => a.id === agentId);
    return agent ? agent.role : "";
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Matching</h1>
          <p className="text-gray-500 dark:text-gray-400">Match the best autonomous agents to your jobs</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Selection and Controls */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Select Job</label>
              <select
                className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg outline-none dark:text-white focus:ring-2 focus:ring-blue-500"
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                disabled={isStreaming}
              >
                <option value="">Choose a job...</option>
                {jobsData?.items?.map((job: Job) => (
                  <option key={job.id} value={job.id}>{job.title}</option>
                ))}
              </select>
            </div>

            <Button
              className="w-full flex items-center gap-2"
              onClick={runMatching}
              disabled={!selectedJobId || isStreaming}
              isLoading={isStreaming}
            >
              {isStreaming ? (
                <>Matching...</>
              ) : (
                <>
                  <Play size={18} />
                  Run AI Match
                </>
              )}
            </Button>
          </div>

          {/* Results Summary */}
          {selectedJobId && !isStreaming && existingMatches?.length > 0 && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-xl border border-blue-100 dark:border-blue-800/50">
              <div className="flex items-center gap-3 text-blue-700 dark:text-blue-400 mb-2">
                <Zap size={20} />
                <h3 className="font-bold">Match Complete</h3>
              </div>
              <p className="text-sm text-blue-600 dark:text-blue-300">
                The AI has identified the top {existingMatches.length} agents for this position based on skills and performance history.
              </p>
            </div>
          )}
        </div>

        {/* Streaming and Results Display */}
        <div className="lg:col-span-2 space-y-6">
          {isStreaming || streamingText ? (
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden shadow-2xl">
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-900/50">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/40"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/40"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/40"></div>
                  </div>
                  <span className="text-xs font-mono text-gray-500 ml-2">AI_MATCHING_ENGINE</span>
                </div>
                {isStreaming && (
                  <div className="flex items-center gap-2 text-blue-400 text-xs font-mono">
                    <Loader2 size={12} className="animate-spin" />
                    STREAMING
                  </div>
                )}
              </div>
              <div 
                ref={scrollRef}
                className="p-6 h-[400px] overflow-y-auto font-mono text-sm text-green-400/90 leading-relaxed scrollbar-thin scrollbar-thumb-gray-800"
              >
                {streamingText.split('\n').map((line, i) => (
                  <div key={i} className="min-h-[1.25rem]">
                    {line}
                    {i === streamingText.split('\n').length - 1 && isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-green-400 animate-pulse"></span>
                    )}
                  </div>
                ))}
                {!streamingText && isStreaming && (
                  <div className="flex items-center gap-2 italic text-gray-500">
                    Initializing neural matching engine...
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {isLoadingMatches ? (
                [1, 2, 3].map((i) => (
                  <div key={i} className="h-32 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-xl border border-gray-200 dark:border-gray-700"></div>
                ))
              ) : existingMatches?.length > 0 ? (
                existingMatches.sort((a: Match, b: Match) => a.rank - b.rank).map((match: Match) => (
                  <div 
                    key={match.id} 
                    className={`relative overflow-hidden bg-white dark:bg-gray-800 p-6 rounded-xl border shadow-sm transition-all hover:shadow-md ${
                      match.rank === 1 ? 'border-amber-200 dark:border-amber-900/50' : 'border-gray-100 dark:border-gray-700'
                    }`}
                  >
                    {match.rank === 1 && (
                      <div className="absolute top-0 right-0 p-2">
                        <Trophy className="text-amber-500" size={24} />
                      </div>
                    )}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                          match.rank === 1 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400' :
                          match.rank === 2 ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' :
                          'bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                        }`}>
                          #{match.rank}
                        </div>
                        <div>
                          <h4 className="text-lg font-bold text-gray-900 dark:text-white">
                            {getAgentName(match.agent_id)}
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {getAgentRole(match.agent_id)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <div className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">Match Score</div>
                          <div className="text-2xl font-black text-blue-600 dark:text-blue-400">
                            {(match.score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div className="w-32 h-2 bg-gray-100 dark:bg-gray-900 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500" 
                            style={{ width: `${match.score * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : selectedJobId ? (
                <div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                  <Zap size={48} className="text-gray-300 dark:text-gray-600 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 text-center px-6">
                    No matches found for this job yet. <br />
                    Click "Run AI Match" to start the process.
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                  <Search size={48} className="text-gray-300 dark:text-gray-600 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">Select a job to view or generate matches.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Matches;
