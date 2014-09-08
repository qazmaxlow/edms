from django.db import models

class Contact(models.Model):
	name = models.CharField(max_length=200)
	email = models.EmailField(max_length=254)
	mobile = models.CharField(max_length=30)

	def __unicode__(self):
		return "%s, %s, %s"%(self.name, self.email, self.mobile)
