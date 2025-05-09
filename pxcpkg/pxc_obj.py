# object module defining all mysql related class tp PXC
import time
import sys
import importlib

from typing import Dict

from common import utils_mb
import common.dbtools as dbtools
from magicbox.mysqlpkg.mysql_obj import Mysql_Node # mysqlpkg.mysql_obj import Mysql_Node


class PXC_Node(Mysql_Node):
    """
    PXC_Node
    
    PCX_Node class extends the Mysql_Node class

    Class implement methods to manage the specifics of a PXC node
    PXC ip and port can be different from the superclass given they reflects the
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

        try:
            if self.variables["wsrep_node_incoming_address"] != None and \
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
        if self.variables !=None \
            and len(self.variables) > 0:
                self.wsrep_provider = utils_mb.parse_label_value_pairs(self.variables["wsrep_provider_options"], ";")
#                print(self.wsrep_provider)

    def is_primary(self):
        if self.status["wsrep_cluster_status"] == "Primary":
            return True
        return False
    
class PXC_Cluster():
    """
    PXC_Cluster 
    
    PXC_Cluster, represent the cluster and provide information about it and methods to manage it 
    
    """
    def __init__(self, pxc_node:PXC_Node):
        self.main_node = pxc_node
        self.name:str 
        self.nodes:Dict[str,PXC_Node] = dict()
        
        if pxc_node.cluster_name != None and len(pxc_node.cluster_name) > 0:
            self.name:str = pxc_node.cluster_name
            self._fill_cluster()
            
        else:
            raise Pxc_Exception("Invalid Cluster name in PXC_node")
        
    
    def _fill_cluster(self):
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
        if not self.main_node.is_primary():
            raise Exception("Cluster is not in Primary state cannot proceed")

        _addresses = self.main_node.get_status_value("wsrep_incoming_addresses").split(",")
        if _addresses != None and len(_addresses) > 0: 
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
    Hostname or IP do not resolve. Current pxc node accessible ip:""" + self.main_node.ip +"""
    Type Q to exit
    Or insert a reachable ip for the given PXC node:"""
                    _reachable_ip = dbtools.ask_shell_for_value(message)
                    if _reachable_ip == "Q":
                        break
                    check = utils_mb.validate_and_check_connection(_reachable_ip,_port,3)
                    
                _uri = self.main_node.user + ":" + self.main_node.password + "@" + _reachable_ip + ":" + _port
     
                _node = PXC_Node(_uri)
                
                if _node is not None:
                    self.nodes[_node.pxc_node_name]=_node
                
            # print(len(self.nodes))
        
        
class Pxc_Exception(Exception):
    pass