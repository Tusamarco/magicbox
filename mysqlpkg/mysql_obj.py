# object module defining all mysql related class
#import mysqlsh
import time
import sys
import importlib

from typing import Dict
#from mysqlsh import mysql
#shell = mysqlsh.globals.shell

from typing import Dict

class Mysql_Node:
    """
    Mysql_Node class
    
    Mysql_Node class, represent a MySQL node and it implements the methods to manage it
    
    Args: 
        requires a valid URI to connect to the MySQL node
        Valid URI form: <user>:[<password>]@<ip>:[<port>]
    
    Returns: One MySQL Node initialized 

    """
    def __init__(self,uri=False):
        self.user = None
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
        
        self.session = dbtools.get_mysql_classic_connection(uri)
        if self.session is not None:
            try:
                self.variables = dbtools.get_variables(self.session,"")
                self.status = dbtools.get_status(self.session,"")                

                print("Connected to data node %s (%s - %s) " % (self.variables["hostname"],self.variables["version"],self.variables["version_comment"]))
                close_conn = dbtools.close_mysql_python_connection(self.session)
                # print(close_conn)
                
            except:
                sys.tracebacklimit = 0
                raise Exception("Not possible to connect to data Node!")

  