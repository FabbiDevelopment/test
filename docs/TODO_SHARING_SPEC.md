# Technical Specification: Todo Sharing

> **Status:** Proposed · **Version:** 1.0 · **Last updated:** 2026-09-18
> This is a Tier 3A design specification. It deliberately defines no implementation work.

## 1. Overview and objective

### Feature summary

An owner can share a Todo list with an existing registered user as either a
**viewer** or an **editor**, can change that permission, and can revoke it at
any time. A viewer may read the list and its Todos. An editor may create,
update, complete, and delete Todos in that list. Only the owner administers
sharing and may delete the list.

The current product has an implicit personal list: every Todo is owned through
`todos.user_id`. This feature introduces an explicit list boundary so a Todo
belongs to one `todo_lists` record. The owner of that list remains the data
owner; a collaborator is never made the owner by editing a Todo.

### Problem statement

Users cannot currently collaborate without disclosing credentials or copying
Todos. That prevents lightweight household, project, or pair-work workflows
and makes revoking access impossible. The feature supplies a least-privilege,
auditable sharing relationship without changing the privacy default: lists are
private unless the owner grants access.

### Goals

- Let an owner grant, change, list, and revoke access to a list for an existing
  user.
- Enforce list-level permissions at the database/service boundary for every
  read and mutation.
- Make revocation effective for all subsequent API requests and prevent stale
  shared-list data from being returned by Redis.
- Preserve existing personal Todos through a backward-compatible migration.

### Non-goals and success measures

The first release does not create public links, pending email invitations, or
team/group sharing. A successful release meets all acceptance criteria and has
no cross-user authorization or stale-after-revoke defect in automated security
tests. Operational metrics should show a share mutation failure rate below 1%
and cache-invalidation failures below 0.1% of successful share mutations.

### Roles and terminology

| Term | Meaning |
|---|---|
| Owner | User in `todo_lists.owner_id`; controls the list and all grants. |
| Viewer | Active collaborator who can read, but cannot mutate, the list or its Todos. |
| Editor | Active collaborator who can read and mutate Todos, but cannot administer access or delete the list. |
| Grant | An active `todo_list_shares` relationship. It is effective immediately; v1 has no acceptance step. |
| Revoke | Change a grant from `active` to `revoked`; it preserves audit history but removes authorization immediately. |
| List access version | Monotonic integer on the list used to version authorization-sensitive cache entries. |

## 2. User stories and acceptance criteria

### US-01 — Grant viewer access

- **As an** owner, **I want to** share a list with a registered user as a
  viewer, **so that** they can track progress without changing my data.
- **Acceptance criteria:**
  - The owner can select a registered user other than themself and grant
    `viewer` access to a list they own.
  - The collaborator sees the list in “Shared with me” and can retrieve its
    Todos after the grant commits.
  - A viewer receives no create, update, delete, permission-change, or revoke
    capability; direct API attempts are denied.
  - The grant action is recorded without Todo title or description content.

### US-02 — Grant editor access

- **As an** owner, **I want to** grant `editor` access, **so that** a trusted
  collaborator can maintain the list.
- **Acceptance criteria:**
  - An editor can create, edit, complete/uncomplete, and delete Todos in that
    shared list.
  - An editor cannot share the list, change another collaborator’s permission,
    revoke access, alter the owner, or delete the list.
  - A Todo created by an editor records that editor as `created_by_id`; the
    list owner is still the resource owner.

### US-03 — Change permission

- **As an** owner, **I want to** promote or demote a collaborator, **so that**
  access matches the current working relationship.
- **Acceptance criteria:**
  - A `viewer` ⇄ `editor` change takes effect for the next authorized request.
  - The API detects a stale share-management screen using the share `version`
    and does not silently overwrite a newer change.
  - Permission changes increment the list access version and invalidate
    affected server and client query state.

### US-04 — Revoke access

- **As an** owner, **I want to** revoke a collaborator, **so that** they can
  no longer see or modify my data.
