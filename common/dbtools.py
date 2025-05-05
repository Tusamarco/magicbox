"""_summary_
    Set of functionalities that allow to connect to a data base 
    Also some most commonly used operations
"""
try:
    import mysqlsh
    import sys
    from mysqlsh import mysql
    shell = mysqlsh.globals.shell
except: 
    pass

import time
from  dataclasses import dataclass
from common import utils_mb

@dataclass
class Mysql_connection:
        connection_my:None = None
        ip_my:str = ""
        port_my:int = 0


import mysql.connector as mysql_connector 
from mysql.connector.constants import ClientFlag
# from mysql.connector.connection_cext import CMySQLConnection
from mysql.connector.aio.abstracts import MySQLConnectionAbstract

def get_mysql_shell_session(uri):
    """_summary_
    Returns a mysql shell classic session
    https://dev.mysql.com/doc/dev/mysqlsh-api-javascript/8.4/classmysqlsh_1_1mysql_1_1_classic_session.html 

    Require a well form uri to connect "user:[pass]@host:port" 
    If Password is not in it will ask it interactively 

    Args:
        uri (string): requires a valid URI to connect to the MySQL node
                      Valid URI form: <user>:[<password>]@<ip>:[<port>]
    Raises:
        Exception: connection 
    Returns:
        session: mysqlsh session (https://dev.mysql.com/doc/dev/mysqlsh-api-javascript/8.4/classmysqlsh_1_1mysql_1_1_classic_session.html)
    """
    
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


def get_mysql_classic_connection(uri):
    """
    Returns a standard Python connection object 

    Require a well form uri to connect "user:[pass]@host:port" 
    If Password is not in it will ask it interactively 

    Args:
        uri (string): requires a valid URI to connect to the MySQL node
                      Valid URI form: <user>:[<password>]@<ip>:[<port>]
    Raises:
        Exception: connection 

    Returns:
        mysql_connection object;
            connection: return a connection from connector object as for (https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysql-connector.html)
            ip: string with the information about the ip
            port: port
    """
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
    
    check = utils_mb.validate_and_check_connection(ip,5)
    if not check["valid"]:
        sys.tracebacklimit = 0
        raise Exception("Invalid Host " + ip + ". Invalid IP or hostname.\nHostname or IP do not resolve" )
        return None
    
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
            'connection_timeout': 0, 
            'client_flags': [ClientFlag.SECURE_CONNECTION],
            # 'conn_attrs':{"ssl-mode":"PREFERRED"},
            }
        connection = mysql_connector.connect(**config)

        # mysql.get_classic_session("%s:%s@%s:%s?ssl-mode=PREFERRED" % (user, __password, ip, port))
        # return connection
        con_obj = Mysql_connection(connection_my=connection,ip_my=ip,port_my=port)
        return con_obj
    except:
        sys.tracebacklimit = 3
        raise Exception("Not possible to connect to data Node!")
        

def close_mysql_python_connection(connection):
    """
    Accept a classic python connection and close it
    If connection is still open

    Args:
        connection (connection): mysql connection (https://github.com/mysql/mysql-connector-python/blob/5e47983957b0ba833b9428dd542bbecba8898347/mysql-connector-python/lib/mysql/connector/connection.py)

    Raises:
        Exception: raise connection execption 

    Returns:
        Boolean: Returns True only if it can close the connection. 
                 False in any other case.

    """
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

def get_variables(connection,filter):
    """
    This function returns a dictionary compose by <Variable name>:<Variable value>
    Accept connection object as incoming parameter and a filter value that must follow the valid MySQL syntax for SHOW

    Raise an exception in case of error and returns None.


    Args:
        connection (connection): MySQL connection Accept connection object as incoming parameter
        filter (string): a filter value that must follow the valid MySQL syntax for SHOW

    Raises:
        Exception: _description_

    Returns:
        dict[string,string]: dictionary compose by <Variable name>:<Variable value>
    """
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
        

def get_status(connection,filter):
    """
    This function returns a dictionary compose by <Variable name>:<Status value>
    Accept connection object as incoming parameter and a filter value that must follow the valid MySQL syntax for SHOW

    Raise an exception in case of error and returns None.


    Args:
        connection (connection): MySQL connection Accept connection object as incoming parameter
        filter (string): a filter value that must follow the valid MySQL syntax for SHOW

    Raises:
        Exception: _description_

    Returns:
        dict[string,string]: dictionary compose by <Variable name>:<Status value>
    """

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
        