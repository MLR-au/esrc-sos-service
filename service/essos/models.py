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
        self.create_session_tables()
        #self.create_user_profile_table()
        self.create_health_check_table()
        #self.create_logging()

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
            
    def create_session_tables(self):
        table_def = """
        CREATE TABLE IF NOT EXISTS session_by_token (
            "token"     uuid PRIMARY KEY,
            "expire"    timestamp,
            "username"  text,
            "fullname"  text,
            "is_admin"  boolean,
        );
        """
        self.create(table_def)

        table_def = """
        CREATE TABLE IF NOT EXISTS session_by_name (
            "username"  text PRIMARY KEY,
            "token"     uuid
        );
        """
        self.create(table_def)

    def create_user_profile_table(self):
        table_def = """
        CREATE TABLE IF NOT EXISTS profile (
            id              uuid PRIMARY KEY,
            fullname        text, 
            primary_email   text,
            username        set<text>
        );
        """
        self.create(table_def)

    def create_health_check_table(self):
        table_def = """
        CREATE TABLE IF NOT EXISTS health_check (
            date            text,
            timestamp       timestamp,
            request_time    float,
            PRIMARY KEY (date, timestamp)
        )
        WITH CLUSTERING ORDER BY (timestamp DESC);
        """
        self.create(table_def)

    def create_logging(self):
        table_def = """
        CREATE TABLE IF NOT EXISTS logging (
            id              uuid,
            timestamp       timestamp,
            source          text,
            message         blob,
            PRIMARY KEY (id, timestamp)
        )
        WITH CLUSTERING ORDER BY (timestamp ASC);
        """
        self.create(table_def)

        index_def = """
        CREATE INDEX ON logging (source);
        """
        self.create(index_def)

class ORM:
    def __init__(self, session):
        self.session = session

    def _validate_list(self, field, name):
        if type(field) != list:
            raise TypeError("%s must be of type list" % name)

    def insert(self, table=[], fields=[], data=[], ttl=None):
        log.debug('ORM::insert')

        # rudimentary error checking
        self._validate_list(fields, 'fields')
        self._validate_list(data, 'data')
        if len(fields) != len(data):
            raise ValueError('fields and data arrays must be the same length')

        # create the placeholder array
        p = [ '?' for f in range(0, len(fields)) ]

        # concatenate the fields array
        fields = ', '.join([ '"%s"' % f for f in fields ])
        log.debug("ORM::insert: %s into: %s" % (fields, table))

        # create the prepared statement
        statement = "INSERT INTO %s (%s) VALUES (%s)" % (table, fields, ', '.join(p))
        if ttl is not None:
            statement += " USING TTL %s;" % ttl 
        else:
            statement += ';'
        log.debug("ORM::insert: prepared statement: %s" % statement)
        prepared_statement = self.session.prepare(statement)

        # execute the statement
        self.session.execute(prepared_statement, data)

        pass

    def update(self, field, value, where):
        pass

    def query(self, table='', fields=[], where=[]):
        log.debug('ORM::query')
        
        # rudimentary error checking
        self._validate_list(fields, 'fields')
        self._validate_list(where, 'where')

        # concatenate the fields array
        if len(fields) == 0:
            fields = '*'
        else:
            fields = ', '.join([ '"%s"' % f for f in fields ])
        log.debug("ORM::query: %s from: %s" % (fields, table))

        # create the prepared statement
        statement = "SELECT %s FROM %s" % (fields, table)
        if len(where) != 0:
            # concatenate the where clauses
            wheres = ' AND '.join(where)
            statement += " WHERE %s;" % wheres
        else:
            statement += ';'

        log.debug("ORM::query: prepared statement: %s" % statement)

        # execute the statement and return the result
        return self.session.execute(statement)

    def delete(self, table='', fields=[], where=[]):
        log.debug('ORM::delete')
        
        # rudimentary error checking
        self._validate_list(fields, 'fields')
        self._validate_list(where, 'where')

        # concatenate the fields array
        if len(fields) == 0:
            fields = ''
        else:
            fields = ', '.join([ '"%s"' % f for f in fields ])
        log.debug("ORM::delete: %s from: %s" % (fields, table))

        # create the prepared statement
        statement = "DELETE %s FROM %s" % (fields, table)
        if len(where) != 0:
            # concatenate the where clauses
            wheres = ' AND '.join(where)
            statement += " WHERE %s;" % wheres
        else:
            statement += ';'
        log.debug("ORM::delete: prepared statement: %s" % statement)

        # execute the statement and return the result
        return self.session.execute(statement)








