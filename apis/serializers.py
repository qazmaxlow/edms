from rest_framework import serializers
from system.models import System
from alert.models import AlertHistory
from user.models import EntrakUser


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class SystemSerializer(serializers.ModelSerializer):

    child_systems = RecursiveField(many=True)

    class Meta:
        model = System
        fields = ('id', 'code', 'name', 'name_tc', 'full_name', 'full_name_tc', 'child_systems')


class SystemOnlySerializer(serializers.ModelSerializer):

    class Meta:
        model = System
        fields = ('id', 'code', 'name', 'name_tc', 'full_name', 'full_name_tc')


class AlertHistorySerializer(serializers.ModelSerializer):

    source_id = serializers.CharField(source='alert.source.id')
    system = SystemOnlySerializer(source='alert.parent_system')
    source_name = serializers.DictField(source='alert.source_name')
    start_time = serializers.TimeField(source='alert.start_time')
    end_time = serializers.TimeField(source='alert.end_time')
    check_date = serializers.DateField(source='create_date')

    class Meta:
        model = AlertHistory
        fields = ("id", "created", "resolved", "resolved_datetime", "diff_percent", "threshold_kwh", "current_kwh", "system", "source_id", "source_name", "start_time", "end_time", "check_date")


class RegisterDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = EntrakUser
        fields = ['id', 'fullname', 'language', 'email', 'is_personal_account', 'is_active', 'device_id', 'device_type']
        read_only_fields = ['id', 'fullname', 'language', 'email', 'is_personal_account', 'is_active']