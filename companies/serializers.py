from rest_framework import serializers

from audit.models import Trail


class TrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trail
        fields = ('action_type', 'user', 'created_time')
