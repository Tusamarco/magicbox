"""
    ProxySQL object module defining all proxysql related class
"""
import logging
from io import StringIO
from typing import Dict
from common import utils_mb
from mysqlpkg.mysql_obj import MysqlNode

import json
import common.dbtools as dbtools


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

    """

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

        # Match is not supported
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
        self.status:str = ""
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

   def to_json(self):
       data:dict[str,str] =dict()
       id:dict[str,str] =dict()
       id["hg_id"] = self.id.hg_id
       id["server_ip"]=self.id.server_ip
       id["server_port"]=self.id.server_port
       data["id"] = id
       data["gtid_port"] = self.gtid_port
       data["status"] = self.status
       data["weight"] = self.weight
       data["compression"] = self.compression
       data["max_connections"] = self.max_connections
       data["max_replication_lag"] = self.max_replication_lag
       data["use_ssl"] = self.use_ssl
       data["max_latency_ms"] = self.max_latency_ms
       data["comment"] = self.comment
       return data

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
        self._load_back_end_nodes()

    def _load_back_end_nodes(self):
        """
        This is an action at __init__
        We load all the backend nodes for processing.
        At this stage we do not care if they have a PXC node in the background or not
        We also do not care if we load all the nodes and they are not relevant because we still do not know.
        Once we have reconciled with the PXC cluster, then only the node currently available for that cluster will be part of the visible backend nodes

        Returns: Void

        """
        sql = ("select * from runtime_mysql_servers")
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
        for server in self.mysql_nodes.keys():

            if server.hg_id == hgid:
                hg_exists = True

            for node in incoming_bck_nodes.keys():
                if node.server_ip == server.server_ip and node.server_port == server.server_port and node.hg_id == server.hg_id:
                    already_present.append(f"Node {node.server_ip} Port: {node.server_port} hostgroup_id: {node.hg_id}")

                    ## NOT HERE here we just check no action
                    # # IF Force is True we flag the node in the Proxysql Server for deletion
                    # self.mysql_nodes[server].action_list.append(ProxyMysqlDataNode.ACTION_DELETE)
                    # # At the same time we mark the node in the incoming list for INSERT
                    # incoming_bck_nodes[node].action_list.append(ProxyMysqlDataNode.ACTION_INSERT)
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
        

    def reconcile_hostgroup(self,hgid:int=0,pxc_node_list:dict=None,number_of_writers:int=0,pxc_handler:int=1):
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

        # First we process the writers
        if number_of_writers==0:
            number_of_writers = 1

        # We get the servers from both sides related to writer HGs (hgid and hgid + 8000)
        # First we check for hgid, if the node are not the same and not in hgid + 8000, then we have an issue and cannot reconcile.
        # Then we need to compare the list of server in HG + 8000 and check if the same, if not we adapt Proxysql server to PXC
        # Adding or deleting

        # Get the list of nodes related to the writer
        _proxysql_backend_servers = None
        _proxysql_backend_servers = self.get_nodes_by_hostgroups([hgid, hgid + 8000])

        count_proxysql_writers = self._get_number_of_backend_nodes_by_hgid(hgid)
        count_proxysql_config_writers = self._get_number_of_backend_nodes_by_hgid(hgid + 8000)
        main_writer_node:ProxyMysqlDataNode = self._get_main_node_from_pxc(pxc_node_list)

        pxc_writer_is_in = False
        pxc_writer_config_is_in = False

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
                        nodes_to_put_offline_soft = self.get_nodes_by_hostgroups([hgid])
                        for node in nodes_to_put_offline_soft.values():
                            self.move_backend_to_offline_soft(node)

                    #  then we add the writer if missed
                    self.insert_backend(pxc_node)

            # let us now check the 8000 group
            if pxc_node.id.hg_id == (hgid + 8000):
                nodes_to_remove = self.get_nodes_by_hostgroups([hgid + 8000])
                if not proxy_config_purged_w:
                    proxy_config_purged_w = True
                    for node in nodes_to_remove.values():
                        self.delete_backend(node)

                self.insert_backend(pxc_node)

            # let us now check the hgid + 1 (reader) group
            if pxc_node.id.hg_id == (hgid + 1):
                nodes_to_remove = self.get_nodes_by_hostgroups([hgid + 1])
                if not proxy_purged_r:
                    proxy_purged_r = True
                    for node in nodes_to_remove.values():
                        self.delete_backend(node)

                self.insert_backend(pxc_node)

            # let us now check the 8000 (reader) group
            if pxc_node.id.hg_id == (hgid + 8001):
                nodes_to_remove = self.get_nodes_by_hostgroups([hgid + 8001])
                if not proxy_config_purged_r:
                    proxy_config_purged_r = True
                    for node in nodes_to_remove.values():
                        self.delete_backend(node)

                self.insert_backend(pxc_node)

        self.apply_backend()

        # Now If we use native galera support
        pass

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
                   f"gtid_port={node.gtid_port},status={node.status},weight={node.weight},compression={node.compression}," +
                   f"max_replication_lag={node.max_replication_lag},max_latency_ms={node.max_latency_ms}" +
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
                return json.dumps(node.to_json())

    def config_nodes(self, json_text:str=None,apply:bool=False):
        """
        The method will configure the nodes as for the Json provided
        :param json_text:JSON
        :param apply:Boolean if true changes will be applied directly, false otherwise you need to explicitly apply the changes to the ProxySQL instance

        :return void
        """
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

                    if apply:
                        self.apply_backend()
                except Exception as e:
                    logging.error(e)

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
            buffer.write(json.dumps(server.to_json(), indent=4, sort_keys=True) + ",\n")

        json_text_body = buffer.getvalue()
        buffer.close()
        return json_text_head + json_text_body + json_text_tail


