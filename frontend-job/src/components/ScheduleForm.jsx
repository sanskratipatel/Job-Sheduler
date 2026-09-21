import { useState } from "react";


const INITIAL_FORM = {
  name: "",
  description: "",

  job_type: "SEND_EMAIL",

  schedule_type: "DAILY",

  timezone: "Asia/Kolkata",

  priority: 5,
  max_attempts: 3,
  timeout_seconds: 60,

  run_at: "",
  run_time: "10:00",

  interval_count: 1,

  days_of_week: [],

  day_of_month: 1,

  month_of_year: 1,

  cron_expression: "",

  run_dates: "",

  start_at: "",
  end_at: "",

  max_runs: "",

  misfire_policy: "SKIP",

  payload: "{}",
};


function ScheduleForm({
  initialData,
  onSubmit,
  submitText = "Create Schedule",
  editMode = false,
}) {

  const [form, setForm] = useState(() => {

    if (!initialData) {
      return INITIAL_FORM;
    }

    return {
      ...INITIAL_FORM,
      ...initialData,

      payload:
        typeof initialData.payload === "string"
          ? initialData.payload
          : JSON.stringify(
              initialData.payload || {},
              null,
              2
            ),

      run_dates:
        initialData.run_dates?.join(", ") || "",

      days_of_week:
        initialData.days_of_week || [],
    };
  });


  const [error, setError] = useState("");


  const handleChange = (event) => {

    const {
      name,
      value,
    } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };


  const handleDayChange = (day) => {

    setForm((previous) => {

      const exists =
        previous.days_of_week.includes(day);

      return {
        ...previous,

        days_of_week: exists
          ? previous.days_of_week.filter(
              (item) => item !== day
            )
          : [
              ...previous.days_of_week,
              day,
            ],
      };
    });
  };


  const handleSubmit = async (event) => {

    event.preventDefault();

    setError("");

    try {

      let parsedPayload;

      try {
        parsedPayload =
          JSON.parse(form.payload || "{}");
      } catch {
        setError(
          "Payload must contain valid JSON."
        );

        return;
      }


      const requestData = {

        name: form.name,

        description:
          form.description || null,

        payload: parsedPayload,

        priority: Number(form.priority),

        max_attempts:
          Number(form.max_attempts),

        timeout_seconds:
          Number(form.timeout_seconds),

        timezone: form.timezone,

        misfire_policy:
          form.misfire_policy,

      };


      if (!editMode) {

        requestData.job_type =
          form.job_type;

        requestData.schedule_type =
          form.schedule_type;
      }


      const scheduleType =
        form.schedule_type;


      if (scheduleType === "ONCE") {

        requestData.run_at =
          form.run_at
            ? new Date(
                form.run_at
              ).toISOString()
            : null;
      }


      if (
        scheduleType === "DAILY" ||
        scheduleType === "WEEKLY" ||
        scheduleType === "MONTHLY" ||
        scheduleType === "YEARLY"
      ) {

        requestData.run_time =
          form.run_time
            ? `${form.run_time}:00`
            : null;
      }


      if (
        scheduleType === "DAILY"
      ) {

        requestData.interval_count =
          Number(
            form.interval_count || 1
          );
      }


      if (
        scheduleType === "WEEKLY"
      ) {

        requestData.days_of_week =
          form.days_of_week;
      }


      if (
        scheduleType === "MONTHLY"
      ) {

        requestData.day_of_month =
          Number(
            form.day_of_month
          );
      }


      if (
        scheduleType === "YEARLY"
      ) {

        requestData.day_of_month =
          Number(
            form.day_of_month
          );

        requestData.month_of_year =
          Number(
            form.month_of_year
          );
      }


      if (
        scheduleType ===
        "SPECIFIC_DATES"
      ) {

        requestData.run_dates =
          form.run_dates
            .split(",")
            .map(
              (date) =>
                date.trim()
            )
            .filter(Boolean);
      }


      if (
        scheduleType === "CRON"
      ) {

        requestData.cron_expression =
          form.cron_expression;
      }


      if (form.start_at) {

        requestData.start_at =
          new Date(
            form.start_at
          ).toISOString();
      }


      if (form.end_at) {

        requestData.end_at =
          new Date(
            form.end_at
          ).toISOString();
      }


      if (form.max_runs) {

        requestData.max_runs =
          Number(
            form.max_runs
          );
      }


      await onSubmit(
        requestData
      );

    } catch (err) {

      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Something went wrong."
      );
    }
  };


  const weekdays = [
    ["Monday", 0],
    ["Tuesday", 1],
    ["Wednesday", 2],
    ["Thursday", 3],
    ["Friday", 4],
    ["Saturday", 5],
    ["Sunday", 6],
  ];


  return (

    <form
      className="schedule-form"
      onSubmit={handleSubmit}
    >

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      <div className="form-group">

        <label>
          Schedule Name
        </label>

        <input
          required
          name="name"
          value={form.name}
          onChange={handleChange}
          placeholder="Daily order sync"
        />

      </div>


      <div className="form-group">

        <label>
          Description
        </label>

        <textarea
          name="description"
          value={form.description || ""}
          onChange={handleChange}
          placeholder="Optional description"
        />

      </div>


      {!editMode && (
        <>

          <div className="form-group">

            <label>
              Job Type
            </label>

            <select
              name="job_type"
              value={form.job_type}
              onChange={handleChange}
            >

              <option value="SEND_EMAIL">
                SEND_EMAIL
              </option>

              <option value="SEND_WEBHOOK">
                SEND_WEBHOOK
              </option>

              <option value="GENERATE_REPORT">
                GENERATE_REPORT
              </option>

              <option value="SYNC_ORDERS">
                SYNC_ORDERS
              </option>

            </select>

          </div>


          <div className="form-group">

            <label>
              Schedule Type
            </label>

            <select
              name="schedule_type"
              value={form.schedule_type}
              onChange={handleChange}
            >

              <option value="ONCE">
                Once
              </option>

              <option value="DAILY">
                Daily
              </option>

              <option value="WEEKLY">
                Weekly
              </option>

              <option value="MONTHLY">
                Monthly
              </option>

              <option value="YEARLY">
                Yearly
              </option>

              <option value="SPECIFIC_DATES">
                Specific Dates
              </option>

              <option value="CRON">
                Cron
              </option>

            </select>

          </div>

        </>
      )}


      <div className="form-group">

        <label>
          Timezone
        </label>

        <input
          name="timezone"
          value={form.timezone}
          onChange={handleChange}
        />

      </div>


      {form.schedule_type === "ONCE" && (

        <div className="form-group">

          <label>
            Run At
          </label>

          <input
            type="datetime-local"
            name="run_at"
            value={form.run_at || ""}
            onChange={handleChange}
          />

        </div>

      )}


      {[
        "DAILY",
        "WEEKLY",
        "MONTHLY",
        "YEARLY",
      ].includes(
        form.schedule_type
      ) && (

        <div className="form-group">

          <label>
            Run Time
          </label>

          <input
            type="time"
            name="run_time"
            value={form.run_time || ""}
            onChange={handleChange}
          />

        </div>

      )}


      {form.schedule_type === "DAILY" && (

        <div className="form-group">

          <label>
            Run Every N Days
          </label>

          <input
            type="number"
            min="1"
            name="interval_count"
            value={form.interval_count}
            onChange={handleChange}
          />

        </div>

      )}


      {form.schedule_type === "WEEKLY" && (

        <div className="form-group">

          <label>
            Days
          </label>

          <div className="checkbox-grid">

            {weekdays.map(
              ([label, value]) => (

                <label
                  key={value}
                  className="checkbox-label"
                >

                  <input
                    type="checkbox"
                    checked={
                      form.days_of_week.includes(
                        value
                      )
                    }
                    onChange={() =>
                      handleDayChange(
                        value
                      )
                    }
                  />

                  {label}

                </label>

              )
            )}

          </div>

        </div>

      )}


      {[
        "MONTHLY",
        "YEARLY",
      ].includes(
        form.schedule_type
      ) && (

        <div className="form-group">

          <label>
            Day Of Month
          </label>

          <input
            type="number"
            min="1"
            max="31"
            name="day_of_month"
            value={form.day_of_month}
            onChange={handleChange}
          />

        </div>

      )}


      {form.schedule_type === "YEARLY" && (

        <div className="form-group">

          <label>
            Month
          </label>

          <select
            name="month_of_year"
            value={
              form.month_of_year
            }
            onChange={
              handleChange
            }
          >

            {Array.from(
              { length: 12 },
              (_, index) => (
                <option
                  key={index + 1}
                  value={index + 1}
                >
                  {index + 1}
                </option>
              )
            )}

          </select>

        </div>

      )}


      {form.schedule_type ===
        "SPECIFIC_DATES" && (

        <div className="form-group">

          <label>
            Dates
          </label>

          <input
            name="run_dates"
            value={form.run_dates}
            onChange={handleChange}
            placeholder="2026-09-25, 2026-09-30"
          />

          <small>
            Separate dates using commas.
          </small>

        </div>

      )}


      {form.schedule_type === "CRON" && (

        <div className="form-group">

          <label>
            Cron Expression
          </label>

          <input
            required
            name="cron_expression"
            value={
              form.cron_expression || ""
            }
            onChange={handleChange}
            placeholder="*/10 * * * *"
          />

          <small>
            Example: */10 * * * * =
            every 10 minutes
          </small>

        </div>

      )}


      <div className="form-row">

        <div className="form-group">

          <label>
            Priority
          </label>

          <input
            type="number"
            name="priority"
            value={form.priority}
            onChange={handleChange}
          />

        </div>


        <div className="form-group">

          <label>
            Max Attempts
          </label>

          <input
            type="number"
            min="1"
            name="max_attempts"
            value={
              form.max_attempts
            }
            onChange={handleChange}
          />

        </div>


        <div className="form-group">

          <label>
            Timeout
          </label>

          <input
            type="number"
            min="1"
            name="timeout_seconds"
            value={
              form.timeout_seconds
            }
            onChange={handleChange}
          />

        </div>

      </div>


      <div className="form-group">

        <label>
          Payload JSON
        </label>

        <textarea
          className="json-editor"
          name="payload"
          value={form.payload}
          onChange={handleChange}
          rows="8"
        />

      </div>


      <div className="form-row">

        <div className="form-group">

          <label>
            Start At
          </label>

          <input
            type="datetime-local"
            name="start_at"
            value={
              form.start_at || ""
            }
            onChange={handleChange}
          />

        </div>


        <div className="form-group">

          <label>
            End At
          </label>

          <input
            type="datetime-local"
            name="end_at"
            value={
              form.end_at || ""
            }
            onChange={handleChange}
          />

        </div>

      </div>


      <div className="form-group">

        <label>
          Maximum Runs
        </label>

        <input
          type="number"
          min="1"
          name="max_runs"
          value={
            form.max_runs || ""
          }
          onChange={handleChange}
        />

      </div>


      <div className="form-group">

        <label>
          Misfire Policy
        </label>

        <select
          name="misfire_policy"
          value={
            form.misfire_policy
          }
          onChange={handleChange}
        >

          <option value="SKIP">
            Skip
          </option>

          <option value="RUN_ONCE">
            Run Once
          </option>

        </select>

      </div>


      <button
        type="submit"
        className="primary-button"
      >
        {submitText}
      </button>

    </form>

  );
}


export default ScheduleForm;