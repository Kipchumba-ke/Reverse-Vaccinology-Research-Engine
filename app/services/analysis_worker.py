from app.services.job_queue import Queue


class AnalysisWorker:
    def __init__(self, queue: Queue):
        self.queue = queue

    def run(self, job_id):
        return self.queue.run(job_id)