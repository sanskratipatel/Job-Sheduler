-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = NOW();
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql; 
-- CREATE TRIGGER trg_job_types_updated_at
-- BEFORE UPDATE ON job_types
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column(); 

-- CREATE TRIGGER trg_workers_updated_at
-- BEFORE UPDATE ON workers
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column(); 
-- CREATE TRIGGER trg_job_schedules_updated_at
-- BEFORE UPDATE ON job_schedules
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column(); 
-- CREATE TRIGGER trg_jobs_updated_at
-- BEFORE UPDATE ON jobs
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column(); 

BEGIN;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_job_types_updated_at
ON job_types;

CREATE TRIGGER trg_job_types_updated_at
BEFORE UPDATE ON job_types
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


DROP TRIGGER IF EXISTS trg_workers_updated_at
ON workers;

CREATE TRIGGER trg_workers_updated_at
BEFORE UPDATE ON workers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


DROP TRIGGER IF EXISTS trg_job_schedules_updated_at
ON job_schedules;

CREATE TRIGGER trg_job_schedules_updated_at
BEFORE UPDATE ON job_schedules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


DROP TRIGGER IF EXISTS trg_jobs_updated_at
ON jobs;

CREATE TRIGGER trg_jobs_updated_at
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMIT;