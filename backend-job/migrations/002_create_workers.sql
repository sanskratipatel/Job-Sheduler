-- CREATE TABLE IF NOT EXISTS workers (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

--     hostname VARCHAR(255) NOT NULL,

--     pid INTEGER,

--     status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',

--     concurrency INTEGER NOT NULL DEFAULT 1,

--     started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     stopped_at TIMESTAMPTZ,

--     version VARCHAR(100),

--     git_sha VARCHAR(100),

--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     CONSTRAINT workers_concurrency_positive
--         CHECK (concurrency > 0),

--     CONSTRAINT workers_status_valid
--         CHECK (
--             status IN (
--                 'ACTIVE',
--                 'DRAINING',
--                 'STOPPED',
--                 'DEAD'
--             )
--         )
-- ); 

BEGIN;

CREATE TABLE IF NOT EXISTS workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    hostname VARCHAR(255) NOT NULL,
    pid INTEGER NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    concurrency INTEGER NOT NULL DEFAULT 1,

    version VARCHAR(100),
    git_sha VARCHAR(100),

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT workers_status_valid
        CHECK (
            status IN (
                'ACTIVE',
                'DRAINING',
                'STOPPED',
                'DEAD'
            )
        ),

    CONSTRAINT workers_concurrency_positive
        CHECK (concurrency > 0)
);

COMMIT;