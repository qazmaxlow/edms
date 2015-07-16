from rest_framework import serializers
from system.models import System


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class SystemSerializer(serializers.ModelSerializer):

    child_systems = RecursiveField(many=True)

    class Meta:
        model = System
        fields = ('code', 'name', 'name_tc', 'full_name', 'full_name_tc', 'child_systems')

