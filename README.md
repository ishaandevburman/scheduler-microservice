# Scheduler Microservice

This project involves developing a **Scheduler Microservice** to manage job scheduling and related information. The microservice will expose API endpoints to **create**, **list**, and **retrieve** job details.

The service will handle dummy jobs number crunching and maintain job-related data, while the actual job execution logic is outside the scope.

---

## Features

- Schedule jobs with custom intervals and metadata.
- Jobs can be created, updated, replaced, or deleted via API.
- Supports active/paused/failed job states.
- Persistent jobs with database storage.
- Resilient job execution with failure logging.
- Scalable to thousands of users and API requests.

---

### Swagger / OpenAPI Documentation

These service automatically exposes interactive API docs:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### API Endpoints

| Method | Endpoint           | Description                         |
| ------ | ------------------ | ----------------------------------- |
| GET    | `/jobs`          | List all jobs                       |
| GET    | `/jobs/{job_id}` | Get details of a specific job       |
| POST   | `/jobs`          | Create a new job                    |
| PUT    | `/jobs/{job_id}` | Replace a job completely            |
| PATCH  | `/jobs/{job_id}` | Update specific fields of a job     |
| DELETE | `/jobs/{job_id}` | Delete a job (`?confirm=true`)    |
| DELETE | `/jobs`          | Delete all jobs (`?confirm=true`) |

#### JSON Example

```json
{
  "name": "Job Example",
  "interval_seconds": 10,
   \\ this contains custom job specific attributes, her it multiplies the result number
  "job_metadata": { "multiplier": 5, "text": "Hello" },
  "status": "active"
}
```

---

### Setup

1. Clone the repo:

---

```bash
git clone https://github.com/ishaandevburman/scheduler-microservice.git
cd scheduler-microservice

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

---

### Configuration

##### Environment variables are stored in .env:

```bash
ENV=development
DATABASE_URL=sqlite:///./scheduler.db
LOG_LEVEL=DEBUG
```

Prod example:

```Bash
ENV=production
DATABASE_URL=postgresql+psycopg2://scheduler:schedulerpass@db:5432/schedulerdb
LOG_LEVEL=INFO
```

#### Running

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```
