from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden
)
from pyramid.response import Response
import ast

import auth
import time
import uuid
import os
import os.path
from datetime import datetime, timedelta, date
from urlparse import urlparse

import logging
log = logging.getLogger()

from models import CSession, ORM
from config import AppsConfig

@view_config(route_name="health_check", request_method="GET", renderer="string")
def health_check(request):
    t1 = time.time()

    # can we connect to an LDAP server
    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    if ldap.conn is None:
        raise HTTPInternalServerError

    # do we have a working connection to cassandra
    session = CSession(request)

    # add a trace into the health_check table
    orm = ORM(session)
    t2 = time.time() - t1
    orm.insert('health_check',
        [ 'date', 'timestamp', 'request_time'], 
        [ str(date.today()), datetime.utcnow(), t2 ]
    )

    return 'OK'

@view_config(route_name='home', request_method="GET", renderer='templates/home.mak')
def home(request):
    r = ''
    if request.GET.has_key('r'):
        r = request.GET['r']
        if not _validate_app_redirect(request, r):
            raise HTTPFound('/')

    e = False
    if request.GET.has_key('e'):
        e = True

    check = _check_user_known(request)
    if check:
        # send the user on
        _move_the_user_on(request, r, check)

    try:
        # if REMOTE_ADDR is not set in the environment then we have to wonder what the
        #  hell is going in. So - if we get an exception here, then the except clause
        #  is to raise a forbidden error.
        log.info("Login redirect from: '%s', remote address: %s" % (r, request.environ['REMOTE_ADDR']))
        return { 'r': r, 'e': e }
    except:
        raise HTTPForbidden

@view_config(route_name='login_staff', request_method="POST", renderer='json')
def login_staff(request):

    check = _check_user_known(request)
    if not request.POST.get('username') and not request.POST.get('pasword') and not check:
        raise HTTPFound('/')

    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = ldap.authenticate(request.POST['username'], request.POST['password'])

    r = request.POST.get('r')
    if r is not None:
        if not _validate_app_redirect(request, r):
            raise HTTPFound('/')

    # if not result means they didn't auth successfully so send
    #  them back to the start (to try again) with a marker (e=True)
    #  to flag that something is wrong.
    if not result and r:
        raise HTTPFound("/?r=%s&e=True")
    elif not result:
        raise HTTPFound('/?e=True')

    # if we get to here then the user has auth'ed successfully
    session = CSession(request)

    # get their data, determine if they're an admin
    user_data = ldap.get_user_data()
    is_admin = False
    for g in request.registry.app_config['general']['admins']:
        if g in user_data[2]:
            is_admin = True

    # if they already have a session, re use that token
    orm = ORM(session)
    data = orm.query('session_by_name',
        where = [ "\"username\" = '%s'" % user_data.username ]
    )
    if data:
        # there's already a session going - use that token
        data = orm.query('session_by_token',
            where = [ "\"token\" = %s" % data[0].token]
        )

    else:
        # no current session so create a token for them
        session_lifetime = int(request.registry.app_config['general']['session.lifetime'])
        expire = datetime.utcnow() + timedelta(session_lifetime)
        token = uuid.uuid4()
        code = uuid.uuid4()

        orm.insert('session_by_token',
            fields = [ 'token', 'code', 'expire', 'username', 'fullname', 'is_admin', ], 
            data = [ token, code, expire, user_data[0], user_data[1], is_admin ],
            ttl = session_lifetime
        )

        orm.insert('session_by_name',
            fields = [ 'token', 'username' ],
            data = [ token, user_data[0] ],
            ttl = session_lifetime
        )

        orm.insert('session_by_code',
            fields = [ 'code', 'token' ],
            data = [ code, token ],
            ttl = session_lifetime
        )

        # we get the data back from cassandra and use that - think
        #  of it as sort of health check
        data = orm.query('session_by_token',
            where = [ "\"token\" = %s" % token]
        )

    # send the user on
    _move_the_user_on(request, r, data[0])

@view_config(route_name="logout", request_method="GET")
def logout(request):
    check = _check_user_known(request)
    if check:
        # ditch the server side token
        session = CSession(request)
        orm = ORM(session)
        orm.delete('session_by_token',
            where = [ "\"token\" = %s" % check.token ])
        orm.delete('session_by_name',
            where = [ "\"username\" = '%s'" % check.username ])

    raise HTTPFound('/')

@view_config(route_name="retrieve_token", request_method="GET", renderer='json')
def retrieve_token(request):
    code = request.matchdict.get('code')
    session = CSession(request)
    orm = ORM(session)
    data = orm.query('session_by_code',
        where = [ "\"code\" = %s" % code ]
    )
    if data:
        orm.delete('session_by_code',
            where = [ "\"code\" = %s" % code ]
        )
        return { 'token': str(data[0].token) }
    return { 'token': '' }

@view_config(route_name="validate_token", request_method="POST", renderer='json')
def validate_token(request):
    token = request.matchdict.get('token')
    session = CSession(request)
    orm = ORM(session)
    data = orm.query('session_by_token',
        where = [ "\"token\" = %s" % token ]
    )
    if data:
        data = data[0]
        return { 'session': 'active', 'username': data.username, 'fullname': data.fullname, 'is_admin': data.is_admin }
    return { 'session': 'expired', 'username': '', 'fullname': '', 'is_admin': False }

def _move_the_user_on(request, r, data):
    # send the user on: either back to where they came
    #  from (if r is not None) or on to their profile page
    if r:
        raise HTTPFound("%s?code=%s" % (r, data.code))
    else:
        request.response.set_cookie('EAT', str(data.token),
            domain=request.registry.app_config['general']['cookie.domain'], path='/',
            secure=ast.literal_eval(request.registry.app_config['general']['cookie.secure']), httponly=True)
        if data.is_admin:
            raise HTTPFound("%s?code=%s" % (request.registry.app_config['general']['admin.app'], data.code), headers=request.response.headers)
        else:
            raise HTTPFound('/profile', headers=request.response.headers)

def _validate_app_redirect(request, r):
    app_configs = os.path.join(os.path.dirname(request.registry.settings['app.config']), request.registry.app_config['general']['apps'])
    apps = {}
    for f in os.listdir(app_configs):
        c = AppsConfig(os.path.join(app_configs, f))
        d = c.load()
        apps[d.name] = d.url
 
    authed_app = False
    for k, v in apps.items():
        if r.find(v) != -1:
            authed_app = True

    return authed_app

def _check_user_known(request):
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
