# object module defining all mysql related class tp PXC
from io import StringIO
from logging import exception
from operator import truediv
from typing import Dict


# Generic import section [START]
# to allow us to import libs no matter where if in mysql shell or outside
# import importlib
#
# def import_flexible(*module_paths):
#     last_error = None
#     for path in module_paths:
#         try:
#             module = importlib.import_module(path)
#             return module
#         except ImportError as e:
#             last_error = e
#     raise ImportError(
#         f"Could not import module from any of: {', '.join(module_paths)}"
#     ) from last_error
#
#
# mon_lib = import_flexible("magicbox.monitorpkg.monitor", "monitorpkg.monitor")
# proxy_lib = import_flexible("magicbox.proxysqlpkg.proxysql_obj", "proxysqlpkg.proxysql_obj")
# # pxc_lib = import_flexible("magicbox.pxcpkg.pxc_obj", "pxcpkg.pxc_obj")
# dbtools = import_flexible("magicbox.common.dbtool", "common.dbtools")
# utils_mb = import_flexible("magicbox.common.utils_mb", "common.utils_mb")
# mysql_lib = import_flexible("magicbox.mysqlpkg.mysql_obj", "mysqlpkg.mysql_obj")
#
#
# Monitor = getattr(mon_lib, "Monitor")
# ProxySQLCluster = getattr(proxy_lib, "ProxySQLCluster")
# ProxySQLNode = getattr(proxy_lib, "ProxySQLNode")
# ProxyMysqlDataNode = getattr(proxy_lib, "ProxyMysqlDataNode")
# # PXCCluster = getattr(pxc_lib, "PXCCluster")
# # utils_mb = utils_lib
# # dbtools = dbtool_lib
# MysqlNode = getattr(mysql_lib, "MysqlNode")
# ServerId = getattr(proxy_lib, "ServerId")
# Hostgroup = getattr(proxy_lib, "Hostgroup")
# Generic import section [END]

try:
    from common import utils_mb, dbtools
    from mysqlpkg.mysql_obj import MysqlNode # mysqlpkg.mysql_obj import Mysql_Node
    from proxysqlpkg.proxysql_obj import ProxySQLNode, ProxyMysqlDataNode, Hostgroup,ServerId
except ImportError:
    from magicbox.common import utils_mb, dbtools
    from magicbox.mysqlpkg.mysql_obj import MysqlNode # mysqlpkg.mysql_obj import Mysql_Node
    from magicbox.proxysqlpkg.proxysql_obj import ProxySQLNode, ProxyMysqlDataNode, Hostgroup,ServerId
    pass

import logging



class PXCNode(MysqlNode):
    """
    PXC_Node
    
    PCX_Node class extends the Mysql_Node class

    Class implement methods to manage the specifics of a PXC node
    PXC ip and port can be different from the superclass given they reflect the
    information coming from wsrep_node_incoming_address.
    """
    def __init__(self, uri=False):
        super().__init__(uri)
        self.wsrep_provider:Dict[str,str]
        self.pxc_node_name = self.get_variable_value("wsrep_node_name")
        self.cluster_name:str = self.get_variable_value("wsrep_cluster_name")
        self.parse_provider()
        self.pxc_ip:str
        self.pxc_port:str
        self.is_main_node:bool = False



        try:
            if self.variables["wsrep_node_incoming_address"] is not None and \
                len(self.variables["wsrep_node_incoming_address"]) >0:
                    
                if self.variables["wsrep_node_incoming_address"].index(":") > 0:
                    self.pxc_ip   = self.variables["wsrep_node_incoming_address"][:self.variables["wsrep_node_incoming_address"].index(":") ]
                    self.pxc_port = self.variables["wsrep_node_incoming_address"][self.variables["wsrep_node_incoming_address"].index(":") +1: ]
                else:
                    self.pxc_ip = self.variables["wsrep_node_incoming_address"]
                    self.pxc_port = "3306"
        except:
            # sys.tracebacklimit = 1
            raise KeyError("Wrong Key name or wrong resource parsed variables: wsrep_node_incoming_address")

    def parse_provider(self):
        self.refresh_variables()
        if self.variables is not None \
            and len(self.variables) > 0:
                self.wsrep_provider = utils_mb.parse_label_value_pairs(self.variables["wsrep_provider_options"], ";")
#                print(self.wsrep_provider)

    def cluster_is_primary(self):
        self.refresh_status()
        if self.status["wsrep_cluster_status"] == "Primary":
            return True
        return False



