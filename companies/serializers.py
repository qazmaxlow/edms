from rest_framework import serializers

from audit.models import Trail


from django.contrib.auth import get_user_model
User = get_user_model()


class EntrakuserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('fullname', 'username')


class TrailSerializer(serializers.HyperlinkedModelSerializer):
    user = EntrakuserSerializer()
    class Meta:
        model = Trail
        fields = ('action_type', 'user', 'created_time')
