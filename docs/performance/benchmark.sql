\set benchmark_user '1bbd9104-7e50-42a9-bc2d-d62886d27cce'

-- Dataset and environment evidence.
SELECT version();
SELECT current_setting('shared_buffers') AS shared_buffers,
       current_setting('work_mem') AS work_mem,
       current_setting('effective_cache_size') AS effective_cache_size,
       current_setting('max_parallel_workers_per_gather')
           AS max_parallel_workers_per_gather;
SELECT (SELECT count(*) FROM users) AS users,
       count(*) AS todos,
       count(*) FILTER (WHERE completed) AS completed,
       round(100.0 * avg(completed::int), 2) AS completed_pct,
       min(created_at) AS min_created_at,
       max(created_at) AS max_created_at
FROM todos;
SELECT user_id,
       count(*) AS todo_count,
       count(*) FILTER (WHERE completed) AS completed_count
FROM todos
GROUP BY user_id
ORDER BY todo_count DESC, user_id
LIMIT 5;
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'todos'
ORDER BY indexname;
SELECT pg_relation_size('todos') AS table_bytes,
       pg_indexes_size('todos') AS index_bytes,
       pg_total_relation_size('todos') AS total_bytes;

-- Q1: exact user-scoped page query emitted by TodoService after the ordering fix.
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = :'benchmark_user'::uuid
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 0;

-- Q2: exact user-scoped count query emitted by TodoService.
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT count(*)
FROM todos
WHERE user_id = :'benchmark_user'::uuid;
