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