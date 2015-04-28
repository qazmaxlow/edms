from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from rest_framework import generics, serializers

from schedulers.models import AutoSendReportSchedular
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
        fields = ('fullname',)


class ReportScheduleSerializer(serializers.ModelSerializer):
    system = SystemSerializer()

    class Meta:
        model = AutoSendReportSchedular
        fields = ('frequency_name', 'system')


class CreateReportScheduleView(generics.CreateAPIView):
    serializer_class = ReportScheduleSerializer


class ReportScheduleTaskListView(generics.ListAPIView):
    serializer_class = ReportScheduleSerializer
    queryset = AutoSendReportSchedular.objects.all()
