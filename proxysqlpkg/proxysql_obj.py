# object module defining all proxysql related class
import mysqlsh
from typing import Dict
from mysqlsh import mysql
import mysqlpkg.mysql_obj as mysql_obj

shell = mysqlsh.globals.shell


class ProxySQLCluster:
    """
    ProxySQL Cluster 
    """
    def __init__(self,uri=False):
        self.name = ""
        self.nodes = Dict[str, ProxySQL] = {}
        self.active = False
        self.user = ""
        self.password = ""
        
    
class ProxySQL:
    """
    ProxySQL Object.
    """
    def __init__(self,uri=False):
        self.actionNodeList = Dict[str,mysql_obj.DataNode] = {}
        self.dns            = str
        self.hostgoups      = Dict[int,Hostgroup] ={}
        self.ip             = str
        self.monitorPassword = str
        self.monitorUser    = str
        self.password       = str
        self.port           = int
        self.user           = str
        self.connection     = 
        # MySQLCluster    *DataClusterImpl
        self.variables      = Dict[str,str]
        self.isInitialized  = False
        self.Weight         = 0
        self.holdLock       = 0
        self.isLockExpired  = False
        self.LastLockTime   = 0
        self.comment        = ""
        # Config          *global.Configuration
        self.pingTimeout    = 0
        
class Hostgroup:
    def __init__(self):
        pass        
            