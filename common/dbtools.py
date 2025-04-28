"""_summary_
    Set of functionalities that allow to connect to a data base 
    Also some most commonly used operations
    test
"""

import mysqlsh
import time
import sys

from mysqlsh import mysql
shell = mysqlsh.globals.shell
import mysql.connector as mysql_connector 
from mysql.connector.constants import ClientFlag
# from mysql.connector.connection_cext import CMySQLConnection
from mysql.connector.aio.abstracts import MySQLConnectionAbstract

'''
Returns a mysql shell classic session
https://dev.mysql.com/doc/dev/mysqlsh-api-javascript/8.4/classmysqlsh_1_1mysql_1_1_classic_session.html 

Require a well form uri to connect "user:[pass]@host:port" 
If Password is not in it will ask it interactively 
'''
def get_mysql_shell_session(uri):
    
        user = None
        ip = None
        port = None
        version = None
        use_ssl = 0
        uri = uri
        
        if uri == "":
            raise Exception("Invalid uri to parse")
        
        user = shell.parse_uri(uri)['user']
        ip = shell.parse_uri(uri)['host']
        port = shell.parse_uri(uri)['port']
        if not "password" in shell.parse_uri(uri):
            __password = shell.prompt('Password: ',{'type': 'password'})
        else:
            __password = shell.parse_uri(uri)['password']
        try:
            session = mysql.get_classic_session("%s:%s@%s:%s?ssl-mode=PREFERRED" % (user, __password, ip, port))
            return session
        except:
            sys.tracebacklimit = 3
            raise Exception("Not possible to connect to data Node!")
'''
Returns a standard Python connection object 

Require a well form uri to connect "user:[pass]@host:port" 
If Password is not in it will ask it interactively 
'''
def get_mysql_classic_connection(uri):
        user = None
        ip = None
        port = None
        version = None
        use_ssl = 0
        uri = uri
        
        if uri == "":
            raise Exception("Invalid uri to parse")
        
        user = shell.parse_uri(uri)['user']
        ip = shell.parse_uri(uri)['host']
        port = shell.parse_uri(uri)['port']
        if not "password" in shell.parse_uri(uri):
            __password = shell.prompt('Password: ',{'type': 'password'})
        else:
            __password = shell.parse_uri(uri)['password']
        try:
            config = {
                'user': user,
                'password': __password,
                'host': ip,
                'port': port,
                'database': 'mysql',
                'raise_on_warnings': True,
                'connection_timeout': 10, 
                'client_flags': [ClientFlag.SECURE_CONNECTION],
                # 'conn_attrs':{"ssl-mode":"PREFERRED"},
                }
            connection = mysql_connector.connect(**config)

            # mysql.get_classic_session("%s:%s@%s:%s?ssl-mode=PREFERRED" % (user, __password, ip, port))
            return connection
        except:
            sys.tracebacklimit = 3
            raise Exception("Not possible to connect to data Node!")
        
'''
Accept a classic python connection and close it
If connection is still open

raise connection execption 

Returns True only if it can close the connection. 
False in any other case.
'''
def close_mysql_python_connection(connection):
    if hasattr(connection,"close"):
        try:
            if connection.is_connected():
                connection.close()
                return True
            else:
                return False
        except:
            sys.tracebacklimit = 3
            raise Exception("Error while closing connection!")
            return False

'''
This function returns a dictionary compose by <Variable name>:<Variable value>
Accept connection object as incoming parameter and a filter value that must follow the valid MySQL syntax for SHOW

Raise an exception in case of error and returns None.
'''
def get_variables(connection,filter):
    sql = "Show global variables"
    try:
        if connection.is_connected():
            variables = dict[str,str]
            cursor = connection.cursor(dictionary=False)
            if filter != "":
                sql = sql + " " + " like '{}'".format(filter)
                print(sql)
            cursor.execute(sql)
            rows = cursor.fetchall()
            variables = {str(row[0]): str(row[1]) for row in rows}
            return variables
        else:
            return None
    
    except:
        sys.tracebacklimit = 3
        raise Exception("Error while getting values!")
        return None
        
'''
This function returns a dictionary compose by <Variable name>:<Status value>
Accept connection object as incoming parameter and a filter value that must follow the valid MySQL syntax for SHOW

Raise an exception in case of error and returns None.
'''
def get_status(connection,filter):
    sql = "Show global status"
    try:
        if connection.is_connected():
            variables = dict[str,str]
            cursor = connection.cursor(dictionary=False)
            if filter != "":
                sql = sql + " " + " like '{}'".format(filter)
                print(sql)
            cursor.execute(sql)
            rows = cursor.fetchall()
            variables = {str(row[0]): str(row[1]) for row in rows}
            return variables
        else:
            return None
    
    except:
        sys.tracebacklimit = 3
        raise Exception("Error while getting values!")
        return None
        