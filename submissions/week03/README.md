# Week 3 Submission — Individual Readiness Lab

## Student information

- Name: LIU Weipei
- Student ID:21341691
- Repository: https://github.com/Likelynice/maie6000c-Likelynice
- Checkpoint tag: `w03-readiness`
- Commit SHA: `709af0581506190f3fef151957d27b0eda02126c`

## 1. What I changed

I changed `GET /health/ready` in `services/api/app/main.py` so that when the
database is unreachable it returns **HTTP 503** with a JSON detail message,
instead of letting the `SQLAlchemyError` raised by `db.execute(text("SELECT 1"))`
escape and become an unhandled **HTTP 500**.

The endpoint now wraps the probe in `try/except SQLAlchemyError`, logs
`readiness_check_failed` at warning level, and raises
`HTTPException(status_code=503, detail="database unavailable")`.

`GET /health/live` is deliberately unchanged: liveness answers "is the process
alive" and must not depend on PostgreSQL, so it stays 200 while the database
is down.

## 2. Files touched

- `services/api/app/main.py` — wrap the readiness probe in
  `try/except SQLAlchemyError`; raise `HTTPException(503, "database unavailable")`;
  add the `SQLAlchemyError` import.
- `tests/integration/test_health_ready.py` — new test asserting the 503 behaviour.
- `submissions/week03/README.md` — this document.

## 3. How I verified it

- New automated test (`tests/integration/test_health_ready.py`): injects a
  session whose `execute()` raises a real `OperationalError` (a subclass of
  `SQLAlchemyError`) and asserts `503` plus
  `detail == "database unavailable"`. It does not require stopping the
  database, so it also runs in CI.
- Suites inside the image:
  - `docker compose run --rm --no-deps api pytest -q tests/integration/test_health_ready.py` → `1 passed`
  - `docker compose run --rm --no-deps api pytest -q tests/unit tests/integration` → `5 passed`
  - `docker compose run --rm --no-deps api pytest -q` → `5 passed, 1 skipped`
    (the skip is `tests/smoke/test_smoke_cases.py`, which needs `SMOKE_BASE_URL`; pre-existing)
  - `docker compose run --rm --no-deps api ruff check .` → `All checks passed!`
- Manual check against the running stack:

  | Action | `/health/ready` | `/health/live` |
  |---|---|---|
  | stack up | 200 | 200 |
  | `docker compose stop db` | **503** + `{"detail":"database unavailable"}` | 200 (unchanged) |
  | `docker compose start db`, then retry | 200 | 200 |

  Before this change, the stopped-database row returned **500** with no detail.

## 4. Known limitations or notes

- Only the database dependency is covered. If the AI service is unavailable the
  case flow still fails as documented, and a failed job is **not retried**.
- `/health/ready` is a dependency probe, not a deep check: it runs `SELECT 1`
  and does not verify schema or migration state.
- The smoke test remains skipped unless `SMOKE_BASE_URL` is provided.
- While the database is stopped, the worker logs `job_processing_failed`
  roughly every 2 seconds; this is expected behaviour, not a regression.
- `tests/integration/test_api_integration.py python` is a pre-existing template
  file whose name does not match pytest's collection pattern; it is left
  untouched.

## 5. AI Use Statement

- **Tool used:** an AI study assistant (Sia / AskSia).
- **What it was used for:** locating the readiness endpoint in the repository,
  suggesting the `try/except SQLAlchemyError → 503 + detail` pattern, and
  drafting the test that injects a failing session.
- **What I verified, changed, or rejected:** I ran every command myself and read
  the final endpoint. I confirmed the before/after behaviour with
  `docker compose stop db` / `start db`. I rejected returning 200 when the
  dependency is down (an "always green" health check), and I kept
  `/health/live` untouched on purpose.
