import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import get_db
from app.core.scheduler import scheduler_manager
from app.main import app
from app.models.job import Job

client = TestClient(app)


@pytest.fixture
def create_job_payload():
    return {
        "name": "Test Job",
        "function_name": "print_hello",
        "interval_seconds": 5,
        "job_metadata": {"multiplier": 10, "text": "hello"},
        "status": "active"
    }

@pytest.fixture
def create_cron_job_payload():
    return {
        "name": "Cron Test Job",
        "function_name": "dummy_number_crunch",
        "cron_expression": "*/5 * * * *",  # every 5 minutes
        "job_metadata": {"multiplier": 10, "text": "cron"},
        "status": "active"
    }
    
# @pytest.fixture(autouse=True)
# def clean_scheduler_and_db():
#     # Clear in-memory scheduler
#     scheduler_manager.scheduler.remove_all_jobs()

#     # Clear DB jobs + apscheduler_jobs
#     db = next(get_db())
#     db.query(Job).delete()
#     db.execute(text("DELETE FROM apscheduler_jobs"))  # raw delete
#     db.commit()
#     db.close()

def test_create_job(create_job_payload):
    response = client.post("/jobs", json=create_job_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == create_job_payload["name"]
    assert data["status"] == "active"
    assert "id" in data


def test_get_job(create_job_payload):
    # Create job first
    create_resp = client.post("/jobs", json=create_job_payload)
    job_id = create_resp.json()["id"]

    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["name"] == create_job_payload["name"]


def test_list_jobs(create_job_payload):
    client.post("/jobs", json=create_job_payload)
    response = client.get("/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_job_full_update(create_job_payload):
    # Create a job first
    create_resp = client.post("/jobs", json=create_job_payload)
    job_id = create_resp.json()["id"]

    put_payload = {
        "name": "Updated Job",
        "interval_seconds": 10,
        "function_name":"dummy_number_crunch",
        "job_metadata": {"multiplier": 99, "text": "updated"},
        "status": "paused"
    }

    response = client.put(f"/jobs/{job_id}", json=put_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Job"
    assert data["interval_seconds"] == 10
    assert data["job_metadata"]["multiplier"] == 99
    assert data["status"] == "paused"


def test_patch_job_partial_update(create_job_payload):
    # Create a job first
    create_resp = client.post("/jobs", json=create_job_payload)
    job_id = create_resp.json()["id"]

    patch_payload = {"interval_seconds": 15, "status": "paused"}
    response = client.patch(f"/jobs/{job_id}", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["interval_seconds"] == 15
    assert data["status"] == "paused"


def test_delete_interval_job(create_job_payload):
    # Create job first
    create_resp = client.post("/jobs", json=create_job_payload)
    job_id = create_resp.json()["id"]

    # Delete without confirmation -> should fail
    response = client.delete(f"/jobs/{job_id}")
    assert response.status_code == 400

    # Delete with confirmation
    response = client.delete(f"/jobs/{job_id}?confirm=true")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify it no longer exists
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 404


def test_create_cron_job(create_cron_job_payload):
    response = client.post("/jobs", json=create_cron_job_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == create_cron_job_payload["name"]
    assert data["cron_expression"] == create_cron_job_payload["cron_expression"]
    assert "id" in data


def test_get_cron_job(create_cron_job_payload):
    create_resp = client.post("/jobs", json=create_cron_job_payload)
    job_id = create_resp.json()["id"]

    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["cron_expression"] == create_cron_job_payload["cron_expression"]


def test_list_cron_jobs(create_cron_job_payload):
    client.post("/jobs", json=create_cron_job_payload)
    response = client.get("/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_cron_job_full_update(create_cron_job_payload):
    create_resp = client.post("/jobs", json=create_cron_job_payload)
    job_id = create_resp.json()["id"]

    put_payload = {
        "name": "Updated Cron Job",
        "function_name":"print_hello",
        "cron_expression": "0 0 * * MON",  # every Monday at midnight
        "job_metadata": {"multiplier": 99, "text": "updated"},
        "status": "paused"
    }

    response = client.put(f"/jobs/{job_id}", json=put_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Cron Job"
    assert data["cron_expression"] == "0 0 * * MON"
    assert data["job_metadata"]["multiplier"] == 99
    assert data["status"] == "paused"


def test_patch_cron_job_partial_update(create_cron_job_payload):
    create_resp = client.post("/jobs", json=create_cron_job_payload)
    job_id = create_resp.json()["id"]

    patch_payload = {"cron_expression": "0 12 * * *", "status": "paused"}  # every day at noon
    response = client.patch(f"/jobs/{job_id}", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cron_expression"] == "0 12 * * *"
    assert data["status"] == "paused"


def test_delete_cron_job(create_cron_job_payload):
    create_resp = client.post("/jobs", json=create_cron_job_payload)
    job_id = create_resp.json()["id"]

    # Delete without confirmation → fail
    response = client.delete(f"/jobs/{job_id}")
    assert response.status_code == 400

    # Delete with confirmation
    response = client.delete(f"/jobs/{job_id}?confirm=true")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify it no longer exists
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 404

  
def test_delete_all_jobs(create_job_payload, create_cron_job_payload):
    """
    Test deleting all jobs when both interval and cron jobs exist.
    """
    # Cleanup leftovers from previous tests
    client.delete("/jobs?confirm=true")

    # Create 2 interval jobs
    for i in range(2):
        payload = create_job_payload.copy()
        payload["name"] = f"Interval Job {i}"
        client.post("/jobs", json=payload)

    # Create 2 cron jobs
    for i in range(2):
        payload = create_cron_job_payload.copy()
        payload["name"] = f"Cron Job {i}"
        client.post("/jobs", json=payload)
        
    for i in range(2):
        paused_job = create_job_payload.copy()
        paused_job["status"] = "paused"
        client.post("/jobs", json=paused_job)


    # Verify jobs exist
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 6  # 2 interval + 2 cron

    # Attempt delete without confirmation → should fail
    response = client.delete("/jobs")
    assert response.status_code == 400
    assert "Confirmation required" in response.json()["detail"]

    # Delete all with confirmation → should succeed
    response = client.delete("/jobs?confirm=true")
    assert response.status_code == 200
    assert "All jobs deleted successfully" in response.json()["message"]

    # Verify the jobs list is empty
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) == 0