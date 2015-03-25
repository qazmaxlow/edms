from django.shortcuts import render

from rest_framework import generics, mixins

from .models import Message
from .serializers import MessageSerializer


class MessageList(generics.ListAPIView):
    queryset = Message.objects.published()
    serializer_class = MessageSerializer
