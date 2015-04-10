from PIL import Image
from StringIO import StringIO
import datetime

from django.core.files.base import ContentFile
from django.test import TestCase

from user.models import EntrakUser
from system.models import System


class AuthViewsTestCase(TestCase):

    def setUp(self):
        user = EntrakUser.objects.create_user('ettester01', 'et01@just.test', '00000')

        logo_file = StringIO()
        logo = Image.new('RGBA', size=(50,50), color=(256,0,0))
        logo.save(logo_file, 'png')
        logo_file.seek(0)

        dlogo_file = ContentFile(logo_file.read(), 'test.png')

        system = System.objects.create(code='ettestsys01',
                              name='ettestsys01',
                              logo=dlogo_file,
                              first_record=datetime.datetime.now()
        )

        user.system = system
        user.save()

    def test_login(self):
        response = self.client.post('/ettestsys01/login/', {
            'username': 'ettester01',
            'password': '00000',
        })

        self.assertRedirects(response, '/ettestsys01/graph/')
        return response
