# Manual test plan

Environment: run `docker compose up --build`, then open `http://localhost:3000`.

| ID | Scenario and steps | Expected result | Priority / severity | Actual result | Status |
|---|---|---|---|---|---|
| M-01 | Register a new email with matching password. | Account is created and the Todo page opens. | P1 / Critical | E2E registration reached the Todo page. | Pass |
| M-02 | Log in with a wrong password. | The API returns 401 with `Invalid email or password`; no account detail is revealed. | P1 / High | Browser check showed the uniform error without redirecting away. | Pass |
| M-03 | In two browser sessions, create a todo as A; use B to GET, PUT and DELETE that todo URL. | Each request by B returns 403; B's list never includes A's todo. | P0 / Critical | API and browser isolation checks returned 403 and an empty list for B. | Pass |
| M-04 | Create a todo with a description; change only its title. | The description remains unchanged. | P1 / High | Backend regression test retained the original description. | Pass |
| M-05 | Mark a todo complete, then mark it active again. | It changes `false → true → false`. | P1 / High | Backend regression test persisted both transitions. | Pass |
| M-06 | Load the list, then create, edit and delete a todo; reload after each action. | The list reflects every change; no stale cached list is shown. | P1 / High | Cache invalidation tests and E2E reload returned current data. | Pass |
| M-07 | Create tags `Work` and `work` for one account. | The second request returns 409; a tag from another account cannot be attached. | P1 / High | Tag tests returned 409 for duplicate casing and 403 for cross-user attachment. | Pass |
| M-08 | Attach a tag, filter by it, then bulk-mark selected todos complete. | Only owned matching todos are shown; the selected todos update together. | P2 / Medium | Tag filter and atomic bulk-ownership tests passed. | Pass |

Record the observed result and status (`Pass` or `Fail`) during execution.
