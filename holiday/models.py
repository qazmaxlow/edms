import datetime
import csv
from django.db import models

class CityHoliday(models.Model):
    city = models.CharField(max_length=200)
    date = models.DateField()
    desc = models.CharField(max_length=200, blank=True)

    @staticmethod
    def insert_holidays_in_csv(city, csv_path):
        holiday_date_infos = []
        with open(csv_path, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
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