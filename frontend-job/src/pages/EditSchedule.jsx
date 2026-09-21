import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getSchedule,
  updateSchedule,
} from "../services/api";

import ScheduleForm from "../components/ScheduleForm";

function EditSchedule() {
  const { scheduleId } = useParams();
  const navigate = useNavigate();

  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadSchedule = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getSchedule(scheduleId);
        setSchedule(data);
      } catch (err) {
        console.error(err);

        setError(
          err.response?.data?.detail ||
          "Failed to load schedule."
        );
      } finally {
        setLoading(false);
      }
    };

    loadSchedule();
  }, [scheduleId]);

  const handleSubmit = async (data) => {
    try {
      setError("");

      await updateSchedule(scheduleId, data);

      navigate(`/schedules/${scheduleId}`);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Failed to update schedule."
      );
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        Loading schedule...
      </div>
    );
  }

  if (error && !schedule) {
    return (
      <div className="page-container">
        <div className="error-message">
          {error}
        </div>

        <button onClick={() => navigate("/schedules")}>
          Back to Schedules
        </button>
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="page-container">
        Schedule not found.
      </div>
    );
  }

  return (
    <div className="page-container">

      <div className="page-header">
        <div>
          <h1>Edit Schedule</h1>
          <p>
            Update schedule configuration
          </p>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <ScheduleForm
        initialData={schedule}
        editMode={true}
        onSubmit={handleSubmit}
        onCancel={() =>
          navigate(`/schedules/${scheduleId}`)
        }
      />

    </div>
  );
}

export default EditSchedule;