# Vulcan — Multi-Agent Workflow Engine

Specialized agents (**Planner → Researcher → Formatter → Critic**) collaborate via a
[LangGraph](https://langchain-ai.github.io/langgraph/) state machine to generate
reports. The Critic can send the draft back for revision (Researcher → Formatter
→ Critic) up to a configurable limit. Exposed via FastAPI, with task state and
full agent traces persisted in Redis.

## Architecture

```
Client --> FastAPI --> LangGraph StateGraph --> Redis (state + trace)
                          |
              Planner -> Researcher -> Formatter -> Critic -> (router)
                              ^                                   |
                              |--------- revise -------------------
                                                                    |
                                                              (approve / budget
                                                               exhausted) -> END
```

- **Planner**: breaks the task into a research/report outline.
- **Researcher**: gathers findings per the plan (or revises based on critic feedback).
- **Formatter**: synthesizes plan + research into a polished Markdown report.
- **Critic**: returns a JSON verdict `{"approved": bool, "feedback": str}`. If not
  approved and the revision budget remains, the graph loops back to the Researcher.
  If the budget is exhausted, the best-effort draft ships as the final report.

Every node appends a `TraceEntry` (agent name, input summary, output, timing,
metadata) to the task's trace, persisted incrementally to Redis after each step.

## Project Layout

```
app/
  api/
    main.py       FastAPI app entrypoint
    routes.py     REST endpoints
  agents/
    planner.py, researcher.py, formatter.py, critic.py
    common.py     shared trace helpers
  core/
    state.py      WorkflowState TypedDict (LangGraph state schema)
    graph.py      StateGraph wiring + routing logic
    llm_client.py Claude client wrapper
    store.py      Redis-backed TaskStore
    runner.py     executes the graph, persists progress
  models/
    schemas.py    Pydantic models (TaskRecord, TraceEntry, etc.)
tests/            pytest suite (fakeredis + mocked LLM, no network needed)
docker/           Dockerfile + docker-compose.yml
scripts/          smoke_test.py (manual end-to-end check)
*.bat             Windows helper scripts (setup, run, test)
```

## Setup (Windows)

```powershell
setup.bat
```

This creates a `.venv`, installs dependencies (including test deps), and
copies `.env.example` to `.env`. **Edit `.env` and set `ANTHROPIC_API_KEY`.**

## Running

### Option 1: Docker Compose (API + Redis)

```powershell
run_docker.bat up
```

Stop with `run_docker.bat down`. View logs with `run_docker.bat logs`.

### Option 2: Local (requires Redis running locally)

```powershell
run_server.bat
```

Server runs at `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

## Running Tests

```powershell
run_tests.bat
```

Tests use `fakeredis` and mock all LLM calls, so no `ANTHROPIC_API_KEY` or
running Redis/network is required. 40 tests cover the state machine, revision
loop, error short-circuiting, Redis store, runner, and full API lifecycle.

## API Reference

### `POST /tasks`
Submit a new task. Runs asynchronously.

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a report on renewable energy trends", "max_revisions": 2}'
```

Response (`202 Accepted`):
```json
{"task_id": "...", "status": "pending", "message": "Task accepted. Poll GET /tasks/{task_id} for status and results."}
```

`max_revisions` is optional (defaults to `MAX_CRITIC_REVISIONS` from `.env`, default `2`).

### `GET /tasks/{task_id}`
Full task record: status, plan, research, critique, final report, revision
count, and full trace.

### `GET /tasks/{task_id}/trace`
Just the agent execution trace - useful for visualizing each agent's
input/output and timing.

### `GET /tasks/{task_id}/result`
Final report only. Returns `409` if not yet completed, `500` if the task failed.

### `GET /tasks`
List recent tasks (most recent first). Optional `?limit=N` (1-200, default 50).

### `DELETE /tasks/{task_id}`
Delete a task record.

### `GET /health`
Liveness probe, includes Redis connectivity check.

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | - | **Required**. Claude API key. |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model used by all agents. |
| `REDIS_URL` | `redis://redis:6379/0` (docker) / `redis://localhost:6379/0` (local) | Redis connection string. |
| `MAX_CRITIC_REVISIONS` | `2` | Default revision budget if not specified per-task. |
| `LOG_LEVEL` | `INFO` | Python logging level. |

## Manual Smoke Test

`scripts/smoke_test.py` exercises the full lifecycle (submit, poll, trace,
result, list, delete) against the API with mocked LLM responses - useful as
a quick sanity check without burning API credits:

```powershell
set PYTHONPATH=.
python scripts\smoke_test.py
```

## Build History

This project was built incrementally:

- **Stage 1**: project scaffolding, config, Docker/Compose, requirements
- **Stage 2**: core state schema + LangGraph state machine (placeholder agent nodes)
- **Stage 3**: real agent implementations (Planner/Researcher/Formatter/Critic via Claude)
- **Stage 4**: Redis-backed TaskStore + workflow runner with incremental persistence
- **Stage 5**: FastAPI REST layer
- **Stage 6**: test suite (40 tests), Windows run scripts, docs
