import unittest
import paste.deploy
import collections

from pyramid import testing
from views import home
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden
)

import sys
import os
import os.path

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class HomeViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):

        with self.assertRaises(HTTPForbidden):
            h = home(self.request)

        self.request.environ = {
            'REMOTE_ADDR': '192.168.190.23'
        }
        h = home(self.request)
        self.assertEqual(h['r'], '')

        self.request.GET = {
            'r': 'https://ohrm.esrc.info'
        }
        h = home(self.request)
        self.assertEqual(h['r'], 'https://ohrm.esrc.info')

        self.request.GET = {
            'e': True
        }
        h = home(self.request)
        self.assertEqual(h['e'], True)
        
