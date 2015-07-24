from rest_framework import viewsets, filters
from rest_framework import generics
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
