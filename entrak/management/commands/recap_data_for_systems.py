import datetime
import pytz
from django.core.management.base import BaseCommand
from utils.utils import Utils
from egauge.manager import SourceManager

class Command(BaseCommand):

    def handle(self, *args, **options):
        system_codes = [code for code in (args[0]).split(',') if code != '']
        start_dt = Utils.utc_dt_from_utc_timestamp(int(args[1]))
        end_dt = Utils.utc_dt_from_utc_timestamp(int(args[2]))

        SourceManager.force_retrieve_reading(start_dt, end_dt, system_codes)
