"""
    ProxySQL object module defining all proxysql related class
"""
import logging
from io import StringIO
from logging import exception
from typing import Dict

# We have different entry points to load modules.
# When inside MySQL Shell we need full path
try:
    from common import utils_mb, dbtools
    from mysqlpkg.mysql_obj import MysqlNode
except ImportError:
    from magicbox.common import utils_mb, dbtools
    from magicbox.mysqlpkg.mysql_obj import MysqlNode
    pass


import json



class ServerId:
    def __init__(self,hgid:int = 0,ip:str = "", port:int = 0):
        self.hg_id:int = int(hgid)
        self.server_ip:str = ip
        self.server_port:int = int(port)


class Hostgroup:
    """
    Class represent the Hosgroup object
    Hostgroup types:
       w writer = hg writer id IE 100
       r reader = hg reader id IE 101
       c catalog = hg unmutable setting IE 8000 + hg_id
       o offline = hg maontenance IE 9000 + hg_id

    The convention is the following:
        given a writer ID x, Reader is X + 1; Catalog is Writer/Reader + 8000; Oflline Writer/Reader + 9000

    """

    @staticmethod
    def identify_hg_role(hgid_main_writer,hgid,handler:int):
        """
        Identify the hg type based on the convention defined in the class definition
        Args:
            hgid_main_writer: the writer HG id
            hgid: the id of the node we need to identify
            handler: the handler that will be used ti manage the cluster on proxysql

        Returns:str type identifier

        """

        if hgid_main_writer == 0:
            return ""

        _code = hgid - hgid_main_writer
        if _code == 0:
            return "w"
        if _code == 1:
            return "r"
        if _code == 8000:
            if handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
                return "c"
            else:
                return "b"

        if _code == 9000 or _code == 7000:
            return "o"


        return ""


    @staticmethod
    def get_hostgroup_ids_by_handler_support(hgid:int=0, handler:int = 0):
        """
        We return a different list of hostgroup id according to the Handler
        if we use the Scheduler we have:
            - defined by user (IE 100) for writer(s)
            - Read defined + 1
            - Configuration write: defined + 8000
            - Configuration read: defined + 8001

        if we use the internal support:
        - defined by user (IE 100) for writing
        - Read defined + 1
        - Backup_writer: defined + 8000
        - Offline: defined + 7000

        :param hgid:int Hostgroup Id define by user

        :return: list of hostgroup id
        """
        ids = []
        if handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
            ids.append(Hostgroup(hgid,"w"))
            ids.append(Hostgroup(hgid + 1, "r"))
            ids.append(Hostgroup(hgid + 8000, "c"))
            ids.append(Hostgroup(hgid + 8001, "c"))

        elif handler == ProxyMysqlDataNode.HANDLER_INTERNAL:
            ids.append(Hostgroup(hgid,"w"))
            ids.append(Hostgroup(hgid + 1, "r"))
            ids.append(Hostgroup(hgid + 7000, "o"))
            ids.append(Hostgroup(hgid + 8000, "b"))

        return ids

    def __init__(self, hg_id: int = 0, hg_type: str = "r"):
        self.hg_id = hg_id
        self.is_writer = False
        self.is_reader = False
        self.is_catalog = False
        self.is_offline = False
        self.is_backup = False
        self.is_active = False
        self.max_writers = 1
        self.is_writer_is_also_reader = True
        self.set_role(hg_type)

    def set_role(self, hg_type:str="r"):
        """
        Set the type of HG base on the code and the defined convention
        Args:
            hg_type:

        Returns: void

        """
        match hg_type:
            case "w":
                self.is_writer = True
            case "r":
                self.is_reader = True
            case "c":
                self.is_catalog = True
            case "o":
                self.is_offline = True
            case "b":
                self.is_backup = True
            case _:
                pass


