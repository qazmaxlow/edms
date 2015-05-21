from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class progressSoFarThisYear(APIView):
    def get(self, request, *args, **kwargs):
        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)

        # using system timezone
        date_today = datetime.datetime.now(sys.time_zone).replace(hour=0, minute=0, second=0, microsecond=0)
        # from this year 1-Jan to current month usage

        info = {}
        response = Response(info, status=status.HTTP_200_OK)
        return response


