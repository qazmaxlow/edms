import datetime
import pytz

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from system.models import System


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

        unitrates = sys.get_money_unitrates(start_from=this_year_first_date)

        # if no unit rate for this year, use the latest one

        info = {}
        response = Response(info, status=status.HTTP_200_OK)
        return response
