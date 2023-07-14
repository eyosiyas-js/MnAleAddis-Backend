from celery.app.base import Celery
# from celery.decorators import task,periodic_task
# from celery.utils.log import get_task_logger

from celery import Celery
from celery.schedules import crontab


# logger = get_task_logger(__name__)

app = Celery()

@app.on_after_configure.connect
def setup_perioidic_tasks(sender, **kwargs):
    #calls test('Hello') every 10 seconds
    sender.add_periodic_task(10.0,test.s('hello'),name='add every 10')

@app.task
def test(arg):
    print(arg)
# @task(name="check_expired_stories")
# def check_expired_stories():
#     """
#      Check's expired stories and deletes them
#     """
#     logger.info("Here to check")
#     return 

# @periodic_task(
#     run_every=(crontab(minute='*/1')),
#     name = 'check_expired_stories',
#     ignore_result = True
# )
# def check_expired_stories():
#     """
#      Check's expired stories and deletes them
#     """
#     logger.info("Here to check")
    # return