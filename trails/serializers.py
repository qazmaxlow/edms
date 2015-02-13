from rest_framework import serializers
from django.utils import timezone

class DateTimeTzAwareField(serializers.DateTimeField):
    def to_representation(self, value):
        value = timezone.localtime(value)
        return super(DateTimeTzAwareField, self).to_representation(value)

class TrailSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=200)
    count = serializers.IntegerField()
    month = serializers.DateTimeField()
    graph_count = serializers.IntegerField()
    ranking_count = serializers.IntegerField()
    progress_count = serializers.IntegerField()
    report_count = serializers.IntegerField()
    display_count = serializers.IntegerField()
    alert_count = serializers.IntegerField()
    printer_count = serializers.IntegerField()
    
class HourSerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    count = serializers.IntegerField()
    
class LastAccessSerializer(serializers.Serializer):
    user__system__code = serializers.CharField(max_length=100)
    user__system__name = serializers.CharField(max_length=200)
    created_time__max = DateTimeTzAwareField()