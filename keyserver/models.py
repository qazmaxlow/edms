from django.db import models
from django.conf import settings

ENTRAK_ENERGY   = 1
ENTRAK_WATER    = 2
ENTRAK_PAPER    = 3
ENTRAK_LIGHTING = 4

PRODUCT_TYPES = (
    (ENTRAK_ENERGY, 'En-Trak Energy'),
    (ENTRAK_WATER, 'En-Trak Water'),
    (ENTRAK_PAPER, 'En-Trak Paper'),
    (ENTRAK_LIGHTING, 'En-trak Smart Lighting'),
)

class ProductKey(models.Model):

    key = models.CharField(max_length=32, unique=True)
    type = models.PositiveIntegerField(choices=PRODUCT_TYPES)
    remark = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    activated_at = models.DateTimeField(blank=True, null=True)
    activated_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='+')

    class Meta:
        ordering = ['-created_by']
