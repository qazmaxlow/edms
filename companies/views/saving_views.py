import datetime
from dateutil.relativedelta import relativedelta
import pytz

from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from baseline.models import BaselineUsage
from system.models import System


def get_unitrate_daterange_map(system, start_from=None, end_to=None, unit_code='money'):
    unitrates = system.get_unitrates(self, start_from, end_to, unit_code)
    _unitrate = unitrates.first()

    _ranges = []

    # date_range
    if _unitrate is None:
        pass
    else:
        if _unitrate.effective_date > start_date:
            # get the unit rate for start_date
            unitrate = system.get_unit_rate(start_date, target_unit=unit_code)
            _ranges.append({
                'from': start_date,
                'to': _unitrate.effective_date,
                'unitrate': unitrate
            })

        for unitrate in unitrates[1:]:
            _ranges.append({
                'from': _unitrate.effective_date,
                'to': unitrate.effective_date,
                'unitrate': _unitrate
            })
            _unitrate = unitrate

    return _ranges


def get_saving(system, start_date, end_date, unit_code):
    unitrates = system.get_unitrates(start_from=start_date, target_unit=unit_code)

    _ranges = []
    _unitrate = unitrates.first()

    # get the closest unit rate if no unit rate in the unit rate to for the all date range
    if _unitrate is None:
        unitrate = system.get_unit_rate(start_date, target_unit=unit_code)
        _ranges.append({'from': start_date,
              'to': end_date,
              'unitrate': unitrate
        })

    else:
        if _unitrate.effective_date > start_date:
            # get the unit rate for start_date
            unitrate = system.get_unit_rate(start_date, target_unit=unit_code)
            _ranges.append({'from': start_date,
                  'to': _unitrate.effective_date,
                  'unitrate': unitrate}
            )

        for unitrate in unitrates[1:]:
            r = {'from': _unitrate.effective_date,
                  'to': unitrate.effective_date,
                  'unitrate': _unitrate}
            _unitrate = unitrate
            _ranges.append(r)

        if _unitrate.effective_date < end_date:
            _ranges.append({
                'from': _unitrate.effective_date,
                'to': end_date,
                'unitrate': _unitrate
            })

    total_cost_changed = 0
    for r in _ranges:
        from_dt = r['from']
        to_dt = r['to']
        unitrate = r['unitrate']

        current_kwh = system.get_total_kwh(from_dt, to_dt)
        last_kwh = system.get_total_kwh(from_dt - relativedelta(years=1), to_dt - relativedelta(years=1))
        cost_change = (current_kwh - last_kwh) * unitrate.rate
        total_cost_changed += cost_change

    return total_cost_changed


class savingSoFarThisYear(APIView):

    def get(self, request, *args, **kwargs):
        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)

        # get this year unit rates
        today = datetime.datetime.now(pytz.utc)

        this_year_first_date = datetime.datetime(
            today.year,
            1, 1
        )
        this_year_first_date = sys.time_zone.localize(this_year_first_date)

        start_dt = this_year_first_date
        end_dt = timezone.now() + datetime.timedelta(days=1)
        cost_changed = get_saving(
            sys,
            this_year_first_date,
            timezone.now(),
            'money'
        )

        co2_changed = get_saving(
            sys,
            this_year_first_date,
            timezone.now(),
            'co2'
        )


        info = {'totalCostChanged': cost_changed, 'co2Changed': co2_changed}
        response = Response(info, status=status.HTTP_200_OK)
        return response


class compareToBaseline(APIView):

    def get(self, request, *args, **kwargs):
        syscode = self.kwargs['system_code']
        system = System.objects.get(code=syscode)

        # first date using entrak
        start_date = system.first_record
        start_date_year = start_date.year

        end_date = timezone.now()
        unitrates = system.get_unitrates(start_from=start_date, target_unit='money')

        # baseline, assume this is one year data
        baselines = BaselineUsage.objects.filter(system=system).order_by('start_dt')
        year_ranges = range(start_date_year, timezone.now().year+1)

        total_changed = 0
        for data_year in year_ranges:
            baseline_year = baselines[0].start_dt.year
            for baseline in baselines:
                compare_year = data_year + (baseline.start_dt.year - baseline_year)
                compare_start_date = baseline.start_dt.replace(year = compare_year)
                compare_end_date = baseline.end_dt.replace(year = compare_year)

                # get all money unit rates of the system
                money_rates = system.get_unitrates(
                    start_from=compare_start_date,
                    to = compare_end_date,
                    target_unit='money')

                # slip date to map the unit rates {start: 2014-05-01, end: 2014-05-30, rate: money_rate}

                # get the closest money rate
                start_money_rate = system.get_unit_rate(compare_start_date)
                end_money_rate = system.get_unit_rate(compare_end_date)

                # get the engry used in the peroid
                meter_kwh = system.get_total_kwh(compare_start_date, compare_end_date)
                changed = meter_kwh - baseline.usage
                total_changed += changed

        info = {'costChanged': total_changed}
        response = Response(info, status=status.HTTP_200_OK)
        return response
