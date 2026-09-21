import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import JobDetails from "./pages/JobDetails";

import Schedules from "./pages/Schedules";
import CreateSchedule from "./pages/CreateSchedule";
import ScheduleDetails from "./pages/ScheduleDetails";
import EditSchedule from "./pages/EditSchedule";

import Navbar from "./components/Navbar";

function App() {
  return (
    <BrowserRouter>

      <Navbar />

      <Routes>

        {/* Dashboard */}
        <Route
          path="/"
          element={<Dashboard />}
        />

        {/* Jobs */}
        <Route
          path="/jobs"
          element={<Jobs />}
        />

        <Route
          path="/jobs/:jobId"
          element={<JobDetails />}
        />

        {/* Schedules */}
        <Route
          path="/schedules"
          element={<Schedules />}
        />

        <Route
          path="/schedules/create"
          element={<CreateSchedule />}
        />

        <Route
          path="/schedules/:scheduleId/edit"
          element={<EditSchedule />}
        />

        <Route
          path="/schedules/:scheduleId"
          element={<ScheduleDetails />}
        />

        {/* Unknown route */}
        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;