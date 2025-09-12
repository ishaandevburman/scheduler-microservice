import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.job import JobStatus

client = TestClient(app)


@pytest.fixture
def create_job_payload():
    return {
        "name": "Test Job",
        "interval_seconds": 5,
        "job_metadata": {"multiplier": 10, "text": "hello"},
        "status": "active"
    }


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


def test_delete_job(create_job_payload):
    # Create job first
    create_resp = client.post("/jobs", json=create_job_payload)
    job_id = create_resp.json()["id"]

    # Delete without confirmation → should fail
    response = client.delete(f"/jobs/{job_id}")
    assert response.status_code == 400

    # Delete with confirmation
    response = client.delete(f"/jobs/{job_id}?confirm=true")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify it no longer exists
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 404


def test_delete_all_jobs(create_job_payload):
    # Create multiple jobs
    for i in range(2):
        payload = create_job_payload.copy()
        payload["name"] = f"Job {i}"
        client.post("/jobs", json=payload)

    # Delete all without confirmation → should fail
    response = client.delete("/jobs")
    assert response.status_code == 400

    # Delete all with confirmation
    response = client.delete("/jobs?confirm=true")
    assert response.status_code == 200
    assert "All jobs deleted successfully" in response.json()["message"]

    # Verify list is empty
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []
