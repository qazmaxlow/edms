from __future__ import absolute_import

import pytz
import datetime
from celery import shared_task
from .manager import SourceManager

@shared_task(ignore_result=True)
def retrieve_all_reading():
	retrieve_time = SourceManager.gen_retrieve_time()
	for grouped_sources in SourceManager.get_grouped_sources():
		xml_url = grouped_sources['_id']
		sources = grouped_sources['sources']

		retrieve_min_reading.delay(xml_url, sources, retrieve_time)

@shared_task(ignore_result=True)
def retrieve_min_reading(xml_url, sources, retrieve_time):
	SourceManager.retrieve_min_reading(xml_url, sources, retrieve_time)

@shared_task(ignore_result=True)
def recover_all_invalid_reading():
	SourceManager.recover_all_invalid_reading()
