# 🤖 AI Code Review System

An AI-powered code review platform that combines **LLM-based reasoning with deterministic static analysis** to identify bugs, security vulnerabilities, design issues, performance concerns, and code-quality problems.

The system supports direct code reviews as well as **GitHub Pull Request reviews**, with asynchronous processing, PostgreSQL persistence, finding aggregation, semantic deduplication, and automated GitHub review comments.

---

## 📌 Overview

Traditional static analysis tools are excellent at detecting known patterns and rule-based issues, but they have limited understanding of higher-level design problems and context.

LLMs provide broader reasoning capabilities, but their outputs can be inconsistent, duplicated, or difficult to validate.

This project combines both approaches:

```text
                Code / GitHub PR
                       │
                       ▼
                ┌─────────────┐
                │   FastAPI   │
                │     API     │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │    Celery   │
                │    Worker   │
                └──────┬──────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       Ruff         Bandit      AST Analyzer
          │            │            │
          └────────────┼────────────┘
                       │
                       ▼
                 LLM Reviewer
                       │
                       ▼
              ┌─────────────────┐
              │   Aggregator    │
              │ Deduplication   │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        PostgreSQL          GitHub Comment
             │
             ▼
      React Dashboard
```

The result is a structured review containing:

* Severity
* Category
* Description
* Suggested fix
* Confidence
* Source of finding
* Rule ID
* File and line location
* Pull-request status

---

# ✨ Features

### 🔍 Multi-layer code analysis

The system combines several analysis techniques:

* **Ruff** — Python linting and static analysis
* **Bandit** — security-focused static analysis
* **Custom AST analyzer** — project-specific Python analysis
* **LLM reviewer** — contextual reasoning for bugs, design, performance, and code quality

### 🧠 Intelligent finding aggregation

Results from multiple analyzers can overlap.

For example:

```text
Bandit → eval() detected
AST Analyzer → dangerous eval() call
LLM → eval() creates a security vulnerability
```

Instead of presenting three separate findings, the aggregation layer identifies overlapping findings and reduces duplication while preserving useful metadata.

### ⚡ Asynchronous review processing

Long-running reviews are handled through:

```text
FastAPI
   ↓
Review Job
   ↓
Celery
   ↓
Memurai / Redis
   ↓
Background Worker
   ↓
Review Pipeline
```

This prevents the API request from being blocked while the review is running.

### 🐙 GitHub Pull Request integration

The system can process GitHub Pull Requests through webhooks.

The PR workflow:

1. GitHub sends a webhook
2. FastAPI validates the event
3. A review job is created
4. Celery processes the review asynchronously
5. Changed files are identified
6. Reviewable source files are analyzed
7. Findings are classified against changed lines
8. Results are persisted in PostgreSQL
9. A formatted review is posted back to the GitHub PR

### 📊 Review dashboard

The React dashboard provides:

* Review history
* Severity summaries
* Total findings
* Detailed review pages
* Finding locations
* Confidence
* Analysis source
* Rule IDs
* PR finding status

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │    React + TypeScript│
                         │      Dashboard      │
                         └──────────┬──────────┘
                                    │
                                    │ HTTP
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │        API          │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
              PostgreSQL         Celery          GitHub API
                    │               │                │
                    │               ▼                │
                    │        Memurai / Redis         │
                    │               │                │
                    │               ▼                │
                    │      ┌──────────────────┐      │
                    │      │  Review Worker   │      │
                    │      └────────┬─────────┘      │
                    │               │                │
                    │       ┌───────┼────────┐       │
                    │       │       │        │       │
                    │       ▼       ▼        ▼       │
                    │     Ruff   Bandit     AST      │
                    │       │       │        │       │
                    │       └───────┼────────┘       │
                    │               ▼                │
                    │        ┌─────────────┐          │
                    │        │ LLM Review  │          │
                    │        └──────┬──────┘          │
                    │               │                 │
                    │               ▼                 │
                    │        ┌─────────────┐           │
                    │        │ Aggregator  │           │
                    │        │ + Deduping  │           │
                    │        └──────┬──────┘           │
                    │               │                  │
                    └───────────────┼──────────────────┘
                                    │
                                    ▼
                           Structured Review
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                    PostgreSQL          GitHub Comment
```

---

# 🔄 Review Pipeline

## Direct Code Review

```text
User submits code
       │
       ▼
POST /reviews/
       │
       ▼
Static Analysis
       │
       ├── Ruff
       ├── Bandit
       └── AST Analyzer
       │
       ▼
LLM Analysis
       │
       ▼
Finding Aggregation
       │
       ▼
Semantic Deduplication
       │
       ▼
Severity Summary
       │
       ▼
PostgreSQL
       │
       ▼
Review Dashboard
```

---

## Asynchronous Review

For longer-running reviews:

```text
POST /reviews/jobs
       │
       ▼
