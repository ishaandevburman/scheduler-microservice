import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Adjustable load parameters
NUM_USERS = 100           # Simulate 50 users initially (scale as needed)
NUM_REQUESTS_PER_USER = 6  # Requests per user

@pytest.mark.parametrize("user_id", range(NUM_USERS))
def test_user_simulation(user_id):
    """
    Simulates a single user performing multiple job-related requests.
    """
    for i in range(NUM_REQUESTS_PER_USER):
        # Step 1: Create a job
        payload = {
            "name": f"Job {user_id}-{i}",
            "interval_seconds": 5,
            "job_metadata": {"multiplier": user_id * i, "text": f"Hello {i}"},
            "status": "active"
        }
        create_resp = client.post("/jobs", json=payload)
        assert create_resp.status_code == 200
        job_data = create_resp.json()
        job_id = job_data["id"]

        # Step 2: Fetch the created job
        get_resp = client.get(f"/jobs/{job_id}")
        assert get_resp.status_code == 200
        fetched_data = get_resp.json()
        assert fetched_data["name"] == payload["name"]
        assert fetched_data["job_metadata"] == payload["job_metadata"]

        # Optional: Update job (PATCH)
        patch_payload = {"interval_seconds": 10, "status": "paused"}
        patch_resp = client.patch(f"/jobs/{job_id}", json=patch_payload)
        assert patch_resp.status_code == 200
        updated_data = patch_resp.json()
        assert updated_data["interval_seconds"] == 10
        assert updated_data["status"] == "paused"

        # Optional: Delete job
        del_resp = client.delete(f"/jobs/{job_id}?confirm=true")
        assert del_resp.status_code == 200
        assert "deleted successfully" in del_resp.json()["message"]

@pytest.mark.parametrize("user_id", range(NUM_USERS))
def test_list_jobs(user_id):
    """
    Ensure that listing jobs works under load.
    """
    response = client.get("/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
