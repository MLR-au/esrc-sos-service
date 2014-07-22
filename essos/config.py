
import os
import os.path
import ConfigParser

from pyramid.httpexceptions import HTTPBadRequest

class Config:

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
        self.cfg.read(conf)

        self.app_config = {
            'general': {
                'admins': self.get('General', 'admins', True),
                'session_lifetime': self.get('General', 'session_lifetime'),
            },
            'ldap': {
                'servers': self.get('LDAP', 'ldap_servers', True),
                'base': self.get('LDAP', 'search_base'),
                'binduser': self.get('LDAP', 'bind_user'),
                'bindpass': self.get('LDAP', 'bind_pass')
            },
            'cassandra': {
                'user': self.get('CASSANDRA', 'user'),
                'pass': self.get('CASSANDRA', 'pass'),
                'nodes': self.get('CASSANDRA', 'nodes', True),
                'keyspace': self.get('CASSANDRA', 'keyspace')
            }
        }


    def get(self, section, param, aslist=False):
        data = self.cfg.get(section, param) if (self.cfg.has_section(section) and self.cfg.has_option(section, param)) else None
        if aslist:
            return [ d.strip() for d in data.split(',') ]
        return data
