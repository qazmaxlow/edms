from django.db import models
from django.utils.encoding import python_2_unicode_compatible


KWH_CATEGORY_CODE = 'kwh'
CO2_CATEGORY_CODE = 'co2'
MONEY_CATEGORY_CODE = 'money'


class ElectricUnitManager(models.Manager):
    def get_queryset(self):
        return super(ElectricUnitManager, self).get_queryset().filter(unit_type__code='electric')


@python_2_unicode_compatible
class UnitType(models.Model):
    code = models.SlugField(max_length=30)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class UnitCategory(models.Model):
    code = models.CharField(max_length=200)
    name = models.CharField(max_length=300)
    name_tc = models.CharField(max_length=300, blank=True)
    short_desc = models.CharField(max_length=200)
    short_desc_tc = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    img_off = models.CharField(max_length=200)
    img_on = models.CharField(max_length=200)
    bg_img = models.CharField(max_length=200)
    is_suffix = models.BooleanField(default=True)
    global_rate = models.FloatField(default=1)
    has_detail_rate = models.BooleanField(default=False)
    city = models.CharField(max_length=200)
    unit_type = models.ManyToManyField(UnitType, related_name="unit_types")

    objects = models.Manager()
    electric_units = ElectricUnitManager()


class UnitRate(models.Model):
    category_code = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    rate = models.FloatField(default=1)
    effective_date = models.DateTimeField()