- **Acceptance criteria:**
  - Revocation is committed atomically with the access-version increment and
    audit event.
  - Subsequent list and Todo requests from the collaborator return `404`; they
    cannot infer whether the list or Todo exists.
  - Cache entries reachable by the revoked user are no longer usable after the
    commit. The backend always authorizes before serving a cached response.
  - A mutation already holding the list write lock may finish before the
    revoke; a mutation starting after revocation commits is rejected.

### US-05 — Discover shared lists

- **As a** collaborator, **I want to** see lists shared with me, **so that** I
  can open only the resources I may access.
- **Acceptance criteria:**
  - The endpoint returns only active grants for the authenticated user, with
    list metadata and effective permission.
  - It never exposes other collaborators, owner email addresses, or revoked
    lists unless the caller is the owner using the owner-only grant endpoint.
  - Results are ordered by most recently granted or changed first and paginated.

## 3. Scope

### In scope

- Explicit private Todo lists; each existing user receives one migrated
  “Personal” list.
- Sharing with an existing, active user by user ID.
- `viewer` and `editor` grants, permission changes, revocation, and owner-only
  grant listing.
- Permission-aware Todo read/create/update/delete APIs and list discovery.
- Redis and React Query isolation/invalidation, audit metadata, migration,
  regression tests, and documented operational behavior.

### Out of scope

- Anonymous/public links, password-protected links, or sharing outside the
  authenticated product.
- Invitations to email addresses without an account, acceptance/decline flows,
  notifications, reminders, groups, or organization roles.
- Delegated administration and collaborator re-sharing.
- Transfer of list ownership, granular per-Todo permissions, comments,
  activity-feed UI, and real-time presence. User-owned Tags are delivered
  independently as Tier 4 work; shared-tag authorization remains out of scope.
- WebSocket/SSE push to force an already-open collaborator browser to repaint.
  API authorization and backend cache invalidation are immediate; the client
  removes inaccessible data on its next fetch or authorization failure.

## 4. Functional behavior and authorization

### Permission matrix

| Action | Owner | Editor | Viewer | Unshared user |
|---|---:|---:|---:|---:|
| Discover/open list | Yes | Yes | Yes | No (`404`) |
| Read Todos | Yes | Yes | Yes | No (`404`) |
| Create Todo | Yes | Yes | No (`403`) | No (`404`) |
| Update/complete Todo | Yes | Yes | No (`403`) | No (`404`) |
| Delete Todo | Yes | Yes | No (`403`) | No (`404`) |
| List grants | Yes | No (`404`) | No (`404`) | No (`404`) |
| Grant/change/revoke access | Yes | No (`404`) | No (`404`) | No (`404`) |
| Delete list | Yes | No (`404`) | No (`404`) | No (`404`) |

`404` is used when a caller has no relationship to the requested list or Todo,
avoiding resource enumeration. An authorized viewer who attempts a mutation
gets `403` with `TODO_LIST_READ_ONLY`, which tells them why their otherwise
visible resource cannot be changed.

### State model

V1 has no `pending` invitation. A valid owner action creates an immediately
active grant. The one share row per `(list_id, collaborator_id)` is retained:

```text
missing ──POST──> active(viewer | editor) ──DELETE──> revoked
                         │                         │
                         └────PATCH permission─────┴──POST re-grant──> active
```

Only the owner triggers transitions. Re-granting a revoked row updates it to
`active`, resets `revoked_at`, increments `version`, and emits a new audit
event; it does not create a duplicate relationship.

### Service-layer rule

Every endpoint resolves access with a single query rooted at `todo_lists`, not
from client-supplied ownership fields. The service returns an effective role
(`owner`, `editor`, `viewer`, or no access) and applies its predicate in the
same transaction as the Todo query or write. UI controls are convenience only,
never authorization.

## 5. Data model and migration

PostgreSQL types below use `UUID`, `TIMESTAMPTZ`, `VARCHAR`, and `INTEGER`.
All timestamps are UTC. Enum values may be native PostgreSQL enums or checked
`VARCHAR` columns; the migration must select one consistently.

### `todo_lists` (new)

