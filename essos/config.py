
import os
import os.path
import ConfigParser

from pyramid.httpexceptions import HTTPBadRequest

class Config:

    def __init__(self, request):
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
        self.cfg.read(request.registry.settings['app.config'])

        self.app_config = {
            'general': {
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
                'nodes': self.get('CASSANDRA', 'nodes', True)
            }
        }


    def get(self, section, param, aslist=False):
        data = self.cfg.get(section, param) if (self.cfg.has_section(section) and self.cfg.has_option(section, param)) else None
        if aslist:
            return data.split(',')
        return data
