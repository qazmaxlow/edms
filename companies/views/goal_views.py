from rest_framework import status
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from baseline.models import BaselineUsage
from system.models import System, SystemEnergyGoal


class goalTracking(APIView):
    def get(self, request, *args, **kwargs):
        info = {}
        response = Response(info, status=status.HTTP_200_OK)
        return response


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemEnergyGoal


class UpdateGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemEnergyGoal

    def update(self, instance, validated_attrs):
        for attr, value in validated_attrs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class GoalSettingsView(generics.ListAPIView):
    serializer_class = GoalSerializer

    def get_queryset(self):
        goals = SystemEnergyGoal.objects.all()
        return goals


class CreateGoalSettingView(generics.CreateAPIView):
    serializer_class = GoalSerializer


class UpdateGoalSettingView(generics.UpdateAPIView):
    serializer_class = UpdateGoalSerializer
    queryset = SystemEnergyGoal.objects.all()


class DestroyGoalSettingView(generics.DestroyAPIView):
    queryset = SystemEnergyGoal.objects.all()