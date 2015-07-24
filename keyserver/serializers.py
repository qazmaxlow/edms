from rest_framework import serializers
from django.utils import timezone
from .models import ProductKey
from companies.serializers import EntrakuserSerializer, DateTimeTzAwareField


class ProductKeySerializer(serializers.ModelSerializer):

    created_at = DateTimeTzAwareField(format='%Y-%m-%d %H:%m:%S HKT')
    created_by = EntrakuserSerializer()
    activated_at = DateTimeTzAwareField(format='%Y-%m-%d %H:%m:%S HKT')


    class Meta:
        model = ProductKey
        fields = ["id", "key", "remark", "created_at", "created_by", "activated_at", "activated_by"]

