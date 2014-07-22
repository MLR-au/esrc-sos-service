#
import ldap
import sys
import collections

import logging
log = logging.getLogger('essos')

class LDAP:
    def __init__(self, servers, base, binduser, bindpass):
        """Establish a connection to an LDAP server

        @params:
        - servers: array of servers to try; must be in the form
            [ ldap://ldap01.internal, ldap://ldap02.internal, ..]
        - base: the base of the LDAP system
        - binduser: DN of the user to bind as
        - bindpass: the bind users password

        @check
        - if self.conn == None then we haven't found a suitable, working
        server.
        """
        self.LDAP_TIMEOUT = 10
        self.servers = servers
        self.base = base
        self.binduser = binduser
        self.bindpass = bindpass
        self.conn = None

        for s in servers:
            log.debug("Trying ldap server: %s" % s)
            try:
                self.conn = ldap.initialize(s)
                self.conn.simple_bind_s(self.binduser, self.bindpass)
                log.debug("Server ok: %s" %s)
                break
            except ldap.SERVER_DOWN:
                # try the next one
                log.debug("Server down: %s" % s)
                self.conn = None
                pass

    def authenticate(self, username, password):
        """Authenticate the user

        How does this work?
        As we've bound ourselves to the LDAP server with the bind user we can 
        search for the user using the username provided. If we get a result, we use
        the DN that is returned along with the password to check that the user has
        authenticated correctly.

        @params:
        - username: the user's username, e.g. jim
        - password: the user's password, e.g. supersekrit

        @returns:
        - True: all is well, auth'ed successfully
        - False: not well: username not found or password wrong: don't care
        """
        data = []
        try:
            ldap_filter = '(&(objectClass=Person)(uid=' + username + '))'
            data = self.conn.search_st(self.base, ldap.SCOPE_SUBTREE, ldap_filter, [ ], 0, timeout=self.LDAP_TIMEOUT)
        except:
            print "**", sys.exc_info()

        if data != []:
            dn = data[0][0]
            self.data = data[0][1]
            try:
                self.conn.bind_s(dn, password)
            except ldap.INVALID_CREDENTIALS:
                # bad password
                log.info("Bad password for: %s" % username)
                return False
            else:
                # hooray - user found and correct pass provided
                self.groups = self.get_user_groups(username)
                log.info("User: %s authenticated successfully" % username)
                return True

        # no user by that name
        log.info("No such user: %s" % username)
        return False

    def get_user_data(self):
        user_data = collections.namedtuple('UserData', 'username, fullname, groups')
        return user_data(self.data['uid'][0], self.data['cn'][0], self.groups)

    def get_user_groups(self, username):
        self.conn.simple_bind_s(self.binduser, self.bindpass)
        data = []
        try:
            ldap_filter = '(&(objectClass=posixGroup)(memberUid=' + username + '))'
            data = self.conn.search_st(self.base, ldap.SCOPE_SUBTREE, ldap_filter, [ 'cn' ], 0, timeout=self.LDAP_TIMEOUT)
        except:
            print "**", sys.exc_info()

        groups = [ g[1]['cn'][0] for g in data ] 
        return groups
