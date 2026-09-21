import { useEffect, useState } from "react";
import { getDashboardStats } from "../services/api";
import StatCard from "../components/StatCard";

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load dashboard statistics.");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <p>Loading dashboard...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div className="dashboard">
      <h1>Job Scheduler Dashboard</h1>

      <div className="stats-grid">
        <StatCard title="Total Jobs" value={stats.total_jobs} />
        <StatCard title="Pending" value={stats.pending_jobs} />
        <StatCard title="Processing" value={stats.processing_jobs} />
        <StatCard title="Succeeded" value={stats.succeeded_jobs} />
        <StatCard title="Failed" value={stats.failed_jobs} />
        <StatCard title="Cancelled" value={stats.cancelled_jobs} />
        <StatCard title="Active Workers" value={stats.active_workers} />
        <StatCard title="Active Schedules" value={stats.active_schedules} />
      </div>
    </div>
  );
}

export default Dashboard;