| Column | Type | Null | Default | Constraint/index | Notes |
|---|---|---:|---|---|---|
| `id` | UUID | No | generated | PK | Stable list identity. |
| `owner_id` | UUID | No | — | FK `users(id)` `ON DELETE CASCADE`; index | Resource owner. |
| `name` | VARCHAR(100) | No | — | non-blank after trim | “Personal” for migrated lists. |
| `access_version` | INTEGER | No | `0` | `CHECK (access_version >= 0)` | Increment on every grant/permission/revoke. |
| `todo_version` | INTEGER | No | `0` | `CHECK (todo_version >= 0)` | Increment on every Todo mutation in the list. |
| `created_at` | TIMESTAMPTZ | No | `now()` | — | UTC. |
| `updated_at` | TIMESTAMPTZ | No | `now()` | — | UTC. |

Constraints: `UNIQUE(owner_id, name)` for v1 names; a partial unique index
`UNIQUE(owner_id) WHERE name = 'Personal'` ensures one migrated personal list
per owner. Index `ix_todo_lists_owner_updated(owner_id, updated_at DESC, id
DESC)` supports the owner’s list page.

### `todos` (altered)

| Change | Rule |
|---|---|
| Add `list_id UUID NOT NULL` | FK `todo_lists(id) ON DELETE CASCADE`; index `(list_id, created_at DESC, id DESC)`. |
| Replace semantic `user_id` with nullable `created_by_id UUID` | Existing value backfills the creator. It has FK `users(id) ON DELETE SET NULL` and is never used for access control after rollout. Keep a compatibility alias only during a defined API deprecation period. |
| Keep title, description, completed, timestamps | Existing validation and partial-update semantics remain unchanged. |

The list owner may delete a Todo created by an editor. `created_by_id` is
nullable with `ON DELETE SET NULL`, so a collaborator’s account deletion cannot
cascade-delete shared Todos. The field remains attribution only, never an
authorization source.

### `todo_list_shares` (new)

| Column | Type | Null | Default | Constraint/index | Notes |
|---|---|---:|---|---|---|
| `id` | UUID | No | generated | PK | Share identifier. |
| `list_id` | UUID | No | — | FK `todo_lists(id) ON DELETE CASCADE`; unique with collaborator | Shared list. |
| `collaborator_id` | UUID | No | — | FK `users(id) ON DELETE CASCADE`; index | Grantee. |
| `permission` | VARCHAR(10) | No | — | `CHECK IN ('viewer','editor')` | Effective role when active. |
| `status` | VARCHAR(10) | No | `active` | `CHECK IN ('active','revoked')` | No pending state in v1. |
| `version` | INTEGER | No | `1` | `CHECK (version > 0)` | Optimistic concurrency token. |
| `granted_by_id` | UUID | Yes | — | FK `users(id) ON DELETE SET NULL` | Must be the current owner at mutation time; retained only as attribution. |
| `created_at` / `updated_at` | TIMESTAMPTZ | No | `now()` | — | UTC. |
| `revoked_at` | TIMESTAMPTZ | Yes | `NULL` | — | Set only while revoked. |

Constraints and indexes:

- `UNIQUE(list_id, collaborator_id)` provides one current/historical row and
  makes concurrent duplicate grants deterministic.
- A PostgreSQL trigger locks the referenced list and rejects
  `collaborator_id = owner_id`; application validation is an early, friendly
  check, not the only protection.
- `ix_todo_list_shares_collaborator_active(collaborator_id, updated_at DESC,
  list_id) WHERE status = 'active'` supports “Shared with me.”
- `ix_todo_list_shares_list(list_id, status)` supports authorization and the
  owner’s grant list.

### `todo_share_audit_events` (new, append-only)

Store `id`, `list_id`, nullable `share_id`, nullable `actor_id`, nullable
`collaborator_id`, `event_type` (`granted`, `permission_changed`, `revoked`,
`regranted`, `denied`), `occurred_at`, `request_id`, and a small JSON metadata
allowlist (`from_permission`, `to_permission`, reason code). Do not store Todo
content, tokens, passwords, or raw email addresses. Retain for 90 days, then
purge under the privacy retention job. List deletion cascades these events;
user deletion anonymizes nullable actor/collaborator references.

### Backward-compatible migration and rollout data backfill

1. Add `todo_lists`, share/audit tables, nullable `todos.list_id`, and indexes
   in a backward-compatible revision; create concurrently where PostgreSQL
   permits it.
