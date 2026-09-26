# AI-Powered Code Review System

An end-to-end code review platform that combines **LLM-based reasoning with deterministic static analysis** to identify bugs, security vulnerabilities, design weaknesses, performance issues, and code-quality problems.

The system supports both direct code reviews and **GitHub Pull Request reviews**, with asynchronous processing, persistent review history, finding aggregation, and automated GitHub PR comments.

---

## Features

* **LLM-powered code analysis** using Groq
* **Deterministic static analysis** using Ruff and Bandit
* **Custom Python AST analysis** for additional security and code-quality checks
* **Finding aggregation and semantic deduplication**
* **Asynchronous review processing** using Celery and Memurai
* **PostgreSQL persistence** for reviews, findings, and jobs
* **GitHub Pull Request integration**
* **GitHub webhook support** for PR events
* **Changed-line analysis** using PR diffs
* **Introduced / pre-existing finding classification**
* **Automated review comments on GitHub PRs**
* **React + TypeScript dashboard**
* **Review history and detailed finding views**
* Structured findings containing:

  * Category
  * Severity
  * Description
  * Suggested fix
  * Confidence
  * Source
  * Rule ID
  * Code location
  * PR status

---

## Architecture

```text
                         ┌─────────────────────┐
                         │   React Dashboard   │
                         │   TypeScript + Axios │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │    REST API Layer   │
                         └──────────┬──────────┘
                                    │
                              Create Job
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Celery + Memurai    │
                         │ Async Job Processing │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Review Pipeline        │
                    │                              │
                    │  ┌────────┐   ┌──────────┐  │
                    │  │ Ruff   │   │  Bandit  │  │
                    │  └────────┘   └──────────┘  │
                    │       │             │        │
                    │       └──────┬──────┘        │
                    │              ▼               │
                    │       ┌────────────┐         │
                    │       │ AST        │         │
                    │       │ Analyzer   │         │
                    │       └─────┬──────┘         │
                    │             │                │
                    │             ▼                │
                    │       ┌────────────┐         │
                    │       │ Groq LLM   │         │
                    │       └─────┬──────┘         │
                    │             │                │
                    │             ▼                │
                    │       ┌────────────┐         │
                    │       │ Aggregator │         │
                    │       │ + Dedup    │         │
                    │       └────────────┘         │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │    PostgreSQL       │
                         │ Reviews / Findings  │
                         │ Jobs / PR Reviews   │
                         └─────────────────────┘


       GitHub Pull Request Workflow

                         ┌──────────────────┐
                         │   GitHub PR      │
                         └────────┬─────────┘
                                  │
                              Webhook
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     FastAPI      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Celery Worker    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ GitHub API       │
                         │ Diff + Contents  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         Review Pipeline
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PostgreSQL       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ GitHub PR        │
                         │ Review Comment   │
                         └──────────────────┘
```

---

## How It Works

### 1. Direct Code Review

A user submits source code and its language through the React dashboard.

```text
React
  ↓
POST /reviews/jobs
  ↓
FastAPI
  ↓
ReviewJob created
  ↓
Celery task queued
  ↓
Ruff + Bandit + AST + LLM
  ↓
Aggregator
  ↓
PostgreSQL
  ↓
Dashboard
```

The review is processed asynchronously so the API does not have to keep the client request open while the analysis is running.

---

### 2. Static Analysis

The system uses deterministic tools alongside the LLM.

#### Ruff

Ruff is used for Python linting and code-quality analysis.

#### Bandit

Bandit is used for Python security analysis.

Examples include detecting potentially dangerous operations such as:

* `eval`
* hardcoded credentials
* unsafe shell execution

#### Custom AST Analyzer

A custom Python AST analyzer identifies additional patterns such as:

* dangerous `eval` / `exec` calls
* excessively large functions

This provides deterministic checks that do not depend on LLM behavior.

---

### 3. LLM Analysis

The LLM analyzes the source code for issues that require broader reasoning.

The review categories are:

```text
BUG
SECURITY
DESIGN
PERFORMANCE
CODE_QUALITY
```

Each finding contains structured information such as:

```text
Category
Severity
Title
Description
Suggestion
Confidence
File
Line
Source
Rule ID
```