Create ReviewJob
       │
       ▼
Celery Queue
       │
       ▼
Background Worker
       │
       ▼
Review Pipeline
       │
       ▼
Save Review
       │
       ▼
Job → COMPLETED
```

The API exposes the job status so clients can track the review without keeping the original request open.

---

# 🐙 GitHub Pull Request Pipeline

```text
GitHub Pull Request
        │
        ▼
GitHub Webhook
        │
        ▼
FastAPI
        │
        ▼
ReviewJob
        │
        ▼
Celery Worker
        │
        ▼
Fetch PR Files
        │
        ▼
Filter Reviewable Files
        │
        ▼
Fetch File Contents
        │
        ▼
Parse Unified Diff
        │
        ▼
Determine Changed Lines
        │
        ▼
Run Code Review
        │
        ▼
Classify Findings
        │
        ├── INTRODUCED
        ├── PRE_EXISTING
        └── MODIFIED
        │
        ▼
Persist Review
        │
        ▼
Generate Markdown Review
        │
        ▼
GitHub PR Comment
```

---

# 🧩 Analysis Architecture

The review engine intentionally does not rely exclusively on an LLM.

## 1. Static Analysis

### Ruff

Ruff is used to detect Python linting and code-quality problems.

Examples include:

* unused variables
* import problems
* common Python errors
* style violations

### Bandit

Bandit is used for security-oriented analysis.

Examples include:

* hardcoded credentials
* unsafe `eval`
* shell execution
* other Python security patterns

---

## 2. Custom AST Analysis

A custom Python AST analyzer performs additional structural checks.

Currently it detects patterns such as:

### Dangerous calls

```python
eval(user_input)
```

### Large functions

Functions exceeding the configured size threshold are flagged as potential maintainability issues.

The AST analyzer also provides structured metadata such as:

```text
category
severity
file
line
title
description
suggestion
confidence
source
rule_id
```

---

# 🧠 LLM Review

The LLM layer provides contextual analysis that deterministic tools cannot easily perform.

The reviewer is instructed to analyze:

* Bugs
* Security
* Design
* Performance
* Code quality

LLM findings are returned using a structured schema rather than free-form text.

Example:

```json
{
  "category": "BUG",
  "severity": "HIGH",
  "title": "Possible division by zero",
  "description": "The function divides by the input denominator without validating that it is non-zero.",
  "suggestion": "Validate the denominator before performing the division.",
  "confidence": 0.95,
  "source": "llm"
}
```

The LLM is currently accessed through the Groq API using the OpenAI-compatible Python SDK.

---

# 🔗 Finding Aggregation

One of the important engineering components is the aggregation layer.

Different tools may report the same underlying problem.

For example:

```text
Ruff
  ↓
Unused variable

LLM
  ↓
Variable assigned but never used
```

These should not appear as two independent findings.

The aggregator therefore performs:

* semantic comparison
* line overlap comparison
* deterministic rule mappings
* same-source rule comparison
* metadata preservation

Some deterministic mappings include:

```text
Ruff F841  ↔  LLM unused-variable finding

Bandit B105 ↔  hardcoded credential

Bandit B307 ↔  eval()

Bandit B605 ↔  shell execution
```

The goal is to produce a cleaner and more actionable final review.

---

# 🗄️ Persistence

PostgreSQL stores the review state and historical results.

The database contains entities for:

* Reviews
* Review Issues
* Review Jobs
* Pull Request Reviews
* Pull Request Files
* Pull Request Issues

This allows the system to support:

* review history
* asynchronous job tracking
* PR review retrieval
* persistent findings
* dashboard queries

---

# 🖥️ Dashboard

## Dashboard

The dashboard provides a high-level view of review activity.

It displays:

* Critical findings
* High-severity findings
* Total issues
* Recent reviews
* Review IDs
* Navigation to individual reviews

### Screenshot

Place the dashboard screenshot here:

```text
docs/screenshots/dashboard.png
```

After adding the image to the repository:

```markdown
![Dashboard](docs/screenshots/dashboard.png)
```markdown
![Dashboard2](docs/screenshots/dashboard2.png)
```

---

## Review Detail

The Review Detail page displays individual findings with:

* Severity
* Category
* File
* Line
* Description
* Suggested fix
* Confidence
* Source
* Rule ID
* PR status

### Screenshot

```text
docs/screenshots/review-detail.png
```

Then add:

```markdown
![Review Detail](docs/screenshots/review-detail.png)
```markdown
![Review Detail1](docs/screenshots/review-detail1.png)
```


---

## New Review

The New Review page allows a user to submit source code for analysis.

### Screenshot

```text
docs/screenshots/new-review.png
```

Then add:

```markdown
![New Review](docs/screenshots/new-review.png)
```markdown
![New Review1](docs/screenshots/new-review1.png)
```markdown
![New Review2](docs/screenshots/new-review2.png)
```markdown
![New Review3](docs/screenshots/new-review3.png)
```

