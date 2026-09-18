# Tier 4 Verification Matrix

## Database

| Requirement | Evidence | Result |
|---|---|---|
| `tags` UUID/user/name/color/timestamps | `Tag` model and migration `d72b94c31e20` | Pass |
| `todo_tags` composite primary key and cascade FKs | Association table model and migration | Pass |
| Case-insensitive names per user | Unique `(user_id, lower(name))` plus API conflict handling | Pass |
| Required indexes | tags user, both mapping directions, todo user/status/date | Pass |

Migration was exercised on PostgreSQL 16 with upgrade → downgrade → upgrade. All declared indexes were queried from `pg_indexes` after the final upgrade.

## API and backend rules

| Requirement | Evidence | Result |
|---|---|---|
| Tag list/create/update/delete | `/api/v1/tags` router | Pass |
| Filtered/paginated todos | status, tag, keyword, date range, page/page_size | Pass |
| Attach/detach tags | ownership-scoped todo and tag lookup | Pass |
| Bulk status transaction | verify every ID belongs to caller before single SQL update | Pass |
| Stable order | `created_at DESC, id DESC` | Pass |
| User/query-scoped cache | SHA-256 of every normalized filter under user prefix | Pass |
| Complete invalidation | create/update/delete/tag mapping/tag changes/bulk status | Pass |
| Cross-user isolation | all todo/tag mutations include authenticated `user_id` | Pass |

Backend test result: 16 passed. Added cases cover case-insensitive duplicate tags, cross-user tag access, another user's tag attachment, tag filtering, atomic mixed-owner bulk rejection, combined filters, successful bulk update, and cache invalidation.

## Frontend

| Requirement | Evidence | Result |
|---|---|---|
| Filter bar | keyword, status, tag, created-from/to, clear | Pass |
| Attached tags | tags rendered per todo with attach/remove controls | Pass |
| Tag management | list/create/rename/delete interface | Pass |
| Bulk actions | select one/all, clear, mark completed/active | Pass |
| React Query filter keys | `['todos', filters]` includes every filter/pagination value | Pass |
| Mutation invalidation | todo and tag mutations invalidate relevant prefixes | Pass |
| Form validation | todo and tag forms use react-hook-form + Zod with backend limits | Pass |
| Logout isolation | login/register/logout/401 paths clear QueryClient state | Pass |

Frontend ESLint and TypeScript/Vite production build pass.

## Known limitations

- The UI uses a fixed `page_size=100`; the backend supports full pagination, while page navigation controls are outside the explicit frontend requirements.
- Browser component tests are not configured on the independent Tier 4 branch; backend integration tests plus frontend lint/type/build checks are included.