The LLM output is validated using Pydantic models before being passed into the rest of the review pipeline.

---

## Finding Aggregation and Deduplication

Different analysis systems can detect the same underlying problem.

For example:

```text
Bandit → eval() security issue
AST     → eval() security issue
LLM     → unsafe eval usage
```

Returning all three independently would produce noisy results.

The aggregation layer therefore:

1. Collects findings from static analysis and the LLM.
2. Compares source, rule IDs, locations, and semantic similarity.
3. Identifies overlapping findings.
4. Merges duplicate findings.
5. Preserves important metadata such as severity, confidence, source, and rule ID.

Deterministic mappings are also used for known overlapping rules such as:

```text
Ruff F841  ↔ unused variable
Bandit B105 ↔ hardcoded credential
Bandit B307 ↔ eval()
Bandit B605 ↔ shell execution
```

This gives the final review a cleaner set of actionable findings instead of simply concatenating outputs from multiple tools.

---

## GitHub Pull Request Integration

The system can review GitHub Pull Requests directly.

A PR review can be triggered through the API or through a GitHub webhook.

Supported PR events include:

```text
opened
synchronize
reopened
```

The webhook creates a review job and dispatches it to Celery.

The worker then:

1. Fetches the PR files through the GitHub API.
2. Retrieves the relevant file contents.
3. Parses the PR diff.
4. Identifies changed lines.
5. Runs the review pipeline.
6. Classifies findings based on changed lines.
7. Stores the results in PostgreSQL.
8. Posts a formatted review comment back to the GitHub PR.

---

## Changed-Line Analysis

The system parses unified Git diffs to determine which lines were changed by the Pull Request.

This allows findings to be classified as:

```text
INTRODUCED
PRE_EXISTING
MODIFIED
```

Currently, `INTRODUCED` is assigned when a finding overlaps with a changed line, while findings outside the changed lines are classified as `PRE_EXISTING`.

`MODIFIED` is reserved for future base-versus-head comparison logic.

This distinction helps prevent the review from treating every existing issue in a repository as a new problem introduced by the PR.

---

## Asynchronous Processing

Long-running review operations are handled asynchronously using:

* **Celery** for background task execution
* **Memurai** as the Redis-compatible broker/backend

For example:

```text
POST /reviews/jobs
        │
        ▼
Create ReviewJob
        │
        ▼
Celery.delay(...)
        │
        ▼
Worker executes review
        │
        ▼
Post result to PostgreSQL
```

The same architecture is used for GitHub PR reviews.

This separates API request handling from potentially expensive analysis operations.

---

## Database

PostgreSQL is used for persistent storage.

The database stores:

* Reviews
* Review findings
* Review jobs
* Pull Request reviews
* Pull Request files
* Pull Request findings

The application uses:

```text
SQLAlchemy
PostgreSQL
psycopg2
```

Review jobs track states such as:

```text
PENDING
RUNNING
COMPLETED
FAILED
```

This makes asynchronous jobs observable and allows failed jobs to retain error information.

---

## Frontend

The frontend is built using:

* React
* TypeScript
* Axios
* React Router

The dashboard provides:

### Dashboard

Displays:

* latest review statistics
* critical issues
* high-severity issues
* total issues
* recent reviews

### Reviews

Provides review history and navigation to individual review details.

### New Code Review

Allows users to submit source code for analysis.

### Review Detail

Displays individual findings with:

* severity
* category
* description
* suggestion
* source
* confidence
* code location

### GitHub PR Review

Allows GitHub Pull Request reviews to be initiated and viewed.

---

## Screenshots

### Dashboard

![Dashboard](docs/screenshots/dashboard.png)

![Dashboard](docs/screenshots/dashboard2.png)

### Review Detail

![Review Detail](docs/screenshots/review-detail.png)

![Review Detail](docs/screenshots/review-detail1.png)

### New Code Review

![New Review](docs/screenshots/new-review.png)

![New Review](docs/screenshots/new-review1.png)

![New Review](docs/screenshots/new-review2.png)

![New Review](docs/screenshots/new-review3.png)

---

## Example Finding

For example, submitting:

