from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from rest_framework import generics, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response


from schedulers.models import AutoSendReportSchedular, AutoSendReportReceiver
from system.models import System
from utils.auth import permission_required


class ReportScheduleView(TemplateView):
    template_name="companies/report_schedule/report_schedule.html"

    @method_decorator(permission_required())
    def dispatch(self, request, *args, **kwargs):
        return super(ReportScheduleView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportScheduleView, self).get_context_data(**kwargs)
        syscode = self.kwargs['system_code']

        systems_info = System.get_systems_info(syscode, self.request.user.system.code)
        context = systems_info

        context['current_system'] = systems_info['systems'][0]
        return context


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ('id', 'fullname',)


class ReceiverSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoSendReportReceiver
        fields = ('email', )


class ReportScheduleSerializer(serializers.ModelSerializer):
    receivers = ReceiverSerializer(many=True)
    system_id = serializers.IntegerField(source='system.id')
    frequency_id = serializers.IntegerField(source='frequency')

    class Meta:
        model = AutoSendReportSchedular
        fields = ('id', 'frequency_id', 'receivers', 'system_id')


class CreateReportScheduleSerializer(serializers.ModelSerializer):
    system_id = serializers.IntegerField(write_only=True)
    receivers = ReceiverSerializer(many=True, read_only=False)
    frequency_id = serializers.IntegerField(source='frequency')

    class Meta:
        model = AutoSendReportSchedular
        fields = ('id', 'frequency_id', 'receivers', 'system_id')

    def create(self, validated_data):
        receivers_data = validated_data.pop('receivers')
        scheduler = AutoSendReportSchedular.objects.create(**validated_data)

        for receiver_item in receivers_data:
            receiver = AutoSendReportReceiver(**receiver_item)
            receiver.scheduler = scheduler
            receiver.save()
        return scheduler


class UpdateReportScheduleSerializer(serializers.ModelSerializer):
    system_id = serializers.IntegerField(write_only=True)
    receivers = ReceiverSerializer(many=True, read_only=True)
    frequency_id = serializers.IntegerField(source='frequency')

    class Meta:
        model = AutoSendReportSchedular
        fields = ('id', 'frequency_id', 'receivers', 'system_id')


class CreateReportScheduleView(generics.CreateAPIView):
    serializer_class = CreateReportScheduleSerializer


class ReportScheduleTaskListView(generics.ListAPIView):
    serializer_class = ReportScheduleSerializer
    queryset = AutoSendReportSchedular.objects.all()


class ReportScheduleTaskDestoryView(generics.DestroyAPIView):
    queryset = AutoSendReportSchedular.objects.all()


class ReportScheduleTaskUpdateView(generics.UpdateAPIView):
    serializer_class = UpdateReportScheduleSerializer
    queryset = AutoSendReportSchedular.objects.all()


from constants.schedulers import FREQUENCIES # will refactor

class FrequencyList(APIView):
    def get(self, request, *args, **kwargs):
        response = Response(FREQUENCIES, status=status.HTTP_200_OK)
        return response
