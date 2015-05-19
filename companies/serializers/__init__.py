from rest_framework import serializers

from audit.models import Trail


from django.contrib.auth import get_user_model
from django.utils import timezone
User = get_user_model()


class DateTimeTzAwareField(serializers.DateTimeField):
    def to_representation(self, value):
        value = timezone.localtime(value)
        return super(DateTimeTzAwareField, self).to_representation(value)


class EntrakuserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('fullname', 'username')


class TrailSerializer(serializers.HyperlinkedModelSerializer):
    created_time = DateTimeTzAwareField()
    user = EntrakuserSerializer()
    class Meta:
        model = Trail
        fields = ('action_name', 'user', 'created_time')


class MeasureSerializer(serializers.Serializer):
    value = serializers.FloatField()
    datetime = DateTimeTzAwareField()


class MeasureTimeSpanSerializer(serializers.Serializer):
    value = serializers.FloatField()
    start_datetime = DateTimeTzAwareField()
    end_datetime = DateTimeTzAwareField()
    is_today = serializers.BooleanField()


class TotalSerializer(serializers.Serializer):
    cost = serializers.FloatField()
    co2 = serializers.FloatField()


class TopThreeConsumersSerializer(serializers.Serializer):
    d_name = serializers.CharField()
    d_name_tc = serializers.CharField()
    value = serializers.FloatField()
    previous_value = serializers.FloatField()
    percentage_change = serializers.FloatField()


class DailyMeasureSerializer(serializers.Serializer):
    date = serializers.CharField()
    weekday = serializers.CharField()
    value = serializers.FloatField()


class LastWeekStatSerializer(serializers.Serializer):
    average = serializers.FloatField()
    minimum = serializers.FloatField()
    maximum = serializers.FloatField()
    percentage_change = serializers.FloatField()
    data = DailyMeasureSerializer( many=True)
    is_weekday = serializers.BooleanField()
