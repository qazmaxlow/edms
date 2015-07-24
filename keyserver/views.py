import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.utils.timezone import localtime
from system.models import System
from .models import ProductKey
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required_trails


class ProductKeyManageView(ListView):

    template_name = 'list.html'

    @method_decorator(permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(ProductKeyManageView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ProductKey.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProductKeyManageView, self).get_context_data(**kwargs)
        company_syscode = 'hq'
        company_system = System.objects.get(code=company_syscode)
        User = get_user_model()
        context['users'] = User.objects.filter(system__code=company_syscode)
        context['other_users'] = []
        for u in context['users']:
            context['other_users'].append(User.objects.filter(system__code=company_syscode).exclude(username=u.username))

        context['company_system'] = company_system

        return context
