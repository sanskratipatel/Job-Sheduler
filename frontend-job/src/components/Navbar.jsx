import {
  NavLink,
} from "react-router-dom";


function Navbar() {

  return (

    <nav className="navbar">

      <div className="navbar-brand">
        Job Scheduler
      </div>


      <div className="navbar-links">

        <NavLink to="/">
          Dashboard
        </NavLink>

        <NavLink to="/jobs">
          Jobs
        </NavLink>

        <NavLink to="/schedules">
          Schedules
        </NavLink>

        <NavLink to="/workers">
          Workers
        </NavLink>

        <NavLink to="/executions">
          Executions
        </NavLink>

      </div>

    </nav>

  );
}


export default Navbar;