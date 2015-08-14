from datetime import datetime
from dateutil import relativedelta
import pytz

from rest_framework import status
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from baseline.models import BaselineUsage
from system.models import System, SystemEnergyGoal


class goalTracking(APIView):
    def get(self, request, *args, **kwargs):

        syscode = self.kwargs['system_code']
        system = System.objects.get(code=syscode)

        goal_type = 'this-month'

        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        now = now.astimezone(request.user.system.time_zone)

        # get this month usage
        start_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_to = start_from + relativedelta.relativedelta(months=1)

        this_month_kwh = system.total_usage(start_from, end_to)['totalKwh']

        # get last month usage
        last_start_from = start_from - relativedelta.relativedelta(months=1)
        last_end_to = start_from

        last_month_kwh = system.total_usage(last_start_from, last_end_to)['totalKwh']

        # month = 2
        goal_setting = SystemEnergyGoal.objects.get(
            system=system,
            goal_type=2,
            validated_date=start_from
        )

        compare_percent = None
        if last_month_kwh > 0:
            compare_percent = float(this_month_kwh - last_month_kwh)/ last_month_kwh * 100

        info = {
            'goal_percent': goal_setting.goal_save_percent,
            'compare_percent': compare_percent,
        }

        response = Response(info, status=status.HTTP_200_OK)
        return response


class GoalSerializer(serializers.ModelSerializer):
    # is_all_systems = serializers.BooleanField()
    class Meta:
        model = SystemEnergyGoal
        exclude = ('created_by',)

    def create(self, validated_data):
        request = self.context.get('request')

        goal_setting = SystemEnergyGoal(**validated_data)
        goal_setting.created_by = request.user

        goal_setting.save()

        return goal_setting


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
        syscode = self.kwargs['system_code']
        goals = SystemEnergyGoal.objects.filter(system__code=syscode)

        return goals


class CreateGoalSettingView(generics.CreateAPIView):
    serializer_class = GoalSerializer

    def create(self, request, *args, **kwargs):
        goal_type = request.data['goal_type']
        is_for_all_systems = request.data['is_all_systems']

        if goal_type == '1':
            syscode = self.kwargs['system_code']
            systems = System.get_systems_within_root(syscode)

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

                if is_for_all_systems == 'true':
                    for s in systems:
                        # assert False
                        request_data['system'] = s.id
                        serializer = self.get_serializer(data=request_data)
                        serializer.is_valid(raise_exception=True)
                        self.perform_create(serializer)
                        headers = self.get_success_headers(serializer.data)
                        response_data.append(serializer.data)

                else:
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
