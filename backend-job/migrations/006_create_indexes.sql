-- CREATE INDEX IF NOT EXISTS idx_jobs_status_queue
-- ON jobs (
--     status_id,
--     priority DESC,
--     scheduled_at ASC,
--     id ASC
-- ); 

-- CREATE INDEX IF NOT EXISTS idx_jobs_lease
-- ON jobs (
--     lease_expires_at
-- )
-- WHERE lease_expires_at IS NOT NULL; 
-- CREATE INDEX IF NOT EXISTS idx_jobs_created_at
-- ON jobs (
--     created_at DESC,
--     id DESC
-- ); 
-- CREATE INDEX IF NOT EXISTS idx_jobs_created_at
-- ON jobs (
--     created_at DESC,
--     id DESC
-- ); 
-- CREATE INDEX IF NOT EXISTS idx_jobs_job_type_id
-- ON jobs (
--     job_type_id
-- ); 
-- CREATE INDEX IF NOT EXISTS idx_job_executions_job_id
-- ON job_executions (
--     job_id,
--     attempt_number DESC
-- ); 
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_idempotency_key
-- ON jobs (
--     idempotency_key
-- )
-- WHERE idempotency_key IS NOT NULL; 


BEGIN;

CREATE INDEX IF NOT EXISTS idx_jobs_claim
ON jobs (
    priority DESC,
    scheduled_at ASC,
    id ASC
)
WHERE status = 'PENDING';


CREATE INDEX IF NOT EXISTS idx_jobs_lease
ON jobs (lease_expires_at)
WHERE status = 'PROCESSING';


CREATE INDEX IF NOT EXISTS idx_jobs_locked_by
ON jobs (locked_by)
WHERE status = 'PROCESSING';


CREATE INDEX IF NOT EXISTS idx_jobs_created_at
ON jobs (
    created_at DESC,
    id DESC
);


CREATE INDEX IF NOT EXISTS idx_jobs_status_created_at
ON jobs (
    status,
    created_at DESC,
    id DESC
);


CREATE INDEX IF NOT EXISTS idx_jobs_job_type_created_at
ON jobs (
    job_type,
    created_at DESC,
    id DESC
);


CREATE UNIQUE INDEX IF NOT EXISTS uq_jobs_idempotency_key
ON jobs (idempotency_key)
WHERE idempotency_key IS NOT NULL;


CREATE UNIQUE INDEX IF NOT EXISTS uq_jobs_schedule_fire
ON jobs (
    schedule_id,
    scheduled_for
)
WHERE schedule_id IS NOT NULL;


CREATE INDEX IF NOT EXISTS idx_job_schedules_due
ON job_schedules (next_run_at)
WHERE status = 'ACTIVE';


CREATE INDEX IF NOT EXISTS idx_job_schedules_created_at
ON job_schedules (
    created_at DESC,
    id DESC
);


CREATE INDEX IF NOT EXISTS idx_workers_heartbeat
ON workers (
    status,
    last_heartbeat_at
);

COMMIT;