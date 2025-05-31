"""
    ProxySQL object module defining all proxysql related class
"""
import logging
from typing import Dict

from common import utils_mb
from pxcpkg.pxc_obj import PXCNode
from mysqlpkg.mysql_obj import MysqlNode
import common.dbtools as dbtools


class ServerId:
    def __init__(self,hgid:int = 0,ip:str = "", port:int = 0):
        self.hg_id:int = int(hgid)
        self.server_ip:str = ip
        self.server_port:int = int(port)


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
        self.nodes:Dict[str, ProxySQLNode] = {}
        self.active = False
        self.user = ""
        self.password = ""
        
    
class ProxySQLNode(MysqlNode):
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
        self.mysql_nodes:Dict[Hostgroup, ProxyMysqlDataNode] = {}
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
        # Initialize the nodes existing
        self._load_nodes()

    def _load_nodes(self):
        """
        We load all the backend nodes for processing.
        At this stage we do not care if they have a PXC node in the background or not
        Returns:

        """
        sql = ("select * from mysql_servers")
        cursor = self.session.cursor(dictionary=True)
        cursor.execute(sql)
        mysql_servers = cursor.fetchall()
        for server in mysql_servers:
            bkend_node = ProxyMysqlDataNode(None,server["hostgroup_id"],None,server["hostname"],server["port"])
            bkend_node.gtid_port = server["gtid_port"]
            bkend_node.status = server["status"]
            bkend_node.weight = server["weight"]
            bkend_node.compression = server["compression"]
            bkend_node.max_connections = server["max_connections"]
            bkend_node.max_replication_lag = server["max_replication_lag"]
            bkend_node.use_ssl=server["use_ssl"]
            bkend_node.max_latency_ms=server["max_latency_ms"]
            bkend_node.comment = server["comment"]
            self.mysql_nodes[bkend_node.id] = bkend_node


    def check_nodes_if_existing(self, incoming_bck_nodes:dict[ServerId]={},hgid:int=0,force:bool=False ):
        """
        For each existing HG we check any nodes in the PXC cluster
        To identify if they already exists and if already assined to that HG
        A node could existes in multiple HG so the match must be:
         nodename (hostname) : HG : PORT

        Args:
            a dict [Hostgroup]ProxyMysqlDataNode instance
            the Hostgroup originating ID
        
        Returns:
            true/false
            
        Flow:
            from the PXC cluster we loop all nodes and check if the nodes are already present

                            
        """
        already_present = []
        for server in self.mysql_nodes.keys():
            # it_exists = False
            for node in incoming_bck_nodes.keys():
                if node.server_ip == server.server_ip and node.server_port == server.server_port and node.hg_id == server.hg_id:
                    already_present.append(f"Node {node.server_ip} Port: {node.server_port} hostgroup_id: {node.hg_id}")

                    # IF Force is True we flag the node in the Proxysql Server for deletion
                    self.mysql_nodes[server].actionlist.append(ProxyMysqlDataNode.ACTION_DELETE)
                    # At the same time we mark the node in the incoming list for INSERT
                    incoming_bck_nodes[node].actionlist.append(ProxyMysqlDataNode.ACTION_INSERT)
                    break

        if len(already_present) > 0:
            logging.warning(utils_mb.print_separator("#", ""))
            # print_line(utils_mb.print_separator("#", "[WARNING]"))
            # print(
            logging.warning(
                f"The following nodes are already present in the HostGroup id: {hgid} and related hostgroup_id={hgid + 1} " +
                f"or hostgroup_id={hgid + 8000} or hostgroup_id={hgid + 8001} or or hostgroup_id={hgid + 9000} or hostgroup_id={hgid + 9001}")

            for node_str in already_present:
                # print(
                logging.warning(node_str)

            logging.warning(utils_mb.print_separator("-"))
            if not force:
                # print(
                logging.warning(f"To automatically remove all related servers use option 'force=True'.\n" +
                                f"Or run delete_pxc_cluster_from_proxysql(hgid={hgid}).\n" +
                                "Or clean all related servers manually then rerun add_nodes_to_proxysql()")
            else:
                # print(
                logging.warning("Forcing is in place all the above nodes will be removed")

            # print_line(
            logging.warning(utils_mb.print_separator("#"))
            return True
        else:

            return False

    # def set_hostgroup(self, hg_id:int = 0,hg_type:str = None):
    #     """
    #     Initialize an host group
    #
    #     Args:
    #         hd_id (int, optional): _description_. Defaults to 0.
    #         hg_type (str, optional): _description_. Defaults to "r".
    #
    #     Returns:
    #         Hostgroup: Return an Hostgroup with minimal setup
    #     """
    #     hg = Hostgroup(hg_id, hg_type)
    #     return hg

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
    def __init__(self,hg_id:int=0, hg_type:str = "r"):
        self.hg_id = hg_id
        self.is_writer = False
        self.is_reader = False
        self.is_catalog = False
        self.is_offline = False
        self.is_active = False
        self.max_writers = 1 
        self.is_writer_is_also_reader = False

        match hg_type:
            case "w":
                self.is_writer = True
            case "r":
                self.is_reader = True
            case "c":
                self.is_catalog = True
            case "o":
                self.is_offline = True
            case _:
                pass


class ProxyMysqlDataNode(PXCNode):
   """
   This class extends MySQL_Node and represent a MySQL server inside ProxySQL
   Unique identifier:
    IP:PORT:HG 
   """
   ACTION_DELETE = "delete"
   ACTION_UPDATE = "update"
   ACTION_INSERT = "insert"
   def __init__(self, node:PXCNode, hgid=0, hgtype:str = "r",ip:str = "",port:int = 0):
        # super().__init__(uri)
        if (node is None or not node.session.is_connected()) and (ip == "" and port == 0):
            raise ValueError("Node cannot be None, or not connected to the MySQL server")
        elif (node is not None and node.session.is_connected()) and (ip == "" and port == 0):
            self.id:ServerId = ServerId(hgid=hgid, ip=node.ip, port=node.port)
            self.hostname:str = node.ip
            self.port:int = node.port
        else:
            self.id: ServerId = ServerId(hgid=hgid, ip=ip, port=port)
            self.hostname:str = ip
            self.port:int = port

        self.hostgroup:Hostgroup = Hostgroup(hgid,hgtype)
        self.gtid_port:int = 0
        self.status:str = ""
        self.weight:int = 1000
        self.compression:bool = False
        self.max_connections:int = 2000
        self.max_replication_lag:int = 0
        self.use_ssl:int = 1
        self.max_latency_ms:int =  0
        self.comment:str =""
        self.processed = False
        self.actionlist = []


   
   