2. Create one `Personal` list for every existing user and set each existing
   Todo’s `list_id` to its former `user_id` owner’s personal list in batches.
3. Validate there are no null `list_id` values, make it `NOT NULL`, then deploy
   dual-read/dual-write-compatible services before removing old ownership use.
4. Backfill `created_by_id` from `todos.user_id`; expose neither field as an
   authorization input. Remove/deprecate `user_id` only in a later, separately
   announced API version.
5. Ship write APIs behind `todo_sharing_v1`; monitor, then enable frontend.
   Rollback disables the flag and reads legacy personal lists. Never drop the
   new schema or grants automatically after users begin sharing.

## 6. API contracts

All endpoints require a valid access JWT and use `/api/v1`. UUID path values
must be valid UUIDs. JSON uses UTC ISO-8601 timestamps. Authorization failures
follow the matrix above.

| Method | Endpoint | Success | Required role | Purpose |
|---|---|---:|---|---|
| GET | `/todo-lists` | 200 | authenticated | List caller-owned lists. |
| GET | `/todo-lists/shared?page=&size=` | 200 | authenticated | List active grants to caller. |
| GET | `/todo-lists/{list_id}` | 200 | owner/viewer/editor | Fetch permitted list metadata and effective role. |
| POST | `/todo-lists/{list_id}/shares` | 201/200 | owner | Grant, or re-grant, a collaborator. |
| GET | `/todo-lists/{list_id}/shares?page=&size=` | 200 | owner | List current and revoked grants. |
| PATCH | `/todo-lists/{list_id}/shares/{share_id}` | 200 | owner | Change active grant permission. |
| DELETE | `/todo-lists/{list_id}/shares/{share_id}` | 204 | owner | Revoke an active grant. |
| GET | `/todo-lists/{list_id}/todos?page=&size=` | 200 | owner/viewer/editor | List permitted Todos. |
| POST | `/todo-lists/{list_id}/todos` | 201 | owner/editor | Create a Todo. |
| GET | `/todos/{todo_id}` | 200 | owner/viewer/editor | Read a Todo after list access check. |
| PATCH | `/todos/{todo_id}` | 200 | owner/editor | Partial update; omitted fields remain unchanged. |
| DELETE | `/todos/{todo_id}` | 204 | owner/editor | Delete a Todo. |

`size` defaults to `20` and is constrained to `1..100`. Lists use stable
`updated_at DESC, id DESC` ordering; Todos use `created_at DESC, id DESC`.

### Share request and response schemas

`POST /todo-lists/{list_id}/shares`

```json
{
  "collaborator_id": "550e8400-e29b-41d4-a716-446655440000",
  "permission": "viewer"
}
```

- `collaborator_id`: required UUID of an active existing user; must not equal
  the owner.
- `permission`: required enum, `viewer` or `editor`.
- Optional `Idempotency-Key` (1–128 printable characters) is retained for 24
  hours per owner/list/key. Retrying the same request returns its original
  response; reuse with a different body returns `409 IDEMPOTENCY_KEY_REUSED`.
- A newly created grant returns `201`; a re-grant of the same revoked row
  returns `200`. A second active grant without the same idempotency key returns
  `409 SHARE_ALREADY_EXISTS`.

```json
{
  "id": "2d0e8400-e29b-41d4-a716-446655440001",
  "list_id": "1d0e8400-e29b-41d4-a716-446655440001",
  "collaborator": { "id": "550e8400-e29b-41d4-a716-446655440000" },
  "permission": "viewer",
  "status": "active",
  "version": 1,
  "created_at": "2026-09-18T10:00:00Z",
  "updated_at": "2026-09-18T10:00:00Z"
}
```

`PATCH /todo-lists/{list_id}/shares/{share_id}` accepts only
`{ "permission": "viewer" | "editor" }` for an active share. It requires
`If-Match: "<share-version>"`; absent yields `428 PRECONDITION_REQUIRED`, and
a mismatch yields `412 SHARE_VERSION_CONFLICT` with the current safe share
representation. `DELETE` also requires `If-Match` and an idempotency key;
repeating the same completed deletion is `204`, while a stale different request
is `412`.

