from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden
)

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
    expire = datetime.utcnow() + timedelta(session_lifetime)
    orm = ORM(session)
    orm.insert('session_by_token',
        fields = [ 'token', 'expire', 'username', 'fullname', 'is_admin' ], 
        data = [uuid.uuid4(), expire, user_data[0], user_data[1], isAdmin],
        ttl = session_lifetime
    )

    # send the user on: either back to where they came
    #  from (if r is not not None) or on to their profile page
    if r:
        raise HTTPFound(r)
    else:
        raise HTTPFound('/profile')





