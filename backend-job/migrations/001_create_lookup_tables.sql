-- CREATE TABLE IF NOT EXISTS job_types (
--     id SMALLSERIAL PRIMARY KEY,

--     code VARCHAR(100) NOT NULL UNIQUE,

--     name VARCHAR(255) NOT NULL,

--     description TEXT,

--     is_active BOOLEAN NOT NULL DEFAULT TRUE,

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );


-- CREATE TABLE IF NOT EXISTS job_statuses (
--     id SMALLSERIAL PRIMARY KEY,

--     code VARCHAR(50) NOT NULL UNIQUE,

--     name VARCHAR(100) NOT NULL,

--     description TEXT,

--     is_terminal BOOLEAN NOT NULL DEFAULT FALSE,

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );


-- CREATE TABLE IF NOT EXISTS execution_statuses (
--     id SMALLSERIAL PRIMARY KEY,

--     code VARCHAR(50) NOT NULL UNIQUE,

--     name VARCHAR(100) NOT NULL,

--     description TEXT,

--     is_terminal BOOLEAN NOT NULL DEFAULT FALSE,

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- ); 

-- INSERT INTO job_statuses (
--     code,
--     name,
--     description,
--     is_terminal
-- )
-- VALUES
--     (
--         'PENDING',
--         'Pending',
--         'Job is waiting to be processed.',
--         FALSE
--     ),
--     (
--         'PROCESSING',
--         'Processing',
--         'Job is currently being processed.',
--         FALSE
--     ),
--     (
--         'SUCCEEDED',
--         'Succeeded',
--         'Job completed successfully.',
--         TRUE
--     ),
--     (
--         'FAILED',
--         'Failed',
--         'Job failed after exhausting its retry attempts.',
--         TRUE
--     ),
--     (
--         'CANCELLED',
--         'Cancelled',
--         'Job was cancelled before completion.',
--         TRUE
--     )
-- ON CONFLICT (code) DO NOTHING; 

-- INSERT INTO execution_statuses (
--     code,
--     name,
--     description,
--     is_terminal
-- )
-- VALUES
--     (
--         'RUNNING',
--         'Running',
--         'Execution attempt is currently running.',
--         FALSE
--     ),
--     (
--         'SUCCEEDED',
--         'Succeeded',
--         'Execution completed successfully.',
--         TRUE
--     ),
--     (
--         'FAILED',
--         'Failed',
--         'Execution failed.',
--         TRUE
--     ),
--     (
--         'TIMED_OUT',
--         'Timed Out',
--         'Execution exceeded its allowed execution time.',
--         TRUE
--     ),
--     (
--         'ABANDONED',
--         'Abandoned',
--         'Execution was abandoned because its worker lost ownership.',
--         TRUE
--     )
-- ON CONFLICT (code) DO NOTHING;



-- INSERT INTO job_types (
--     code,
--     name,
--     description
-- )
-- VALUES
-- (
--     'SEND_EMAIL',
--     'Send Email',
--     'Send an email notification.'
-- ),
-- (
--     'SEND_WEBHOOK',
--     'Send Webhook',
--     'Send an HTTP webhook.'
-- ),
-- (
--     'GENERATE_REPORT',
--     'Generate Report',
--     'Generate a report.'
-- ),
-- (
--     'SYNC_ORDERS',
--     'Sync Orders',
--     'Synchronize order data.'
-- )
-- ON CONFLICT (code) DO NOTHING; 

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS job_types (
    code VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT job_types_code_format
        CHECK (code ~ '^[A-Z][A-Z0-9_]*$')
);

INSERT INTO job_types (
    code,
    name,
    description
)
VALUES
    (
        'SEND_EMAIL',
        'Send Email',
        'Send an email notification.'
    ),
    (
        'SEND_WEBHOOK',
        'Send Webhook',
        'Send an HTTP webhook.'
    ),
    (
        'GENERATE_REPORT',
        'Generate Report',
        'Generate a report.'
    ),
    (
        'SYNC_ORDERS',
        'Sync Orders',
        'Synchronize order data.'
    )
ON CONFLICT (code) DO NOTHING;

COMMIT;