```python
def process_user_input(user_input):
    result = eval(user_input)
    return result
```

can produce findings such as:

```text
SECURITY
Unsafe use of eval on untrusted input

Source: Bandit
Rule: B307

Suggestion:
Avoid eval() on untrusted input and use a safer
parsing or validation approach.
```

The same code may also produce a code-quality finding from the LLM. The aggregation layer prevents overlapping findings from unnecessarily appearing multiple times.

---

## Technology Stack

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* PostgreSQL
* Celery
* Memurai
* Groq API
* GitHub API

### Code Analysis

* Ruff
* Bandit
* Python AST
* LLM reasoning

### Frontend

* React
* TypeScript
* Axios
* React Router
* Vite

### Testing

* pytest

---

## Project Structure

```text
ai-code-reviewer/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── db/
│   │   ├── repositories/
│   │   └── tasks/
│   │
│   ├── tests/
│   ├── create_tables.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
│
└── docs/
    └── screenshots/
```

---

## Running Locally

### Prerequisites

Install:

* Python
* Node.js
* PostgreSQL
* Memurai

---

### Backend Setup

Navigate to the backend:

```cmd
cd backend
```

Create and activate a virtual environment:

```cmd
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

Create the PostgreSQL database:

```text
ai_code_reviewer
```

Configure the backend `.env` file:

```env
DATABASE_URL=postgresql+psycopg2://<username>:<password>@localhost:5432/ai_code_reviewer

GROQ_API_KEY=<your_groq_api_key>
GROQ_MODEL=openai/gpt-oss-120b

REDIS_URL=redis://localhost:6379/0

GITHUB_TOKEN=<your_github_token>
```

Create the database tables:

```cmd
python create_tables.py
```

---

### Start FastAPI

```cmd
uvicorn app.main:app --reload
```

The backend runs on:

```text
http://localhost:8000
```

---

### Start Memurai

Verify that Memurai is running:

```cmd
memurai-cli ping
```

Expected:

```text
PONG
```

---

### Start Celery

Open another terminal:

```cmd
cd backend
venv\Scripts\activate
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

---

### Frontend Setup

Open another terminal:

```cmd
cd frontend
npm install
```

Start the development server:

```cmd
npm run dev
```

The frontend will be available through the Vite development server.

---

## Testing

The backend includes tests covering:

* static analysis
* AST analysis
* LLM integration
* issue aggregation
* semantic deduplication
* review service
* API endpoints
* database operations
* repositories
* Celery tasks
* GitHub API integration
* Pull Request processing
* diff parsing
* PR finding classification
* GitHub webhooks

Run the test suite:

```cmd
cd backend
venv\Scripts\activate
pytest
```

The project currently has **114 passing backend tests**.

---

## Error Handling

The application handles failures across multiple parts of the pipeline.

Examples include:

* LLM API errors
* LLM rate limits and timeouts
* GitHub API failures
* invalid Python source
* failed background jobs
* database transaction failures

For asynchronous jobs, failures are persisted using the `FAILED` job status along with an error message.

GitHub comment failures are isolated from successful review generation and persistence, preventing a comment-posting failure from incorrectly marking the entire review as failed.

---

## Current Limitations

* Python is currently the primary supported language for deterministic static analysis.
* Public production deployment has not been implemented.
* Real GitHub-to-local webhook delivery requires a publicly reachable backend.
* `MODIFIED` PR finding classification is reserved for future base-versus-head comparison.
* No formal benchmark dataset or accuracy evaluation has been implemented yet.

---

## Future Improvements

Potential future improvements include:

* Docker-based deployment
* Cloud deployment
* Support for additional programming languages
* Inline GitHub review comments tied to specific lines
* Base-versus-head comparison for `MODIFIED` findings
* Formal benchmark evaluation
* Review caching
* Authentication and user accounts
* More advanced LLM-based semantic deduplication

---

## Repository

**GitHub:**
https://github.com/Angel2023111/ai-code-reviewer

---

## Author

**Angel**

Built as a full-stack software engineering project combining backend systems, asynchronous processing, static analysis, LLM reasoning, database persistence, GitHub integration, and a React dashboard.