### Todo schemas and compatibility

The existing Todo create/update field validation remains: `title` is 1–200
characters after validation, `description` is nullable, and `completed` is
boolean. `PATCH` uses `exclude_unset`: omitted values are preserved, explicit
`false` persists, and explicit `null` clears `description`. Todo response adds
`list_id` and `created_by_id`; it never implies that a collaborator owns the
list.

### Error contract

Every non-validation error has the following public-safe shape. Existing FastAPI
`422` field-validation responses may retain its standard `detail` array but
must include a stable top-level code when the API error middleware is added.

```json
{
  "detail": "The requested Todo list was not found.",
  "code": "TODO_LIST_NOT_FOUND",
  "request_id": "01J..."
}
```

| Status | Code examples | When |
|---:|---|---|
| 400 | `SELF_SHARE_NOT_ALLOWED`, `USER_INACTIVE` | Semantically invalid request. |
| 401 | `AUTHENTICATION_REQUIRED` | Missing, expired, malformed, or wrong-type JWT. |
| 403 | `TODO_LIST_READ_ONLY` | Viewer attempts an allowed-to-see mutation. |
| 404 | `TODO_LIST_NOT_FOUND`, `TODO_NOT_FOUND`, `SHARE_NOT_FOUND` | Missing or inaccessible resource; do not distinguish for unshared callers. |
| 409 | `SHARE_ALREADY_EXISTS`, `IDEMPOTENCY_KEY_REUSED` | Active duplicate or idempotency-body conflict. |
| 412 | `SHARE_VERSION_CONFLICT` | Stale `If-Match` precondition. |
| 422 | `VALIDATION_ERROR` | Invalid UUID, enum, bounds, or body shape. |
| 428 | `PRECONDITION_REQUIRED` | Required `If-Match` is absent. |

## 7. Transactions, edge cases, and caching

### Concurrency decisions

| Scenario | Required behavior |
|---|---|
| Two simultaneous grants to the same collaborator | Database uniqueness allows one; the other returns `409`, or the same stored response for an identical idempotency key. |
| Self-share | Reject before write and enforce again with the database trigger. |
| Re-grant after revoke | Reuse the single share row, increment its version, clear `revoked_at`, emit `regranted`, and increment list access version. |
| Permission changes at once | One `If-Match` succeeds; stale writers receive `412` and reload. |
| Revoke while editor mutates | Both take `SELECT ... FOR UPDATE` on the list row. The operation that obtains it first is linearized first; no mutation begun after revoke commits can succeed. |
| Owner deletes a list while collaborator reads/writes | Delete takes the list lock and cascades. A request that loses the race returns `404`; no orphan Todo/share remains. |
| Collaborator deleted/disabled | Active grants are cascaded on deletion; disabled accounts fail authentication before authorization. |
| Redis unavailable | Never serve shared data from an unauthenticated cache fallback. Commit the DB transaction; enqueue durable invalidation/outbox work, alert, and let a short TTL be only a safety net. |

### Cache design and invalidation

The backend must authorize against PostgreSQL before reading any list/Todo cache.
It then obtains the current `access_version` and `todo_version` from the
authorized list. Cache keys therefore cannot be replayed after a grant change:

```text
todo-list:v1:{list_id}:access={access_version}:todo={todo_version}
todos:list:v1:{list_id}:user={viewer_id}:role={role}:access={access_version}:todo={todo_version}:page={page}:size={size}
todo-lists:shared:v1:user={collaborator_id}:version={shared_lists_version}:page={page}:size={size}
```

`shared_lists_version` is a Redis counter changed by the after-commit outbox
consumer. It is a cache-busting optimization only; PostgreSQL grant lookup and
the persisted list `access_version` remain the authorization source of truth.

- On create/update/delete Todo: increment `todo_version` in the same database
  transaction; invalidate the initiating user’s React Query keys and publish an
  after-commit event for server-cache invalidation. Other readers refetch a new
  versioned server response rather than receiving stale cached API data.
- On grant, permission change, re-grant, revoke, or list deletion: increment
  `access_version`; update affected users’ `shared_lists_version`; publish an
  outbox invalidation event only after commit.
