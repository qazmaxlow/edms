from django.db import models

class Contact(models.Model):
    system = models.ForeignKey('system.System')
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=254)
    mobile = models.CharField(max_length=30, blank=True)

    def __unicode__(self):
        return "%s, %s, %s"%(self.name, self.email, self.mobile)