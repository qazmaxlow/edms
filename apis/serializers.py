from rest_framework import serializers
from system.models import System
from alert.models import AlertHistory


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class SystemSerializer(serializers.ModelSerializer):

    child_systems = RecursiveField(many=True)

    class Meta:
        model = System
        fields = ('code', 'name', 'name_tc', 'full_name', 'full_name_tc', 'child_systems')


class AlertHistorySerializer(serializers.ModelSerializer):

    system_name = serializers.DictField(source='alert.parent_system_name')
    source_name = serializers.DictField(source='alert.source_name')

    class Meta:
        model = AlertHistory
        fields = ("id", "created", "resolved", "resolved_datetime", "diff_percent", "threshold_kwh", "current_kwh", "system_name", "source_name")