- The outbox worker deletes old-version keys opportunistically. Versioned keys
  make deletion failure safe because new authorized reads use a new key. TTL is
  five minutes for capacity control, not access control.
- On `404`/`403` from a shared-list API, the frontend removes that list’s
  queries immediately and redirects to the shared-list index. Logout clears all
  user-scoped React Query state. Without real-time transport, an idle browser
  may display already-rendered content until it refetches; it must never obtain
  fresh protected content after revocation.

## 8. Security, privacy, and observability

- Validate access-token signature, expiration, claims, and `type=access` for
  all endpoints. Do not accept refresh tokens.
- Resolve owner and collaborator IDs server-side; never trust `owner_id`,
  permission, list membership, or creator IDs from the client.
- Rate-limit share create/change/revoke per owner and list (for example, 30 per
  hour) and log abuse-safe reason codes. Do not reveal whether an arbitrary
  UUID maps to a user to non-owners.
- Emit structured audit events and metrics for grant/revoke/change, denied
  authorization, idempotency conflict, stale version, outbox delay, and cache
  invalidation failure. Logs include request/list/share IDs only—never tokens,
  Todo text, descriptions, or email addresses.
- Alert on sustained cache-outbox backlog, elevated authorization denials, and
  repeated mutation/version conflicts. Emergency revocation increments access
  version for the list and processes its invalidation event with priority.

## 9. Testing and rollout acceptance

### Required automated coverage

- Owner, editor, viewer, and unshared-user matrix for every list and Todo
  endpoint, including direct API calls that bypass the UI.
- Self-share, inactive/missing collaborator, active duplicate, concurrent
  duplicate, re-grant, and stale `If-Match` cases.
- Cross-user `404` behavior, viewer `403` mutations, and editor restrictions
  on grant administration/list deletion.
- Revocation while an editor mutation races; prove the stated lock ordering.
- Redis key isolation by list, user, role, pagination/query, access version,
  and Todo version; prove mutation and revoke do not return stale data.
- Migration backfill validation, cascade behavior, database constraints, and
  rollback/feature-flag compatibility using PostgreSQL.
- E2E: owner grants viewer/editor; viewer reads but cannot mutate; editor
  performs permitted changes; revoked collaborator loses API access and cached
  UI data after refetch.

### Release gates

1. Migration is reviewed, rehearsed on a production-shaped PostgreSQL backup,
   and reports zero Todos without `list_id` before the `NOT NULL` constraint.
2. Backend authorization/cache and frontend query-isolation tests pass.
3. Feature flag starts disabled; observability dashboards and outbox alerting
   are available before enabling it for internal users.
4. Security reviews the permission matrix and API error enumeration behavior.
5. Rollback disables new writes/UI only; it does not delete created lists,
   grants, audit events, or cache-version records.

## 10. Alternatives considered

| Option | Advantages | Disadvantages | Decision |
|---|---|---|---|
| Keep implicit user-owned list; add `owner_id/collaborator_id` to every Todo | Smallest schema change | Repeats grants per Todo, makes list sharing and revoke/cache semantics error-prone | Rejected |
| Explicit `todo_lists` with list-level grants | Clear authorization boundary, supports multiple lists later, efficient access checks | Requires careful backfill and API evolution | Accepted |
| Email invitation/pending acceptance | Familiar invitation UX | Requires notifications, acceptance state, expiry, and unregistered-user privacy design | Deferred |
| Hard-delete share rows on revoke | Simple query shape | Loses operational/audit evidence and complicates duplicate handling | Rejected |
| Soft-revoke one unique share row plus append-only audit | Deterministic re-grant and useful audit trail | Requires explicit status/version rules | Accepted |

## 11. Approval checklist

- [ ] Product approves editor’s create/update/delete scope and v1 no-invite boundary.
- [ ] Security approves `404`/`403` enumeration policy, trigger, lock ordering, and audit privacy.
- [ ] Backend approves schema, PostgreSQL migration/backfill, transactional outbox, and cache versions.
- [ ] Frontend approves permission-aware views, query keys, and refetch-after-revoke behavior.
- [ ] Operations approves retention, dashboards, alerts, feature flag, and rollback plan.
