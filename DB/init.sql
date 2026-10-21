-- DB/init.sql
-- Optional one-shot schema for the users table.
-- The Flask app also creates this at boot (see backend/app.py ensure_table()),
-- so this file is documentation by default. To make it functional, mount it as
-- a ConfigMap into the StatefulSet at /docker-entrypoint-initdb.d/ (see STEP 5
-- in the reorganisation guide).
--
-- The official postgres image runs every *.sql file in /docker-entrypoint-initdb.d/
-- on first database initialisation ONLY (i.e., when PGDATA is empty).

CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);