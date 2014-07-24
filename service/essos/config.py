
import os
import sys
import os.path
import ConfigParser
import collections

from pyramid.httpexceptions import HTTPBadRequest

import logging
log = logging.getLogger('essos')


class ConfigBase:
    def __init__(self):
        pass

    def get(self, section, param, aslist=False):
        data = self.cfg.get(section, param) if (self.cfg.has_section(section) and self.cfg.has_option(section, param)) else None
        if aslist:
            return [ d.strip() for d in data.split(',') ]
        return data

class Config(ConfigBase):

    def __init__(self, conf):
        """
        Expects to be called with a pyramid request object.

        The path to the configs will be extracted from the pyramid
        configuration and a config object will be returned.

        The params from the config will be available as instance
        variables.

        @params:
        request: a pyramid request object
        """
        self.cfg = ConfigParser.SafeConfigParser()
        try:
            self.cfg.read(conf)
        except ConfigParser.ParsingError:
            log.error('Config file parsing errors')
            log.error(sys.exc_info()[1])
            sys.exit()

        self.app_config = {
            'general': {
                'admins': self.get('General', 'admins', aslist=True),
                'admin.app': self.get('General', 'admin.app'),
                'apps': self.get('General', 'apps'),
                'session.lifetime': self.get('General', 'session.lifetime'),
            },
            'ldap': {
                'servers': self.get('LDAP', 'ldap.servers', aslist=True),
                'base': self.get('LDAP', 'search.base'),
                'binduser': self.get('LDAP', 'bind.user'),
                'bindpass': self.get('LDAP', 'bind.pass')
            },
            'cassandra': {
                'user': self.get('CASSANDRA', 'user'),
                'pass': self.get('CASSANDRA', 'pass'),
                'nodes': self.get('CASSANDRA', 'nodes', aslist=True),
                'keyspace': self.get('CASSANDRA', 'keyspace')
            }
        }

class AppsConfig(ConfigBase):
    def __init__(self, conf):
        self.cfg = ConfigParser.SafeConfigParser()
        try:
            self.cfg.read(conf)
        except ConfigParser.ParsingError:
            log.error('Config file parsing errors')
            log.error(sys.exc_info()[1])
            sys.exit()

    def load(self):
        conf = collections.namedtuple('appsconf', [ 'name', 'url' ])
        return conf(self.get('General', 'name'), self.get('General', 'url'))





