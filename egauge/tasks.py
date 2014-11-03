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
def retrieve_hkis_hs_measures():
    system_code = 'hkis-high'
    file_paths = [
        {'source_name': 'air-conditioning', 'path': '/home/hkisftp/entrak/measures/csv/upload/HS+HS-AC_2.csv'},
        {'source_name': 'lights-and-sockets', 'path': '/home/hkisftp/entrak/measures/csv/upload/HS+HS-Main_1.csv'},
    ]

    retrieve_hkis_measures(system_code, file_paths)


@shared_task(ignore_result=True)
def retrieve_hkis_ms_measures():
    system_code = 'hkis-middle'
    file_paths = [
        {'source_name': 'air-conditioning', 'path': '/home/hkisftp/entrak/measures/csv/upload/MidSch+MS-AC_3.csv'},
        {'source_name': 'lights-and-sockets', 'path': '/home/hkisftp/entrak/measures/csv/upload/MidSch+MS-Main_4.csv'},
    ]

    retrieve_hkis_measures(system_code, file_paths)


@shared_task(ignore_result=True)
def retrieve_hkis_ups_measures():
    system_code = 'hkis-upper-primary'
    file_paths = [
        {'source_name': 'air-conditioning', 'path': '/home/hkisftp/entrak/measures/csv/upload/UPS-Main + UPS-Main(AC)_7.csv'},
        {'source_name': 'lights-and-sockets', 'path': '/home/hkisftp/entrak/measures/csv/upload/UPS-Sub + UPS-AC_8.csv'},
    ]

    retrieve_hkis_measures(system_code, file_paths)


def retrieve_hkis_measures(system_code, file_paths):
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

        last_time_newrecord = None

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
                    if last_time_newrecord is None:
                        last_time_newrecord = timestamp1
            except Exception:
                pass

            if last_time_newrecord:
                SourceManager.update_sum(last_time_newrecord, 'Asia/Hong_Kong', [source.id])


def import_v2_hkis_hs():
    import_v2_hkis('hkis_v2_data/hkis_hs.csv', 'hkis-high', 'air-conditioning', 'lights-and-sockets')


def import_v2_hkis_ms():
    import_v2_hkis('hkis_v2_data/hkis_ms.csv', 'hkis-middle', 'air-conditioning', 'lights-and-sockets')


def import_v2_hkis_ps():
    import_v2_hkis('hkis_v2_data/hkis_ps.csv', 'hkis-upper-primary', 'air-conditioning', 'lights-and-sockets')


# Just for import the old data from v2, will be removed later
def import_v2_hkis(csv_filename, system_code, source1_name, source2_name):
    source1 = Source.objects(
        system_code=system_code, name=source1_name).first()

    source2 = Source.objects(
        system_code=system_code, name=source2_name).first()

    row_read_count = 0
    last_time_newrecord = None
    with open(csv_filename, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        # Skip first line headers
        spamreader.next()

        # Update data every 3 records
        for row in spamreader:
            try:
                timestamp1 = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                hk_tz = pytz.timezone('Asia/Hong_Kong')
                timestamp1 = hk_tz.localize(timestamp1)

                print(row[0])
                print(timestamp1)
                consumption1 = float(row[1])
                source_reading_min = SourceReadingMin(
                    source_id = source1.id,
                    datetime = timestamp1,
                    value = consumption1
                )
                SourceReadingMin.objects.insert(source_reading_min)

                consumption2 = float(row[2])
                source_reading_min = SourceReadingMin(
                    source_id = source2.id,
                    datetime = timestamp1,
                    value = consumption2
                )
                SourceReadingMin.objects.insert(source_reading_min)

                row_read_count += 1
                if last_time_newrecord is None:
                    last_time_newrecord = timestamp1
                # update sum for every 3 record
                if row_read_count % 3 == 0:
                    SourceManager.update_sum(last_time_newrecord, 'Asia/Hong_Kong', [source1.id, source2.id])
                    last_time_newrecord = None

            except Exception as e:
                print(e)
