from __future__ import absolute_import

from celery import shared_task
from .manager import SourceManager

@shared_task
def add(x, y):
	import time
	time.sleep(3)
	return (x + y)