---

# 📝 Example Review

### Input

```python
def divide(a, b):
    return a / b
```

### Example output

```text
AI Code Review
────────────────────────────────────

1. Possible division by zero

Severity: HIGH
Category: BUG
Location: example.py:2

Description:
The function divides by the value of `b` without
checking whether it is zero. Calling divide(a, 0)
will raise ZeroDivisionError.

Suggestion:
Validate the denominator before performing the
division or explicitly handle the exception.

Confidence: 0.95
Source: llm
```

The actual application returns structured JSON and renders the finding through the dashboard.

---

# 🛠️ Tech Stack

| Layer                       | Technology                 |
| --------------------------- | -------------------------- |
| Frontend                    | React + TypeScript         |
| Backend                     | Python + FastAPI           |
| Database                    | PostgreSQL                 |
| ORM                         | SQLAlchemy                 |
| Task Queue                  | Celery                     |
| Message Broker              | Memurai / Redis-compatible |
| LLM                         | Groq API                   |
| Static Analysis             | Ruff                       |
| Security Analysis           | Bandit                     |
| Code Analysis               | Python AST                 |
| Version Control Integration | GitHub API + Webhooks      |
| HTTP Client                 | Axios                      |
| Testing                     | Pytest                     |

---

# 📁 Project Structure

```text
ai-code-reviewer/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       └── reviews.py
│   │   │
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   │
│   │   ├── repositories/
│   │   │   └── review_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   └── review.py
│   │   │
│   │   ├── services/
│   │   │   ├── aggregator_service.py
│   │   │   ├── ast_analysis_service.py
│   │   │   ├── diff_service.py
│   │   │   ├── github_comment_service.py
│   │   │   ├── github_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── pr_classification_service.py
│   │   │   ├── pr_review_service.py
│   │   │   ├── pr_service.py
│   │   │   ├── review_service.py
│   │   │   └── static_analysis_service.py
│   │   │
│   │   ├── tasks/
│   │   │   └── review_tasks.py
│   │   │
│   │   ├── celery_app.py
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── test_aggregator.py
│   │   ├── test_ast_analysis.py
│   │   ├── test_database.py
│   │   ├── test_diff_service.py
│   │   ├── test_github_service.py
│   │   ├── test_github_comment_service.py
│   │   ├── test_llm_service.py
│   │   ├── test_pr_classification_service.py
│   │   ├── test_pr_review_service.py
│   │   ├── test_pr_service.py
│   │   ├── test_review_service.py
│   │   ├── test_review_repository.py
│   │   ├── test_review_tasks.py
│   │   ├── test_reviews_api.py
│   │   ├── test_static_analysis.py
│   │   └── test_webhooks.py
│   │
│   ├── create_tables.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── NewReview.tsx
│   │   │   └── ReviewDetail.tsx
│   │   │
│   │   ├── services/
│   │   │   └── api.ts
│   │   │
│   │   ├── types/
│   │   │   └── review.ts
│   │   │
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── index.css
│   │
│   └── package.json
│
└── README.md
```

---

# ⚙️ Setup

## Prerequisites

Install:

* Python 3.10+
* Node.js
* PostgreSQL
* Memurai
* Git

You will also need a Groq API key.

**Never commit API keys or other secrets to the repository.**

---

# 🔐 Environment Variables

Create:

```text
backend/.env
```

Example:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ai_code_reviewer

REDIS_URL=redis://localhost:6379/0
```

Replace the database credentials with your local PostgreSQL configuration.

---

# 🗄️ Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE ai_code_reviewer;
```

Then:

```cmd
cd backend
python create_tables.py
```

This creates the application's database tables.

---

# 🐍 Backend Setup

From the project root:

```cmd
cd backend
```

Create a virtual environment:

```cmd
python -m venv venv
```

Activate it:

```cmd
venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

Start FastAPI:

```cmd
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

# ⚡ Start Memurai

Make sure Memurai is running before starting Celery.

You can verify the Redis-compatible server with:

```cmd
memurai-cli ping
```

Expected:

```text
PONG
```

If Memurai is installed as a Windows service:

```cmd
net start Memurai
```

---

# 👷 Start Celery Worker

Open another terminal:

```cmd
cd backend
```

Activate the virtual environment:

```cmd
venv\Scripts\activate
```

Start the worker:

