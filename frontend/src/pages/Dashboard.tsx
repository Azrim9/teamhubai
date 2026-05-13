import React from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../lib/api";
import { Badge } from "../components/ui/Badge";
import { Users, Briefcase, Zap } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  isLoading: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, isLoading }) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
        {isLoading ? (
          <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 animate-pulse rounded mt-1"></div>
        ) : (
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</h3>
        )}
      </div>
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

const SkeletonList = () => (
  <div className="space-y-4">
    {[1, 2, 3, 4, 5].map((i) => (
      <div key={i} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg animate-pulse">
        <div className="space-y-2">
          <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="h-3 w-24 bg-gray-100 dark:bg-gray-800 rounded"></div>
        </div>
        <div className="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
      </div>
    ))}
  </div>
);

const Dashboard: React.FC = () => {
  const { data: agentsData, isLoading: isLoadingAgents } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const { data } = await api.get("/agents");
      return data;
    },
  });

  const { data: jobsData, isLoading: isLoadingJobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const { data } = await api.get("/jobs");
      return data;
    },
  });

  const { data: matchesData, isLoading: isLoadingMatches } = useQuery({
    queryKey: ["matches"],
    queryFn: async () => {
      const { data } = await api.get("/matches");
      return data;
    },
  });

  const recentAgents = agentsData?.items?.slice(0, 5) || [];
  const recentJobs = jobsData?.items?.slice(0, 5) || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400">Overview of your AI operations</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          label="Total Agents"
          value={agentsData?.total || 0}
          icon={<Users size={24} />}
          isLoading={isLoadingAgents}
        />
        <StatCard
          label="Total Jobs"
          value={jobsData?.total || 0}
          icon={<Briefcase size={24} />}
          isLoading={isLoadingJobs}
        />
        <StatCard
          label="Total Matches"
          value={matchesData?.length || 0}
          icon={<Zap size={24} />}
          isLoading={isLoadingMatches}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Agents */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Recent Agents</h2>
          {isLoadingAgents ? (
            <SkeletonList />
          ) : recentAgents.length > 0 ? (
            <div className="space-y-4">
              {recentAgents.map((agent: any) => (
                <div key={agent.id} className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors border border-gray-50 dark:border-gray-700">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">{agent.name}</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{agent.role}</p>
                  </div>
                  <Badge variant={agent.status}>{agent.status}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8 text-gray-500 dark:text-gray-400 italic">No agents found.</p>
          )}
        </div>

        {/* Recent Jobs */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Recent Jobs</h2>
          {isLoadingJobs ? (
            <SkeletonList />
          ) : recentJobs.length > 0 ? (
            <div className="space-y-4">
              {recentJobs.map((job: any) => (
                <div key={job.id} className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors border border-gray-50 dark:border-gray-700">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">{job.title}</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Created {new Date(job.created_at).toLocaleDateString()}</p>
                  </div>
                  <Badge variant={job.status}>{job.status}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8 text-gray-500 dark:text-gray-400 italic">No jobs found.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
