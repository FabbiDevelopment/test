\set ON_ERROR_STOP on
\timing on

-- Select a representative high-cardinality user so both phases use the same ID.
SELECT user_id AS target_user_id
FROM todos
GROUP BY user_id
ORDER BY count(*) DESC
LIMIT 1
\gset

\echo 'Target user: ' :target_user_id

DROP INDEX IF EXISTS ix_todos_user_created_id;
DROP INDEX IF EXISTS ix_todos_user_completed_created_id;
ANALYZE todos;

\echo 'BEFORE: user list ordered by created_at/id'
EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT TEXT)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = :'target_user_id'
ORDER BY created_at DESC, id DESC
LIMIT 20;

\echo 'BEFORE: user todo count'
EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT TEXT)
SELECT count(*) FROM todos WHERE user_id = :'target_user_id';

\echo 'BEFORE: completed-filtered list'
EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT TEXT)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = :'target_user_id' AND completed = false
ORDER BY created_at DESC, id DESC
LIMIT 20;

CREATE INDEX ix_todos_user_created_id
ON todos (user_id, created_at DESC, id DESC);
CREATE INDEX ix_todos_user_completed_created_id
ON todos (user_id, completed, created_at DESC, id DESC);
ANALYZE todos;

\echo 'AFTER: user list ordered by created_at/id'
EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT TEXT)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = :'target_user_id'
ORDER BY created_at DESC, id DESC
LIMIT 20;

\echo 'AFTER: user todo count'
EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT TEXT)
SELECT count(*) FROM todos WHERE user_id = :'target_user_id';

\echo 'AFTER: completed-filtered list'
EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT TEXT)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = :'target_user_id' AND completed = false
ORDER BY created_at DESC, id DESC
LIMIT 20;
