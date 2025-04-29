"""
    ProxySQL object module defining all proxysql related class
"""

#import mysqlsh
from typing import Dict
#from mysqlsh import mysql
from magicbox.pxcpkg.pxcprocessor import PXC_Node 
from magicbox.pxcpkg.pxcprocessor import Pxc_processor


#shell = mysqlsh.globals.shell


class ProxySQLCluster:
    """
    ProxySQL Cluster class
    """
    def __init__(self,uri=False):
        """
        Returns a ProxySQL cluster object

        Args:
            uri (bool, optional): requires a valid URI to connect to the MySQL node
                                  Valid URI form: <user>:[<password>]@<ip>:[<port>]
        """
        self.name = ""
        self.nodes:Dict[str, ProxySQL] = {}
        self.active = False
        self.user = ""
        self.password = ""
        
    
class ProxySQL:
    """
    ProxySQL Object.
    """
    def __init__(self,uri=False):
        """
        Returns a ProxySQL Node object

        Args:
            uri (bool, optional): requires a valid URI to connect to the MySQL node
                                  Valid URI form: <user>:[<password>]@<ip>:[<port>]
        """

        self.actionNodeList:Dict[str,mysql_obj.Pxc_Node] = {}
        self.dns:str            = ""
        self.hostgoups:Dict[int,Hostgroup] ={}
        self.ip:str             = ""
        self.monitorPassword = ""
        self.monitorUser    = ""
        self.password       = ""
        self.port           = 0
        self.user           = ""
        self.connection     = None
        # MySQLCluster    *DataClusterImpl
        self.variables:Dict[str,str] = {}
        self.isInitialized  = False
        self.Weight         = 0
        self.holdLock       = 0
        self.isLockExpired  = False
        self.LastLockTime   = 0
        self.comment        = ""
        # Config          *global.Configuration
        self.pingTimeout    = 0
        
class Hostgroup:
    """
    Class represent the Hosgroup object
    """
    def __init__(self):
        pass        
            