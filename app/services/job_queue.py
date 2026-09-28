class JobQueue:
    def __init__(self):
        self._jobs = {}

    def enqueue(self, job):
        self._jobs[job.analysis_id] = job
        return job.analysis_id

    def get(self, job_id):
        return self._jobs.get(job_id)

    def run(self, job_id):
        job = self.get(job_id)

        if job is None:
            raise ValueError(f"Job {job_id} not found.")

        return job.run()