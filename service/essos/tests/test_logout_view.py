import unittest
import paste.deploy
import collections

from pyramid import testing
from views import logout
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    HTTPUnauthorized
)

import sys
import os
import os.path
from config import Config

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class HomeViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

    def tearDown(self):
        testing.tearDown()

    def test_logout(self):
        with self.assertRaises(HTTPUnauthorized):
            l = logout(self.request)

        
