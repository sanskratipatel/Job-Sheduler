import { useNavigate } from "react-router-dom";

import ScheduleForm from "../components/ScheduleForm";
import { createSchedule } from "../services/api";


function CreateSchedule() {

  const navigate = useNavigate();


  const handleCreate = async (data) => {

    const schedule =
      await createSchedule(data);

    navigate(
      `/schedules/${schedule.id}`
    );
  };


  return (

    <div className="page-container">

      <div className="page-header">

        <div>

          <h1>
            Create Schedule
          </h1>

          <p>
            Schedule a recurring or
            one-time background job.
          </p>

        </div>

      </div>


      <ScheduleForm
        onSubmit={handleCreate}
        submitText="Create Schedule"
      />

    </div>

  );
}


export default CreateSchedule;