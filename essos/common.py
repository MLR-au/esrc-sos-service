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
from connectors import MongoDBConnection as mdb

from config import AppsConfig

def set_cookie(request, token):
    request.response.set_cookie('EAT', str(token),
        domain=request.registry.app_config['general']['cookie.domain'], path='/',
        secure=ast.literal_eval(request.registry.app_config['general']['cookie.secure']))

def delete_cookie(request):
    request.response.delete_cookie('EAT', path='/', domain=request.registry.app_config['general']['cookie.domain'])

def move_the_user_on(request, r, token):
    # send the user on: either back to where they came
    #  from (if r is not None) or on to their profile page
    set_cookie(request, token)

    if r is not None and validate_app_redirect(request, r):
        raise HTTPFound("%s" % r, headers=request.response.headers)
    else:
        raise HTTPFound('/profile', headers=request.response.headers)

def validate_app_redirect(request, r):
    authed_app = False
    if r is not None:
        apps = get_app_data(request)
    
        for app in apps:
            if compare(r, app.url):
                authed_app = True

    return authed_app

def get_app_data(request):
    app_configs = os.path.join(os.path.dirname(request.registry.settings['app.config']), request.registry.app_config['general']['apps'])
    apps = []
    for f in os.listdir(app_configs):
        c = AppsConfig(os.path.join(app_configs, f))
        d = c.load()
        apps.append(d)
    return apps


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
    log.debug("%s: Method: check_user_known" % request.client_addr)
    # is there a token in the request?
    token = request.cookies.get('EAT')
    if token is None:
        log.debug("%s: No existing token found" % request.client_addr)
        return False

    # is the token still valid?
    db = mdb(request)
    user = db.session.find_one(token=token)
    if user is not None:
        return user
    else:
        return False

def lockout_ip(request):
    db = mdb(request)
    doc = db.lockout.find_one( { 'ip': request.client_addr })
    if doc is not None:
        pass
    else:
        db.lockout.insert({
            'ip':  request.client_addr,
            'attempts': [ datetime.utcnow() ]
        })
    
    
