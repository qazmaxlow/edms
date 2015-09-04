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
    unitrates = system.get_unitrates(start_from, end_to, unit_code)
    _unitrate = unitrates.first()

    _ranges = []

    if _unitrate is None:
        unitrate = system.get_unit_rate(start_from, target_unit=unit_code)
        _ranges.append({
            'from': start_from,
            'to': end_to,
            'unitrate': unitrate
        })
        return _ranges
    else:
        if _unitrate.effective_date > start_from:
            # get the unit rate for start_date
            unitrate = system.get_unit_rate(start_from, target_unit=unit_code)
            _ranges.append({
                'from': start_from,
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

        if _unitrate.effective_date < end_to:
            _ranges.append({
                'from': _unitrate.effective_date,
                'to': end_to,
                'unitrate': _unitrate
            })

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


        info = {'costChanged': cost_changed, 'co2Changed': co2_changed}
        response = Response(info, status=status.HTTP_200_OK)
        return response


class compareToBaseline(APIView):

    def get(self, request, *args, **kwargs):
        syscode = self.kwargs['system_code']
        _system = System.objects.get(code=syscode)

        system_and_childs = System.get_systems_within_root(_system.code)
        changed_cost = 0
        changed_co2 = 0
        baseline_year = None

        for system in system_and_childs:
            # first date using entrak
            start_date = system.first_record
            start_date_year = start_date.year

            end_date = timezone.now()
            unitrates = system.get_unitrates(start_from=start_date, target_unit='money')

            # baseline, assume this is one year data

            baselines = BaselineUsage.objects.filter(system=system).order_by('start_dt')
            # year_ranges = range(start_date_year, timezone.now().year+1)

            # no baseline data
            # if baselines is None:
                # return Response({'noBaseline': True}, status=status.HTTP_200_OK)

            # total_co2_changed = 0
            # total_changed = 0

            if baselines.exists():


                from utils import calculation


                # baseline_daily_usages = BaselineUsage.transform_to_daily_usages(grouped_baselines[system.id], system.time_zone)
                baseline_daily_usages = BaselineUsage.transform_to_daily_usages(
                    # grouped_baselines[system.id],
                    baselines,
                    system.time_zone)



            urs = get_unitrate_daterange_map(system, start_date, end_date, 'money')
            for ur in urs:
                unit_start_date = ur['from']
                unit_end_date = ur['to']

                kwh = 0
                if baselines.exists():
                    baseline_year = min(baseline_year or unit_start_date.year, unit_start_date.year)
                    kwh = calculation.calculate_total_baseline_energy_usage(
                        unit_start_date,
                        unit_end_date,
                        baseline_daily_usages
                    )

                sids = [s.id for s in system.direct_sources]
                if len(sids) > 0:
                    total_usages = system.total_usage(unit_start_date, unit_end_date, source_ids=sids)
                    changed_cost += (total_usages['totalKwh'] - kwh) * ur['unitrate'].rate



            urs = get_unitrate_daterange_map(system, start_date, end_date, 'co2')
            for ur in urs:
                unit_start_date = ur['from']
                unit_end_date = ur['to']

                kwh = 0
                if baselines.exists():
                    kwh = calculation.calculate_total_baseline_energy_usage(
                        unit_start_date,
                        unit_end_date,
                        baseline_daily_usages
                    )

                sids = [s.id for s in system.direct_sources]
                if len(sids) > 0:
                    total_usages = system.total_usage(unit_start_date, unit_end_date, source_ids=sids)
                    changed_co2 += (total_usages['totalKwh'] - kwh) * ur['unitrate'].rate

        if baseline_year:
            info = {'costChanged': changed_cost, 'co2Changed': changed_co2, 'baselineYear': baseline_year}
        else:
            info = {'costChanged': None, 'co2Changed': None, 'baselineYear': None}
        response = Response(info, status=status.HTTP_200_OK)
        return response
