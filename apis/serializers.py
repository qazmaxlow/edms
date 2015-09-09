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


class SourceSerializer(serializers.Serializer):

    id = serializers.CharField()
    en = serializers.CharField(source='d_name')
    zh_tw = serializers.CharField(source='d_name_tc')


class AlertHistorySerializer(serializers.ModelSerializer):

    system = SystemOnlySerializer(source='alert.parent_system')
    name_en = serializers.CharField(source='alert.source_info.nameInfo.en')
    name_zh_tw = serializers.CharField(source='alert.source_info.nameInfo.zh-tw')
    sources =  SourceSerializer(source='alert.sources', many=True)
    start_time = serializers.TimeField(source='alert.start_time')
    end_time = serializers.TimeField(source='alert.end_time')
    check_date = serializers.DateField(source='create_date')

    class Meta:
        model = AlertHistory
        fields = ("id", "created", "resolved", "resolved_datetime", "diff_percent", "threshold_kwh", "current_kwh", "system", "name_en", "name_zh_tw", "sources", "start_time", "end_time", "check_date")


class RegisterDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = EntrakUser
        fields = ['id', 'fullname', 'language', 'email', 'is_personal_account', 'is_active', 'device_id', 'device_type']
        read_only_fields = ['id', 'fullname', 'language', 'email', 'is_personal_account', 'is_active']