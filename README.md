# Scheduler Microservice

This microservice allows you to **register custom job functions**, schedule them via **intervals** or **cron expressions**, and manage them via a **REST API**.

---

## 1. Adding Custom Job Functions

1. Create your job function in `app/jobs/custom.py` (or any module in `app/jobs/`):

```python
from app.jobs.registry import register_job

@register_job("my_custom_job")
def my_custom_job(job_id: str, job_metadata: dict = None):
    # Your job logic here
    print(f"Running job {job_id} with metadata: {job_metadata}")
```

- Use the @register_job("name") decorator to make your function available for scheduling.
- The function must accept job_id and optional job_metadata arguments.
- Ensure your module is imported in app/main.py:

```python
# app/main.py
import app.jobs.custom  # import custom job functions
```

> This populates the JOB_REGISTRY used by the scheduler.

## 2. Scheduling Jobs (Interval or Cron)

Each job can be scheduled in **one** of two ways:

* **Interval-based** : runs every `n` seconds (`interval_seconds`).
* **Cron-based** : runs according to a cron expression (`cron_expression`).

> Only **one** of `interval_seconds` or `cron_expression` can be provided per job.

### Example JSON for API

**Interval job:**

```
{
  "name": "Number Cruncher",
  "function_name": "dummy_number_crunch",
  "interval_seconds": 10,
  "job_metadata": { "multiplier": 5, "text": "Hello" },
  "status": "active"
}
```

**Cron job:**

```
{
  "name": "Hourly Reporter",
  "function_name": "print_hello",
  "cron_expression": "0 * * * *",
  "job_metadata": { "text": "Hourly update" },
  "status": "paused"
}
```

## 3. Managing Jobs via API

| Method | Endpoint           | Description                         |
| ------ | ------------------ | ----------------------------------- |
| POST   | `/jobs`          | Create a new job                    |
| PUT    | `/jobs/{job_id}` | Replace a job completely            |
| PATCH  | `/jobs/{job_id}` | Update fields of an existing job    |
| GET    | `/jobs`          | List all jobs                       |
| GET    | `/jobs/{job_id}` | Retrieve a specific job             |
| DELETE | `/jobs/{job_id}` | Delete a job (`?confirm=true`)    |
| DELETE | `/jobs`          | Delete all jobs (`?confirm=true`) |

> Active jobs are scheduled automatically when created or replaced. Paused jobs are stored but not scheduled.

## 4. Swagger / OpenAPI Documentation

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 5. Scheduler Behavior

* **Next run time** (`next_run_at`) is automatically computed from interval or cron expression.
* Failed job executions are logged and marked `failed` in the database.
* Jobs can be  **rescheduled** , replaced, or removed dynamically.

---

## 6. Example: Adding and Running a Custom Job

1. Define the function:

```python
@register_job("log_time")
def log_time(job_id: str, job_metadata: dict = None):
    from datetime import datetime
    print(f"[{datetime.utcnow()}] Job {job_id}: {job_metadata}")
```

2. Import it in `main.py`:

```python
import app.jobs.custom
```

3. Create via API (interval every 15 seconds):

```json
{
  "name": "Time Logger",
  "function_name": "log_time",
  "interval_seconds": 15,
  "job_metadata": { "text": "Logging every 15s" },
  "status": "active"
}
```

> The scheduler will now automatically execute log_time every 15 seconds.

## 7. Setup & Configuration

1. Clone the repo:

```bash
git clone https://github.com/ishaandevburman/scheduler-microservice.git
cd scheduler-microservice

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

2. Environment variables (.env):

```bash
ENV=development
DATABASE_URL=sqlite:///./scheduler.db
LOG_LEVEL=DEBUG
```

Production example:

```bash
ENV=production
DATABASE_URL=postgresql+psycopg2://scheduler:schedulerpass@db:5432/schedulerdb
LOG_LEVEL=INFO
```

3. Run the service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

## 8. Job Flow

API Client
   ↓ POST /jobs, PUT /jobs/{id}, PATCH /jobs/{id}
FastAPI Endpoints
   ↓ Validate input & store job
Database (Job Table)
   ↓ Compute `next_run_at`
Scheduler (APScheduler)
   ↓ Lookup function in JOB_REGISTRY
Custom Job Function (custom.py)
   ↓ Execute job logic
