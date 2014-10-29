from __future__ import absolute_import

import pytz
import datetime
from celery import shared_task
from .models import Source, SourceReadingMinInvalid
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
    for xml_url in SourceReadingMinInvalid.objects.distinct('xml_url'):
        recover_min_reading_for_xml_url.delay(xml_url)

@shared_task(ignore_result=True)
def recover_min_reading_for_xml_url(xml_url):
    SourceManager.recover_min_reading_for_xml_url(xml_url)

@shared_task(ignore_result=True)
def force_retrieve_reading(start_dt, end_dt, system_codes):
    SourceManager.force_retrieve_reading(start_dt, end_dt, system_codes, force_retrieve_hour_reading)

@shared_task(ignore_result=True)
def force_retrieve_hour_reading(all_grouped_sources, start_dt, hour_idx):
    SourceManager.force_retrieve_hour_reading(all_grouped_sources, start_dt, hour_idx)


import csv
from ftplib import FTP
import urllib
from StringIO import StringIO

from egauge.models import SourceReadingMin
from system.models import System


@shared_task(ignore_result=True)
def retrieve_hkis_hs_reading():
    system_code = 'hkis-high'
    file_paths = [
        {'source_name': 'air-conditioning', 'path': '/home/hkisftp/entrak/measures/csv/upload/HS+HS-AC_2.csv'},
        {'source_name': 'lights-and-sockets', 'path': '/home/hkisftp/entrak/measures/csv/upload/HS+HS-Main_1.csv'},
    ]

    retrieve_hkis_reading(system_code, file_paths)


@shared_task(ignore_result=True)
def retrieve_hkis_reading(system_code, file_paths):
    ftp_info = {
        'HOST': 'ec2-54-169-17-125.ap-southeast-1.compute.amazonaws.com',
        'USER': 'hkisftp',
        'PASSWORD': 'HKis1P@ssword'
    }

    ftp = FTP(ftp_info['HOST'])
    ftp.login(ftp_info['USER'], ftp_info['PASSWORD'])

    for file_path in file_paths:
        r = StringIO()
        ftp.retrbinary('RETR ' + file_path['path'], r.write)
        rl = r.getvalue().splitlines()
        r.close()

        source = Source.objects(
            system_code=system_code, name=file_path['source_name']).first()

        # last 4 records and calculate consumption...
        csv_reader = csv.reader(rl[-4:])
        previous_row = csv_reader.next()

        for row in csv_reader:
            try:
                timestamp1 = row[2]
                timestamp1 = datetime.datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
                hk_tz = pytz.timezone('Asia/Hong_Kong')
                timestamp1 = hk_tz.localize(timestamp1)
                print(timestamp1)
                consumption1 = float(row[4]) - float(previous_row[4])
                consumption1 = consumption1/5.0 # the value was in 5 min, convert to per min
                previous_row = row
                for i in range(5):
                    measure_time = timestamp1 + datetime.timedelta(seconds=60)*i
                    source_reading_min = SourceReadingMin(
                        source_id = source.id,
                        datetime = measure_time,
                        value = consumption1
                    )
                    SourceReadingMin.objects.insert(source_reading_min)
            except Exception:
                pass

            # neccessary?
            retrieve_time = datetime.datetime.utcnow()
            retrieve_time = pytz.utc.localize(retrieve_time.replace(second=0, microsecond=0))
            retrieve_time -= datetime.timedelta(minutes=2)

            SourceManager.update_sum(retrieve_time, 'Asia/Hong_Kong', [source.id])
