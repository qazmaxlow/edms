from bson.objectid import ObjectId
import datetime
from mongoengine import connection

from rest_framework import generics, serializers

from egauge.models import StatusMonitor, Source


class MeterStatusSerializer(serializers.Serializer):
    system_code = serializers.CharField()
    source_id = serializers.CharField()
    value = serializers.FloatField()
    status = serializers.CharField()


class MeterStatusList(generics.ListAPIView):
    serializer_class = MeterStatusSerializer

    def get_queryset(self):
        system_code = self.kwargs['system_code']

        data = []
        mdb_conn = connection.get_db()


        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(hours=1)


        for status_monitor in StatusMonitor.objects.filter():
            current_hour_kwh = 0

            reading = mdb_conn.source_reading_min.aggregate([
                {'$match': {
                    # 'source_id': {'$in': source_ids},
                    'source_id': ObjectId(status_monitor.source_id),
                    'datetime': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }},
                {'$group': {
                    '_id': None,
                    'kwh': {'$sum': '$value'}
                }}
            ])

            if reading['result']:
                current_hour_kwh = reading['result'][0]['kwh']


            if current_hour_kwh > status_monitor.threshold:
                status = 'on'
            else:
                status = 'off'

            source = Source.objects(id=ObjectId(status_monitor.source_id)).first()
            status = {
                'system_code': source.system_code,
                'source_id': status_monitor.source_id,
                'value': current_hour_kwh,
                'status': status,
            }

            data.append(status)

        return data
