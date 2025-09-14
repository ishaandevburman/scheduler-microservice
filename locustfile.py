import random
import uuid

from locust import HttpUser, between, task


class SchedulerUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3)  # Simulate user think time, odd no overlap

    @task
    def job_lifecycle(self):
        """
        Simulate full job lifecycle: create -> get -> patch -> delete
        """
        # Step 1: Create a new job
        job_name = f"Job-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": job_name,
            "cron_expression":"*/5 * * * *",
            "function_name":"dummy_number_crunch",
            "job_metadata": {"multiplier": random.randint(1, 1000), "text": f"Hello {job_name}"},
            "status": "active"
        }
        create_resp = self.client.post("/jobs", json=payload)
        if create_resp.status_code != 200:
            return

        job_id = create_resp.json()["id"]

        # Step 2: Fetch job details
        self.client.get(f"/jobs/{job_id}")

        # Step 3: Update job partially (PATCH) -> mark as paused
        patch_payload = {"interval_seconds": random.randint(5, 20), "status": "paused"}
        self.client.patch(f"/jobs/{job_id}", json=patch_payload)

        # Step 4: Delete the job
        self.client.delete(f"/jobs/{job_id}?confirm=true")

    @task(2)
    def list_jobs(self):
        """
        Simulate frequent listing of all jobs
        """
        self.client.get("/jobs")
