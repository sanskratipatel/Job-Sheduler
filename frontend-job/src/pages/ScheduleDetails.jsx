import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  archiveSchedule,
  getSchedule,
  pauseSchedule,
  resumeSchedule,
} from "../services/api";


function ScheduleDetails() {

  const { scheduleId } =
    useParams();

  const navigate =
    useNavigate();

  const [
    schedule,
    setSchedule,
  ] = useState(null);

  const [error, setError] =
    useState("");


  const loadSchedule = async () => {

    try {

      const data =
        await getSchedule(
          scheduleId
        );

      setSchedule(data);

    } catch (err) {

      console.error(err);

      setError(
        "Failed to load schedule."
      );
    }
  };


  useEffect(() => {
    loadSchedule();
  }, [scheduleId]);


  const handlePause =
    async () => {

      await pauseSchedule(
        scheduleId
      );

      await loadSchedule();
    };


  const handleResume =
    async () => {

      await resumeSchedule(
        scheduleId
      );

      await loadSchedule();
    };


  const handleArchive =
    async () => {

      if (
        !window.confirm(
          "Archive this schedule?"
        )
      ) {
        return;
      }

      await archiveSchedule(
        scheduleId
      );

      navigate(
        "/schedules"
      );
    };


  if (error) {

    return (
      <div className="page-container">
        {error}
      </div>
    );
  }


  if (!schedule) {

    return (
      <div className="page-container">
        Loading...
      </div>
    );
  }


  return (

    <div className="page-container">

      <div className="page-header">

        <div>

          <h1>
            {schedule.name}
          </h1>

          <p>
            Schedule details and execution configuration
          </p>

        </div>


        <div className="header-actions">

          {schedule.status !==
            "ARCHIVED" && (

            <button
              onClick={() =>
                navigate(
                  `/schedules/${schedule.id}/edit`
                )
              }
            >
              Edit
            </button>

          )}


          {schedule.status ===
            "ACTIVE" && (

            <button
              onClick={handlePause}
            >
              Pause
            </button>

          )}


          {schedule.status ===
            "PAUSED" && (

            <button
              onClick={handleResume}
            >
              Resume
            </button>

          )}


          {schedule.status !==
            "ARCHIVED" && (

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
          label="Status"
          value={schedule.status}
        />

        <Detail
          label="Job Type"
          value={
            schedule.job_type
          }
        />

        <Detail
          label="Schedule Type"
          value={
            schedule.schedule_type
          }
        />

        <Detail
          label="Timezone"
          value={
            schedule.timezone
          }
        />

        <Detail
          label="Priority"
          value={
            schedule.priority
          }
        />

        <Detail
          label="Attempts"
          value={
            schedule.max_attempts
          }
        />

        <Detail
          label="Timeout"
          value={
            `${schedule.timeout_seconds} seconds`
          }
        />

        <Detail
          label="Run Count"
          value={
            schedule.run_count
          }
        />

        <Detail
          label="Next Run"
          value={
            schedule.next_run_at
              ? new Date(
                  schedule.next_run_at
                ).toLocaleString()
              : "-"
          }
        />

        <Detail
          label="Last Run"
          value={
            schedule.last_run_at
              ? new Date(
                  schedule.last_run_at
                ).toLocaleString()
              : "-"
          }
        />

      </div>


      {schedule.schedule_type ===
        "CRON" && (

        <section className="detail-section">

          <h2>
            Cron Configuration
          </h2>

          <code className="cron-code">
            {
              schedule.cron_expression
            }
          </code>

        </section>

      )}


      {schedule.schedule_type ===
        "WEEKLY" && (

        <section className="detail-section">

          <h2>
            Weekly Schedule
          </h2>

          <p>
            Days:{" "}
            {
              schedule.days_of_week?.join(
                ", "
              )
            }
          </p>

          <p>
            Time:{" "}
            {schedule.run_time}
          </p>

        </section>

      )}


      {schedule.schedule_type ===
        "MONTHLY" && (

        <section className="detail-section">

          <h2>
            Monthly Schedule
          </h2>

          <p>
            Day:{" "}
            {
              schedule.day_of_month
            }
          </p>

          <p>
            Time:{" "}
            {schedule.run_time}
          </p>

        </section>

      )}


      <section className="detail-section">

        <h2>
          Payload
        </h2>

        <pre className="payload-box">
          {JSON.stringify(
            schedule.payload,
            null,
            2
          )}
        </pre>

      </section>


      <section className="detail-section">

        <h2>
          Description
        </h2>

        <p>
          {schedule.description ||
            "No description"}
        </p>

      </section>


      <section className="detail-section">

        <h2>
          Internal Details
        </h2>

        <p>
          <strong>ID:</strong>{" "}
          {schedule.id}
        </p>

        <p>
          <strong>
            Created:
          </strong>{" "}
          {new Date(
            schedule.created_at
          ).toLocaleString()}
        </p>

        <p>
          <strong>
            Updated:
          </strong>{" "}
          {new Date(
            schedule.updated_at
          ).toLocaleString()}
        </p>

      </section>

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


export default ScheduleDetails;