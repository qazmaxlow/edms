from django.utils.translation import ugettext_lazy as _

WEEKLY = 1
MONTHLY = 2

FREQUENCIES = [
    {'id': WEEKLY, 'name': _('Weekly')},
    {'id': MONTHLY, 'name': _('Monthly')},
]