```cmd
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

The worker should connect to the Memurai/Redis broker and begin accepting review jobs.

---

# ⚛️ Frontend Setup

Open another terminal:

```cmd
cd frontend
```

Install dependencies:

```cmd
npm install
```

Start the development server:

```cmd
npm run dev
```

Open the URL shown by Vite, typically:

```text
http://localhost:5173
```

---

# ▶️ Running the Full System

For the complete local setup, run these components:

### Terminal 1 — PostgreSQL

Make sure PostgreSQL is running.

### Terminal 2 — Memurai

```cmd
memurai-cli ping
```

### Terminal 3 — FastAPI

```cmd
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Terminal 4 — Celery

```cmd
cd backend
venv\Scripts\activate
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

### Terminal 5 — React

```cmd
cd frontend
npm run dev
```

---

# 🔌 API Endpoints

| Method | Endpoint                         | Purpose                    |
| ------ | -------------------------------- | -------------------------- |
| `POST` | `/reviews/`                      | Review source code         |
| `GET`  | `/reviews/`                      | Review history             |
| `GET`  | `/reviews/{review_id}`           | Retrieve a review          |
| `POST` | `/reviews/jobs`                  | Create asynchronous review |
| `GET`  | `/reviews/jobs/{job_id}`         | Check review job           |
| `POST` | `/reviews/github-pr`             | Review a GitHub PR         |
| `GET`  | `/reviews/github-pr/{review_id}` | Retrieve PR review         |
| `POST` | `/reviews/webhooks/github`       | Receive GitHub PR webhook  |
| `GET`  | `/health`                        | Health check               |

Interactive API documentation is available through FastAPI Swagger at:

```text
http://localhost:8000/docs
```

---

# 🧪 Testing

The backend has a comprehensive automated test suite covering:

* Static analysis
* AST analysis
* LLM service
* Finding aggregation
* Semantic deduplication
* Review service
* Database models
* Repository operations
* Review APIs
* Asynchronous jobs
* Celery tasks
* GitHub API integration
* GitHub comments
* Diff parsing
* PR classification
* GitHub webhooks

Run:

```cmd
cd backend
pytest
```

Current test suite:

```text
114 passed
```

---

# 🔒 Security Considerations

The project includes security-focused analysis through Bandit and custom AST checks.

Examples include detection of:

* hardcoded credentials
* unsafe `eval`
* shell execution
* other security-sensitive Python patterns

Secrets such as:

```text
GROQ_API_KEY
DATABASE_URL
GitHub tokens
```

should be stored in environment variables and excluded from version control.

---

# 💡 Engineering Decisions

## Why combine static analysis and LLMs?

Static analysis provides deterministic and reproducible results for known patterns.

LLMs provide contextual reasoning for problems that require understanding developer intent and surrounding code.

Combining both allows the system to use:

```text
Deterministic Analysis
        +
Contextual Reasoning
        ↓
More comprehensive review
```

---

## Why use an aggregation layer?

Multiple analyzers can detect the same underlying problem.

Without aggregation:

```text
3 analyzers
     ↓
3 duplicate findings
```

With aggregation:

```text
3 analyzers
     ↓
Aggregator
     ↓
1 consolidated finding
```

This improves the usability of the final review.

---

## Why asynchronous processing?

Code analysis can involve multiple operations:

* static analysis
* AST parsing
* LLM requests
* GitHub API requests
* database operations

Running all of this synchronously inside an HTTP request can make the API slow and difficult to scale.

Celery allows the review workload to run independently from the API process.

---

## Why PostgreSQL?

The application needs persistent storage for:

* reviews
* findings
* jobs
* pull requests
* historical results

A relational database also makes it possible to query review history and associate findings with their corresponding reviews and PRs.

---

# 🚧 Current Limitations

The current implementation primarily focuses on Python code analysis.

Some planned improvements include:

* broader language support
* more sophisticated PR diff analysis
* inline GitHub review comments
* review evaluation benchmarks
* precision/recall measurement
* containerized deployment
* cloud deployment
* improved authentication and user management
* richer dashboard analytics

---

# 🚀 Future Improvements

Potential extensions include:

```text
Multi-language Analysis
        ↓
Repository-level Context
        ↓
Historical Finding Tracking
        ↓
Automated Evaluation
        ↓
Confidence Calibration
        ↓
Cloud Deployment
```

The evaluation layer can eventually measure:

* precision
* recall
* false-positive rate
* false-negative rate
* review latency
* LLM token usage
* cost per review

---

# 🎯 Project Goals

The project was designed around a practical software-engineering problem:

> **How can automated code review combine deterministic developer tooling with LLM reasoning without overwhelming developers with duplicate or low-value findings?**

The architecture therefore emphasizes:

* deterministic analysis
* structured outputs
* asynchronous processing
* persistent state
* finding aggregation
* GitHub integration
* automated testing

rather than treating the project as a simple LLM wrapper.

---

# 👨‍💻 Author

Built as a software engineering project exploring:

**Backend Systems · Distributed Processing · Static Analysis · LLM Applications · GitHub Automation · Full-Stack Development**
