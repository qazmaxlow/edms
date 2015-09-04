from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.response import Response

def return_error_response(msg="Invalid Request", status=HTTP_400_BAD_REQUEST):
  return Response({"detail": msg}, status=status)