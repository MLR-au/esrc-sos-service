from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)
from pyramid.response import Response
import logging
log = logging.getLogger('essos')

import ast
import os
from urlparse import urlparse
from models import CSession, ORM

from config import AppsConfig

def move_the_user_on(request, r, data):
    # send the user on: either back to where they came
    #  from (if r is not None) or on to their profile page
    request.response.set_cookie('EAT', str(data.token),
        domain=request.registry.app_config['general']['cookie.domain'], path='/',
        secure=ast.literal_eval(request.registry.app_config['general']['cookie.secure']), httponly=True)

    if not data.is_admin:
        if r and compare(r, request.registry.app_config['general']['admin.app']):
            log.debug("Non admin user %s trying to access admin console via redirect param." % data.username )
            raise HTTPFound('/')

    if data.is_admin:
        raise HTTPFound("%s?s=%s" % (request.registry.app_config['general']['admin.app'], data.code), headers=request.response.headers)
    elif r and not compare(request.registry.app_config['general']['admin.app'], r):
        raise HTTPFound("%s?s=%s" % (r, data.code), headers=request.response.headers)
    else:
        raise HTTPFound('/profile', headers=request.response.headers)

def validate_app_redirect(request, r):
    authed_app = False
    if r is not None:
        if compare(r, request.registry.app_config['general']['admin.app']):
            authed_app = True
        else:
            app_configs = os.path.join(os.path.dirname(request.registry.settings['app.config']), request.registry.app_config['general']['apps'])
            apps = {}
            for f in os.listdir(app_configs):
                c = AppsConfig(os.path.join(app_configs, f))
                d = c.load()
                apps[d.name] = d.url
         
            for k, v in apps.items():
                if compare(r, v):
                    authed_app = True

    return authed_app

def compare(a, b):
    # expects a couple of urls - urlparse will be used to 
    #  split the components for comparison
    a = urlparse(a)
    b = urlparse(b)
    if a.scheme == b.scheme and a.netloc == b.netloc:
        return True
    else:
        return False

def check_user_known(request):
    # is there a token in the request?
    token = request.cookies.get('EAT')
    if token is None:
        return False

    # is the token still valid?
    session = CSession(request)
    orm = ORM(session)
    data = orm.query('session_by_token',
        where = [ "\"token\" = %s" % token ]
    )
    if not data:
        return False

    # if we get to here then the user is known
    #   so we return the data we have about them.
    return data[0]
