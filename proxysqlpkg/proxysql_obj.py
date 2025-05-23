"""
    ProxySQL object module defining all proxysql related class
"""

from typing import Dict
from pxcpkg.pxc_obj import PXC_Node 
from mysqlpkg.mysql_obj import Mysql_Node

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
        self.nodes:Dict[str, ProxySQL_Node] = {}
        self.active = False
        self.user = ""
        self.password = ""
        
    
class ProxySQL_Node(Mysql_Node):
    """
    ProxySQL Object.
    """
    def __init__(self,uri=False):
        """
        Returns a ProxySQL Node object, this object represent a ProxySQL server instance
        The unique identifier is:
            IP:PORT

        Args:
            uri (bool, optional): requires a valid URI to connect to the MySQL node
                                  Valid URI form: <user>:[<password>]@<ip>:[<port>]
        """
#        self.actionNodeList:Dict[str,PXC_Node] = {}
        super().__init__(uri)
        self.dns:str            = ""
        self.hostgoups:Dict[int,Hostgroup] ={}
        self.monitorPassword = ""
        self.monitorUser    = ""
        self.connection     = None
        # MySQLCluster    *DataClusterImpl
        self.Weight         = 0
        self.holdLock       = 0
        self.isLockExpired  = False
        self.LastLockTime   = 0
        self.comment        = ""
        # Config          *global.Configuration
        self.pingTimeout    = 0
        
    def check_nodes_if_existing(self, node_hostname:str = None, port:int = 0):
        """
        For each existing HG we check any nodes in the PXC cluster
        To identify if they already exists and if already assined to that HG
        A node could existes in multiple HG so the match must be:
         nodename (hostname) : HG : PORT

        Args:
            node_name (str, optional): the hostname . Defaults to None.
        
        Returns:
            true/false
            
        Flow:
            from the PXC cluster we loop all nodes and check if the nodes are already present
            if already there then we may want to:
                - raise an alert
                - ask for what action
                            
        """
        return False
    
    def set_hostgroup(self, hg_id:int = 0,hg_type:str = None):
        """
        Initialize an host group
        
        Args:
            hd_id (int, optional): _description_. Defaults to 0.
            hg_type (str, optional): _description_. Defaults to "r".

        Returns:
            Hostgroup: Return an Hostgroup with minimal setup
        """
        hg = Hostgroup(hg_id)
       
        match hg_type:
            case "w":
                hg.is_writer = True
            case "r":
                hg.is_reader = True
            case "c":
                hg.is_catalog = True
            case "o":
                hg.is_offline = True
            case _:
                pass
        return hg

    def check_hostgroup_exist(self, hg_id:int = 0):
        """
        Check ig an hostgroup is already present in the Proxysql server

        Args:
            hg_id (int, optional): hostgroup id. Defaults to 0.

        Returns:
            boolean
        """
        if hg_id in self.hostgoups:
            return True
        
        return False
        
class Hostgroup:
    """
    Class represent the Hosgroup object
    Hostgroup types:
       w writer = hg writer id IE 100
       r reader = hg reader id IE 101
       c catalog = hg unmutable setting IE 8000 + hg_id
       o offline = hg maontenance IE 9000 + hg_id
    
    """
    def __init__(self,hg_id:int=0,nodes:dict={}):
        self.hg_id = hg_id
        self.nodes:dict = nodes
        self.is_writer = False
        self.is_reader = False
        self.is_catalog = False
        self.is_offline = False
        self.is_active = False
        self.max_writers = 1 
        self.is_writer_is_also_reader = False



class Proxy_mysql_data_node:
   """
   This class extends MySQL_Node and represent a MySQL server inside ProxySQL
   Unique identifier:
    IP:PORT:HG 
   """ 
   def __init__(self,uri=False):
        super().__init__(uri)
        self.hostgroup_id:int =0
        self.hostname:str =""
        self.port:int = 0
        gtid_port:int = 0
        status:str = ""
        weight:int = 1000
        compression:bool = False
        max_connections:int = 2000
        max_replication_lag:int = 0
        use_ssl:int = 1
        max_latency_ms:int =  0
        comment:str =""
   
   