import datetime
import csv
import codecs
from django.db import models

class CityHoliday(models.Model):
    city = models.CharField(max_length=200)
    date = models.DateField()
    desc = models.CharField(max_length=200, blank=True)

    @staticmethod
    def insert_holidays_in_csv(city, csv_path):
        with open(csv_path, 'rb') as csv_file:
            CityHoliday.insert_holidays_with_file(city, csv_file)

    @staticmethod
    def insert_holidays_with_file(city, csv_file):
        holiday_date_infos = []

        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if row[0].startswith(codecs.BOM_UTF8):
                row[0] = row[0].decode('utf-8-sig').encode('utf-8')
            holiday_date_infos.append((datetime.datetime.strptime(row[0], '%Y-%m-%d').date(), row[1]))

        duplicate_holiday_dates = CityHoliday.objects.filter(
            city=city, date__in=[info[0] for info in holiday_date_infos]
        ).values_list('date', flat=True)
        need_insert_holidays = []
        for info in holiday_date_infos:
            if info[0] not in duplicate_holiday_dates:
                need_insert_holidays.append(CityHoliday(city=city, date=info[0], desc=info[1]))

        CityHoliday.objects.bulk_create(need_insert_holidays)

class Holiday(models.Model):
    system = models.ForeignKey('system.System')
    date = models.DateField()
    desc = models.CharField(max_length=200, blank=True)