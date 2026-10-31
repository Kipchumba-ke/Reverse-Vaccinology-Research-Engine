from app.services.celery_queue import celery_app


def test_background_tasks_have_time_limits():
    soft = celery_app.conf.task_soft_time_limit
    hard = celery_app.conf.task_time_limit

    assert soft and hard
    assert hard > soft
