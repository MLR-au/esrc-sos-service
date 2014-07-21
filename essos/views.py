from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPInternalServerError
)

import auth
import time
import uuid
from datetime import datetime, timedelta

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
    resp = session.execute('SELECT * FROM essos.session;');

    # add a trace into the health_check table
    orm = ORM(session, 'essos', 'health_check')
    t2 = time.time() - t1
    orm.insert([ 'id', 'timestamp', 'request_time'], [ uuid.uuid4(), datetime.utcnow(), t2 ])

    return 'OK'

@view_config(route_name='home', renderer='templates/home.mak')
def home(request):
    r = ''
    if request.GET.has_key('r'):
        r = request.GET['r']

    e = False
    if request.GET.has_key('e'):
        e = request.GET['e']

    log.info("Login redirect from: '%s', remote address: %s" % (r, request.environ['REMOTE_ADDR']))
    return { 'r': r, 'e': e }

@view_config(route_name='login_staff', renderer='json')
def login_staff(request):
    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = ldap.authenticate(request.POST['username'], request.POST['password'])
    try:
        r = request.POST['r']
    except KeyError:
        r = None

    # if not result means they didn't auth successfully so send
    #  them back to the start (to try again) with a marker (e=True)
    #  noting that something is wrong.
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
    orm = ORM(session, 'essos', 'session')
    orm.insert(
        [ 'id', 'expiration', 'username', 'fullname', 'is_admin' ], 
        [uuid.uuid4(), (datetime.utcnow() + timedelta(minutes=session_lifetime)), user_data[0], user_data[1], isAdmin]
    )

    # send the user on: either back to where they came
    #  from (if r is not not None) or on their profile page
    if r:
        raise HTTPFound(r)
    else:
        raise HTTPFound('/profile')

    return {}




