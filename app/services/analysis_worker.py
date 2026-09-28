from app.services.job_queue import JobQueue


class AnalysisWorker:
    def __init__(self, queue: JobQueue):
        self.queue = queue

    def run(self, job_id):
        return self.queue.run(job_id)