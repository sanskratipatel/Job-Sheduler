import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});


// =============================
// Dashboard
// =============================

export const getDashboardStats = async () => {
  const response = await api.get("/dashboard/stats");
  return response.data;
};


// =============================
// Jobs
// =============================

export const getJobs = async (params = {}) => {
  const response = await api.get("/jobs", { params });
  return response.data;
};

export const getJob = async (jobId) => {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
};

export const createJob = async (data) => {
  const response = await api.post("/jobs", data);
  return response.data;
};

export const updateJob = async (jobId, data) => {
  const response = await api.patch(`/jobs/${jobId}`, data);
  return response.data;
};

export const archiveJob = async (jobId) => {
  const response = await api.delete(`/jobs/${jobId}`);
  return response.data;
};

export const cancelJob = async (jobId) => {
  const response = await api.post(`/jobs/${jobId}/cancel`);
  return response.data;
};

export const retryJob = async (jobId) => {
  const response = await api.post(`/jobs/${jobId}/retry`);
  return response.data;
};

export const getJobExecutions = async (jobId) => {
  const response = await api.get(
    `/jobs/${jobId}/executions`
  );

  return response.data;
};


// =============================
// Schedules
// =============================

export const getSchedules = async (params = {}) => {
  const response = await api.get(
    "/schedules",
    { params }
  );

  return response.data;
};

export const getSchedule = async (scheduleId) => {
  const response = await api.get(
    `/schedules/${scheduleId}`
  );

  return response.data;
};

export const createSchedule = async (data) => {
  const response = await api.post(
    "/schedules",
    data
  );

  return response.data;
};

export const updateSchedule = async (
  scheduleId,
  data
) => {
  const response = await api.patch(
    `/schedules/${scheduleId}`,
    data
  );

  return response.data;
};

export const pauseSchedule = async (
  scheduleId
) => {
  const response = await api.post(
    `/schedules/${scheduleId}/pause`
  );

  return response.data;
};

export const resumeSchedule = async (
  scheduleId
) => {
  const response = await api.post(
    `/schedules/${scheduleId}/resume`
  );

  return response.data;
};

export const archiveSchedule = async (
  scheduleId
) => {
  const response = await api.delete(
    `/schedules/${scheduleId}`
  );

  return response.data;
};


// =============================
// Workers
// =============================

export const getWorkers = async () => {
  const response = await api.get("/workers");

  return response.data;
};


// =============================
// Executions
// =============================

export const getExecutions = async (
  params = {}
) => {
  const response = await api.get(
    "/executions",
    { params }
  );

  return response.data;
};


export default api;