class ProxyMysqlDataNode(MysqlNode):
   """
   This class extends PXC_NODE and represent a PXC server inside ProxySQL
   Unique identifier:
    IP:PORT:HG
   """
   NODE_ONLINE = "ONLINE"
   NODE_SHUNNED = "SHUNNED"
   NODE_OFFLINE_SOFT = "OFFLINE_SOFT"
   NODE_OFFLINE_HARD = "OFFLINE_HARD"
   ACTION_DELETE = "delete"
   ACTION_UPDATE = "update"
   ACTION_INSERT = "insert"
   HANDLER_SCHEDULER = 1
   HANDLER_INTERNAL = 2
   JSON_CONFIGURABLE = ["gtid_port","status","weight","compression","max_connections","max_replication_lag","use_ssl","max_latency_ms","comment"]


   def serialize_proxysql_node(self) -> str:
       """
       Converts a ProxyMysqlDataNode instance into a JSON string representation.
       Returns:
           A JSON formatted string representing the instance's attributes.
       """
       node_instance = self

       if not isinstance(node_instance, ProxyMysqlDataNode):
           raise TypeError("Input must be an instance of ProxyMysqlDataNode.")

       data = {}
       # Iterate through all instance attributes (excluding special/private ones)
       for key, value in node_instance.__dict__.items():
           # Skip attributes that are typically not part of the data model
           # or are internal Python mechanisms.
           if key.startswith('_') or key in ["session", "action_list"]:
               continue

           if isinstance(value, (int, str, bool, float, type(None))):
               # Directly include primitive types
               data[key] = value
           elif isinstance(value, (ServerId, Hostgroup)):
               # If it's a custom object with a to_dict() method, use it.
               # This makes the serialization of nested objects explicit and clean.
               if hasattr(value, 'to_dict') and callable(value.to_dict):
                   data[key] = value.to_dict()
               else:
                   # Fallback for custom objects without to_dict(), try to serialize their __dict__
                   # This might be less robust for complex objects.
                   try:
                       data[key] = value.__dict__
                   except AttributeError:
                       # If an object doesn't have __dict__ (e.g., slots), represent as string
                       data[key] = str(value)
           elif isinstance(value, list):
               # Handle lists, e.g., action_list
               serializable_list = []
               for item in value:
                   if isinstance(item, (int, str, bool, float, type(None))):
                       serializable_list.append(item)
                   elif hasattr(item, 'to_dict') and callable(item.to_dict):
                       serializable_list.append(item.to_dict())
                   else:
                       try:
                           serializable_list.append(item.__dict__)
                       except AttributeError:
                           serializable_list.append(str(item))
               data[key] = serializable_list
           else:
               # For other complex types, we might choose to skip, represent as string,
               # or raise an error if not explicitly handled.
               data[key] = str(value)  # Default to string representation for unhandled types

       return json.dumps(data, indent=2)

   def __init__(self, node:MysqlNode, hgid=0, hgtype:str = "r",ip:str = "",port:int = 0):
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
        self.status:str = "ONLINE"
        self.weight:int = 1000
        self.compression:bool = False
        self.max_connections:int = 2000
        self.max_replication_lag:int = 0
        self.use_ssl:int = 1
        self.max_latency_ms:int =  0
        self.comment:str =""
        self.processed = False
        self.action_list = []
        self.main_writer = False

   #  Deprecated
   # def to_json(self):
   #     data:dict[str,str] =dict()
   #     id:dict[str,str] =dict()
   #     id["hg_id"] = self.id.hg_id
   #     id["server_ip"]=self.id.server_ip
   #     id["server_port"]=self.id.server_port
   #     data["id"] = id
   #     data["gtid_port"] = self.gtid_port
   #     data["status"] = self.status
   #     data["weight"] = self.weight
   #     data["compression"] = self.compression
   #     data["max_connections"] = self.max_connections
   #     data["max_replication_lag"] = self.max_replication_lag
   #     data["use_ssl"] = self.use_ssl
   #     data["max_latency_ms"] = self.max_latency_ms
   #     data["comment"] = self.comment
   #     return data

   def return_data_from_json(self,json_text):
       data = json.loads(json_text)
       return data



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

    VALID_BACKEND_STATE=['ONLINE','OFFLINE_SOFT','OFFLINE_HARD']

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
        self.mysql_nodes:Dict[ServerId, ProxyMysqlDataNode] = {}
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
        self._current_cluster_writer_id = 0
        self.handler = ProxyMysqlDataNode.HANDLER_SCHEDULER
        self._load_back_end_nodes()


    def set_current_cluster_writer_id(self,hgid:int):
        """
        Set the active cluster ID.
        A ProxySQL server instance can deal with ONE cluster writer id a time
        Args:
            hgid:

        Returns:

        """
        self._current_cluster_writer_id = hgid
        self._identify_hostgroup_role_based_on_main_writer_hgid()


    def get_current_cluster_writer_id(self):
        return self._current_cluster_writer_id


    def _load_back_end_nodes(self):
        """
        This is an action at __init__
        We load all the backend nodes for processing.
        At this stage we do not care if they have a PXC node in the background or not
        We also do not care if we load all the nodes and they are not relevant because we still do not know.
        Once we have reconciled with the PXC cluster, then only the node currently available for that cluster will be part of the visible backend nodes

        However, we need to respect/follow a convention to identify the
        Returns: Void

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

    def refresh_bakend_nodes(self):
        self.mysql_nodes = {}
        self._load_back_end_nodes()
        self._identify_hostgroup_role_based_on_main_writer_hgid()

    def _identify_hostgroup_role_based_on_main_writer_hgid(self):
        if self._current_cluster_writer_id == 0:
            return

        for node in self.mysql_nodes.values():
            hgcode = Hostgroup.identify_hg_role(self._current_cluster_writer_id,node.id.hg_id, self.handler)
            if hgcode != "":
                node.hostgroup.set_role(hgcode)




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
        hg_exists = False
        # Loop the incoming server list and compare with the backend nodes in Proxysql
        for server in self.mysql_nodes.keys():

            if server.hg_id == hgid:
                hg_exists = True

            for node in incoming_bck_nodes.keys():
                if node.server_ip == server.server_ip and node.server_port == server.server_port and node.hg_id == server.hg_id:
                    already_present.append(f"Node {node.server_ip} Port: {node.server_port} hostgroup_id: {node.hg_id}")

                    break

        if len(already_present) > 0:
            logging.warning(utils_mb.print_separator("#", ""))
            # print_line(utils_mb.print_separator("#", "[WARNING]"))
            # print(
            logging.warning(
                f"The following nodes are already present in the HostGroup id: {hgid} and related hostgroup_id")

            for node_str in already_present:
                # print(
                logging.warning(node_str)

            logging.warning(utils_mb.print_separator("-"))
            logging.warning("Nodes already existing")
            # if not force:
            #     print(
            #     logging.warning(f"I will try to reconcile the cluster with the ProxySQL backend nodes.  To automatically remove all related servers use option 'force=True'.\n" +
            #                     f"Or run delete_pxc_cluster_from_proxysql(hgid={hgid}).\n" +
            #                     "Or clean all related servers manually then rerun add_nodes_to_proxysql()")
            # else:
            #     # print(
            #     logging.warning("Forcing is in place all the above nodes will be removed")

            # print_line(
            # logging.warning(utils_mb.print_separator("#"))
            return {"servers" : True, "hg" :hg_exists}
        else:
            return {"servers" : False, "hg" :hg_exists}




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
        for node in self.mysql_nodes:
            if hg_id == node.hg_id:
                return True
        
        return False
        

    def reconcile_hostgroup(self,hgid:int=0,pxc_node_list:dict=None,number_of_writers:int=0):
        """
        Here the logic is a bit more complex.
        We need to keep in mind that we should never disrupt production service, so also if we 1 writer and that writer at the moment of reconcile
        is not the main node, we should never remove the current writer and insert the main node.
        This because in proxy sql the action will result as connection drop, causing serius impact on service.
        So we need to:
        - check if we have more than one writer
        - check if the writer we have are already online or not (if we have one writer and the one online is not main DO NOT remove it)
        - add writers not present (if one writer add as OFFLINE_SOFT)
        - Add all the others
        """

        # First, we process the writers
        if number_of_writers==0:
            number_of_writers = 1

        # Get the list of nodes related to the writer
        # _proxysql_backend_servers = None
        # _proxysql_backend_servers = self.get_nodes_by_hostgroups([hgid, hgid + 8000])

        # count_proxysql_writers = self._get_number_of_backend_nodes_by_hgid(hgid)
        # count_proxysql_config_writers = self._get_number_of_backend_nodes_by_hgid(hgid + 8000)
        main_writer_node:ProxyMysqlDataNode = self._get_main_node_from_pxc(pxc_node_list)

        # pxc_writer_is_in = False
        # pxc_writer_config_is_in = False

        proxy_config_purged_w = False
        proxy_config_purged_r = False
        proxy_purged_r = False

        # First check if we need to add nodes in writer hg
        for pxc_node in pxc_node_list.values():
            if pxc_node.id.hg_id == hgid:

                # Main node (default writer) is not present in the ProxySQL list of nodes to use for write we need to insert it
                if self._is_node_equal_to_node(pxc_node, main_writer_node) and not self._get_if_node_exists_in_backend_nodes(pxc_node.id):
                    logging.warning(f"Preferred writer node {pxc_node.id.hg_id}:{pxc_node.id.server_ip}:{pxc_node.id.server_port} is not present in the ProxySQL HG {hgid}, will add it")
                    # If number of writers is 1 then we will add it and set OFFLINE_SOFT the current one
                    if number_of_writers == 1:
                        nodes_to_put_offline_soft = self.get_nodes_by_hostgroups([hgid,])
                        for node in nodes_to_put_offline_soft.values():
                            self.move_backend_to_offline_soft(node)

                    #  then we add the writer if missed
                    self.update_backend(pxc_node)

            # let us now check the 8000 group
            if pxc_node.id.hg_id == (hgid + 8000):
                self.update_backend(pxc_node)

            # let us now check the hgid + 1 (reader) group
            if pxc_node.id.hg_id == (hgid + 1):
                self.update_backend(pxc_node)

            # let us now check the 8000 (reader) group
            if pxc_node.id.hg_id == (hgid + 8001):
                self.update_backend(pxc_node)

        self.apply_backend()
        self.refresh_bakend_nodes()


    def _get_number_of_backend_nodes_by_hgid(self, hgid):
        """
        internal function to get the number of elements in a Hg

        :param hgid:
        :return:int number of nodes
        """
        counter = 0

        for node_id in self.mysql_nodes:
            if node_id.hg_id == hgid:
                counter += 1

        return counter
    def _is_node_equal_to_node(self,node1:ProxyMysqlDataNode,node2:ProxyMysqlDataNode):
        """
        Compare two nodes by id and return true if they match
        :param node1:ProxyMysqlDataNode
        :param node2:ProxyMysqlDataNode
        :return:bool
        """
        if node1.id.hg_id == node2.id.hg_id and node1.id.server_ip == node2.id.server_ip and node1.id.server_port == node1.id.server_port:
            return True

        return False

    def _get_if_node_exists_in_backend_nodes(self,serverid:ServerId):
        """
        Internal function to get if a node with the given id exists in the backend
        :param serverid:
        :return:bool

        """
        for bckend_id in self.mysql_nodes:
            if serverid.hg_id == bckend_id.hg_id and serverid.server_ip == bckend_id.server_ip and serverid.server_port == bckend_id.server_port:
                return True

        return False

    def _get_main_node_from_pxc(self,pxc_nodes):
        """
        Internal function to identify the main node out from the PXC list
        Main node is by default the preferred primary
        :param pxc_nodes:
        :return: ProxyMySQLDataNode instance
        """
        for pxc_node in pxc_nodes.values():
            if pxc_node.main_writer:
                return pxc_node

        return None

    def move_backend_to_offline_soft(self,node:ProxyMysqlDataNode=None,apply:bool=False):
        """
        Move the node to offline soft
        :param node:
        :param apply:

        Raise:
            Exception
        """
        if node is None:
            return False
        try:
            cursor = self.session.cursor(dictionary=False)
            cursor.execute(f"Update mysql_servers set status='OFFLINE_SOFT' where hostgroup_id={node.id.hg_id} and hostname='{node.id.server_ip}' and port={node.id.server_port}")
            if apply:
                self.apply_backend()
        except:
            raise Exception("Error while moving mysql server to offline soft")

        return True

    def move_backend_to_online(self,node:ProxyMysqlDataNode=None,apply:bool=False):
        """
        Move the node to ONLINE
        :param node:
        :param apply:

        Raise:
            Exception
        """
        if node is None:
            return False
        try:
            cursor = self.session.cursor(dictionary=False)
            cursor.execute(f"Update mysql_servers set status='ONLINE' where hostgroup_id={node.id.hg_id} and hostname='{node.id.server_ip}' and port={node.id.server_port}")
            if apply:
                self.apply_backend()
        except:
            raise Exception("Error while moving mysql server to ONLINE")

        return True

    def delete_backend(self,node:ProxyMysqlDataNode=None,apply:bool=False):
        """
        Delete the node
        :param node:
        :param apply:

        Raise:
            Exception

        """
        if node is None:
            return False
        try:
            cursor = self.session.cursor(dictionary=False)
            cursor.execute(f"delete from mysql_servers where hostgroup_id={node.id.hg_id} and hostname='{node.id.server_ip}' and port={node.id.server_port}")
            if apply:
                self.apply_backend()
        except:
            raise Exception("Error while moving mysql server to offline soft")

        return True
    def insert_backend(self,node:ProxyMysqlDataNode=None,apply:bool=False):
        """
        Insert the node
        :param node:
        :param apply:

        Raise:
            Exception

        """
        if node is None:
            return False
        try:
            cursor = self.session.cursor(dictionary=False)
            sql= f"insert into mysql_servers (hostname,hostgroup_id,port,weight,max_connections,use_ssl,comment) values('{node.id.server_ip}',{node.id.hg_id},{node.id.server_port},{node.weight},{node.max_connections},{node.use_ssl},'{node.comment}')"
            cursor.execute(sql)

            if apply:
                self.apply_backend()
        except:
            raise Exception("Error while inserting a new mysql server ")

        return True

    def update_backend(self,node:ProxyMysqlDataNode=None,apply:bool=False):
        """
        update the node
        :param node:
        :param apply:

        Raise:
            Exception

        Attributes updated:
            self.gtid_port:int = 0
            self.status:str = ""
            self.weight:int = 1000
            self.compression:bool = False
            self.max_connections:int = 2000
            self.max_replication_lag:int = 0
            self.use_ssl:int = 1
            self.max_latency_ms:int =  0

        """
        if node is None:
            return False
        try:
            cursor = self.session.cursor(dictionary=False)
            sql = (f"update mysql_servers set " +
                   f"weight={node.weight},max_connections={node.max_connections},use_ssl={node.use_ssl},comment='{node.comment}'," +
                   f"gtid_port={node.gtid_port},status='{node.status}',weight={node.weight},compression={node.compression}," +
                   f"max_replication_lag={node.max_replication_lag},max_latency_ms={node.max_latency_ms} " +
                   f"where hostname='{node.id.server_ip}' and hostgroup_id = {node.id.hg_id} and port = {node.id.server_port}")
            cursor.execute(sql)

            if apply:
                self.apply_backend()
        except:
            raise Exception("Error while inserting a new mysql server ")

        return True

    def apply_backend(self):
        """
        Applies the backend to Runtime and Disk
        """
        try:
            cursor = self.session.cursor(dictionary=False)
            cursor.execute("LOAD MYSQL SERVERS TO RUNTIME")
            cursor.execute("SAVE MYSQL SERVERS TO DISK")

        except:
            raise Exception("Error while applying mysql server")

    def remove_writers_not_preferred(self,node:ProxyMysqlDataNode=None,apply:bool=False):
        """
        The method will remove all writers that are not the Preferred node
        Where the preferred node is the one passed
        :param node:ProxyMysqlDataNode Preferred node to keep
        :param apply: Will apply all changes to the database

        """
        if ServerId is None:
            return False

        try:
            cursor = self.session.cursor(dictionary=False)
            cursor.execute(f"delete mysql_servers where hostgroup_id={node.id.hg_id} and hostname !='{node.id.server_ip}' and port !={node.id.server_port}")
            if apply:
                self.apply_backend()

        except:
            raise Exception("Error while removing backend writer nodes not preferred")

    def get_nodes_by_hostgroups(self,hgisd:[]=None):
        """
        The function returns a dictionary containing the server who matches the given ids
        :param hgisd:

        Raises:
        ValueError: If hgisd is not

        Returns:
        dict: Dictionary[ServerId, ProxySQLNode]
        """
        proxysql_backend_by_hg:Dict[ServerId, ProxyMysqlDataNode] = {}
        if hgisd is None:
            logging.error("List of hostgroup id to reconcile is None, this is not fine")
            raise Exception("List of hostgroup id to reconcile is None")

        for server in self.mysql_nodes.values():
            # for hgid in hgisd:
            if server.id.hg_id in hgisd:
                proxysql_backend_by_hg[server.id] = server

        return proxysql_backend_by_hg

    def _get_node_by_id(self,server_id:ServerId):
       """
       The function will return the node matching the composite Server ID
       :param server_id:ServerId 
       :return ProxyMySQLDataNode
       """
       if server_id is not None and server_id :
        for node in self.mysql_nodes.values():
            if node.id.hg_id == server_id.hg_id and node.id.server_ip == server_id.server_ip and node.id.server_port == server_id.server_port:
                return node
        return None

    def get_json_node_definitions(self,server_id:ServerId=None):
        """
        The method will return the Json representation of the ProxySQLMySQLDataNode, focus on ProxySQL aatributes

        :param server_id:ServerId of the node
        :return Json
        """
        if server_id is not None:
            node = self._get_node_by_id(server_id)
            if node is not None and node.id.hg_id >= 0:
                return node.serialize_proxysql_node()
                # json.dumps(node.to_json())

    def config_nodes(self, json_text:str=None):
        """
        The method will configure the nodes as for the Json provided
        The nodes will be modified ONLY in the ProxySQLServer instance and not on the ProxySQL server DB
        :param json_text:JSON

        :return List of modified nodes
        """
        return_node_list = []
        if json_text is not None:
            data = json.loads(json_text)
            if data["cluster"] is not None:
                try:
                    cluster = data["cluster"]
                    nodes = cluster["nodes"]
                    if len(nodes) > 0:
                        for node_conf in nodes:
                            for node in self.mysql_nodes.values():
                                id = node_conf["id"]
                                if id["hg_id"] == node.id.hg_id and id["server_ip"] == node.id.server_ip and id["server_port"] == node.id.server_port:
                                    for key in ProxyMysqlDataNode.JSON_CONFIGURABLE:
                                        if key in node_conf:
                                            setattr(node, key, node_conf[key])
                                    return_node_list.append(node)
                                    # No this method is only to Update the node in Proxysql instance not to save it to disk
                                    # self.update_backend(node)

                    # if apply:
                    #     self.apply_backend()
                except Exception as e:
                    logging.error(e)
        return return_node_list

    def get_json_by_hostgroups(self,ids:list=None):
        """
        The method return the json representation of all nodes matching the list of hostgroup given in the list.

        :param ids: the list of hostgroup ids
        :return: the json representation of all nodes
        """
        if ids is None or len(ids) == 0:
            return ""

        server_list= self.get_nodes_by_hostgroups(ids)

        json_text_head='''
{
   "cluster":{
      "nodes":[
        '''
        json_text_tail = '''
      ]
   }
}
        '''

        buffer = StringIO()

        for server in server_list.values():
            buffer.write(server.serialize_proxysql_node() + ",")

        json_text_body = buffer.getvalue()
        buffer.close()
        return json_text_head + json_text_body + json_text_tail


    def setup_cluster_manager(self, apply:bool = True):
        """
        The method will setup the cluster manager, setting up the scheduler or the ProxySQL internal support.
        We cannot have both active
        Args:
            None
        Returns:void
        Raises: current_cluster_writer_id not define
        """
        if self.get_current_cluster_writer_id() == 0:
            logging.error("Setting up cluster manager cannot be done without define first the Preferred cluster writer id ")
            raise exception("current_cluster_writer_id not define. The ProxySQL instance does not have a Cluster associated, have you execute <pxc_cluster>.add_cluster_to_proxysql()?")

        pxc_manager_id = self._get_pxc_manager_id()

        logging.info(f"Set up cluster manager id: {pxc_manager_id} [START]")
        if self.handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
            self._setup_scheduler(pxc_manager_id,apply)
        else:
            self._setup_galera_internal(pxc_manager_id,apply)

        logging.info(f"Set up cluster manager id: {pxc_manager_id} [END]")

    def _get_pxc_manager_id(self):
        """
        Internal method that returns the string representation of the cluster id to be used in the manager configuration
        Returns:str manager id
        """
        pxc_manager_id = "{ hgW:" + str(self.get_current_cluster_writer_id()) + ", hgR:" + str(
            self.get_current_cluster_writer_id() + 1) + " }"
        return pxc_manager_id

    def _setup_scheduler(self,pxc_manager_id, apply:bool = False):
        """
        Specifically, set the scheduler manager
        Args:
            pxc_manager_id:

        Returns: void

        """
        try:
            # First, we check if the scheduler is already defined in the scheduler table
            cursor = self.session.cursor(dictionary=True)
            sql = f"select * from scheduler where comment = '{pxc_manager_id}'"
            exists, row_count = self._test_for_active_manager(sql)

            if 0 < row_count < 2:
                logging.warning(
                    f"Scheduler already define (id:{pxc_manager_id}), please manage it with update/delete/activate/deactivate methods")
                return

            elif row_count == 1:
                logging.error(
                    f"We have multiple entries in the scheduler matching the id {pxc_manager_id}. This is not fixable, please check if there is some refuse from previous installations and clen it")
                return
        except:
            raise Exception("Error while checking scheduler")

        # If we reach this, it means no entry in the scheduler so we can add it
        # TODO: find a way to pass the parameters about the binary location and the config file
        # Also I need to be able to write the config file based on a template fillign it with some parameters
        sql = (f"INSERT  INTO scheduler (active,interval_ms,filename,arg1,arg2,comment) values" +
               f" (0,2000,'/var/lib/proxysql/proxysql_scheduler/proxysql_checker','--configfile=config.toml','--configpath=/var/lib/proxysql/','{pxc_manager_id}')")

        self._execute_sql(sql)
        if apply:
            self._execute_sql("LOAD SCHEDULER TO RUNTIME")
            self._execute_sql("SAVE SCHEDULER TO DISK")

        logging.info("Scheduler setup complete, but not active")

    def _setup_galera_internal(self,pxc_manager_id, apply:bool = False):
        """
        Specifically, set the ProxySQL internal manager
        Args:
            pxc_manager_id:

        Returns: void

        """
        # We now need to setup the internal galera support
        host_groups: [Hostgroup] = Hostgroup.get_hostgroup_ids_by_handler_support(self.get_current_cluster_writer_id(),self.handler)
        writer_id = 0
        reader_id = 0
        writer_bck_id = 0
        offline_id = 0

        for host_group in host_groups:
            if host_group.is_writer:
                writer_id = host_group.hg_id

            if host_group.is_reader:
                reader_id = host_group.hg_id

            if host_group.is_offline:
                offline_id = host_group.hg_id

            if host_group.is_backup:
                writer_bck_id = host_group.hg_id

        # Let us check if there is already a definition for this cluster
        sql = (f"select * from mysql_galera_hostgroups where (writer_hostgroup={writer_id} and " +
               f"backup_writer_hostgroup={writer_bck_id} and reader_hostgroup={reader_id} and offline_hostgroup={offline_id}) or comment='{pxc_manager_id}'")

        exists,row_count = self._test_for_active_manager(sql)

        if 0 < row_count < 2:
            logging.warning(
                f"PXC support already define in the mysql_galera_hostgroup table, please manage it with update/delete/activate/deactivate methods")
            return

        elif row_count > 1:
            logging.error(
                f"We have multiple entries in mysql_galera_hostgroup matching the id {pxc_manager_id}. This is not fixable, please check if there is some refuse from previous installations and clen it")
            return

        # If we reach this it means that no entry in the mysql_galera_hostgroup so we cna go ahead and insert
        sql = ("INSERT INTO mysql_galera_hostgroups (writer_hostgroup,backup_writer_hostgroup,reader_hostgroup," +
               "offline_hostgroup,active,max_writers,writer_is_also_reader,max_transactions_behind,comment) " +
               f"VALUES ({writer_id},{writer_bck_id},{reader_id},{offline_id},0,1,1,100,'{pxc_manager_id}')")

        self._execute_sql(sql)
        if apply:
            self.apply_backend()

    def activate_cluster_manager(self, apply:bool = True):
        """
        Method to activate the PXC manager

        Returns: void
        """
        logging.info(f"Activate cluster manager id: {self._get_pxc_manager_id()} [START]")

        _sql = ""
        if self.handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
            # First we check if there is an internal manager active if not we activate it
            _sql = f"select * from mysql_galera_hostgroups where active=1 and writer_hostgroup={self._current_cluster_writer_id}"
        else:
            _sql =f"select * from scheduler where comment={self._current_cluster_writer_id}"

        exists, rows = self._test_for_active_manager(_sql)

        if exists:
            logging.error(f"Cannot activate a manager instance already exists for cluster id:{self._get_pxc_manager_id()}")
        else:
            if self.handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
                self._execute_sql(f"update scheduler set active=1 where comment='{self._get_pxc_manager_id()}'")
                if apply:
                    self._execute_sql("LOAD SCHEDULER TO RUNTIME")
                    self._execute_sql("SAVE SCHEDULER TO DISK")
            else:
                self._execute_sql(f"update mysql_galera_hostgroups set active=1 where writer_hostgroup={self.get_current_cluster_writer_id()}")
                if apply:
                    self.apply_backend()

        logging.info(f"Activate cluster manager id: {self._get_pxc_manager_id()} [END]")

    def deactivate_cluster_manager(self,apply:bool = True):
        """
        Method to deactivate the PXC Manger
        Returns: void

        """
        logging.info(f"Deactivate cluster manager id: {self._get_pxc_manager_id()} [START]")

        if self.handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
            self._execute_sql(f"update scheduler set active=0 where comment='{self._get_pxc_manager_id()}'")
            if apply:
                self._execute_sql("LOAD SCHEDULER TO RUNTIME")
                self._execute_sql("SAVE SCHEDULER TO DISK")
        else:
            self._execute_sql(
                f"update mysql_galera_hostgroups set active=0 where writer_hostgroup={self.get_current_cluster_writer_id()}")
            if apply:
                self.apply_backend()

        logging.info(f"Deactivate cluster manager id: {self._get_pxc_manager_id()} [END]")

    def delete_cluster_manager(self, apply:bool = True):
        """
        Remove the PXC Manager
        Args:
            apply: bool True

        Returns: void

        """
        logging.info(f"Removing cluster manager id: {self._get_pxc_manager_id()} [START]")

        if self.handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
            self._execute_sql(f"delete from scheduler where comment='{self._get_pxc_manager_id()}'")
            if apply:
                self._execute_sql("LOAD SCHEDULER TO RUNTIME")
                self._execute_sql("SAVE SCHEDULER TO DISK")
        else:
            self._execute_sql(
                f"delete from mysql_galera_hostgroups where writer_hostgroup={self.get_current_cluster_writer_id()}")
            if apply:
                self.apply_backend()

        logging.info(f"Removing cluster manager id: {self._get_pxc_manager_id()} [END]")

    def delete_cluster(self,nodes:dict[ServerId:ProxyMysqlDataNode] = None, apply:bool = False):
        """
        Method to delete a set of nodes.
        If not set is pass then it will delete the current active cluster
        Args:
            nodes:

        Returns:

        """
        logging.info(f"Delete cluster id: {self._get_pxc_manager_id()} [START]")

        if nodes is None:
            nodes = self.get_active_cluster_nodes()

        if nodes is None or len(nodes) == 0:
            logging.error(f"Error looking for the nodes to delete with HG id:{self.get_current_cluster_writer_id()}")

        if self.get_current_cluster_writer_id() == 0:
            logging.error("Cannot delete the cluster missing Preferred cluster writer id ")
            raise exception("current_cluster_writer_id not define. The ProxySQL instance does not have a Cluster associated, have you execute <pxc_cluster>.add_cluster_to_proxysql()?")

        for node in nodes:
            sql = f"delete from mysql_servers where hostname = '{node.id.server_ip}' and port = '{node.id.server_port}' and hostgroup_id = {node.id.hg_id}"
            logging.debug(sql)
            self._execute_sql(sql)

        if apply:
            self.apply_backend()

        # Also cleanup the manager
        self.delete_cluster_manager()
        logging.info(f"Delete cluster id: {self._get_pxc_manager_id()} [END]")

    def update_nodes(self,modified_nodes:[ProxyMysqlDataNode] = None, apply:bool = False):
        """
        Update on mysql_servers table the list of nodes
        Args:
            modified_nodes:
            apply: bool Default False

        Returns:

        """
        if modified_nodes is None or len(modified_nodes) == 0:
            return

        for node in modified_nodes:
            self.update_backend(node)

        if apply:
            self.apply_backend()


    def _test_for_active_manager(self,sql):
        """
        Internal function to test a generic sql returning rows
        Args:
            sql:str The sql to run to check the manager
        Returns:
            bool: True if there are rows False if not
            int: number of rows

        """
        try:
            cursor = self.session.cursor(dictionary=True)
            cursor.execute(sql)
            cursor.fetchall()
            rows_number = cursor.rowcount
            if rows_number > 0:
                return True,rows_number
            return False,0

        except:
            raise Exception()


    def _execute_sql(self,sql):
        """
        Internal method to execute SQL command on the ProxySQL instance
        Args:
            sql: SQL to execute

        Returns: none
        Exceptions: Generic Exception()

        """
        try:
            cursor = self.session.cursor(dictionary=False)
            cursor.execute(sql)
            return cursor.rowcount
        except:
            raise Exception()

    def get_active_hostgroups_id(self):
        """
        Method return a list with the ID (int) of any Hostgroup involved in the PXC cluster activities
        Returns: [int]
        """
        hostgroup_ids = Hostgroup.get_hostgroup_ids_by_handler_support(self.get_current_cluster_writer_id(),
                                                                       self.handler)
        return hostgroup_ids
    def get_active_cluster_nodes(self):
        """
        This method return a list with all the nodes related to the current active writer
        Returns: List of ProxyMysqlDataNode

        """

        hostgroup_ids = self.get_active_hostgroups_id()

        # We need to transform the Hosgroup list into int list
        hostgroup_ids_lookup = []
        for hostgroup_id in hostgroup_ids:
            hostgroup_ids_lookup.append(hostgroup_id.hg_id)

        found_nodes = []
        nodes_to_put_offline_soft = self.get_nodes_by_hostgroups(hostgroup_ids_lookup)
        for node in nodes_to_put_offline_soft.values():
            found_nodes.append(node)

        # found_nodes = self.get_nodes_by_hostgroups(hostgroup_ids_lookup)
        if found_nodes is None or len(found_nodes) == 0  :
            return None

        return found_nodes

    def add_backend_nodes(self,nodes_list:[ProxyMysqlDataNode]=None, apply:bool = False):
        """
        Inserting nodes in the mysql_server table
        Args:
            nodes_list: list of backend
            apply: bool If to save to runtime/disk

        Returns: Void

        """
        if nodes_list is None or nodes_list == []:
            logging.warning(f"No nodes to add to ProxySQL instance for cluster {self._get_pxc_manager_id()}")

        for node in nodes_list:
            self.insert_backend(node,apply)

    def change_backend_nodes_status(self,nodes_dict:{} = None,status:str = "ONLINE",apply:bool = False):
        """
        Modify the STATUS of the passed nodes in Proxysql
        Args:
            nodes_list:[ProxyMysqlDataNode] List of bacend nodes
            status: str A valid state to apply to the nodes
            apply: bool If to save to runtime/disk

        Returns:

        """

        if nodes_dict is None or nodes_dict == {}:
            logging.warning(f"No nodes to modify for cluster {self._get_pxc_manager_id()}")

        if status not in self.VALID_BACKEND_STATE:
            logging.warning(f" Trying to set an invalid status: {status} valid statuses {self.VALID_BACKEND_STATE}")

        node_list = []
        for node in nodes_dict.values():
            node.status = status
            node_list.append(node)

        self.update_nodes(node_list,True)


    def monitor_get_connectivity_summary(self):

        '''
        | weight | hostgroup | srv_host      | srv_port | status       | ConnUsed | ConnFree | ConnOK | ConnERR | MaxConnUsed | Queries | Queries_GTID_sync | Bytes_data_sent | Bytes_data_recv | Latency_us |
        +--------+-----------+---------------+----------+--------------+----------+----------+--------+---------+-------------+---------+-------------------+-----------------+-----------------+------------+
        | 999    | 100       | 192.168.4.21  | 3306     | OFFLINE_SOFT | 0        | 0        | 0      | 0       | 0           | 0       | 0                 | 0               | 0               | 1394       |
        '''

        sql = (f"select b.weight, c.* from stats_mysql_connection_pool c left JOIN runtime_mysql_servers b"
               f" ON  c.hostgroup=b.hostgroup_id and c.srv_host=b.hostname and c.srv_port = b.port order by hostgroup,srv_host desc;")
        table = dbtools.get_resultset_as_table_formatted(self.session,sql)

        return table



    def monitor_get_connection_by_backend(self):
        """

        Returns:

        """

        '''
        select srv_host,srv_port,command,avg(time_ms) time_ms, count(ThreadID) connections from stats_mysql_processlist group by srv_host,srv_port,command;
        +---------------+---------+--------------+-----------------+
        | srv_host      | command | avg(time_ms) | count(ThreadID) |
        +---------------+---------+--------------+-----------------+
        | NULL          | Sleep   | 0.0          | 2               |
        | 192.168.4.205 | Query   | 0.0          | 1               |
        | 192.168.4.231 | Query   | 0.0          | 1               |
        +---------------+---------+--------------+-----------------+
        '''
        sql = f"select srv_host,srv_port,command,avg(time_ms) time_ms, count(ThreadID) connections from stats_mysql_processlist group by srv_host,srv_port,command"
        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table

    def monitor_get_connections_by_user(self):
        """

        Returns:

        """
        '''
        select * from stats_mysql_users;
        +----------+----------------------+--------------------------+
        | username | frontend_connections | frontend_max_connections |
        +----------+----------------------+--------------------------+
        | app_test | 4                    | 10000                    |
        | dba      | 0                    | 10000                    |
        | test     | 0                    | 10000                    |
        | user1    | 0                    | 10000                    |
        | user2    | 0                    | 10000                    |
        +----------+----------------------+--------------------------+
        '''
        sql = f"select * from stats_mysql_users"
        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table



    def monitor_get_mysql_galera_log(self):
        """

        Returns:

        """
        '''
        select * from mysql_server_galera_log  order by time_start_us desc limit 10;
        +---------------+------+------------------+-----------------+-------------------+-----------+------------------------+-------------------+--------------+----------------------+---------------------------------+----------------+-------+
        | hostname      | port | time_start_us    | success_time_us | primary_partition | read_only | wsrep_local_recv_queue | wsrep_local_state | wsrep_desync | wsrep_reject_queries | wsrep_sst_donor_rejects_queries | pxc_maint_mode | error |
        +---------------+------+------------------+-----------------+-------------------+-----------+------------------------+-------------------+--------------+----------------------+---------------------------------+----------------+-------+
        | 192.168.4.21  | 3306 | 1750347275139267 | 22000           | YES               | NO        | 0                      | 4                 | NO           | NO                   | NO                              | NO             | NULL  |
        | 192.168.4.231 | 3306 | 1750347275127157 | 20806           | YES               | NO        | 0                      | 4                 | NO           | NO                   | NO                              | NO             | NULL  |
        | 192.168.4.205 | 3306 | 1750347275124895 | 21230           | YES               | NO        | 0                      | 4                 | NO           | NO                   | NO                              | NO             | NULL  |
        +---------------+------+------------------+-----------------+-------------------+-----------+------------------------+-------------------+--------------+----------------------+---------------------------------+----------------+-------+
        '''
        sql = f"select * from mysql_server_galera_log  order by time_start_us desc limit 10"
        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table

    def monitor_get_query_rules_for_running_PXC_cluster(self):
        """

        Returns:

        """
        '''
        select * from mysql_query_rules order by 1;
        +---------+--------+----------+------------+--------+-------------+------------+------------+--------+---------------------+---------------+----------------------+--------------+---------+-----------------+-----------------------+-----------+--------------------+---------------+-----------+---------+---------+-------+-------------------+----------------+------------------+-----------+--------+-------------+-----------+---------------------+-----+-------+------------+---------+
        | rule_id | active | username | schemaname | flagIN | client_addr | proxy_addr | proxy_port | digest | match_digest        | match_pattern | negate_match_pattern | re_modifiers | flagOUT | replace_pattern | destination_hostgroup | cache_ttl | cache_empty_result | cache_timeout | reconnect | timeout | retries | delay | next_query_flagIN | mirror_flagOUT | mirror_hostgroup | error_msg | OK_msg | sticky_conn | multiplex | gtid_from_hostgroup | log | apply | attributes | comment |
        +---------+--------+----------+------------+--------+-------------+------------+------------+--------+---------------------+---------------+----------------------+--------------+---------+-----------------+-----------------------+-----------+--------------------+---------------+-----------+---------+---------+-------+-------------------+----------------+------------------+-----------+--------+-------------+-----------+---------------------+-----+-------+------------+---------+
        | 1040    | 1      | app_test | NULL       | 0      | NULL        | NULL       | 6033       | NULL   | ^SELECT.*FOR UPDATE | NULL          | 0                    | CASELESS     | NULL    | NULL            | 100                   | NULL      | NULL               | NULL          | NULL      | NULL    | 3       | NULL  | NULL              | NULL           | NULL             | NULL      | NULL   | NULL        | NULL      | NULL                | NULL | 1     |            | NULL    |
        | 1042    | 1      | app_test | NULL       | 0      | NULL        | NULL       | 6033       | NULL   | ^SELECT.*$          | NULL          | 0                    | CASELESS     | NULL    | NULL            | 101                   | NULL      | NULL               | NULL          | NULL      | NULL    | 3       | NULL  | NULL              | NULL           | NULL             | NULL      | NULL   | NULL        | NULL      | NULL                | NULL | 1     |            | NULL    |
        +---------+--------+----------+------------+--------+-------------+------------+------------+--------+---------------------+---------------+----------------------+--------------+---------+-----------------+-----------------------+-----------+--------------------+---------------+-----------+---------+---------+-------+-------------------+----------------+------------------+-----------+--------+-------------+-----------+---------------------+-----+-------+------------+---------+
        '''
        # We limit the query to the relevant Hostgroup only
        ids_str = self._get_hgids_as_string_comma_separated()

        sql = f"select * from mysql_query_rules where destination_hostgroup in ({ids_str}) order by rule_id"
        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table

    def _get_hgids_as_string_comma_separated(self):
        """
        transform a list of Hostgroups into a string comma separated of HG ides only
        Returns: string

        """
        hgids = self.get_active_hostgroups_id()
        ids_str = ""
        for hgid in hgids:
            ids_str += f" {hgid.hg_id},"
        return ids_str[:-1]

    def monitor_query_rules_with_usage_stats(self):
        """

        Returns:

        """
        '''
        SELECT stats.stats_mysql_query_rules.rule_id,active,match_pattern,destination_hostgroup,apply,hits, mysql_query_rules.error_msg AS error_message FROM  stats.stats_mysql_query_rules JOIN mysql_query_rules ON stats_mysql_query_rules.rule_id = mysql_query_rules.rule_id where destination_hostgroup in (100,101)  ORDER BY hits DESC;
        +---------+--------+---------------+-----------------------+-------+---------+---------------+
        | rule_id | active | match_pattern | destination_hostgroup | apply | hits    | error_message |
        +---------+--------+---------------+-----------------------+-------+---------+---------------+
        | 1042    | 1      | NULL          | 101                   | 1     | 1222364 | NULL          |
        | 1040    | 1      | NULL          | 100                   | 1     | 0       | NULL          |
        +---------+--------+---------------+-----------------------+-------+---------+---------------+

        '''
        ids_str = self._get_hgids_as_string_comma_separated()

        sql =(f"SELECT stats.stats_mysql_query_rules.rule_id,active,match_pattern,destination_hostgroup,apply,hits, mysql_query_rules.error_msg AS error_message "
              f"FROM  stats.stats_mysql_query_rules JOIN mysql_query_rules ON stats_mysql_query_rules.rule_id = mysql_query_rules.rule_id "
              f"where destination_hostgroup in ({ids_str})  ORDER BY hits DESC;")

        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table

    def monitor_recently_matched_rules_with_query_digest(self):
        """

        Returns:

        """
        '''
        SELECT hostgroup,digest, digest_text,count_star, first_seen,last_seen FROM stats.stats_mysql_query_digest where hostgroup in (100,101) ORDER BY last_seen DESC LIMIT 10;
        +-----------+--------------------+-----------------------------------------------------------------------------------------------------+------------+------------+------------+
        | hostgroup | digest             | digest_text                                                                                         | count_star | first_seen | last_seen  |
        +-----------+--------------------+-----------------------------------------------------------------------------------------------------+------------+------------+------------+
        | 101       | 0xA49078C76EB6DFD9 | SELECT id,millid,date,continent,active,kwatts_s FROM mill7 WHERE id BETWEEN ? AND ? ORDER BY millid | 8883       | 1750688675 | 1750700705 |
        | 101       | 0xF5EC6EE9EEB86037 | SELECT id,millid,date,continent,active,kwatts_s FROM mill3 WHERE id BETWEEN ? AND ?                 | 9020       | 1750688674 | 1750700705 |
        +-----------+--------------------+-----------------------------------------------------------------------------------------------------+------------+------------+------------+
    
        '''
        ids_str = self._get_hgids_as_string_comma_separated()
        sql = f"SELECT hostgroup,digest, digest_text,count_star, first_seen,last_seen FROM stats.stats_mysql_query_digest where hostgroup in ({ids_str}) ORDER BY last_seen DESC LIMIT 10"

        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table


    def monitor_expensive_queries(self):
        """

        Returns:

        """
        '''
        select hostgroup,schemaname, username, client_address,digest, SUBSTRING(digest_text,1,60), count_star, sum_time, sum_rows_affected,sum_rows_sent from stats.stats_mysql_query_digest order by sum_time desc limit 2;
        +-----------+-----------------+----------+----------------+--------------------+--------------------------------------------------------------+------------+-----------+-------------------+---------------+
        | hostgroup | schemaname      | username | client_address | digest             | SUBSTRING(digest_text,1,60)                                  | count_star | sum_time  | sum_rows_affected | sum_rows_sent |
        +-----------+-----------------+----------+----------------+--------------------+--------------------------------------------------------------+------------+-----------+-------------------+---------------+
        | 101       | windmills_small | app_test |                | 0x43967E4BA20AC4E1 | SELECT id,millid,date,continent,active,kwatts_s FROM mill5 W | 100910     | 220102685 | 0                 | 66599         |
        | 101       | windmills_small | app_test |                | 0x78C8B71D0F1D2974 | SELECT id,millid,date,continent,active,kwatts_s FROM mill10  | 100796     | 219731617 | 0                 | 67089         |
        +-----------+-----------------+----------+----------------+--------------------+--------------------------------------------------------------+------------+-----------+-------------------+---------------+
        '''
        ids_str = self._get_hgids_as_string_comma_separated()
        sql = f"select hostgroup,schemaname, username, client_address,digest, SUBSTRING(digest_text,1,60), count_star, sum_time, sum_rows_affected,sum_rows_sent from stats.stats_mysql_query_digest where hostgroup in ({ids_str}) order by sum_time desc limit 10"

        table = dbtools.get_resultset_as_table_formatted(self.session,sql)
        return table
