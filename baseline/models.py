import calendar
import datetime
from django.db import models

class BaselineUsage(models.Model):
    system = models.ForeignKey('system.System')
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    usage = models.FloatField()

    @staticmethod
    def get_baselines_for_systems(system_ids):
        result = {}
        for system_id in system_ids:
            result[system_id] = []
        baselines = BaselineUsage.objects.filter(system_id__in=system_ids).order_by('start_dt')
        for baseline in baselines:
            result[baseline.system_id].append(baseline)

        return result

    @staticmethod
    def transform_to_daily_usages(baselines, tz):
        result = {}

        for baseline in baselines:
            start_dt = baseline.start_dt.astimezone(tz)
            num_of_days = (baseline.end_dt.astimezone(tz) - start_dt).days + 1
            daily_usage = baseline.usage/num_of_days
            for day_diff in xrange(num_of_days):
                target_dt = start_dt + datetime.timedelta(days=day_diff)
                if target_dt.month not in result:
                    result[target_dt.month] = {'dt': target_dt, 'usages':{}}
                result[target_dt.month]['usages'][target_dt.day] = daily_usage

        for month, month_info in result.items():
            # not care about the year for month
            require_month_days = 28 if (month == 2) else calendar.monthrange(1984, month)[1]
            month_usages = month_info['usages']
            if len(month_usages) < require_month_days:
                missing_days = [day for day in xrange(1,require_month_days+1) if (day not in month_usages)]
                missing_days.sort()

                if missing_days[0] == 1:
                    prev_month = 12 if (month == 1) else (month - 1)
                    prev_last_day = sorted(result[prev_month]['usages'])[-1]
                    prev_usage = result[prev_month]['usages'][prev_last_day]
                else:
                    prev_usage = month_usages[missing_days[0]-1]

                for missing_day in missing_days:
                    month_usages[missing_day] = prev_usage

        return result

    @staticmethod
    def transform_to_monthly_usages(baselines, tz):
        daily_usages = BaselineUsage.transform_to_daily_usages(baselines, tz)
        result = {}
        for month, month_info in daily_usages.items():
            total = 0
            for _, usage in month_info['usages'].items():
                total += usage

            result[month] = {'dt': month_info['dt'], 'usage': total}

        return result
