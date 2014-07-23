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
from datetime import datetime, timedelta, date

import logging
log = logging.getLogger()

from models import CSession, ORM

@view_config(route_name="health_check", renderer="string")
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

@view_config(route_name='home', renderer='templates/home.mak')
def home(request):
    # is a user with a valid session trying to log in?
    check = _check_user_known(request)
    if check:
        if check.is_admin:
            raise HTTPFound('/admin')
        else:
            raise HTTPFound('/profile')

    r = ''
    if request.GET.has_key('r'):
        r = request.GET['r']

    e = False
    if request.GET.has_key('e'):
        e = True

    try:
        # if REMOTE_ADDR is not set in the environment then we have to wonder what the
        #  hell is going in. So - if we get an exception here, then the except clause
        #  is to raise a forbidden error.
        log.info("Login redirect from: '%s', remote address: %s" % (r, request.environ['REMOTE_ADDR']))
        return { 'r': r, 'e': e }
    except:
        raise HTTPForbidden

@view_config(route_name='login_staff', renderer='json')
def login_staff(request):
    check = _check_user_known(request)
    if check:
        if check.is_admin:
            raise HTTPFound('/admin')
        else:
            raise HTTPFound('/profile')
    else:
        if not request.POST.get('username') and not request.POST.get('pasword'):
            raise HTTPFound('/')

    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = ldap.authenticate(request.POST['username'], request.POST['password'])
    try:
        r = request.GET['r']
    except KeyError:
        r = None

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
    isAdmin = False
    for g in request.registry.app_config['general']['admins']:
        if g in user_data[2]:
            isAdmin = True

    # and create a session for them
    session_lifetime = int(request.registry.app_config['general']['session_lifetime'])
    cookie_secure = ast.literal_eval(request.registry.app_config['general']['cookie.secure'])
    expire = datetime.utcnow() + timedelta(session_lifetime)
    token = uuid.uuid4()
    domain = request.registry.app_config['general']['cookie.domain']
    path = '/'
    if r:
        domain = r

    orm = ORM(session)
    orm.insert('session_by_token',
        fields = [ 'token', 'expire', 'username', 'fullname', 'is_admin', 'domain', 'path' ], 
        data = [token, expire, user_data[0], user_data[1], isAdmin, domain, path],
        ttl = session_lifetime
    )

    orm.insert('session_by_name',
        fields = [ 'token', 'username' ],
        data = [ token, user_data[0] ],
        ttl = session_lifetime
    )
    # set the cookie
    request.response.set_cookie('EAT', str(token), 
        domain=domain, path=path, 
        secure=cookie_secure, httponly=True)

    # send the user on: either back to where they came
    #  from (if r is not None) or on to their profile page
    if r:
        raise HTTPFound(r, headers=request.response.headers)
    else:
        if isAdmin:
            raise HTTPFound("/admin", headers=request.response.headers)
        else:
            raise HTTPFound('/profile', headers=request.response.headers)

@view_config(route_name="admin", renderer='templates/admin.mak')
def admin(request):
    check = _check_user_known(request)
    if check:
        if not check.is_admin:
            raise HTTPFound('/profile')
    else:
        raise HTTPFound('/')

    return {}

@view_config(route_name="logout")
def logout(request):
    check = _check_user_known(request)
    if not check:
        log.debug('not logged in')
        raise HTTPFound('/')
    else:
        session = CSession(request)
        orm = ORM(session)
        orm.delete('session_by_token',
            where = [ "\"token\" = %s" % check.token ])
        request.response.delete_cookie('EAT', path=check.path, domain=check.domain)

    raise HTTPFound('/', headers=request.response.headers)

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



