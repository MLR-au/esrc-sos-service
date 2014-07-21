# we assume the keyspace for our app has been created by puppet
import cassandra
import sys

import logging
log = logging.getLogger('essos')

def CSession(request):
    return request.registry.app_config['cassandra']['session']

class Models:
    def __init__(self, session):
        self.session = session
        self.create_session_table()
        self.create_user_profile_table()
        self.create_health_check_table()
        self.create_logging()

    def create(self, table_def):
        try:
            self.session.execute(table_def)
        except cassandra.AlreadyExists:
            pass
        except cassandra.InvalidRequest:
            if str(sys.exc_info()[1]) == 'code=2200 [Invalid query] message="Index already exists"':
                pass
            else:
                print sys.exc_info()
            

    def create_session_table(self):
        table_def = """
        CREATE TABLE essos.session (
            id          uuid PRIMARY KEY,
            expiration  timestamp,
            username    text,
            fullname    text,
            is_admin    boolean 
        );
        """
        self.create(table_def)

    def create_user_profile_table(self):
        table_def = """
        CREATE TABLE essos.profile (
            id              uuid PRIMARY KEY,
            fullname        text, 
            primary_email   text,
            username        set<text>
        );
        """
        self.create(table_def)

    def create_health_check_table(self):
        table_def = """
        CREATE TABLE essos.health_check (
            id              uuid PRIMARY KEY,
            timestamp       timestamp,
            request_time    float 
        );
        """
        self.create(table_def)

    def create_logging(self):
        table_def = """
        CREATE TABLE essos.logging (
            id              uuid PRIMARY KEY,
            timestamp       timestamp,
            source          text,
            message         text
        );
        """
        self.create(table_def)

        index_def = """
        CREATE INDEX logging_source ON essos.logging (source);
        """
        self.create(index_def)


class ORM:
    def __init__(self, session, keyspace, table):
        self.session = session
        self.keyspace = keyspace 
        self.table = table

    def insert(self, fields, data):
        log.debug('ORM::insert')

        # rudimentary error checking
        if type(fields) != list or type(data) != list:
            log.error('ORM::insert: fields and data params must be of type list')
        if len(fields) != len(data):
            log.error('ORM::insert: ensure the number of elements in data is the same as the number in fields')

        # create the placeholder array
        p = [ '?' for f in range(0, len(fields)) ]

        # concatenate the fields array
        fields = ', '.join(fields)
        log.debug("ORM::insert: %s into: %s" % (fields, self.table))

        # create the prepared statement
        statement = "INSERT INTO %s.%s (%s) VALUES (%s);" % (self.keyspace, self.table, fields, ', '.join(p))
        log.debug("ORM::insert: prepared statement: %s" % statement)
        prepared_statement = self.session.prepare(statement)

        # execute the statement
        self.session.execute(prepared_statement, data)

        pass
    def update(self, field, value, where):
        pass
    def query(self, fields, where):

        pass

