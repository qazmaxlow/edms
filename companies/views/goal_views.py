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

    def create(self, request, *args, **kwargs):
        goal_type = request.data['goal_type']

        if goal_type == '1':
            import datetime
            import pytz
            from dateutil.relativedelta import relativedelta

            now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
            now = now.astimezone(request.user.system.time_zone)

            this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = this_month

            response_data = []
            for i in range(12):
                next_month += relativedelta(months=1)

                request_data = dict(request.data.items())
                request_data['goal_type'] = '2'
                request_data['validated_date'] = next_month

                serializer = self.get_serializer(data=request_data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                response_data.append(serializer.data)

            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UpdateGoalSettingView(generics.UpdateAPIView):
    serializer_class = UpdateGoalSerializer
    queryset = SystemEnergyGoal.objects.all()


class DestroyGoalSettingView(generics.DestroyAPIView):
    queryset = SystemEnergyGoal.objects.all()
