import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  archiveSchedule,
  getSchedules,
  pauseSchedule,
  resumeSchedule,
} from "../services/api";


function Schedules() {

  const navigate = useNavigate();

  const [schedules, setSchedules] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const loadSchedules = async () => {

    try {

      setLoading(true);

      const data =
        await getSchedules({
          limit: 100,
          offset: 0,
        });


      setSchedules(
        data.items || data
      );

    } catch (err) {

      console.error(err);

      setError(
        "Failed to load schedules."
      );

    } finally {

      setLoading(false);
    }
  };


  useEffect(() => {
    loadSchedules();
  }, []);


  const handlePause =
    async (scheduleId) => {

      await pauseSchedule(
        scheduleId
      );

      await loadSchedules();
    };


  const handleResume =
    async (scheduleId) => {

      await resumeSchedule(
        scheduleId
      );

      await loadSchedules();
    };


  const handleArchive =
    async (scheduleId) => {

      const confirmed =
        window.confirm(
          "Archive this schedule?"
        );

      if (!confirmed) {
        return;
      }

      await archiveSchedule(
        scheduleId
      );

      await loadSchedules();
    };


  if (loading) {

    return (
      <div className="page-container">
        Loading schedules...
      </div>
    );
  }


  return (

    <div className="page-container">

      <div className="page-header">

        <div>

          <h1>
            Schedules
          </h1>

          <p>
            Manage recurring and cron jobs.
          </p>

        </div>


        <Link
          to="/schedules/create"
          className="primary-button"
        >
          + Create Schedule
        </Link>

      </div>


      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      <div className="table-container">

        <table>

          <thead>

            <tr>

              <th>Name</th>

              <th>
                Job Type
              </th>

              <th>
                Schedule
              </th>

              <th>
                Status
              </th>

              <th>
                Next Run
              </th>

              <th>
                Runs
              </th>

              <th>
                Actions
              </th>

            </tr>

          </thead>


          <tbody>

            {schedules.map(
              (schedule) => (

                <tr key={schedule.id}>

                  <td>

                    <button
                      className="link-button"
                      onClick={() =>
                        navigate(
                          `/schedules/${schedule.id}`
                        )
                      }
                    >
                      {schedule.name}
                    </button>

                  </td>


                  <td>
                    {schedule.job_type}
                  </td>


                  <td>

                    <strong>
                      {
                        schedule.schedule_type
                      }
                    </strong>

                    {schedule.schedule_type ===
                      "CRON" && (

                      <div className="small-text">
                        {
                          schedule.cron_expression
                        }
                      </div>

                    )}

                  </td>


                  <td>

                    <span
                      className={`status status-${schedule.status?.toLowerCase()}`}
                    >
                      {schedule.status}
                    </span>

                  </td>


                  <td>

                    {schedule.next_run_at
                      ? new Date(
                          schedule.next_run_at
                        ).toLocaleString()
                      : "-"}

                  </td>


                  <td>

                    {schedule.run_count || 0}

                    {schedule.max_runs
                      ? ` / ${schedule.max_runs}`
                      : ""}

                  </td>


                  <td>

                    <div className="table-actions">

                      <button
                        onClick={() =>
                          navigate(
                            `/schedules/${schedule.id}`
                          )
                        }
                      >
                        View
                      </button>


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
                          onClick={() =>
                            handlePause(
                              schedule.id
                            )
                          }
                        >
                          Pause
                        </button>

                      )}


                      {schedule.status ===
                        "PAUSED" && (

                        <button
                          onClick={() =>
                            handleResume(
                              schedule.id
                            )
                          }
                        >
                          Resume
                        </button>

                      )}


                      {schedule.status !==
                        "ARCHIVED" && (

                        <button
                          className="danger-button"
                          onClick={() =>
                            handleArchive(
                              schedule.id
                            )
                          }
                        >
                          Archive
                        </button>

                      )}

                    </div>

                  </td>

                </tr>

              )
            )}


            {schedules.length === 0 && (

              <tr>

                <td
                  colSpan="7"
                  className="empty-table"
                >
                  No schedules found.
                </td>

              </tr>

            )}

          </tbody>

        </table>

      </div>

    </div>

  );
}


export default Schedules;