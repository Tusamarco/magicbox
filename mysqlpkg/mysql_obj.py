# object module defining all mysql related class
#import mysqlsh
import time
import sys
import importlib

from typing import Dict
#from mysqlsh import mysql
#shell = mysqlsh.globals.shell

class Mysql_Node:
    """
    Mysql_Node class
    
    Mysql_Node class, represent a MySQL node and it implements the methods to manage it
    
    Args: 
        requires a valid URI to connect to the MySQL node
        Valid URI form: <user>:[<password>]@<ip>:[<port>]
    
    Returns: One MySQL Node initialized 

    """
    """
    TODO
    I really think that pw should net be here but at moment I have no better idea than this or raise the ask at each connection
    which may prevent the auto reconnect and cluster discovery
    """
    def __init__(self,uri=False):
        self.user = None
        self.password:str = None
        self.ip = None
        self.port = None
        self.version = None
        self.use_ssl = 0
        self.uri = uri
        self.session = None
        self.processed    = False
        self.read_only     = False
        self.status:Dict[str,str]
        self.variables:Dict[str,str]
        
        # Comment           string
        # Compression       int
        # Connection        *sql.DB
        # self.conn_used     = 0
        # self.dns:str       = ""
        # self.HostgroupId  = 0
        self.hostgroups   = [] #Hostgroup
        # self.ip:str           = ""
        # MaxConnection     int
        # MaxLatency        int
        # MaxReplicationLag int
        # Name              string
        # NodeTCPDown       bool
        # Password          string
        # self.port         = 0
        # self.processed    = False
        # ProcessStatus     int
        # ProxyStatus       string
        # self.read_only     = False
        # Ssl               *SslCertificates
        # self.status       = Dict[str,str]
        # UseSsl            bool
        # User              string
        # self.variables    = Dict[str,str]
        # Weight            int
        # PingTimeout       int

        # //pxc
        # self.pxcMaintMode   = str
        # self.wsrep_connected = False
        # self.wsrep_desinccount = 0
        # self.wsrep_donor_rejectqueries = False
        # self.wsrep_gcommUuid   = str
        # self.wsrep_local_index  = 0
        # self.wsrep_pc_weight    = 0
        # self.wsrep_provider    = Dict[str,str]
        # self.wsrep_ready       = False
        # self.wsrep_reject_queries  =False
        # self.wsrep_local_recv_queue = 0
        # self.wsrep_segment        = 0
        # self.wsrep_status         = 0
        # self.wsrep_cluster_size    = 0
        # self.wsrep_cluster_name    = str
        # self.wsrep_cluster_status  = str
        # self.wsrep_node_name       = str
        # self.has_primary_state     = False
        # PxcView                 PxcClusterView

        
        import common.dbtools as dbtools
        
        importlib.reload(dbtools)
        
        my_connection =  dbtools.get_mysql_classic_connection(uri)
        # self.session = dbtools.get_mysql_classic_connection(uri)
        self.session = my_connection.connection_my
        self.ip =  my_connection.ip_my
        self.port =  my_connection.port_my
        self.user = my_connection.user
        self.password = my_connection.password
        
        if self.session is not None:
            try:
                self.variables = dbtools.get_variables(self.session,"")
                self.status = dbtools.get_status(self.session,"")                

                print("Connected to data node %s (%s - %s) " % (self.variables["hostname"],self.variables["version"],self.variables["version_comment"]))
                '''
                 TODO
                 to find a common way to close the connection to the db at the end of the operation
                '''
                # close_conn = dbtools.close_mysql_python_connection(self.session)
                
                
            except:
                sys.tracebacklimit = 0
                raise Exception("Not possible to connect to data Node!")

    def get_variable_value(self,key:str):
        """
        return  the value of a variables variable

        Args:
            key (str): variables variable key 
        
        Raises:
            KeyNot found execption 
            Dict not initialized     
        
        Returns:
            Value string  
        """
        
        if self.variables is None:
            raise Exception("Variables dictionary not initialized")
        elif not self.variables:
            raise Exception("Variables dictionary initialized but empty")
        elif self.variables[key] is None:
            raise KeyError("Wrong Key name or wrong resource parsed key: " + key)

        return self.variables[key]    
    
    def get_status_value(self,key:str):
        """
        return  the value of a status variable

        Args:
            key (str): status variable key 
        
        Raises:
            KeyNot found execption 
            Dict not initialized     
        
        Returns:
            Value string 
        """
        
        if self.status is None:
            raise Exception("Status dictionary not initialized")
        elif not self.status:
            raise Exception("Status dictionary initialized but empty")
        elif self.status[key] is None:
            raise KeyError("Wrong Key name or wrong resource parsed key: " + key)

        return self.status[key]    