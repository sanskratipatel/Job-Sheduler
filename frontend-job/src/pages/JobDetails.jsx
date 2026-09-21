
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getJob,
  getJobExecutions,
  cancelJob,
  retryJob,
  archiveJob,
} from "../services/api";


function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  const loadJob = async () => {
    try {
      setLoading(true);
      setError("");

      const jobData = await getJob(jobId);
      setJob(jobData);

      try {
        const executionData =
          await getJobExecutions(jobId);

        setExecutions(
          executionData.items || executionData || []
        );
      } catch (executionError) {
        console.error(
          "Failed to load executions:",
          executionError
        );
      }

    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Failed to load job."
      );
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadJob();
  }, [jobId]);


  const handleCancel = async () => {
    if (
      !window.confirm(
        "Are you sure you want to cancel this job?"
      )
    ) {
      return;
    }

    try {
      await cancelJob(jobId);
      await loadJob();
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Failed to cancel job."
      );
    }
  };


  const handleRetry = async () => {
    try {
      await retryJob(jobId);
      await loadJob();
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Failed to retry job."
      );
    }
  };


  const handleArchive = async () => {
    if (
      !window.confirm(
        "Are you sure you want to archive this job?"
      )
    ) {
      return;
    }

    try {
      await archiveJob(jobId);

      navigate("/jobs");
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Failed to archive job."
      );
    }
  };


  if (loading) {
    return (
      <div className="page-container">
        Loading job...
      </div>
    );
  }


  if (error) {
    return (
      <div className="page-container">
        <div className="error-message">
          {error}
        </div>

        <button
          onClick={() => navigate("/jobs")}
        >
          Back to Jobs
        </button>
      </div>
    );
  }


  if (!job) {
    return (
      <div className="page-container">
        Job not found.
      </div>
    );
  }


  return (
    <div className="page-container">

      <div className="page-header">

        <div>
          <h1>{job.name}</h1>

          <p>
            Job details and execution history
          </p>
        </div>


        <div className="header-actions">

          <button
            onClick={() =>
              navigate(`/jobs/${job.id}/edit`)
            }
          >
            Edit
          </button>


          {job.status === "PENDING" && (
            <button
              onClick={handleCancel}
            >
              Cancel
            </button>
          )}


          {job.status === "FAILED" && (
            <button
              onClick={handleRetry}
            >
              Retry
            </button>
          )}


          {job.status === "PENDING" && (
            <button
              className="danger-button"
              onClick={handleArchive}
            >
              Archive
            </button>
          )}

        </div>

      </div>


      <div className="details-grid">

        <Detail
          label="Job ID"
          value={job.id}
        />

        <Detail
          label="Job Type"
          value={job.job_type}
        />

        <Detail
          label="Status"
          value={job.status}
        />

        <Detail
          label="Priority"
          value={job.priority}
        />

        <Detail
          label="Attempts"
          value={`${job.attempt_count || 0} / ${job.max_attempts}`}
        />

        <Detail
          label="Timeout"
          value={`${job.timeout_seconds} seconds`}
        />

        <Detail
          label="Scheduled At"
          value={
            job.scheduled_at
              ? new Date(
                  job.scheduled_at
                ).toLocaleString()
              : "-"
          }
        />

        <Detail
          label="Created At"
          value={
            job.created_at
              ? new Date(
                  job.created_at
                ).toLocaleString()
              : "-"
          }
        />

        <Detail
          label="Started At"
          value={
            job.started_at
              ? new Date(
                  job.started_at
                ).toLocaleString()
              : "-"
          }
        />

        <Detail
          label="Completed At"
          value={
            job.completed_at
              ? new Date(
                  job.completed_at
                ).toLocaleString()
              : "-"
          }
        />

      </div>


      {job.last_error && (
        <section className="detail-section">

          <h2>
            Last Error
          </h2>

          <pre className="payload-box">
            {job.last_error}
          </pre>

        </section>
      )}


      <section className="detail-section">

        <h2>
          Payload
        </h2>

        <pre className="payload-box">
          {JSON.stringify(
            job.payload,
            null,
            2
          )}
        </pre>

      </section>


      <section className="detail-section">

        <h2>
          Execution History
        </h2>


        {executions.length === 0 ? (

          <p>
            No executions found.
          </p>

        ) : (

          <div className="table-container">

            <table>

              <thead>
                <tr>
                  <th>Attempt</th>
                  <th>Status</th>
                  <th>Worker</th>
                  <th>Started</th>
                  <th>Finished</th>
                  <th>Duration</th>
                </tr>
              </thead>


              <tbody>

                {executions.map(
                  (execution) => (

                    <tr
                      key={execution.id}
                    >

                      <td>
                        {execution.attempt_number}
                      </td>

                      <td>
                        <span
                          className={`status status-${execution.status?.toLowerCase()}`}
                        >
                          {execution.status}
                        </span>
                      </td>

                      <td>
                        {execution.worker_id || "-"}
                      </td>

                      <td>
                        {execution.started_at
                          ? new Date(
                              execution.started_at
                            ).toLocaleString()
                          : "-"}
                      </td>

                      <td>
                        {execution.finished_at
                          ? new Date(
                              execution.finished_at
                            ).toLocaleString()
                          : "-"}
                      </td>

                      <td>
                        {execution.duration_ms != null
                          ? `${execution.duration_ms} ms`
                          : "-"}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      <button
        onClick={() =>
          navigate("/jobs")
        }
      >
        ← Back to Jobs
      </button>

    </div>
  );
}


function Detail({
  label,
  value,
}) {
  return (
    <div className="detail-card">

      <span className="detail-label">
        {label}
      </span>

      <strong>
        {value ?? "-"}
      </strong>

    </div>
  );
}


export default JobDetails;