class PXCCluster:
    """
    PXC_Cluster 
    
    PXC_Cluster, represent the cluster and provide information about it and methods to manage it 
    
    """

    def __init__(self, pxc_node:PXCNode,addresses:list[str]=None,handler:int = ProxyMysqlDataNode.HANDLER_SCHEDULER):
        self.main_node = pxc_node
        self.name:str 
        self.nodes:Dict[str,PXCNode] = dict()
        self.is_primary:bool = False
        self.proxysql_node:ProxySQLNode = None
        self._handler:str = handler
        self.number_of_writers: int = 1

        if pxc_node.cluster_name is not None and len(pxc_node.cluster_name) > 0:
            self.name:str = pxc_node.cluster_name
            self.discover_nodes(addresses)
            
        else:
            raise Pxc_Exception("Invalid Cluster name in PXC_node")

    @staticmethod
    def connect_cluster(uri:str=None,addresses:list[str]=None):
        """
         This static method will read the main_node to identify the cluster and will set the basic information

         Args:
             - self
             - uri
                 if a valid URI to connect to the MySQL node is pass and the main ode is not present
                 then the main node is created
                 Valid URI form: <user>:[<password>]@<ip>:[<port>]

         Raises:
             - exception for:
                 missing pxc_node
                 pxc_node not in primary state

         Returns
             PXC_cluster
         """
        node = PXCNode(uri)
        return PXCCluster(node,addresses)

    def set_handler(self, handler:int=ProxyMysqlDataNode.HANDLER_SCHEDULER):
        """
        Handler setter. We also sync the handler on the proxysql node if defined
        Args:
            handler: int
        """
        _handler = handler

        if self.proxysql_node is not None:
            self.proxysql_node.handler == self._handler

    def discover_nodes(self,addresses:list[str]=None, force:bool=False):
        """
        This method will read the main_node to identify the other nodes in the cluster
        to discover which nodes it will use the wsrep_incoming_addresseses and assign it to pxc_ip/port
        It will also create the pxc cluster object filled with all the information
        Args: 
            - self
            - uri
                if a valid URI to connect to the MySQL node is pass and the main ode is not present 
                then the main node is created
                Valid URI form: <user>:[<password>]@<ip>:[<port>]

        Raises:
            - exception for:
                missing pxc_node
                pxc_node not in primary state

        Returns         
            PXC_cluster

        Connect to main node and discover the other clusters node using status variable wsrep_incoming_addresses
        1) check if main node is in primary state
        2) check the wsrep_incoming_addresses 
        3) connect to each node (using same credential as for main_node) 
        4) build a PXC cluster object with all nodes in
        """
        if not self.main_node.cluster_is_primary() and not force:
            raise Exception("Cluster is not in Primary state cannot proceed with discovery of nodes. Please check the cluster status and try again. You may want to try with force = true")
        else:
            self.is_primary = True
        if addresses is None or len(addresses) == 0:
            _addresses = self.main_node.get_status_value("wsrep_incoming_addresses").split(",")
        else:
            _addresses = addresses

        if _addresses is not None and len(_addresses) > 0: 
            for address in _addresses:
                _ip = ""
                _port = 0
                # Strip whitespace and skip empty pairs
                address = address.strip()
                if not address:
                    continue
                    
                # Split each address into ip port 
                if ':' in address:
                    _ip, _port = address.split(':', 1)  # Split on first ':' only
                else:
                    # Handle cases where there's no ':' (treat the lack of port as default 3306)
                    _ip = address.strip()
                    _port = "3306"
                
                _uri = self.main_node.user + ":" + self.main_node.password + "@" + _ip + ":" + _port
                
                """ 
                We check if the ip is reachable or not if not we are going to ask though the MySQL Shell
                for a valid IP from user
                """
                _reachable_ip = _ip
                check = utils_mb.validate_and_check_connection(_reachable_ip,_port,3)
                while not check["valid"]:
                    message = """
    Unreachable Host by wsrep_incoming_addresses """ + _ip + """. Invalid IP or hostname.
    Hostname or IP does not resolve. Current pxc node accessible ip:""" + self.main_node.ip +"""
    Type Q to exit
    Or insert a reachable ip for the given PXC node:"""
                    _reachable_ip = dbtools.ask_shell_for_value(message)
                    if _reachable_ip == "Q":
                        break
                    check = utils_mb.validate_and_check_connection(_reachable_ip,_port,3)

                _uri = self.main_node.user + ":" + self.main_node.password + "@" + _reachable_ip + ":" + _port
                _node = PXCNode(_uri)
                
                """
                If node is valid we will add to the cluster plus will do some check and settings
                - if the node has same name of the Main node we will set the node as Main node (Primary/preferred writer)
                """
                if _node is not None:
                    if _node.pxc_node_name == self.main_node.pxc_node_name:
                        _node.is_main_node = True
                    
                    # Finally we add the node to the cluster nodes
                    self.nodes[_node.pxc_node_name]=_node                
            
            # print(len(self.nodes))

    def refresh_pxc_cluster(self,uri:str=None,addresses:list[str]=None, force:bool=False):
        """
        Refresh action force the given cluster to close all connections to the nodes
        Then to reopen them pointing to the given uri if given, otherwise the previously assigned uri will be used

        Args:
            force: force the discovery also if not in Primary state
            addresses: Listo of addresses to use for the discovery of the nodes in case we have a different C class
            uri (_type_): Require a well form uri to connect "user:[pass]@host:port"
                          If Password is not in it will ask it interactively

        Returns:
            Void
        """
        if len(self) > 0 :
            self.close_all()
            self.nodes = None

        if uri is not None:
            self.main_node = None
            self.connect_cluster(uri)
        else:
            uri = self.main_node.uri

        self.discover_nodes(uri,addresses,force)


    def close_connections(self):
        """
        If object contains nodes then we loop, close connection to target
        remove from dict 
        delete it
        """
        if self.nodes is not None and len(self.nodes) > 0:
            for _node in list(self.nodes.values()):
                _node.close_connection()
                del self.nodes[_node.pxc_node_name]    
                
                
    def __len__(self):
        """
        We implement len() here as cluster len == nodes.len()

        Returns:
            int: length of the nodes
        """
        if self.nodes is not None:
            return len(self.nodes)
        return 0


    def connect_proxysql_node(self,uri:str=None):
        """
        This method will add a proxysql node to the cluster
        Then we use this node to setup/manage the PXC cluster nodes in Proxysql

        Args:
            - self
            - uri
                if a valid URI to connect to the MySQL node is pass and the main ode is not present
                then the main node is created
                Valid URI form: <user>:[<password>]@<ip>:[<port>]

        Raises:
            - exception for:
                missing proxysql node


        Returns
            Void
        """
        # from proxysqlpkg.proxysql_obj import ProxySQLNode
        if dbtools.validate_uri(uri):
            self.proxysql_node = ProxySQLNode(uri)
            self.proxysql_node.handler = self._handler
        else:
            logging.warning("Invalid uri: " + uri)


    def add_cluster_to_proxysql(self, hgid:int = 0,force:bool=False):
        """
        Done 1) build ProxySQL node object
        2) verify if servers inside Proxy already exists 
        3) we need to create 2 different set of HG Main hg 100-101 for w-r and 8000 for configuration 
            - verify if hgs already exists 
                - if exists verify if any node inside hgs are the same
                - if not, it means this is a different cluster and we need to build a different one.
                    - change HGs ids and check ... until we found a good set
                - if is the same then no need to add again the nodes
            - create new hgs (by adding the servers)
                - look for Main node and identify which is the correspondent node in Nodes
                    make it primary true 
                - for each node in nodes:
                    - if primary add it to 100/101 and set weight 1000
                        - add to 8000 set weight = 1000
                        - add to 8001 set weight = 1000
                    - if not primary add it to 1001 and set weight 1000
                        - add to 8000 set weight = weight -1
                        - add to 8001 set weight = 1000
                - comment for each server is the name and role 
            - Add users set all users as by defult pointing to the write HG
            - add query rules For 100/101 linked to username. (I am not sure but this is to be consistent with that shit of proxysql-admin)

        """

        self.proxysql_node.set_current_cluster_writer_id(hgid)
        proxy_node = self.proxysql_node
        if proxy_node is None or not proxy_node.session.is_connected():
            return Exception("Proxy node cannot be None, or not connected to the ProxySQL server")
        if len(self) == 0:
            return exception(msg="Nothing to add cluster is empty")
        # 2) Check if nodes are already assigned to any hostgroup in this specific case when adding a full cluster we should not have the nodes in already.
        # 3.1) check if the hostgroup id given is present or not. If present and not force then we raise the message also informing the servers in
        #      if force we will remove the hostgroup and all the nodes in it (also all the nodes in related HGs such as 8000 and 9000)

        # Before running any check, we convert the PXC nodes into ProxySQL Backend servers

        _proxysql_backend = self._transform_pxc_nodes_to_proxysql_backend(hgid)

        check_results = self.check_cluster_on_proxysql(hgid)

        if check_results["code"] > 0:
            # We have node if force is in place we will delete them otherwise will not continue
            logging.info(utils_mb.print_separator("#", ""))

            if check_results["code"] == 1:
                logging.info("Nodes are already present in a different HG id. Reconcile option is possible modifying HG id")

            if check_results["code"] == 2:
                logging.info("Nodes are not present but HG is, no reconcile option is possible change HG id")

            if check_results["code"] == 3:
                logging.info("Nodes and HG are present, reconcile action is possible")


            # logging.warning(utils_mb.print_separator("#", ""))

            # if force:
            #     #delete all
            #     logging.debug("Delete all nodes")
            #     logging.debug("Add all nodes")
            #     pass
            # else:
            #     logging.debug("Exit")
        else:
            # No node is present we can add without problem
            logging.info("No nodes or Host Group present in ProxySQL server")
            logging.info("Add cluster starts")
            for node in _proxysql_backend.values():
                self.proxysql_node.insert_backend(node)

            logging.info("Refresh ProxySQL backend nodes")
            self.proxysql_node.refresh_bakend_nodes()

            logging.info("Add cluster ended")


    def reconcile_cluster(self, hgid):
        """
        Reconcile cluster is checking that the list of given PXC cluster's nodes and ProxySQL backend servers matches in roles and number.
        If we have missed some node we will tage it to insert, as well if there is a node that should not be there we will remove it.
        node_list_from_pxc = self.get_node_list_from_pxc(hgid)

        """
        pxc_node_list = self._transform_pxc_nodes_to_proxysql_backend(hgid)
        self.proxysql_node.reconcile_hostgroup(hgid, pxc_node_list,self.number_of_writers)


    def add_nodes_to_proxy(self, hgid ):
        """
        This method add all the nodes to the ProxySQL, no check or reconciliation is done, so it assume an empty ProxySQL or that you have already done all the relevant checks

        :param hgid:int hgid of the Host Group to add nodes to

        """
        pxc_node_list = self._transform_pxc_nodes_to_proxysql_backend(hgid)
        self.proxysql_node.add_backend_nodes(pxc_node_list)

    def check_cluster_on_proxysql(self,hgid:int=0):
        """
        This function checks if the PXC nodes are already present in the ProxySQL Server
        If the PXC handler is Scheduler it will check for all HGs related to the requested HG
        If handler is internal it will check against the given HG and then mysql_galera_hostgroups

        We cannot check all the different cases so we wil stay stick to the following:
         - Are the nodes present in the given HG?
         - Is the given HG already present in the ProxySQL Server and have different servers?

        Args:
            hgid:

        Returns: _proxysql_backend: list of PXC nodes , int: Code 0 no server or HG found, 1 server(s) found on different hg ,
                2 no server found but HG already in use, 3 Servers and HG found

        """

        proxy_node = self.proxysql_node
        if proxy_node is None or not proxy_node.session.is_connected():
            return Exception("Proxy node cannot be None, or not connected to the ProxySQL server")

        if len(self) == 0:
            return exception(msg="Nothing to add cluster is empty")

        # In case of Scheduler handler we will build the full server list and if auto is in place try to reconcile
        # If auto is not in place we return that we had reconcile
        # if self.handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
        _proxysql_backend = self._transform_pxc_nodes_to_proxysql_backend(hgid)

        # Refresh backend node in proxysql to be sure we get the last scenario
        proxy_node.refresh_bakend_nodes()

        check = proxy_node.check_nodes_if_existing(_proxysql_backend, hgid)
        servers = check["servers"]
        check_hg = check["hg"]

        if servers and not check_hg:
            return {"list": _proxysql_backend, "code": 1}

        elif check_hg and not servers:
            return {"list": _proxysql_backend, "code": 2}

        elif check_hg and servers:
            return {"list": _proxysql_backend, "code": 3}

        return {"list": _proxysql_backend, "code": 0}

        # else:
        #     pass


    def _transform_pxc_nodes_to_proxysql_backend(self, hgid:int = 0):
        """
        This internal method has the logic to configure the PXC backend nodes following the rules:
        - we have 4 Hostgroups:
            Write
            Read
            Catalog Write
            Catalog Read
        - Node matching Is_main_node is the Preferred Primary
        - If single writer 
            Preferred writer will have higher weight (1000) and the others will have last_weight_value -1
            Only Preferred writer will be assigned to the active Write HG (ie 100) but all nodes will be assign to configuration nodes 8000 + hgid
        - If multiple writers
            All the nodes will have weight 1000 all nodes will be assigned to configuration group

        Returns:

        """

        # This is valid if we use the scheduler to handle the cluster
        # In case not we need to check mmysql_galera_hostgroups

        _proxysql_backend:Dict[ServerId,ProxyMysqlDataNode] = {}
        # If we have more than one writer then we loop and add, otherwise we check for the main node and by default we set that as writer.

        counter = 0
        for _node in self.nodes.values():
            _p_node_bkend_w:ProxyMysqlDataNode=None

            # If we have more than one writer we identify main node by ip + port
            if _node.ip == self.main_node.ip and _node.port == self.main_node.port:
                _p_node_bkend_w = ProxyMysqlDataNode(_node, hgid, "w")
                _p_node_bkend_w.main_writer = True

            if counter < self.number_of_writers -1 and (_node.ip + ":" + str(_node.port)) != (self.main_node.ip + ":" +  str(self.main_node.port)):
                _p_node_bkend_w = ProxyMysqlDataNode(_node, hgid, "w")
                counter += 1

            _p_node_bkend_r = ProxyMysqlDataNode(_node, hgid + 1, "r")

            # We set the additional HG only if using the scheduler otherwise we will use the internal table
            if self._handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
                _p_node_bkend_cw = ProxyMysqlDataNode(_node, hgid + 8000, "c")
                _p_node_bkend_cr = ProxyMysqlDataNode(_node, hgid + 8001, "c")

            if _p_node_bkend_w is not None:
                _proxysql_backend[_p_node_bkend_w.id] = _p_node_bkend_w

            _proxysql_backend[_p_node_bkend_r.id] = _p_node_bkend_r

            # We set the additional HG only if using the scheduler otherwise we will use the internal table
            if self._handler == ProxyMysqlDataNode.HANDLER_SCHEDULER:
                _proxysql_backend[_p_node_bkend_cw.id] = _p_node_bkend_cw
                _proxysql_backend[_p_node_bkend_cr.id] = _p_node_bkend_cr

        return _proxysql_backend

    def get_hostgroup_ids_by_handler_support(self,hgid:int=0):
        """
        We return a different list of hostgroup id according to the Handler

        :param hgid:int Hostgroup Id define by user

        :return: list of hostgroup id
        """

        ids = Hostgroup.get_hostgroup_ids_by_handler_support(hgid, self._handler)
        return ids

    def get_node_by_pxc_name(self,pxc_node_name:str=None):
        """
        Return a node that match the given PXC naode name

        :param pxc_node_name: name of the pxc node, mandatory
        :return: pxc node
        """
        if pxc_node_name is None:
            return None

        for pxc in self.nodes.values():
            if pxc_node_name == pxc.pxc_node_name:
                return pxc

    def get_Proxysql_backend_by_pxc_name(self,pxc_node_name:str=None,hgid:int=0):
        """
        Return the Proxysql backend that match the given PXC by name

        :param pxc_node_name: name of the pxc node, mandatory
        :return: proxysql backend
        """
        if pxc_node_name is None:
            return None

        pxc_node = self.get_node_by_pxc_name(pxc_node_name)
        if pxc_node is None:
            return None

        for backend in self.proxysql_node.mysql_nodes.values():
            if backend.id.server_ip == pxc_node.ip and str(backend.id.server_port) == pxc_node.port and backend.id.hg_id == hgid:
                return backend

    def set_handler(self,handler:int = ProxyMysqlDataNode.HANDLER_SCHEDULER):
        self._handler = handler

    def put_cluster_offline(self):
        _node_list = self._transform_pxc_nodes_to_proxysql_backend(self.proxysql_node.get_current_cluster_writer_id())
        self.proxysql_node.change_backend_nodes_status(_node_list,"OFFLINE_SOFT",True)

    def put_cluster_onine(self):
        _node_list = self._transform_pxc_nodes_to_proxysql_backend(self.proxysql_node.get_current_cluster_writer_id())
        self.proxysql_node.change_backend_nodes_status(_node_list,"ONLINE",True)



class Pxc_Exception(Exception):
    pass


