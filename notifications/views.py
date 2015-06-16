import datetime

from django.shortcuts import render

from rest_framework import generics, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Message
from user.models import UserMessages
from .serializers import MessageSerializer


class MessageList(generics.ListAPIView):
    serializer_class = MessageSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        read_messages = UserMessages.objects.filter(user_id=user.id).exclude(read_at=None)
        unread_messages = Message.objects.published().exclude(id__in=[m.message_id for m in read_messages])
        print(unread_messages.query)
        return unread_messages


class ReadMessageView(generics.UpdateAPIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):

        user = self.request.user
        message = Message.objects.get(id=self.kwargs['message_id'])

        try:
            m = UserMessages.objects.get(
                    user_id = user.id,
                    message_id = message.id
                )
        except UserMessages.DoesNotExist:
            m = UserMessages(
                    user_id = user.id,
                    message_id = message.id
                )

        m.read_at = datetime.datetime.now()
        m.save()
        read_messages = UserMessages.objects.filter(user_id=user.id).exclude(read_at=None)
        unread_messages = Message.objects.published().exclude(id__in=[m.message_id for m in read_messages])
        return Response({"unread_messages": len(unread_messages)})
