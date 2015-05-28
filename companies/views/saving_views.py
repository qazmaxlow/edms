import datetime
from dateutil.relativedelta import relativedelta
import pytz

from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from system.models import System


def get_saving(system, start_date, end_date, unitrates):
    # if no unit rate for this year, use the latest one

    # start_dt = this_year_first_date
    # end_dt = timezone.now() + datetime.timedelta(days=1)

    _ranges = []
    # _st = this_year_first_date
    _unitrate = unitrates[0]

    if _unitrate.effective_date > start_date:
        # get the unit rate for this year
        unitrate = system.get_unit_rate(start_date)
        _ranges.append({'from': start_date,
              'to': unitrate.effective_date,
              'unitrate': unitrate}
        )
        _unitrate = unitrate

    for unitrate in unitrates[1:]:
        # _to = unitrate.effective_date
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

        unitrates = sys.get_unitrates(start_from=this_year_first_date)


        # if no unit rate for this year, use the latest one

        start_dt = this_year_first_date
        end_dt = timezone.now() + datetime.timedelta(days=1)
        cost_changed = get_saving(
            sys,
            this_year_first_date,
            timezone.now() + datetime.timedelta(days=1),
            unitrates
        )

        info = {'totalCostChanged': cost_changed}
        response = Response(info, status=status.HTTP_200_OK)
        return response
