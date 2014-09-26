
import os
import sys
import os.path
import ConfigParser
import collections
import traceback
import ast

from pyramid.httpexceptions import HTTPBadRequest

import logging
log = logging.getLogger(__name__)


class ConfigBase:
    def __init__(self):
        pass

    def get(self, section, param, aslist=False):
        data = self.cfg.get(section, param) if (self.cfg.has_section(section) and self.cfg.has_option(section, param)) else None
        if data == None:
            log.error("Missing parameter %s in section %s" % (param, section))
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
                'session.lifetime': self.get('General', 'session.lifetime'),
                'apps': self.get('General', 'apps'),
                'jwt.pub': self.get('General', 'jwt.pub'),
                'jwt.priv': self.get('General', 'jwt.priv'),
                'lockout.time': self.get('General', 'lockout.time')
            },
            'ldap': {
                'servers': self.get('LDAP', 'ldap.servers', aslist=True),
                'base': self.get('LDAP', 'search.base'),
                'binduser': self.get('LDAP', 'bind.user'),
                'bindpass': self.get('LDAP', 'bind.pass')
            },
            'mongodb': {
                'nodes': self.get('MONGODB', 'nodes', aslist=True),
                'user': self.get('MONGODB', 'user'),
                'pass': self.get('MONGODB', 'pass'),
                'db': self.get('MONGODB', 'db'),
                'replica_set': self.get('MONGODB', 'replica.set'),
                'write_concern': self.get('MONGODB', 'write.concern')
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
        conf = collections.namedtuple('appsconf', 
            [ 'name', 'url', 'description', 'login_callback', 'forbidden_callback', 'allow', 'deny_social', 'admins' ]
        )
        return conf(self.get('General', 'name'), 
                    self.get('General', 'url'), 
                    self.get('General', 'description'),
                    self.get('General', 'login_callback'),
                    self.get('General', 'forbidden_callback'),
                    self.get('General', 'allow', aslist=True),
                    ast.literal_eval(self.get('General', 'deny_social')),
                    self.get('General', 'admins', aslist=True)
                    )
