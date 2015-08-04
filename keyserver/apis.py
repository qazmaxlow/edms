import uuid
import datetime
import pytz

from rest_framework import viewsets, filters
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import ProductKey
from .serializers import ProductKeySerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'pageSize'
    max_page_size = 100


class ProductKeyListView(generics.ListAPIView):

    serializer_class = ProductKeySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ProductKey.objects.all()


class GenerateKeyView(generics.CreateAPIView):

    serializer_class = ProductKeySerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        data = request.data
        user = request.user

        key  =  ProductKey.objects.create(
                    key=uuid.uuid1().hex,
                    type=3,
                    remark=data['remark'],
                    created_by=user,
                )

        product_key = ProductKeySerializer(key)
        return Response({"results": product_key.data})


class ActivateKeyView(generics.UpdateAPIView):

    serializer_class = ProductKeySerializer
    permission_classes = (IsAuthenticated,)

    def put(self, request, format=None):

        request_user = request.user
        data = request.data

        key =   ProductKey.objects.filter(
                    key=data['key'],
                    type=3,
                    activated_by=None,
                ).first()

        if key:
            key.activated_at = pytz.utc.localize(datetime.datetime.now())
            key.activated_by = request_user
            key.save()
            product_key = ProductKeySerializer(key)
            return Response({"results": product_key.data})
        else:
            content = {'error': 'Invalid key or key already activated'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

