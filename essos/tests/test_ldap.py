import unittest
import paste.deploy

from pyramid import testing
import sys
import os
import os.path

from config import Config
from auth import LDAP
import ldap

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class LDAPTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        conf = Config(settings['app.config'])

        servers = conf.app_config['ldap']['servers']
        base = conf.app_config['ldap']['base']
        binduser = conf.app_config['ldap']['binduser']
        bindpass = conf.app_config['ldap']['bindpass']

        self.ldap = LDAP(servers, base, binduser, bindpass)

    def tearDown(self):
        testing.tearDown()

    def test_ldap_init(self):
        self.assertIsInstance(self.ldap.conn, ldap.ldapobject.SimpleLDAPObject)

    def test_ldap_authenticate(self):
        # check user known and pass correct
        user = 'u1'
        passwd = 'p1'
        self.assertTrue(self.ldap.authenticate(user, passwd))

        # check good user, bad pass
        user = 'u1'
        passwd = 'no'
        self.assertFalse(self.ldap.authenticate(user, passwd))

        # check bad user, good pass
        user = 'unkown'
        passwd = 'p1'
        self.assertFalse(self.ldap.authenticate(user, passwd))

    def test_ldap_get_user_data(self):
        user = 'u1'
        fullname = 'test user'
        passwd = 'p1'
        result = self.ldap.authenticate(user, passwd)

        user_data = self.ldap.get_user_data()
        self.assertEqual(user_data.username, user)
        self.assertEqual(user_data.fullname, fullname)

